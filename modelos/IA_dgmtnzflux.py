import replicate, requests
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string):
    
    # Definir los parámetros de entrada para el modelo
    image_input = {
        "model": "dev",
        "prompt": f"DGMTNZ {section} {content}, a photo in the context of the PowerPoint of {nuevo_string}",
        "lora_scale": 1,
        "num_outputs": 1,
        "aspect_ratio": "1:1",
        "output_format": "webp",
        "guidance_scale": 3,
        "output_quality": 80,
        "prompt_strength": 0.8,
        "extra_lora_scale": 1,
        "num_inference_steps": 28,
        "negative_prompt": "worst quality, low quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
        "disable_safety_checker": True
    }

    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "dgmtnz/dgmtnzflux:2df4f3bc8070ddda1854e25218cf5ac159cc0d51c9fcfdd08447712075807e8b",
        input=image_input
    )
    
    # Obtener la URL de la imagen generada  
    image_url = output[0]
    # Realizar una solicitud HTTP para obtener la imagen
    response = requests.get(image_url)
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img