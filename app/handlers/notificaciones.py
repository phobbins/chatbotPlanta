from app.utils.usuarios import configuracion_usuarios, guardar_usuarios_registrados

async def configurar_notificaciones(update, context):
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

async def desactivar_notificaciones(update, context):
    """Desactivar notificaciones automáticas"""
    user_id = update.effective_user.id
    configuracion_usuarios[user_id]["activo"] = False
    guardar_usuarios_registrados()
    await update.message.reply_text("🔕 Notificaciones desactivadas. Ya no te voy a molestar automáticamente.\n\nPuedes reactivarlas con /notif_on")

async def activar_notificaciones(update, context):
    """Reactivar notificaciones automáticas"""
    user_id = update.effective_user.id
    configuracion_usuarios[user_id]["activo"] = True
    guardar_usuarios_registrados()
    
    intervalo_min = configuracion_usuarios[user_id]["intervalo"] // 60
    await update.message.reply_text(f"🔔 ¡Notificaciones reactivadas! Te voy a avisar cada {intervalo_min} minutos sobre mi estado.")
