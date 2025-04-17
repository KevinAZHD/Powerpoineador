import replicate, requests
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):

    # Definir los parámetros de entrada para el modelo
    image_input = {
        "prompt": f"{section} {content}, a cinematic representative photo in the context of the PowerPoint of {nuevo_string}",
        "num_outputs": 1,
        "seed": 0,
        "width": 848,
        "height": 848,
        "aspect_ratio": "1:1",
        "output_format": "webp",
        "guidance_scale": 3.5,
        "output_quality": 80,
        "num_inference_steps": 8,
        "negative_prompt": "worst quality, low quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
        "disable_safety_checker": True
    }
    
    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "bytedance/hyper-flux-8step:16084e9731223a4367228928a6cb393b21736da2a0ca6a5a492ce311f0a97143",
        input=image_input
    )
    
    # Obtener la URL de la imagen generada
    image_url = output[0]
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img