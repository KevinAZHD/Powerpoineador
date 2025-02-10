import replicate, requests
from PIL import Image
from io import BytesIO
from deep_translator import GoogleTranslator

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):
    # Detectar el idioma de origen y traducir al inglés usando Google Translate
    translator = GoogleTranslator(target='en')
    try:
        section_en = translator.translate(section)
        content_en = translator.translate(content)
        nuevo_string_en = translator.translate(nuevo_string)
        
    except Exception as e:
        print(f"Error en la traducción: {str(e)}")
        section_en = section
        content_en = content
        nuevo_string_en = nuevo_string
    
    # Definir los parámetros de entrada para el modelo
    image_input = {
        "prompt": f"{section_en} {content_en}, a photo in the context of the PowerPoint of {nuevo_string_en}, professional photographers style with soft lighting, high resolution and exceptional clarity, professional color grading",
        "aspect_ratio": "1:1"
    }
    
    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "google/imagen-3",
        input=image_input
    )
    
    # Los modelos de Google devuelven directamente la URL de la imagen
    image_url = output
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img 