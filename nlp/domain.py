def es_fuera_de_dominio(texto: str) -> bool:
    texto = texto.lower()
    temas_prohibidos = ["messi", "película", "política", "fútbol", "crimen", "chatgpt", "ai", "auto"]

    return any(palabra in texto for palabra in temas_prohibidos)
