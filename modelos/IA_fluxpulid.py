import replicate, requests, base64
from PIL import Image
from io import BytesIO

# Función para generar una imagen basada en la sección, contenido, descripción e imagen personalizada del usuario
def generar_imagen(section, content, nuevo_string, imagen_path):
    with open(imagen_path, "rb") as image_file:
        # Leer la imagen personalizada del usuario y codificarla en base64
        Image1 = base64.b64encode(image_file.read()).decode('utf-8')

    # Definir los parámetros de entrada para el modelo
    input_params = {
        "width": 896,
        "height": 1152,
        "prompt": f"A person photo {section} {content} ,photo in the context of a PowerPoint of {nuevo_string}",
        "true_cfg": 1,
        "id_weight": 1,
        "num_steps": 20,
        "start_step": 0,
        "num_outputs": 1,
        "output_format": "webp",
        "guidance_scale": 4,
        "output_quality": 80,
        "main_face_image": f"data:image/jpeg;base64,{Image1}",
        "negative_prompt": "worst quality, low quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
        "max_sequence_length": 128,
        "disable_safety_checker": True
    }

    # Ejecutar el modelo para generar la imagen
    output = replicate.run(
        "zsxkib/flux-pulid:8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b",
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