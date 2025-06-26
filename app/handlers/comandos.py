from telegram import Update
from telegram.ext import ContextTypes
from app.utils.sensores import formatear_datos_sensores
from app.utils.usuarios import usuarios_registrados, guardar_usuarios_registrados, configuracion_usuarios
from app.db.db_connection import obtener_datos_mas_recentes, obtener_estado_hace_tiempo
from datetime import timedelta

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
