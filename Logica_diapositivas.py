import random, os
from pptx import Presentation
from Diseños_diapositivas import Diapositivas
from IA_llama import obtener_respuesta_modelo as obtener_respuesta_modelo_llama
from IA_dolphin import obtener_respuesta_modelo as obtener_respuesta_modelo_dolphin
from IA_grok import obtener_respuesta_modelo as obtener_respuesta_modelo_grok
from IA_sdxl import generar_imagen as generar_imagen_sdxl
from IA_fluxschnell import generar_imagen as generar_imagen_fluxschnell
from IA_flux8 import generar_imagen as generar_imagen_flux8
from IA_flux16 import generar_imagen as generar_imagen_flux16
from IA_dgmtnzflux import generar_imagen as generar_imagen_diego
from IA_fluxpulid import generar_imagen as generar_imagen_flux
from IA_photomaker import generar_imagen as generar_imagen_photomaker

# Función para obtener respuesta del modelo con reintentos
def intentar_obtener_respuesta(descripcion, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))

    try:
        # Obtener la respuesta del modelo
        from IA_llama import obtener_respuesta_modelo
        respuesta = obtener_respuesta_modelo(descripcion, signals)
        # Verificar si la respuesta es un diccionario válido
        if respuesta:
            log_message(f"Respuesta del modelo: {respuesta}")
        return respuesta
    except Exception as e:
        error_msg = f"Error al obtener respuesta: {str(e)}"
        log_message(error_msg)
        return None

# Función para obtener respuesta del modelo con reintentos
def obtener_respuesta_ia(descripcion, modelo, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))

    try:
        # Imprimir un mensaje indicando que se está intentando generar una respuesta
        log_message(f"Intentando generar respuesta con el modelo {modelo}...")
        
        # Verificar cuál es el modelo que se está utilizando
        if modelo == 'meta-llama-3.1-405b-instruct (con censura)':
            from IA_llama import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        elif modelo == 'grok-2-1212 (experimental)':
            from IA_grok import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        else:
            from IA_dolphin import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)

        # Verificar si se pudo obtener respuesta del modelo
        if respuesta:
            log_message(f"Respuesta del modelo {modelo}: {respuesta}")
            log_message(f"La tupla generada por el modelo fue: {respuesta}")
            return respuesta
        
        return None
        
    except Exception as e:
        # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
        log_message(f"Error en obtener_respuesta_ia: {str(e)}")
        return None
    # Finalizar la ejecución del programa
    finally:
        import gc
        gc.collect()

# Función para generar una imagen con un modelo de IA
def generar_imagen_ia(section, content, descripcion, modelo, image1):
    try:
        if modelo == 'sdxl-lightning-4step (barata sin censura)':
            return generar_imagen_sdxl(section, content, descripcion)
        elif modelo == 'flux-schnell (rápida)':
            return generar_imagen_fluxschnell(section, content, descripcion)
        elif modelo == 'hyper-flux-8step (rápida y muy barata)':
            return generar_imagen_flux8(section, content, descripcion)
        elif modelo == 'photomaker (con caras mejorado)':
            return generar_imagen_photomaker(section, content, descripcion, image1)
        elif modelo == 'hyper-flux-16step (rápida y barata)':
            return generar_imagen_flux16(section, content, descripcion)
        elif modelo == 'flux-diego (meme)':
            return generar_imagen_diego(section, content, descripcion)
        else:
            return generar_imagen_flux(section, content, descripcion, image1)
    except Exception as e:
        raise RuntimeError(f'Error al generar imagen: {str(e)}')

