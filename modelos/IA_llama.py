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
        "(Basandote en esta tupla de python, genera una con la misma estructura que genere informacion para un power point sobre "
        + nuevo_string +
        " SOLO GENERA EL INTERIOR DE LA TUPLA, ES DECIR EMPIEZA POR { SOLO QUIERO QUE GENERES LA ESTRUCTURA DE LA TUPLA"
        "{\"Title1\":\"Content1\",\"Title2\":\"Content2\",\"Title3\":\"Content3\"} TITLES CANT BE JUST NUMBERS AND SOULD BE "
        "BETWEEN QUOTES DONT GENERATE AN INTRODUCTION EITHER sections =, DONT  sections = { "
        "\"Introduction\": \"Artificial Intelligence (AI) has revolutionized the way we live and work, transforming industries and improving lives.\", "
        "\"History of AI\": \"From Alan Turing's 1950s vision to modern-day advancements, AI has come a long way, with significant breakthroughs in "
        "machine learning, natural language processing, and computer vision.\", "
        "\"Applications of AI\": \"AI is being used in healthcare for disease diagnosis, in finance for fraud detection, in transportation for autonomous "
        "vehicles, and in education for personalized learning.\", "
        "\"Benefits of AI\": \"AI increases efficiency, reduces costs, enhances customer experience, and enables data-driven decision making, making it an "
        "essential tool for businesses and individuals alike.\", "
        "\"Types of AI\": \"From narrow or weak AI to general or strong AI, and from supervised to unsupervised learning, the possibilities are endless, "
        "with new developments emerging every day.\", "
        "\"Challenges and Limitations\": \"Despite its benefits, AI raises concerns about job displacement, bias, and ethics, highlighting the need for "
        "responsible development and deployment.\", "
        "\"Future of AI\": \"As AI continues to evolve, it holds immense potential to solve complex problems, improve lives, and transform the world.\" })"
    )
    
    # Inicializar la respuesta como una cadena vacía
    respuesta_completa = ""
    
    try:
        # Ejecutar el modelo para obtener la respuesta
        for event in replicate.stream(
            "meta/meta-llama-3.1-405b-instruct",
            input={
                "prompt": prompt,
                "top_k": 50,
                "top_p": 0.9,
                "max_tokens": 8000,
                "min_tokens": 0,
                "temperature": 0.6,
                "system_prompt": "You are a helpful assistant that generates the text for the PowerPoint presentations in a tuple structure of python, you only generate the text for the PowerPoint presentations, you do not generate any other text. The structure of the tuple is {Title1:Content1,Title2:Content2,Title3:Content3}",
                "presence_penalty": 0,
                "frequency_penalty": 0
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
        # Manejar cualquier error que ocurra durante la generación de respuesta
        log_message(f"Error en la generación de respuesta: {str(e)}")
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

    while True:
        try:
            # Imprimir un mensaje indicando que se está intentando generar una respuesta
            log_message(f"Intentando generar respuesta...")
            
            # Obtener la respuesta del modelo
            respuesta = obtener_respuesta_modelo(descripcion, signals)
            # Verificar si la respuesta es un diccionario válido
            if isinstance(respuesta, dict):
                log_message(f"Respuesta generada exitosamente")
                return respuesta
            else:
                # Imprimir un mensaje indicando que la respuesta no es un diccionario válido
                log_message(f"La respuesta no es un diccionario válido, reintentando...")
                time.sleep(3)
        except Exception as e:
            # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
            log_message(f"Error al obtener respuesta: {str(e)}")
            time.sleep(3)