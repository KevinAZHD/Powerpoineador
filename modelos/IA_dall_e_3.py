import replicate, requests
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):

    # Definir los parámetros de entrada para el modelo
    image_input = {
        "prompt": f"{section} {content}, a photo in the context of the PowerPoint of {nuevo_string}",
        "aspect_ratio": "1:1",
        "style": "natural",
        "disable_safety_checker": True
    }
    
    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "openai/dall-e-3",
        input=image_input
    )
    
    # Obtener la URL de la imagen generada
    image_url = output[0]
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img