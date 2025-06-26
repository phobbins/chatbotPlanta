import json
from collections import defaultdict

usuarios_registrados = set()

# Configuración de notificaciones por usuario: user_id -> {"intervalo": segundos, "activo": bool}
configuracion_usuarios = defaultdict(lambda: {"intervalo": 1800, "activo": True, "ultimo_envio": 0})

def cargar_usuarios_registrados():
    try:
        with open("usuarios.json", "r") as f:
            data = json.load(f)
            return set(data.get("usuarios", [])), dict(data.get("configuraciones", {}))
    except FileNotFoundError:
        return set(), {}

def guardar_usuarios_registrados():
    with open("usuarios.json", "w") as f:
        json.dump({
            "usuarios": list(usuarios_registrados),
            "configuraciones": dict(configuracion_usuarios)
        }, f, indent=2)