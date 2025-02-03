import replicate, requests, base64
from PIL import Image
from io import BytesIO
# Función para generar una imagen basada en la sección, contenido, descripción e imagen personalizada del usuario
def generar_imagen(section, content, nuevo_string, imagen_path):
    # Leer la imagen personalizada del usuario y codificarla en base64
    with open(imagen_path, "rb") as image_file:
        Image1 = base64.b64encode(image_file.read()).decode('utf-8')

    # Definir los parámetros de entrada para el modelo
    input_params = {
        "prompt": f"A person img {section} {content} ,photo in the context of a PowerPoint of {nuevo_string}",
        "num_steps": 50,
        "style_name": "Photographic (Default)",
        "input_image": f"data:image/jpeg;base64,{Image1}",
        "num_outputs": 1,
        "guidance_scale": 5,
        "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
        "style_strength_ratio": 20,
        "disable_safety_checker": True
    }

    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4",
        input=input_params
    )

    # Realizar una solicitud HTTP para obtener la imagen generada
    response = requests.get(output[0])
    # Abrir la imagen generada en formato PIL
    img = Image.open(BytesIO(response.content))
    
    return img

# Función para codificar una imagen en base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Función para convertir una URL de imagen a base64
def image_url_to_base64(url):
    response = requests.get(url)
    img = Image.open(BytesIO(response.content))
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Función para guardar la imagen generada en un archivo
def save_generated_image(img, slide_number):
    img.save(f"Slide{slide_number}.jpg")