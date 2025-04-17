import replicate, requests
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):
    # Definir los parámetros de entrada para el modelo
    image_input = {
        "prompt": f"{section} {content}, a photo in the context of the PowerPoint of {nuevo_string}, professional photographers style with soft lighting and exceptional clarity",
        "aspect_ratio": "1:1"
    }
    
    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "google/imagen-3-fast",
        input=image_input
    )
    
    # Los modelos de Google devuelven directamente la URL de la imagen
    image_url = output
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img 