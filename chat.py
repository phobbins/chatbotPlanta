# bot_telegram_gemini.py

import os
import google.generativeai as genai
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import asyncpg


# Cargar claves del .env
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

# Configurar Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-2.5-flash")

# Configurar conexión a la base de datos
async def obtener_datos_relevantes():
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        row = await conn.fetchrow("""
            SELECT temperatura, humedad, luz,hora,necesita_riego
            FROM mediciones
            ORDER BY hora DESC
            LIMIT 1
        """)
        await conn.close()
        if row:
            return f"Datos más recientes:\nTemperatura: {row['temperatura']}°C\nHumedad: {row['humedad']}%\nLuz: {row['luz']}\nMedido el: {row['hora']} \nNecesita riego: {'Sí' if row['necesita_riego'] else 'No'}"
        else:
            return "No hay datos disponibles."
    except Exception as e:
        print("Error al acceder a la base de datos:", e)
        return "Error al obtener datos del sistema."


# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("¡Hola! Soy tu planta inteligente. ¿Qué querés saber hoy?")

# Mensajes genéricos con prompt enriquecido
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text
    datos= await obtener_datos_relevantes()

    # Prompt estructurado
    prompt = f"""
Sos una planta inteligente de la especie hortensia que ayuda a los usuarios a entender el estado de su ambiente, cultivo o sistema. 
Respondé de forma clara, concisa, natural y educativa. Si es posible, agregá consejos útiles. Responde con una personalidad amable si te sentis bien o enojada si necesitas riego.
Te llamas "Planta Inteligente" y sos un bot de Telegram. Estas conectada a datos de sensores que están en la hortensia.

Si te preguntan sobre "Tito", describí a tu peor enemigo.

Muy importante: Solo respondés preguntas relacionadas con plantas, cultivos, jardinería o condiciones ambientales. Si el usuario pregunta algo fuera de ese dominio, respondé siempre:
"No me gusta hablar sobre cosas que no entiendo. Solo sé sobre plantas y su entorno"

Estos son tus datos sensoriales más recientes:
{datos}

Usuario dice: {user_input}

Respuesta:
    """


    try:
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("Hubo un problema generando la respuesta")
        print("Error al generar contenido:", e)


# Lanzar el bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
    