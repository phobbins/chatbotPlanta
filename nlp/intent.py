def detectar_intencion(texto: str) -> str:
    texto = texto.lower()

    if "hace" in texto and ("minuto" in texto or "hora" in texto):
        return "consulta_estado_pasado"
    if "cómo estás" in texto or "estado" in texto:
        return "estado_actual"
    if "riego" in texto or "regar" in texto:
        return "consulta_riego"
    if "cuidados" in texto or "recomenda" in texto:
        return "cuidados_planta"
    return "desconocido"
