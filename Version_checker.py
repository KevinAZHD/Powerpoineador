import requests, re
from packaging import version

# Definir la versión actual de la aplicación
VERSION_ACTUAL = "v0.1.9b"

# Función para obtener la última versión disponible en GitHub
def obtener_ultima_version():
    try:
        response = requests.get("https://github.com/KevinAZHD/Powerpoineador/releases")
        if response.status_code == 200:
            version_match = re.search(r'href="/KevinAZHD/Powerpoineador/releases/tag/(v\d+\.\d+\.\d+b)"', response.text)
            if version_match:
                return version_match.group(1)
    except Exception as e:
        print(f"Error al verificar actualizaciones: {str(e)}")
    return None

# Función para normalizar la versión
def _normalizar_version(ver):
    ver = ver.lstrip('v')
    ver = ver.rstrip('b')
    return version.parse(ver)

# Función para verificar si hay una actualización disponible
def hay_actualizacion_disponible():
    ultima_version = obtener_ultima_version()
    if ultima_version:
        try:
            version_actual_norm = _normalizar_version(VERSION_ACTUAL)
            ultima_version_norm = _normalizar_version(ultima_version)
            
            if version_actual_norm == ultima_version_norm:
                return False
                
            return ultima_version_norm > version_actual_norm
        except Exception as e:
            print(f"Error al comparar versiones: {str(e)}")
    return False

# Función para obtener la URL de descarga de la última versión
def obtener_url_descarga():
    ultima_version = obtener_ultima_version()
    if ultima_version:
        return f"https://github.com/KevinAZHD/Powerpoineador/releases/tag/{ultima_version}"
    return "https://github.com/KevinAZHD/Powerpoineador/releases"

# Función para obtener la versión actual
def obtener_version_actual():
    return VERSION_ACTUAL