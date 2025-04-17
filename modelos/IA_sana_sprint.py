import replicate, requests
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):
    # Definir los parámetros de entrada para el modelo
    image_input = {
        "seed": -1,
        "width": 1024,
        "height": 1024,
        "prompt": f"{section} {content}, a photo in the context of the PowerPoint of {nuevo_string}",
        "output_format": "jpg",
        "guidance_scale": 4.5,
        "output_quality": 80,
        "inference_steps": 2,
        "intermediate_timesteps": 1.3,
        "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
        "disable_safety_checker": True
    }
    
    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "nvidia/sana-sprint-1.6b:6ed1ce77cdc8db65550e76d5ab82556d0cb31ac8ab3c4947b168a0bda7b962e4",
        input=image_input
    )
    
    # Obtener la URL de la imagen generada
    image_url = str(output)
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img