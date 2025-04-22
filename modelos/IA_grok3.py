import requests, ast, time, os
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
    
    # Definir los encabezados para la solicitud HTTP
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
    }
    
    # Definir los datos para la solicitud HTTP
    data = {
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant that generates the text for PowerPoint presentations in a tuple structure of python. You only generate the text for the PowerPoint presentations, you do not generate any other text. The structure of the tuple is {Title1:Content1,Title2:Content2,Title3:Content3}"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "model": "grok-3-beta",
        "stream": False,
        "temperature": 0.6
    }
    
    # Inicializar la respuesta como una cadena vacía
    respuesta_completa = ""
    
    try:
        # Realizar la solicitud HTTP
        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers=headers,
            json=data
        )
        
        # Verificar si la solicitud fue exitosa
        if response.status_code == 200:
            respuesta_completa = response.json()['choices'][0]['message']['content']
            log_message(obtener_traduccion('respuesta_completa_modelo', current_language).format(respuesta=respuesta_completa))
            
            # Extraer el contenido entre llaves de la respuesta completa
            respuesta_procesada = extraer_entre_llaves(respuesta_completa)
            log_message(obtener_traduccion('respuesta_procesada', current_language).format(respuesta=respuesta_procesada))
            
            # Intentar evaluar la respuesta procesada como un diccionario
            try:
                contenido = ast.literal_eval(respuesta_procesada)
                return contenido
            except:
                return respuesta_procesada
        else:
            error_msg = f"Error: {response.status_code}\nResponse: {response.text}"
            log_message(error_msg)
            return None

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
            log_message(obtener_traduccion('intentando_generar_respuesta', current_language).format(modelo="Grok"))
            
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