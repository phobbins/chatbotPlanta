from datetime import datetime, timedelta

def formatear_datos_sensores(data, tiempo_desc="más recientes"):
    if not data:
        return "No tengo datos sensoriales disponibles."
    
    # Ajustar fecha
    hora_original = data['hora']
    hora_ajustada = hora_original - timedelta(hours=3)
    hora_formateada = hora_ajustada.strftime("%Y-%m-%d %H:%M:%S")

    # Calcular humedad
    humedad_pct = 100 - (100 * int(data['humedad']) / 4095)
    
    return f"""Datos {tiempo_desc}:
🌡 Temperatura: {float(data['temperatura']):.2f}°C
💧 Humedad: {humedad_pct:.2f}%
☀️ Luz: {float(data['luz']):.2f}
🕒 Medido el: {hora_formateada}
🚿 ¿Necesita riego?: {'Sí' if data['necesita_riego'] else 'No'}"""



