import re
from datetime import timedelta

def extraer_tiempo(texto: str) -> timedelta | None:
    texto = texto.lower()

    patrones = [
        (r"hace (\d+) minutos?", lambda x: timedelta(minutes=int(x))),
        (r"hace (\d+) horas?", lambda x: timedelta(hours=int(x))),
        (r"hace (\d+) horas? y (\d+) minutos?", lambda x, y: timedelta(hours=int(x), minutes=int(y)))
    ]

    for patron, constructor in patrones:
        match = re.search(patron, texto)
        if match:
            return constructor(*match.groups())
    return None
