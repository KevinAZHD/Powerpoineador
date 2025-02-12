import replicate, time, ast

# Función para obtener respuesta del modelo con reintentos
def obtener_respuesta_modelo(nuevo_string, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))

    # Definir el prompt para el modelo
    prompt = (
        "(Basandote en esta tupla de python, genera una con la misma estructura que genere información para un powerpoint sobre "
        + nuevo_string +
        " SOLO GENERA EL INTERIOR DE LA TUPLA, ES DECIR EMPIEZA POR { SOLO QUIERO QUE GENERES LA ESTRUCTURA DE LA TUPLA"
        "{\"Title1\":\"Content1\",\"Title2\":\"Content2\",\"Title3\":\"Content3\"} TITLES CANT BE JUST NUMBERS AND SHOULD BE "
        "BETWEEN QUOTES DONT GENERATE AN INTRODUCTION EITHER sections =, DONT  sections = { "
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
            "anthropic/claude-3.5-haiku",
            input={
                "prompt": prompt,
                "max_tokens": 8192,
                "system_prompt": "You are a helpful assistant that generates the text for the PowerPoint presentations in a tuple structure of python, you only generate the text for the PowerPoint presentations, you do not generate any other text. The structure of the tuple is {Title1:Content1,Title2:Content2,Title3:Content3}"
            }
        ):
            # Imprimir el evento actual
            print(event, end="")
            # Agregar el evento actual a la respuesta completa
            respuesta_completa += str(event)

        # Extraer el contenido entre llaves de la respuesta completa
        respuesta_procesada = extraer_entre_llaves(respuesta_completa)
        
        # Imprimir la respuesta completa y procesada
        log_message(f"Respuesta completa del modelo: {respuesta_completa}")
        log_message(f"Respuesta procesada: {respuesta_procesada}")
        
        # Intentar evaluar la respuesta procesada como un diccionario
        try:
            contenido = ast.literal_eval(respuesta_procesada)
            return contenido
        except:
            return respuesta_procesada
            
    except Exception as e:
        # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
        log_message(f"Error en la generación de respuesta: {str(e)}")
        return None
    finally:
        # Limpiar la memoria
        import gc
        gc.collect()

# Función para extraer el contenido entre llaves
def extraer_entre_llaves(texto):
    inicio = texto.find('{')
    fin = texto.rfind('}')
    if inicio != -1 and fin != -1:
        return texto[inicio:fin+1]
    return texto

# Función para obtener respuesta del modelo con reintentos
def intentar_obtener_respuesta(descripcion, signals=None):
    max_intentos = 3
    for intento in range(max_intentos):
        try:
            # Obtener la respuesta del modelo
            respuesta = obtener_respuesta_modelo(descripcion, signals)
            if respuesta:
                return respuesta
        except Exception as e:
            # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
            if signals:
                signals.update_log.emit(f"Error en intento {intento + 1}: {str(e)}")
            time.sleep(2)
    return None 