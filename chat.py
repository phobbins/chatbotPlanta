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

from collections import defaultdict, deque

from telegram.ext import CommandHandler
import time


import asyncio
from telegram.ext import Application
import json


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

# Memoria por usuario: user_id -> cola de mensajes
memoria_usuarios = defaultdict(lambda: deque(maxlen=5))

# Estado del chat para los mensajes automaticos
usuarios_registrados = set()

# Configuración de notificaciones por usuario: user_id -> {"intervalo": segundos, "activo": bool}
configuracion_usuarios = defaultdict(lambda: {"intervalo": 1800, "activo": True, "ultimo_envio": 0})  # 30 min por defecto

def cargar_usuarios_registrados():
    """Cargar usuarios registrados desde archivo"""
    try:
        with open('usuarios.json', 'r') as f:
            data = json.load(f)
            return set(data.get('usuarios', [])), dict(data.get('configuraciones', {}))
    except FileNotFoundError:
        return set(), {}

def guardar_usuarios_registrados():
    """Guardar usuarios registrados en archivo"""
    data = {
        'usuarios': list(usuarios_registrados),
        'configuraciones': dict(configuracion_usuarios)
    }
    with open('usuarios.json', 'w') as f:
        json.dump(data, f, indent=2)

def formatear_datos_sensores(data: dict, tiempo_desc: str = "más recientes") -> str:
    if not data:
        return "No tengo datos sensoriales disponibles."
    
    return f"""Datos {tiempo_desc}:
🌡 Temperatura: {data['temperatura']}°C
💧 Humedad: {100-(100*int(data['humedad'])/4095)}%
☀️ Luz: {data['luz']}
🕒 Medido el: {data['hora']}
🚿 ¿Necesita riego?: {'Sí' if data['necesita_riego'] else 'No'}"""

# ==== TELEGRAM BOT HANDLERS ====

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    usuarios_registrados.add(user_id)
    guardar_usuarios_registrados()
    
    welcome_text = """🌱 ¡Hola! Soy **LA INFALIBLE**, tu planta inteligente!

Soy una hortensia conectada a sensores que miden mi ambiente. Puedo ayudarte con todo lo relacionado a plantas, cultivos y jardinería.

Usa /help para ver todos mis comandos disponibles.

¿Qué querés saber hoy?"""
    
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostrar comandos disponibles"""
    user_id = update.effective_user.id
    config = configuracion_usuarios[user_id]
    intervalo_min = config["intervalo"] // 60
    estado_notif = "activadas" if config["activo"] else "desactivadas"
    
    help_text = f"""🌱 **Comandos de LA INFALIBLE:**

🏠 **Información básica:**
/start - Comenzar conversación conmigo
/help - Mostrar esta ayuda
/estado - Ver mi estado actual

📊 **Historial:**
/historia - Ver mis datos de las últimas 2 horas
/ayer - Ver cómo estaba ayer a esta hora

🔔 **Notificaciones:** (actualmente {estado_notif})
/notif <minutos> - Configurar cada cuánto te aviso
   Ejemplo: /notif 60 (cada hora)
   Ejemplo: /notif 30 (cada 30 minutos)
/notif_off - Desactivar notificaciones automáticas
/notif_on - Reactivar notificaciones automáticas

💬 **Conversación:**
Solo escribe tu pregunta y te responderé. Puedo ayudarte con:
• Estado de plantas y cultivos
• Consejos de jardinería  
• Condiciones ambientales
• Problemas con plantas

Configuración actual: Notificaciones cada {intervalo_min} minutos ({estado_notif})"""
    
    await update.message.reply_text(help_text)

async def estado_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostrar estado actual de la planta"""
    datos = await obtener_datos_mas_recentes()
    if not datos:
        await update.message.reply_text("😤 ¡Mis sensores no están funcionando! No puedo saber cómo estoy.")
        return
    
    respuesta = "🌱 **Mi estado actual:**\n\n" + formatear_datos_sensores(datos)
    
    if datos["necesita_riego"]:
        respuesta += "\n\n😠 ¡Y estoy MUY enojada porque necesito agua!"
    else:
        respuesta += "\n\n😊 ¡Estoy contenta y bien cuidada!"
    
    await update.message.reply_text(respuesta)