# Función para generar una presentación con un modelo de IA
def generar_presentacion(modelo_texto, modelo_imagen, descripcion, auto_open, imagen_personalizada, filename, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))

    try:
        # Obtener la ruta de la carpeta de imágenes
        APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
        IMAGES_DIR = os.path.join(APP_DATA_DIR, 'images')
        if not os.path.exists(IMAGES_DIR):
            os.makedirs(IMAGES_DIR)
        
        # Crear una nueva presentación
        presentation = Presentation()
        # Crear un objeto para aplicar diseños a las diapositivas
        slide_designs = Diapositivas(presentation)

        # Imprimir un mensaje indicando que se está generando texto con el modelo
        log_message(f"Generando texto con el modelo {modelo_texto}...")
        
        # Obtener la respuesta del modelo
        respuesta = obtener_respuesta_ia(descripcion, modelo_texto, signals)
        
        # Verificar si se pudo obtener respuesta del modelo
        if not respuesta:
            raise Exception("No se pudo obtener respuesta del modelo de texto")
        
        # Obtener las secciones del contenido
        sections = respuesta
        # Inicializar el número de diapositiva
        slide_number = 1
        # Obtener el número total de diapositivas
        total_slides = len(sections)
        # Crear una lista para almacenar las imágenes generadas
        imagenes_generadas = []
        
        # Iterar sobre las secciones del contenido
        for section, content in sections.items():
            # Imprimir un mensaje indicando que se está generando una imagen
            log_message(f"\nGenerando imagen {slide_number}/{total_slides}")
            try:
                # Verificar cuál es el modelo que se está utilizando
                if modelo_imagen == 'flux-pulid (con caras)':
                    img = generar_imagen_flux(section, content, descripcion, imagen_personalizada)
                elif modelo_imagen == 'photomaker (con caras mejorado)':
                    img = generar_imagen_photomaker(section, content, descripcion, imagen_personalizada)
                else:
                    img = generar_imagen_ia(section, content, descripcion, modelo_imagen, None)
                
                # Guardar la imagen generada en la carpeta de imágenes
                imagen_path = os.path.join(IMAGES_DIR, f"Slide{slide_number}.jpg")
                img.save(imagen_path)
                # Agregar la ruta de la imagen generada a la lista de imágenes generadas
                imagenes_generadas.append(imagen_path)
                # Imprimir un mensaje indicando que la imagen se generó correctamente
                log_message(f"Imagen {slide_number} generada correctamente")
                
                if signals:
                    # Emitir una señal para actualizar el progreso
                    signals.update_progress.emit(slide_number, total_slides)
                
                slide_number += 1
            except Exception as e:
                # Imprimir un mensaje indicando que ocurrió un error al generar la imagen
                log_message(f"Error generando imagen {slide_number}: {str(e)}")
                raise

        # Imprimir un mensaje indicando que se está aplicando diseños a las diapositivas
        log_message("\nAplicando diseños a las diapositivas...")
        # Crear una lista con los diseños disponibles
        designs = list(range(1, 8))
        # Mezclar los diseños disponibles
        random.shuffle(designs)
        # Iterar sobre las secciones del contenido
        for i, (section, content) in enumerate(sections.items()):
            try:
                # Verificar si es la primera diapositiva
                if i == 0:
                    slide_designs.design0(presentation.slides, section, content, imagenes_generadas[i])
                else:
                    # Obtener el diseño a aplicar
                    design = designs[(i-1) % len(designs)]
                    # Verificar cuál es el diseño que se está aplicando
                    if design == 1:
                        slide_designs.design1(presentation.slides, section, content, imagenes_generadas[i])
                    elif design == 2:
                        slide_designs.design2(presentation.slides, section, content, imagenes_generadas[i])
                    elif design == 3:
                        slide_designs.design3(presentation.slides, section, content, imagenes_generadas[i])
                    elif design == 4:
                        slide_designs.design4(presentation.slides, section, content, imagenes_generadas[i])
                    elif design == 5:
                        slide_designs.design5(presentation.slides, section, content, imagenes_generadas[i])
                    elif design == 6:
                        slide_designs.design6(presentation.slides, section, content, imagenes_generadas[i])
                    elif design == 7:
                        slide_designs.design7(presentation.slides, section, content, imagenes_generadas[i])
                # Imprimir un mensaje indicando que la diapositiva se completó correctamente
                log_message(f"Diapositiva {i+1}/{total_slides} completada")
            except Exception as e:
                # Imprimir un mensaje indicando que ocurrió un error al aplicar el diseño a la diapositiva
                log_message(f"Error aplicando diseño a diapositiva {i+1}: {str(e)}")
                raise

        # Guardar la presentación en un archivo
        presentation.save(filename)

        # Liberar memoria
        presentation = None
        slide_designs = None

        # Emitir una señal para indicar que el proceso terminó
        if signals:
            signals.finished.emit()

    except Exception as e:
        # Imprimir un mensaje indicando que ocurrió un error durante la generación de la presentación
        log_message(f"Error durante la generación de la presentación: {str(e)}")
        raise
    finally:
        # Liberar memoria
        import gc
        gc.collect()

# Función para obtener respuesta del modelo con reintentos
def intentar_obtener_respuesta_llama(descripcion, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))
            
    try:
        # Obtener la respuesta del modelo
        return obtener_respuesta_modelo_llama(descripcion, signals)
    except Exception as e:
        # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
        error_msg = f"Error al obtener respuesta: {str(e)}"
        log_message(error_msg)
        return None

# Función para obtener respuesta del modelo con reintentos
def intentar_obtener_respuesta_dolphin(descripcion, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))
            
    try:
        # Obtener la respuesta del modelo
        return obtener_respuesta_modelo_dolphin(descripcion, signals)
    except Exception as e:
        # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
        error_msg = f"Error al obtener respuesta: {str(e)}"
        log_message(error_msg)
        return None

# Función para obtener respuesta del modelo con reintentos
def intentar_obtener_respuesta_grok(descripcion, signals=None):
    # Función interna para manejar logs
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))
            
    try:
        # Obtener la respuesta del modelo
        return obtener_respuesta_modelo_grok(descripcion, signals)
    except Exception as e:
        # Imprimir un mensaje indicando que ocurrió un error al obtener la respuesta
        error_msg = f"Error al obtener respuesta: {str(e)}"
        log_message(error_msg)
        return None