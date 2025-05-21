import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
from Traducciones import obtener_traduccion

# Excepción personalizada para errores de compatibilidad regional
class RegionCompatibilityError(Exception):
    pass

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string, signals=None):
    # Obtener el idioma actual
    current_language = 'es'
    if signals and hasattr(signals, 'current_language'):
        current_language = signals.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'current_language'):
        current_language = signals.parent.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'parent') and hasattr(signals.parent.parent, 'current_language'):
        current_language = signals.parent.parent.current_language
    
    try:
        # Inicializar el cliente de Google AI
        client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        
        # Construir el prompt para la generación de imagen
        prompt = f"Generate an image about {content}."
        
        # Ejecutar el modelo para obtener la imagen
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=2,
                max_output_tokens=8192,
                response_modalities=["Text", "Image"],
                safety_settings=[
                    types.SafetySetting(
                        category="HARM_CATEGORY_HARASSMENT",
                        threshold="BLOCK_NONE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_HATE_SPEECH",
                        threshold="BLOCK_NONE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        threshold="BLOCK_NONE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_DANGEROUS_CONTENT",
                        threshold="BLOCK_NONE",
                    ),
                    types.SafetySetting(
                        category="HARM_CATEGORY_CIVIC_INTEGRITY",
                        threshold="BLOCK_NONE",
                    ),
                ]
            )
        )
        
        # Procesar la respuesta para obtener la imagen
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                # Convertir los datos binarios a una imagen PIL
                image = Image.open(BytesIO(part.inline_data.data))
                return image
            elif part.text is not None:
                mensaje = f"Texto recibido del modelo: {part.text}"
                print(mensaje)
                if signals:
                    signals.update_log.emit(obtener_traduccion('texto_recibido_modelo', current_language).format(texto=part.text))
        
        # Si no se encontró ninguna imagen en la respuesta
        error_mensaje = "No se generó ninguna imagen en la respuesta"
        if signals:
            signals.update_log.emit(obtener_traduccion('imagen_no_generada', current_language))
        raise Exception(error_mensaje)
        
    except Exception as e:
        error_message = str(e)
        # Verificar si el error es el específico que queremos manejar
        if "models/gemini-2.0-flash-preview-image-generation is not found" in error_message and "NOT_FOUND" in error_message:
            custom_error_key = 'error_gemini_region_incompatible'
            custom_error_message = obtener_traduccion(custom_error_key, current_language)
            print(custom_error_message)
            if signals:
                signals.update_log.emit(custom_error_message)
            # Lanzar una excepción personalizada que será capturada específicamente
            raise RegionCompatibilityError(custom_error_message)
        else:
            # Manejo de otros errores como estaba antes
            print(obtener_traduccion('error_generacion_imagen_gemini', current_language).format(error=error_message))
            if signals:
                signals.update_log.emit(obtener_traduccion('error_generacion_imagen_gemini', current_language).format(error=error_message))
            raise
