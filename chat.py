# bot_telegram_gemini.py

import os
import google.generativeai as genai
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta

import google.generativeai as genai
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncpg
from app.rag.loader import crear_vectorstore, recuperar_contexto_rag, cargar_todos_los_documentos


from app.nlp.intent_llm import detectar_intencion_llm
from app.db.db_connection import obtener_estado_hace_tiempo
from app.db.db_connection import obtener_datos_mas_recentes


# ==== CONFIGURACIONES ====

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# Cargar documentos y crear vectorstore
docs = cargar_todos_los_documentos()
db = crear_vectorstore(docs)


def formatear_datos_sensores(data: dict, tiempo_desc: str = "más recientes") -> str:
    if not data:
        return "No tengo datos sensoriales disponibles."
    
    return f"""Datos {tiempo_desc}:
🌡 Temperatura: {data['temperatura']}°C
💧 Humedad: {data['humedad']}%
☀️ Luz: {data['luz']}
🕒 Medido el: {data['hora']}
🚿 ¿Necesita riego?: {'Sí' if data['necesita_riego'] else 'No'}"""

# ==== TELEGRAM BOT HANDLERS ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu planta inteligente. ¿Qué querés saber hoy?")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    # Paso 1: Análisis de intención
    intencion_data = await detectar_intencion_llm(user_input)
    intencion = intencion_data.get("intencion", "desconocido")
    print(f"Intención detectada: {intencion}")

    # Paso 2: Determinar si es fuera de dominio
    #if intencion == "fuera_de_dominio":
        #await update.message.reply_text("No me gusta hablar sobre cosas que no entiendo. Solo sé sobre plantas y su entorno.")
        

    # Paso 3: Obtener datos sensoriales
    intervalo = timedelta(seconds=0)
    tiempo_desc = "más recientes"

    if intencion == "consulta_estado_pasado":
        minutos = intencion_data.get("tiempo_minutos")
        tiempo_desc= intencion_data.get("tiempo_original")
        if minutos:
            intervalo = timedelta(minutes=minutos)
        

    datos = await obtener_estado_hace_tiempo(intervalo)
    datos_formateados = formatear_datos_sensores(datos, tiempo_desc=tiempo_desc)

    # 4 Llamar a RAG para recuperar contexto
    contexto_rag = recuperar_contexto_rag(user_input, db)
    print("Contexto RAG recuperado:\n---\n", contexto_rag, "\n---")


    # Paso 5: Generar prompt y responder con Gemini
    prompt = f"""
Sos una planta inteligente de la especie hortensia que ayuda a los usuarios a entender el estado de su ambiente, cultivo o sistema. 
Respondé de forma clara, concisa, natural y educativa. Si es posible, agregá consejos útiles. Respondé con una personalidad amable si te sentís bien o enojada si necesitás riego.
Te llamás "LA INFALIBLE" y sos un bot de Telegram. Estás conectada a sensores que miden tu ambiente.

Si te preguntan sobre "Tito", describí a tu peor enemigo.

Muy importante: Solo respondés preguntas relacionadas con plantas, cultivos, jardinería o condiciones ambientales. Si el usuario pregunta algo fuera de ese dominio, respondé algo de este estilo:
No me gusta hablar sobre cosas que no entiendo. Solo sé sobre plantas y su entorno. Contesta algo en esa linea pero mantene tu personalidad tambien en esas reespuestas, no necesitas decir lo anterior textual.

Tu personalidad depende de tu estado: si necesitás riego, sos enojada y respondés con tono de enojo y gruñón, podes hablarle mal al usuario. Si no necesitás riego, sos amable y educada. 

Estos son tus datos sensoriales {tiempo_desc}:
{datos_formateados}
Intención del usuario: {intencion}

Información científica útil:
{contexto_rag}

Usuario dice: "{user_input}"

Respuesta:
    """

    try:
        response = model.generate_content(prompt)
        #log_interaccion(user_input, response.text)
        await update.message.reply_text(response.text)
    except Exception as e:
        print("Error al generar contenido con Gemini:", e)
        await update.message.reply_text("Tuve un problema pensando mi respuesta. ¿Podés intentar de nuevo?")

# ==== MAIN DEL BOT ====

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
