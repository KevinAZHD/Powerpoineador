import replicate, requests
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):
    # Definir los parámetros de entrada para el modelo
    image_input = {
        "width": 1024,
        "height": 1024,
        "prompt": f"{section} {content}, a photo in the context of the PowerPoint of {nuevo_string}",
        "model_variant": "1600M-1024px",
        "guidance_scale": 5,
        "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
        "pag_guidance_scale": 2,
        "num_inference_steps": 18,
        "disable_safety_checker": True
    }
    
    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "nvidia/sana:c6b5d2b7459910fec94432e9e1203c3cdce92d6db20f714f1355747990b52fa6",
        input=image_input
    )
    
    # Obtener la URL de la imagen generada
    image_url = str(output)
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img