import sys, os, random
from pptx import Presentation
from Diseños_diapositivas import Diapositivas
from modelos.IA_sdxl import generar_imagen as generar_imagen_sdxl
from modelos.IA_fluxschnell import generar_imagen as generar_imagen_fluxschnell
from modelos.IA_flux8 import generar_imagen as generar_imagen_flux8
from modelos.IA_flux16 import generar_imagen as generar_imagen_flux16
from modelos.IA_dgmtnzflux import generar_imagen as generar_imagen_diego
from modelos.IA_fluxpulid import generar_imagen as generar_imagen_flux
from modelos.IA_photomaker import generar_imagen as generar_imagen_photomaker
from modelos.IA_imagen3 import generar_imagen as generar_imagen_imagen3
from modelos.IA_imagen3fast import generar_imagen as generar_imagen_imagen3fast
from modelos.IA_sana import generar_imagen as generar_imagen_sana
from modelos.IA_model3_4 import generar_imagen as generar_imagen_model3_4
from modelos.IA_grok_2_image import generar_imagen as generar_imagen_grok

# Definir la ruta de la carpeta de datos de la aplicación según el sistema operativo
if sys.platform == 'win32':
    APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
else:
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.Powerpoineador')

# Crear carpeta de imágenes si no existe
IMAGES_DIR = os.path.join(APP_DATA_DIR, 'images')
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

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
        if modelo == 'meta-llama-3.1-405b-instruct (con censura) [$0.0067]':
            from modelos.IA_llama import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        elif modelo == 'claude-3.7-sonnet (más inteligente) [$0.0105]':
            from modelos.IA_sonnet_3_7 import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        elif modelo == 'claude-3.5-sonnet (inteligente) [$0.0131]':
            from modelos.IA_sonnet_3_5 import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        elif modelo == 'claude-3.5-haiku (económico) [$0.0035]':
            from modelos.IA_haiku import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        elif modelo == 'grok-2-1212 (experimental)':
            from modelos.IA_grok_2 import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        elif modelo == 'deepseek-r1 (razonador) [$0.007]':
            from modelos.IA_deepseek import intentar_obtener_respuesta
            respuesta = intentar_obtener_respuesta(descripcion, signals)
        else:
            from modelos.IA_dolphin import intentar_obtener_respuesta
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
    finally:
        import gc
        gc.collect()

# Función para generar una imagen con un modelo de IA
def generar_imagen_ia(section, content, descripcion, modelo, image1):
    try:
        if modelo == 'sdxl-lightning-4step (barata sin censura) [$0.0014]':
            return generar_imagen_sdxl(section, content, descripcion)
        elif modelo == 'flux-schnell (rápida) [$0.003]':
            return generar_imagen_fluxschnell(section, content, descripcion)
        elif modelo == 'hyper-flux-8step (rápida y muy barata) [$0.0063]':
            return generar_imagen_flux8(section, content, descripcion)
        elif modelo == 'photomaker (con caras mejorado) [$0.0069]':
            return generar_imagen_photomaker(section, content, descripcion, image1)
        elif modelo == 'hyper-flux-16step (rápida y barata) [$0.0667]':
            return generar_imagen_flux16(section, content, descripcion)
        elif modelo == 'dgmtnzflux (meme) [$0.03]':
            return generar_imagen_diego(section, content, descripcion)
        elif modelo == 'sana (calidad-precio) [$0.0042]':
            return generar_imagen_sana(section, content, descripcion)
        elif modelo == 'imagen-3 (mejor calidad) [$0.05]':
            return generar_imagen_imagen3(section, content, descripcion)
        elif modelo == 'imagen-3-fast (barata y rápida) [$0.025]':
            return generar_imagen_imagen3fast(section, content, descripcion)
        elif modelo == 'model3_4 (muy económico y sin censura) [$0.00098]':
            return generar_imagen_model3_4(section, content, descripcion)
        elif modelo == 'grok-2-image-1212 (experimental) [$0.07]':
            return generar_imagen_grok(section, content, descripcion)
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
                if modelo_imagen == 'flux-pulid (con caras) [$0.037]':
                    img = generar_imagen_flux(section, content, descripcion, imagen_personalizada)
                elif modelo_imagen == 'photomaker (con caras mejorado) [$0.0069]':
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
                
                # Emitir señal para actualizar la vista previa con imagen y texto
                if signals:
                    signals.nueva_diapositiva.emit(imagen_path, section, content)
                
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