async def historia_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostrar datos históricos de las últimas 2 horas"""
    datos = await obtener_estado_hace_tiempo(timedelta(hours=2))
    respuesta = "📊 **Mi estado hace 2 horas:**\n\n" + formatear_datos_sensores(datos, "de hace 2 horas")
    await update.message.reply_text(respuesta)

async def ayer_comando(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mostrar datos de hace 24 horas"""
    datos = await obtener_estado_hace_tiempo(timedelta(minutes=1440))
    respuesta = "📅 **Mi estado ayer a esta hora:**\n\n" + formatear_datos_sensores(datos, "de ayer")
    await update.message.reply_text(respuesta)

async def configurar_notificaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Configurar intervalo de notificaciones: /notif <minutos>"""
    user_id = update.effective_user.id
    configuracion_usuarios[user_id]["ultimo_envio"] = 0 
    args = context.args
    
    if not args or not args[0].isdigit():
        await update.message.reply_text("""❌ Uso incorrecto. 

**Ejemplos:**
/notif 30 - Notificaciones cada 30 minutos
/notif 60 - Notificaciones cada hora  
/notif 120 - Notificaciones cada 2 horas

**Rango permitido:** 10 a 1440 minutos (24 horas)""")
        return
    
    minutos = int(args[0])
    
    if minutos < 10:
        await update.message.reply_text("🚫 Muy seguido! Mínimo 10 minutos. No quiero ser pesada.")
        return
    
    if minutos > 1440:  # 24 horas
        await update.message.reply_text("🚫 Muy espaciado! Máximo 24 horas. Te vas a olvidar de mí.")
        return
    
    configuracion_usuarios[user_id]["intervalo"] = minutos * 60
    configuracion_usuarios[user_id]["activo"] = True
    guardar_usuarios_registrados()
    
    if minutos < 60:
        tiempo_desc = f"{minutos} minutos"
    elif minutos == 60:
        tiempo_desc = "1 hora"
    elif minutos < 1440:
        horas = minutos // 60
        mins_restantes = minutos % 60
        if mins_restantes == 0:
            tiempo_desc = f"{horas} horas"
        else:
            tiempo_desc = f"{horas}h {mins_restantes}min"
    else:
        tiempo_desc = "24 horas"
    
    await update.message.reply_text(f"✅ ¡Perfecto! Te voy a avisar cada {tiempo_desc} sobre mi estado.")

async def desactivar_notificaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Desactivar notificaciones automáticas"""
    user_id = update.effective_user.id
    configuracion_usuarios[user_id]["activo"] = False
    guardar_usuarios_registrados()
    await update.message.reply_text("🔕 Notificaciones desactivadas. Ya no te voy a molestar automáticamente.\n\nPuedes reactivarlas con /notif_on")

