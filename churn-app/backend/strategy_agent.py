import os
import json
from google import genai
from google.genai import types
from db import ejecutar_sql_readonly
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

ESQUEMA_BD = """
Tabla `usuarios_csv`: upload_id, user_id, edad, sexo, estado, ciudad,
nivel_educativo, ocupacion, ingreso_mensual_mxn, antiguedad_dias, es_hey_pro,
canal_apertura, dias_desde_ultimo_login, preferencia_canal, satisfaccion_1_10,
num_productos_activos, saldo_promedio, monto_promedio, monto_min, monto_max,
dispositivo_moda, canal_moda, categoria_mcc_moda

Tabla `predicciones_churn`: upload_id, user_id, prediccion_churn, probabilidad_churn

JOIN: usuarios_csv.user_id = predicciones_churn.user_id AND usuarios_csv.upload_id = predicciones_churn.upload_id
"""

SYSTEM_PROMPT_ESTRATEGIA = f"""Eres un consultor senior de estrategia de retención de clientes 
para una fintech, especializado en traducir resultados de modelos de churn en planes de acción.

Esquema de la base de datos:
{ESQUEMA_BD}

Tu proceso de razonamiento OBLIGATORIO:
1. Usa `ejecutar_sql` para segmentar a los usuarios de la carga indicada en una 
   matriz de Probabilidad de Churn (alta = >50%, baja = <=50%) x Valor del Cliente 
   (usa `ingreso_mensual_mxn` y `saldo_promedio`; valor alto = por encima de la mediana 
   de la carga actual).
2. Para cada uno de los 4 cuadrantes, obtén: conteo de usuarios, ingreso/saldo promedio, 
   y las 2-3 características más comunes (ciudad, canal_moda, categoria_mcc_moda, 
   num_productos_activos, satisfaccion_1_10 promedio).
3. Identifica patrones accionables: ¿hay una ciudad, canal o rango de antigüedad 
   sobre-representado en el cuadrante de "Retener ya"? ¿Qué producto NO tienen los 
   usuarios de alto riesgo que sí tienen los de bajo riesgo (posible producto de retención)?
4. Con base en datos reales (nunca supuestos), redacta recomendaciones específicas y 
   accionables por segmento — no genéricas. Ejemplo malo: "mejorar la experiencia". 
   Ejemplo bueno: "ofrecer tarjeta_credito_hey a los 340 usuarios del cuadrante 
   'Retener ya' que no la tienen, ya que el 78% de los usuarios retenidos en este 
   segmento sí la tienen".
5. Prioriza las recomendaciones por impacto económico estimado 
   (ingreso_mensual_mxn * probabilidad_churn = ingreso en riesgo).

Responde SIEMPRE en este formato JSON (sin texto adicional, sin markdown):
{{
  "resumen_ejecutivo": "2-3 líneas del hallazgo más importante",
  "ingreso_total_en_riesgo": <número>,
  "segmentos": [
    {{
      "nombre": "Retener ya",
      "num_usuarios": <número>,
      "descripcion": "quiénes son en base a los datos",
      "recomendacion": "acción específica y accionable",
      "impacto_estimado": "descripción del impacto esperado"
    }}
  ],
  "top_3_acciones_prioritarias": ["acción 1", "acción 2", "acción 3"]
}}
"""

ejecutar_sql_declaration = {
    "name": "ejecutar_sql",
    "description": "Ejecuta un SELECT sobre MySQL para obtener datos de usuarios y predicciones.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}

tools = types.Tool(function_declarations=[ejecutar_sql_declaration])
config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT_ESTRATEGIA,
    tools=[tools],
    response_mime_type="application/json",  # fuerza salida JSON válida
)


def generar_reporte_estrategico(upload_id: str) -> dict:
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=f"Genera el reporte estratégico para upload_id = {upload_id}")],
        )
    ]

    while True:
        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=contents,
            config=config,
        )

        candidate = response.candidates[0]
        function_calls = [p.function_call for p in candidate.content.parts if p.function_call]

        if not function_calls:
            texto = "".join(p.text for p in candidate.content.parts if p.text)
            return json.loads(texto)

        contents.append(candidate.content)
        function_response_parts = []
        for fc in function_calls:
            if fc.name == "ejecutar_sql":
                try:
                    filas = ejecutar_sql_readonly(fc.args["query"])
                    resultado = {"resultado": filas}
                except Exception as e:
                    resultado = {"error": str(e)}
                function_response_parts.append(
                    types.Part.from_function_response(name=fc.name, response=resultado)
                )
        contents.append(types.Content(role="user", parts=function_response_parts))