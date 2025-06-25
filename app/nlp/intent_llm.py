import google.generativeai as genai
import json
import re
from dotenv import load_dotenv

model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

async def detectar_intencion_llm(texto_usuario: str) -> dict:
    prompt = f"""
Analizá el siguiente mensaje y devolvé una intención en formato JSON.

Sólo usá una de las siguientes intenciones:
- "estado_actual": cuando pregunta cómo está la planta ahora
- "consulta_estado_pasado": si pregunta por el estado en un momento anterior
- "consulta_riego": si pregunta por si necesita agua o si debe regarse
- "cuidados_planta": si pide consejos o cuidados
- "fuera_de_dominio": si el tema no tiene que ver con plantas, jardinería o ambiente
- "desconocido": si no se puede determinar la intención

ES IMPORTANTE QUE EL USUARIO PUEDA INTERACTUAR CON LA PLANTA, NO CON UN OBJETO INANIMADO. Por ejemplo, si dice "cómo está mi auto", eso es fuera de dominio. PERO SI DICE COMO ESTAS? ESO NO ES FUERA DE DOMINIO. EL FUERA DE DOMINIO ES EN CASOS QUE ES MUY CLARO

Además, si detectás un tiempo en la pregunta (por ejemplo "hace 30 minutos", "hace 1 hora y 15 minutos", "hace medio mes"), devolvelo parseado en dos formas:

1. Como texto libre en la clave "tiempo_original" con el texto exacto detectado.

2. Como número total de minutos en la clave "tiempo_minutos", aproximado.

Ejemplo de salida:

{{
  "intencion": "consulta_estado_pasado",
  "tiempo_original": "1 hora 15 minutos",
  "tiempo_minutos": 75
}}

Si no detectás tiempo, no incluyas esas claves.

Ejemplo de salida:
{{
  "intencion": "consulta_estado_pasado",
  "tiempo": "1 hora 15 minutos"
}}

Mensaje del usuario:
"{texto_usuario}"

Solo devolvé el JSON. No expliques nada.
    """

    try:
        respuesta = model.generate_content(prompt)
        text = respuesta.text.strip()

        # Extraer solo la parte entre llaves { ... } usando regex
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            json_text = match.group(0)
            print("JSON detectado:", json_text)
            return json.loads(json_text)
        else:
            print("No se encontró JSON en la respuesta de Gemini.")
            return {"intencion": "desconocido"}
    except Exception as e:
        print("Error al detectar intención con LLM:", e)
        return {"intencion": "desconocido"}
     