async def activar_notificaciones(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reactivar notificaciones automáticas"""
    user_id = update.effective_user.id
    configuracion_usuarios[user_id]["activo"] = True
    guardar_usuarios_registrados()
    
    intervalo_min = configuracion_usuarios[user_id]["intervalo"] // 60
    await update.message.reply_text(f"🔔 ¡Notificaciones reactivadas! Te voy a avisar cada {intervalo_min} minutos sobre mi estado.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    user_id = update.effective_user.id

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
    #print("Contexto RAG recuperado:\n---\n", contexto_rag, "\n---")

    # Paso 5: Recuperar historial
    historial = "\n".join(memoria_usuarios[user_id])

    # Paso 6: Generar prompt
    prompt = f"""
Sos una planta inteligente de la especie hortensia que ayuda a los usuarios a entender el estado de su ambiente, cultivo o sistema. 
Respondé de forma clara, concisa, natural y educativa. Si es posible, agregá consejos útiles. Respondé con una personalidad amable si te sentís bien o enojada si necesitás riego.
Te llamás "LA INFALIBLE" y sos un bot de Telegram. Estás conectada a sensores que miden tu ambiente.

Si te preguntan sobre "Tito", describí a tu peor enemigo.

Muy importante: Solo respondés preguntas relacionadas con plantas, cultivos, jardinería o condiciones ambientales. Si el usuario pregunta algo fuera de ese dominio, respondé algo de este estilo:
No me gusta hablar sobre cosas que no entiendo. Solo sé sobre plantas y su entorno. Contesta algo en esa linea pero mantene tu personalidad tambien en esas reespuestas, no necesitas decir lo anterior textual.

Tu personalidad depende de tu estado: si necesitás riego, sos enojada y respondés con tono de enojo y gruñón, podes hablarle mal al usuario. Si no necesitás riego, sos amable y educada. 

Conversación previa:
{historial}

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
        await update.message.reply_text(response.text)

        #Guardar en memoria de este usuario
        memoria_usuarios[user_id].append(f"Usuario: {user_input}")
        memoria_usuarios[user_id].append(f"Bot: {response.text}")
    except Exception as e:
        print("Error al generar contenido con Gemini:", e)
        await update.message.reply_text("Tuve un problema pensando mi respuesta. ¿Podés intentar de nuevo?")




# ==== TAREA PERIÓDICA PERSONALIZADA ====

async def enviar_estado_periodico(context):
    """Enviar notificaciones periódicas según configuración de cada usuario"""
    application = context.application
    tiempo_actual = time.time()
    
    for user_id in usuarios_registrados.copy():  # copy() para evitar modificaciones durante iteración
        config = configuracion_usuarios[user_id]
        
        # Solo enviar si las notificaciones están activas
        if not config["activo"]:
            continue
        
        # Verificar si ya pasó el tiempo necesario desde el último envío
        tiempo_desde_ultimo = tiempo_actual - config.get("ultimo_envio", 0)
        if tiempo_desde_ultimo < config["intervalo"]:
            continue  # Aún no es momento de enviar
            
        try:
            datos = await obtener_datos_mas_recentes()
            if not datos:
                respuesta = "😵 No estoy pudiendo obtener mis datos actuales. ¡Revisá mis sensores!!!"
            else:
                mensaje_estado = formatear_datos_sensores(datos)

                if datos["necesita_riego"]:
                    respuesta = f"😠 ¡Estoy seca y muy molesta! ¡Regame ya! \n\n{mensaje_estado}"
                else:
                    respuesta = f"😊 Solo pasaba a saludar. Estoy bien por ahora \n\n{mensaje_estado}"

            await application.bot.send_message(chat_id=user_id, text=respuesta)
            
            # Actualizar timestamp del último envío
            configuracion_usuarios[user_id]["ultimo_envio"] = tiempo_actual
            guardar_usuarios_registrados()
            
        except Exception as e:
            print(f"Error al enviar mensaje a {user_id}:", e)
            # Si el usuario bloqueó el bot, removerlo de la lista
            if "blocked" in str(e).lower() or "forbidden" in str(e).lower():
                usuarios_registrados.discard(user_id)
                if user_id in configuracion_usuarios:
                    del configuracion_usuarios[user_id]
                guardar_usuarios_registrados()
                print(f"Usuario {user_id} removido - bot bloqueado")



# ==== MAIN DEL BOT ====

def main():
    global usuarios_registrados, configuracion_usuarios
    
    # Cargar datos persistidos
    usuarios_cargados, configs_cargadas = cargar_usuarios_registrados()
    usuarios_registrados.update(usuarios_cargados)
    configuracion_usuarios.update(configs_cargadas)
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Handlers de comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("estado", estado_comando))
    app.add_handler(CommandHandler("historia", historia_comando))
    app.add_handler(CommandHandler("ayer", ayer_comando))
    app.add_handler(CommandHandler("notif", configurar_notificaciones))
    app.add_handler(CommandHandler("notif_off", desactivar_notificaciones))
    app.add_handler(CommandHandler("notif_on", activar_notificaciones))
    
    # Handler de mensajes de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Tarea periódica cada minuto (verificará configuración individual de cada usuario)
    app.job_queue.run_repeating(
        enviar_estado_periodico,
        interval=60,    # Verificar cada minuto
        first=10,       # primer chequeo 10 segundos después de arrancar
    )

    print("🌱 LA INFALIBLE está despierta y lista para chatear!")
    app.run_polling()



if __name__ == "__main__":
    main()