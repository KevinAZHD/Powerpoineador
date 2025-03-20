import requests, os
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):
    # Definir los encabezados para la solicitud HTTP
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
    }
    
    # Definir los datos para la solicitud HTTP
    data = {
        "model": "grok-2-image-1212",
        "prompt": f"{section} {content}, a photo in the context of the PowerPoint of {nuevo_string}",
        "n": 1,
        "response_format": "url"
    }
    
    try:
        # Realizar la solicitud HTTP
        response = requests.post(
            "https://api.x.ai/v1/images/generations",
            headers=headers,
            json=data
        )
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            # Obtener la URL de la imagen generada
            image_url = response.json()['data'][0]['url']
            
            # Realizar una solicitud HTTP para obtener la imagen
            img_response = requests.get(image_url)
            
            # Abrir la imagen generada en formato PIL
            img = Image.open(BytesIO(img_response.content))
            
            return img
        else:
            error_msg = f"Error: {response.status_code}\nResponse: {response.text}"
            print(error_msg)
            raise Exception(error_msg)

    except Exception as e:
        print(f"Error en la generación de imagen: {str(e)}")
        raise
