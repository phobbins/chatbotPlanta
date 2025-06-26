import time
from app.utils.sensores import formatear_datos_sensores
from app.utils.usuarios import configuracion_usuarios, usuarios_registrados, guardar_usuarios_registrados
from app.db.db_connection import obtener_datos_mas_recentes

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

