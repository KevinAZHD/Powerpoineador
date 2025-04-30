import replicate, requests
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):
    # Definir los parámetros de entrada para el modelo
    image_input = {
        "width": 1024,
        "height": 1024,
        "prompt": f"a photo in the context of the PowerPoint of {content} {section}",
        "scheduler": "K_EULER",
        "num_outputs": 1,
        "guidance_scale": 3.5,
        "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
        "num_inference_steps": 28,
        "nsfw_chekcer": False,
        "output_format": "png",
        "output_quality": 100
    }
    
    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "lightweight-ai/model3_4:3db8401934ab8847047c76cce766bc7390a54ae0a5342e42da8b27098b78f5ca",
        input=image_input
    )
    
    # Obtener la URL de la imagen generada
    image_url = output[0]
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img 