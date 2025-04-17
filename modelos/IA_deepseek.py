import replicate, ast, time
import os
from Traducciones import obtener_traduccion

# Función para eliminar el contenido del think antes de procesar
def eliminar_think(texto):
    while True:
        inicio = texto.find('<think>')
        fin = texto.find('</think>')
        if inicio == -1 or fin == -1:
            break
        texto = texto[:inicio] + texto[fin + 8:]
    return texto.strip()

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
        " SOLO GENERA EL INTERIOR DE LA TUPLA, ES DECIR EMPIEZA POR { SOLO QUIERO QUE GENERES LA ESTRUCTURA DE LA TUPLA. "
        "Ejemplo de estructura correcta: "
        "{\"Historia de Hitler\":\"Adolf Hitler nació el 20 de abril de 1889 en Braunau am Inn, Austria. Fue un líder político y militar alemán, conocido por ser el fundador del Partido Nazi y el principal responsable del Holocausto.\", "
        "\"Ideología Nazi\":\"El nazismo fue una ideología política totalitaria basada en la supremacía de la raza aria. Hitler consideraba que los alemanes eran superiores a todas las demás razas.\", "
        "\"Segunda Guerra Mundial\":\"Hitler inició la Segunda Guerra Mundial en 1939 con la invasión de Polonia, desencadenando el conflicto más devastador de la historia.\"} "
        "TITLES CANT BE JUST NUMBERS AND SHOULD BE BETWEEN QUOTES DONT GENERATE AN INTRODUCTION EITHER)"
    )
    
    # Inicializar la respuesta como una cadena vacía
    respuesta_completa = ""
    
    try:
        # Ejecutar el modelo para obtener la respuesta
        for event in replicate.stream(
            "deepseek-ai/deepseek-r1",
            input={
                "prompt": prompt,
                "top_p": 1,
                "max_tokens": 20480,
                "temperature": 0.1,
                "presence_penalty": 0,
                "frequency_penalty": 0
            }
        ):
            # Imprimir el evento actual
            print(event, end="")
            # Agregar el evento actual a la respuesta completa
            respuesta_completa += str(event)

        # Limpieza y procesamiento de la respuesta
        respuesta_limpia = eliminar_think(respuesta_completa)
        respuesta_procesada = extraer_entre_llaves(respuesta_limpia)
        
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
            log_message(obtener_traduccion('intentando_generar_respuesta', current_language).format(modelo="DeepSeek"))
            
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