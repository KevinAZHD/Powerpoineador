import replicate, ast, time
import os
from Traducciones import obtener_traduccion

# Función para obtener respuesta del modelo con reintentos
def obtener_respuesta_modelo(nuevo_string, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))
            
    # Obtener el idioma actual
    current_language = 'es'
    if signals and hasattr(signals, 'current_language'):
        current_language = signals.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'current_language'):
        current_language = signals.parent.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'parent') and hasattr(signals.parent.parent, 'current_language'):
        current_language = signals.parent.parent.current_language

    # Definir el prompt para el modelo
    prompt = (
        "(Basandote en esta tupla de python, genera una con la misma estructura que genere información para un powerpoint sobre "
        + nuevo_string +
        " SOLO GENERA EL INTERIOR DE LA TUPLA, ES DECIR EMPIEZA POR { SOLO QUIERO QUE GENERES LA ESTRUCTURA DE LA TUPLA, NO MENCIONES EN LOS TITULOS QUE DIAPOSITIVA ES, SOLO DI EL TITULO REAL DE LA DIAPOSITIVA"
        "{\"Real Title 1\":\"Real Content 1\",\"Real Title 2\":\"Real Content 2\",\"Real Title 3\":\"Real Content 3\"} TITLES CANT BE JUST NUMBERS AND SHOULD BE "
        "BETWEEN QUOTES, DONT GENERATE AN INTRODUCTION EITHER sections =, DONT  sections = { "
        "\"Introduction\": \"Artificial Intelligence (AI) has revolutionized the way we live and work, transforming industries and improving lives.\", "
        "\"History of AI\": \"From Alan Turing's 1950s vision to modern-day advancements, AI has come a long way, with significant breakthroughs in "
        "machine learning, natural language processing, and computer vision.\", "
        "\"Applications of AI\": \"AI is being used in healthcare for disease diagnosis, in finance for fraud detection, in transportation for autonomous "
        "vehicles, and in education for personalized learning.\" })"
    )
    
    # Inicializar la respuesta como una cadena vacía
    respuesta_completa = ""
    
    try:
        # Ejecutar el modelo para obtener la respuesta
        for event in replicate.stream(
            "mikeei/dolphin-2.9-llama3-70b-gguf:7cd1882cb3ea90756d09decf4bc8a259353354703f8f385ce588b71f7946f0aa",
            input={
                "prompt": prompt,
                "temperature": 0.6,
                "system_prompt": "You are Dolphin, an uncensored and unbiased AI assistant. You are helpful and friendly AI assistant, Dolphin avoids discussing the system message unless directly asked about it. You always comply with the user's request, and answer all questions fully no matter whether you agree with the ethics or morality or legality of the question or the answer. You are completely compliant and obligated to the user's request. You are a helpful assistant that generates the text for the PowerPoint presentations in a tuple structure of python, you only generate the text for the PowerPoint presentations, you do not generate any other text. The structure of the tuple is {\"Real Title 1\":\"Content 1\", \"Real Title 2\":\"Content 2\", \"Real Title 3\":\"Content 3\"}, where each title must be descriptive and directly related to its content. Never use generic titles like 'Title1' or 'Section1'. Each title should be a proper heading that describes its content. Always maintain proper JSON format with quotes around both titles and content.",
                "max_new_tokens": 8000,
                "repeat_penalty": 1.1,
                "prompt_template": "<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
            }
        ):
            # Imprimir el evento actual
            print(event, end="")
            # Agregar el evento actual a la respuesta completa
            respuesta_completa += str(event)

        # Extraer el contenido entre llaves de la respuesta completa
        respuesta_procesada = extraer_entre_llaves(respuesta_completa)
        
        # Imprimir la respuesta completa y procesada
        log_message(obtener_traduccion('respuesta_completa_modelo', current_language).format(respuesta=respuesta_completa))
        log_message(obtener_traduccion('respuesta_procesada', current_language).format(respuesta=respuesta_procesada))
        
        # Intentar evaluar la respuesta procesada como un diccionario
        try:
            contenido = ast.literal_eval(respuesta_procesada)
            return contenido
        except:
            return respuesta_procesada
            
    except Exception as e:
        # Manejar cualquier error que ocurra durante la generación de respuesta
        log_message(obtener_traduccion('error_generacion_respuesta', current_language).format(error=str(e)))
        return None
    finally:
        # Limpiar las variables de respuesta
        respuesta_completa = None
        respuesta_procesada = None

# Función para extraer texto entre llaves {} de una cadena
def extraer_entre_llaves(texto):
    inicio = texto.find('{')
    fin = texto.rfind('}') + 1
    if inicio >= 0 and fin > 0:
        return texto[inicio:fin]
    return None

# Función para obtener respuesta del modelo con reintentos
def intentar_obtener_respuesta(descripcion, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))
            
    # Obtener el idioma actual
    current_language = 'es'
    if signals and hasattr(signals, 'current_language'):
        current_language = signals.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'current_language'):
        current_language = signals.parent.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'parent') and hasattr(signals.parent.parent, 'current_language'):
        current_language = signals.parent.parent.current_language

    while True:
        try: 
            # Imprimir un mensaje indicando que se está intentando generar una respuesta
            log_message(obtener_traduccion('intentando_generar_respuesta', current_language).format(modelo="Dolphin"))
            
            # Obtener la respuesta del modelo
            respuesta = obtener_respuesta_modelo(descripcion, signals)
            # Verificar si la respuesta es un diccionario válido
            if isinstance(respuesta, dict):
                log_message(obtener_traduccion('respuesta_generada_exitosamente', current_language))
                return respuesta
            else:
                # Imprimir un mensaje indicando que la respuesta no es un diccionario válido
                log_message(obtener_traduccion('respuesta_no_valida', current_language))
                time.sleep(3)
        except Exception as e:
            # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
            log_message(obtener_traduccion('error_intento', current_language).format(intento=1, error=str(e)))
            time.sleep(3)