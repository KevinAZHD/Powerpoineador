import replicate, time, ast, json, re
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
            "anthropic/claude-4-sonnet",
            input={
                "prompt": prompt,
                "max_tokens": 64000,
                "system_prompt": "You are a helpful assistant that generates the text for the PowerPoint presentations in ONLY ONE tuple structure of python, you only generate the text for the PowerPoint presentations, you do not generate any other text. The structure of the tuple is {Title1:Content1,Title2:Content2,Title3:Content3}"
            }
        ):
            # Imprimir el evento actual
            print(event, end="")
            # Agregar el evento actual a la respuesta completa
            respuesta_completa += str(event)

        log_message(obtener_traduccion('respuesta_completa_modelo', current_language).format(respuesta=respuesta_completa))

        # Extraer y procesar la primera tupla válida
        contenido_procesado = extraer_primera_tupla_valida(respuesta_completa)
        
        # Imprimir la respuesta procesada
        log_message(obtener_traduccion('respuesta_procesada', current_language).format(respuesta=contenido_procesado))
        log_message(obtener_traduccion('respuesta_modelo', current_language).format(modelo="claude-4-sonnet", costo="$0.0105", respuesta=contenido_procesado))
        
        # Verificar si el contenido procesado es un diccionario válido
        if isinstance(contenido_procesado, dict):
            return contenido_procesado
        else:
            # Si no es un diccionario, intentar convertirlo
            try:
                contenido = ast.literal_eval(str(contenido_procesado))
                return contenido
            except:
                return None
            
    except Exception as e:
        # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
        log_message(obtener_traduccion('error_generacion_respuesta', current_language).format(error=str(e)))
        log_message(obtener_traduccion('error_generacion_presentacion', current_language).format(error=str(e)))
        return None
    finally:
        # Limpiar la memoria
        import gc
        gc.collect()

# Función mejorada para extraer y procesar la primera tupla válida
def extraer_primera_tupla_valida(texto):
    try:
        # Buscar todos los objetos JSON en el texto
        objetos_json = encontrar_objetos_json(texto)
        
        if objetos_json:
            # Tomar el primer objeto JSON válido
            primer_objeto = objetos_json[0]
            try:
                # Intentar parsearlo como JSON
                resultado = json.loads(primer_objeto)
                return resultado
            except json.JSONDecodeError:
                # Si falla JSON, intentar con ast.literal_eval
                try:
                    resultado = ast.literal_eval(primer_objeto)
                    return resultado
                except:
                    return primer_objeto
        
        # Si no se encuentran objetos JSON, usar el método original
        return extraer_entre_llaves(texto)
        
    except Exception as e:
        return extraer_entre_llaves(texto)

# Función para encontrar todos los objetos JSON en un texto
def encontrar_objetos_json(texto):
    objetos = []
    i = 0
    
    while i < len(texto):
        # Buscar el inicio de un objeto JSON
        inicio = texto.find('{', i)
        if inicio == -1:
            break
            
        # Contar llaves para encontrar el final del objeto
        contador_llaves = 0
        j = inicio
        dentro_comillas = False
        escape_siguiente = False
        
        while j < len(texto):
            char = texto[j]
            
            if escape_siguiente:
                escape_siguiente = False
            elif char == '\\':
                escape_siguiente = True
            elif char == '"' and not escape_siguiente:
                dentro_comillas = not dentro_comillas
            elif not dentro_comillas:
                if char == '{':
                    contador_llaves += 1
                elif char == '}':
                    contador_llaves -= 1
                    
                    if contador_llaves == 0:
                        # Encontramos el final del objeto
                        objeto = texto[inicio:j+1]
                        objetos.append(objeto)
                        i = j + 1
                        break
            j += 1
        else:
            # Si llegamos aquí, no se encontró el cierre
            break
    
    return objetos

# Función para extraer el contenido entre llaves (método original como respaldo)
def extraer_entre_llaves(texto):
    inicio = texto.find('{')
    fin = texto.rfind('}')
    if inicio != -1 and fin != -1:
        # Si hay múltiples objetos, buscar el final del primer objeto completo
        contador_llaves = 0
        i = inicio
        dentro_comillas = False
        escape_siguiente = False
        
        while i <= fin:
            char = texto[i]
            
            if escape_siguiente:
                escape_siguiente = False
            elif char == '\\':
                escape_siguiente = True
            elif char == '"' and not escape_siguiente:
                dentro_comillas = not dentro_comillas
            elif not dentro_comillas:
                if char == '{':
                    contador_llaves += 1
                elif char == '}':
                    contador_llaves -= 1
                    if contador_llaves == 0:
                        return texto[inicio:i+1]
            i += 1
        
        return texto[inicio:fin+1]
    return texto

# Función para obtener respuesta del modelo con reintentos
def intentar_obtener_respuesta(descripcion, signals=None):
    # Obtener el idioma actual
    current_language = 'es'
    if signals and hasattr(signals, 'current_language'):
        current_language = signals.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'current_language'):
        current_language = signals.parent.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'parent') and hasattr(signals.parent.parent, 'current_language'):
        current_language = signals.parent.parent.current_language
        
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
                signals.update_log.emit(obtener_traduccion('error_intento', current_language).format(intento=intento + 1, error=str(e)))
            time.sleep(2)
    return None