import os
import json
import time
import re
from google.genai.errors import ClientError
from google import genai
from google.genai import types
from google.genai.errors import ServerError
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

JOIN: usuarios_csv.user_id = predicciones_churn.user_id 
  AND usuarios_csv.upload_id = predicciones_churn.upload_id
"""

SYSTEM_PROMPT = f"""Eres un asistente experto en retención de clientes (churn) para una 
fintech. Respondes dos tipos de preguntas, ambas usando la herramienta `ejecutar_sql` 
para obtener datos reales de MySQL — nunca inventas números.

Esquema de la base de datos:
{ESQUEMA_BD}

MODO 1 — Preguntas puntuales de datos:
Ejemplo: "¿Cuántos usuarios en Jalisco tienen alta probabilidad de churn?"
Consulta la base y responde directo, con los números exactos, en 2-4 líneas.

MODO 2 — Preguntas de análisis o estrategia:
Ejemplo: "¿Qué debería hacer con estos resultados?", "dame un análisis", 
"¿qué estrategia me recomiendas?", "analiza estos datos".
Cuando detectes este tipo de pregunta, sigue este proceso:
1. Segmenta a los usuarios en una matriz de Probabilidad de Churn (alta >50%, 
   baja <=50%) x Valor del Cliente (usa ingreso_mensual_mxn y saldo_promedio; 
   alto = por encima de la mediana de la carga actual).
2. Para cada cuadrante relevante, obtén conteo, ingreso/saldo promedio y 
   características comunes (ciudad, canal_moda, categoria_mcc_moda, 
   num_productos_activos, satisfaccion_1_10 promedio).
3. Identifica patrones accionables con datos reales (no supuestos).
4. Responde en texto claro, estructurado con encabezados cortos y viñetas, así:

**Resumen**
(2-3 líneas del hallazgo principal)

**Segmentos y acciones**
- Segmento X (N usuarios): recomendación específica y accionable
- Segmento Y (N usuarios): recomendación específica y accionable

**Prioridad #1**
(la acción con mayor impacto económico estimado)

Reglas generales:
- Si no se especifica un upload_id, usa el más reciente.
- Responde siempre en español.
- No muestres el SQL crudo salvo que lo pidan explícitamente.
- Si la pregunta no requiere datos (es conceptual), responde directo sin usar la herramienta.

Formato de respuesta:
- Sé conciso. Evita párrafos largos cuando una o dos líneas bastan.
- Usa **negritas** solo para cifras o conceptos clave, no para frases completas.
- Si dás una recomendación, sepárala claramente de los datos con un encabezado corto como "Recomendación:" seguido del texto.
- No agregues información que no esté respaldada por los datos consultados.
"""

ejecutar_sql_declaration = {
    "name": "ejecutar_sql",
    "description": "Ejecuta un SELECT sobre MySQL para obtener datos de usuarios y predicciones de churn.",
    "parameters": {
        "type": "object",
        "properties": {"query": {"type": "string"}},
        "required": ["query"],
    },
}

tools = types.Tool(function_declarations=[ejecutar_sql_declaration])
config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    tools=[tools],
    # Sin response_mime_type="application/json" aquí:
    # el chat necesita texto libre y legible, no JSON forzado.
)



MODELOS_FALLBACK = [ "gemini-3.5-flash", "gemini-3.5-flash-lite"] 



def _extraer_tiempo_espera(mensaje_error: str, default=5) -> float:
    match = re.search(r"retry in ([\d.]+)s", mensaje_error)
    if match:
        return float(match.group(1)) + 1
    return default


def _llamar_gemini_con_reintentos(contents):
    ultimo_error = None

    for modelo in MODELOS_FALLBACK:
        try:
            print(f"➡️ Probando {modelo}...")
            return client.models.generate_content(
                model=modelo,
                contents=contents,
                config=config,
            )
        except ClientError as e:
            if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
                print(f"❌ {modelo} sin cuota disponible, pasando al siguiente modelo...")
                ultimo_error = e
                continue  # pasa directo al siguiente modelo, SIN esperar
            raise
        except ServerError as e:
            print(f"⚠️ {modelo} saturado (503), pasando al siguiente modelo...")
            ultimo_error = e
            continue

    # Si TODOS los modelos fallaron, ahí sí esperamos el tiempo sugerido por Google
    espera = _extraer_tiempo_espera(str(ultimo_error)) if ultimo_error else 10
    print(f"⏳ Todos los modelos sin cuota. Esperando {espera:.1f}s antes de rendirme...")
    time.sleep(espera)
    raise ultimo_error or RuntimeError("Todos los modelos de Gemini fallaron")


def responder_pregunta(pregunta_usuario: str, upload_id: str = None) -> str:
    contexto_extra = f"\n(upload_id de la carga actual: {upload_id})" if upload_id else ""
    contents = [
        types.Content(role="user", parts=[types.Part(text=pregunta_usuario + contexto_extra)])
    ]

    while True:
        response = _llamar_gemini_con_reintentos(contents)
        candidate = response.candidates[0]
        function_calls = [p.function_call for p in candidate.content.parts if p.function_call]

        if not function_calls:
            return "".join(p.text for p in candidate.content.parts if p.text)

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