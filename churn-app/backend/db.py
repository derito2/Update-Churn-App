import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from decimal import Decimal
from datetime import date, datetime

load_dotenv()

# Conexión con permisos de escritura (usada por /predict para insertar)
WRITE_URL = (
    f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
)
write_engine = create_engine(WRITE_URL, pool_pre_ping=True)

# Conexión de solo lectura (usada por el agente SQL)
READONLY_URL = (
    f"mysql+pymysql://{os.getenv('MYSQL_READONLY_USER')}:{os.getenv('MYSQL_READONLY_PASSWORD')}"
    f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT')}/{os.getenv('MYSQL_DB')}"
)
readonly_engine = create_engine(READONLY_URL, pool_pre_ping=True)


def guardar_csv_y_predicciones(df, upload_id: str):
    """Guarda el CSV subido y las predicciones en sus respectivas tablas."""
    columnas_csv = [
        "user_id", "edad", "sexo", "estado", "ciudad", "nivel_educativo",
        "ocupacion", "ingreso_mensual_mxn", "antiguedad_dias", "es_hey_pro",
        "canal_apertura", "dias_desde_ultimo_login", "preferencia_canal",
        "satisfaccion_1_10", "num_productos_activos", "saldo_promedio",
        "monto_promedio", "monto_min", "monto_max", "dispositivo_moda",
        "canal_moda", "categoria_mcc_moda",
    ]
    df_csv = df[[c for c in columnas_csv if c in df.columns]].copy()
    df_csv["upload_id"] = upload_id
    df_csv.to_sql("usuarios_csv", write_engine, if_exists="append", index=False)

    df_pred = df[["user_id", "prediccion_churn", "probabilidad_churn"]].copy()
    df_pred["upload_id"] = upload_id
    df_pred.to_sql("predicciones_churn", write_engine, if_exists="append", index=False)


def _sanear_valor(valor):
    """Convierte tipos de MySQL/SQLAlchemy no serializables a JSON en tipos nativos."""
    if isinstance(valor, Decimal):
        return float(valor)
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, bytes):
        return valor.decode("utf-8", errors="ignore")
    return valor


def ejecutar_sql_readonly(query: str):
    """Ejecuta una consulta SELECT de solo lectura y devuelve los resultados."""
    query_limpia = query.strip().rstrip(";")
    if not query_limpia.lower().startswith("select"):
        raise ValueError("Solo se permiten consultas SELECT.")

    with readonly_engine.connect() as conn:
        result = conn.execute(text(query_limpia))
        columnas = list(result.keys())
        filas = [
            {col: _sanear_valor(val) for col, val in zip(columnas, row)}
            for row in result.fetchall()
        ]
    return filas