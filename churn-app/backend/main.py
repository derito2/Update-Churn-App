import io
import uuid
import traceback
import joblib
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from db import guardar_csv_y_predicciones
from chat_agent import responder_pregunta
from strategy_agent import generar_reporte_estrategico

from collections import defaultdict
from db import ejecutar_sql_readonly, readonly_engine



app = FastAPI(title="Churn Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

model = joblib.load("models/catboost_churn_model.pkl")
feature_cols = joblib.load("models/feature_columns.pkl")
cat_features = joblib.load("models/cat_features.pkl")

# Solo estas columnas se muestran en pantalla (la BD guarda todas las demás)
COLUMNAS_TABLA = [
    "user_id",
    "sexo",
    "ciudad",
    "prediccion_churn",
    "probabilidad_churn",
]


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un CSV")

    contenido = await file.read()
    df = pd.read_csv(io.BytesIO(contenido))

    faltantes = [c for c in feature_cols if c not in df.columns]
    if faltantes:
        raise HTTPException(status_code=400, detail=f"Faltan columnas: {faltantes}")

    X = df[feature_cols].copy()
    for col in cat_features:
        X[col] = X[col].astype(str).fillna("desconocido")

    proba = model.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)

    df["probabilidad_churn"] = (proba * 100).round(1)
    df["prediccion_churn"] = pred
    df["prediccion_churn"] = df["prediccion_churn"].map({1: "Sí", 0: "No"})

    # --- Guardar en MySQL, con manejo de error explícito ---
    upload_id = str(uuid.uuid4())
    try:
        guardar_csv_y_predicciones(df, upload_id)
        print(f"✅ Guardado exitoso en MySQL. upload_id = {upload_id}")
    except Exception as e:
        print("❌ ERROR guardando en MySQL:")
        traceback.print_exc()  # muestra el error completo, no solo el mensaje

    # --- KPIs ---
    total_usuarios = len(df)
    tasa_churn = round((pred.sum() / total_usuarios) * 100, 1) if total_usuarios else 0
    satisfaccion_prom = round(df["satisfaccion_1_10"].mean(), 1) if "satisfaccion_1_10" in df else None
    ingreso_prom = round(df["ingreso_mensual_mxn"].mean(), 0) if "ingreso_mensual_mxn" in df else None

    kpis = {
        "total_usuarios": int(total_usuarios),
        "tasa_churn_predicha": tasa_churn,
        "satisfaccion_promedio": satisfaccion_prom,
        "ingreso_promedio": ingreso_prom,
    }

    # --- Tabla filtrada a solo las columnas pedidas ---
    columnas_disponibles = [c for c in COLUMNAS_TABLA if c in df.columns]
    resultados = df[columnas_disponibles].to_dict(orient="records")

    return {"kpis": kpis, "resultados": resultados, "upload_id": upload_id}


class ChatRequest(BaseModel):
    pregunta: str
    upload_id: str | None = None


@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        respuesta = responder_pregunta(req.pregunta, req.upload_id)
        return {"respuesta": respuesta}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/estrategia/{upload_id}")
async def estrategia(upload_id: str):
    try:
        reporte = generar_reporte_estrategico(upload_id)
        return reporte
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@app.get("/churn-por-estado-sexo/{upload_id}")
async def churn_por_estado_sexo(upload_id: str):
    query = f"""
        SELECT u.estado, u.sexo, COUNT(*) AS total
        FROM usuarios_csv u
        JOIN predicciones_churn p 
          ON u.user_id = p.user_id AND u.upload_id = p.upload_id
        WHERE u.upload_id = '{upload_id}' AND p.prediccion_churn = 'Sí'
        GROUP BY u.estado, u.sexo
    """
    try:
        filas = ejecutar_sql_readonly(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    totales_por_estado = defaultdict(int)
    for f in filas:
        totales_por_estado[f["estado"]] += f["total"]

    top5_estados = sorted(totales_por_estado, key=totales_por_estado.get, reverse=True)[:5]
    sexos = sorted(set(f["sexo"] for f in filas))

    resultado = []
    for estado in top5_estados:
        fila = {"estado": estado}
        for s in sexos:
            fila[s] = 0
        resultado.append(fila)

    mapa = {r["estado"]: r for r in resultado}
    for f in filas:
        if f["estado"] in mapa:
            mapa[f["estado"]][f["sexo"]] = f["total"]

    return {"datos": resultado, "sexos": sexos}


@app.get("/correlaciones/{upload_id}")
async def correlaciones(upload_id: str):
    query = f"""
        SELECT u.edad, u.ingreso_mensual_mxn, u.antiguedad_dias, 
               u.dias_desde_ultimo_login, u.satisfaccion_1_10, 
               u.num_productos_activos, u.saldo_promedio, 
               u.monto_promedio, p.probabilidad_churn
        FROM usuarios_csv u
        JOIN predicciones_churn p 
          ON u.user_id = p.user_id AND u.upload_id = p.upload_id
        WHERE u.upload_id = '{upload_id}'
    """
    try:
        df = pd.read_sql(query, readonly_engine)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if df.empty or len(df) < 3:
        raise HTTPException(status_code=400, detail="No hay suficientes datos para calcular correlaciones")

    serie = df.corr(numeric_only=True)["probabilidad_churn"].drop("probabilidad_churn")
    serie = serie.reindex(serie.abs().sort_values(ascending=False).index)

    nombres_legibles = {
        "edad": "Edad",
        "ingreso_mensual_mxn": "Ingreso mensual",
        "antiguedad_dias": "Antigüedad (días)",
        "dias_desde_ultimo_login": "Días desde último login",
        "satisfaccion_1_10": "Satisfacción",
        "num_productos_activos": "Productos activos",
        "saldo_promedio": "Saldo promedio",
        "monto_promedio": "Monto promedio",
    }

    resultado = [
        {"variable": nombres_legibles.get(col, col), "correlacion": round(float(val), 3)}
        for col, val in serie.items()
        if pd.notna(val)
    ]

    return {"correlaciones": resultado}