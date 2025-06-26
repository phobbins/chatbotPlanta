import asyncpg
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


async def obtener_datos_mas_recentes():
    return await obtener_estado_hace_tiempo(timedelta(seconds=0))

async def obtener_estado_hace_tiempo(intervalo: timedelta):
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        ahora = datetime.utcnow() # Ajuste de zona horaria a UTC-3 (Uruguay)
        momento_inicio = ahora - intervalo - timedelta(minutes=5)
        momento_objetivo = ahora - intervalo + timedelta(minutes=5)

        row = await conn.fetchrow("""
            SELECT temperatura, humedad, luz, hora, necesita_riego
            FROM mediciones
            WHERE hora BETWEEN $1 AND $2
            ORDER BY hora DESC
            LIMIT 1
        """, momento_inicio, momento_objetivo)


        await conn.close()

        if row:
            return {
                "temperatura": row["temperatura"],
                "humedad": row["humedad"],
                "luz": row["luz"],
                "hora": row["hora"],
                "necesita_riego": row["necesita_riego"]
            }
        else:
            return None
    except Exception as e:
        print("Error al acceder a la base de datos:", e)
        return None
    
