import sys, os, random
from pptx import Presentation
from Diseños_diapositivas import Diapositivas
from Agentes_IA import PresentacionParalela
import tempfile
from PIL import Image

# Definir la ruta de la carpeta de datos de la aplicación según el sistema operativo
if sys.platform == 'win32':
    APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
else:
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.Powerpoineador')

# Crear carpeta de imágenes si no existe
IMAGES_DIR = os.path.join(APP_DATA_DIR, 'images')
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

# Función para generar una presentación con el nuevo sistema de agentes
def generar_presentacion(modelo_texto, modelo_imagen, descripcion, auto_open, imagen_personalizada, filename, signals=None, num_diapositivas=5):
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

        # Imprimir un mensaje indicando que se está iniciando el proceso
        log_message(f"Iniciando generación de presentación sobre: {descripcion}")
        
        # Crear y utilizar el sistema de generación paralela
        generador = PresentacionParalela(signals)
        
        # Generar todos los componentes de la presentación en paralelo
        diapositivas = generador.generar_presentacion(
            tema=descripcion,
            num_diapositivas=num_diapositivas,
            modelo_texto=modelo_texto,
            modelo_imagen=modelo_imagen,
            imagen_personalizada=imagen_personalizada
        )
        
        # Verificar si se generaron diapositivas
        if not diapositivas:
            raise Exception("No se pudieron generar las diapositivas")
        
        log_message(f"Se han generado {len(diapositivas)} diapositivas")
        
        # Inicializar el número de diapositiva y total
        slide_number = 1
        total_slides = len(diapositivas)
        
        # Lista para almacenar las rutas de las imágenes
        imagenes_generadas = []
        
        # Primero guardamos todas las imágenes
        for i, diapositiva in enumerate(diapositivas):
            try:
                # Guardar la imagen generada en la carpeta de imágenes
                imagen_path = os.path.join(IMAGES_DIR, f"Slide{i+1}.jpg")
                
                # Si la imagen está en formato PIL, guardarla
                if isinstance(diapositiva['imagen'], Image.Image):
                    diapositiva['imagen'].save(imagen_path)
                else:
                    # Si por algún motivo la imagen no es un objeto PIL, crear una imagen genérica
                    error_img = Image.new('RGB', (800, 600), color=(240, 240, 240))
                    error_img.save(imagen_path)
                
                # Agregar la ruta de la imagen a la lista
                imagenes_generadas.append(imagen_path)
                
                # Emitir señal para actualizar la vista previa con imagen y texto
                if signals:
                    signals.nueva_diapositiva.emit(imagen_path, diapositiva['titulo'], diapositiva['contenido'])
                
                if signals:
                    # Emitir una señal para actualizar el progreso
                    signals.update_progress.emit(i+1, total_slides)
                
            except Exception as e:
                log_message(f"Error al guardar imagen {i+1}: {str(e)}")
                # Crear una imagen de error genérica
                imagen_path = os.path.join(IMAGES_DIR, f"Slide{i+1}.jpg")
                error_img = Image.new('RGB', (800, 600), color=(240, 240, 240))
                error_img.save(imagen_path)
                imagenes_generadas.append(imagen_path)
        
        # Aplicar los diseños a las diapositivas
        log_message("\nAplicando diseños a las diapositivas...")
        # Crear una lista con los diseños disponibles
        designs = list(range(1, 8))
        # Mezclar los diseños disponibles
        random.shuffle(designs)
        
        # Crear las diapositivas con sus respectivos diseños
        for i, diapositiva in enumerate(diapositivas):
            try:
                # Obtener los datos de la diapositiva
                titulo = diapositiva['titulo']
                contenido = diapositiva['contenido']
                imagen_path = imagenes_generadas[i]
                
                # Verificar si es la primera diapositiva (portada)
                if i == 0:
                    slide_designs.design0(presentation.slides, titulo, contenido, imagen_path)
                else:
                    # Obtener el diseño a aplicar
                    design = designs[(i-1) % len(designs)]
                    # Aplicar el diseño correspondiente
                    if design == 1:
                        slide_designs.design1(presentation.slides, titulo, contenido, imagen_path)
                    elif design == 2:
                        slide_designs.design2(presentation.slides, titulo, contenido, imagen_path)
                    elif design == 3:
                        slide_designs.design3(presentation.slides, titulo, contenido, imagen_path)
                    elif design == 4:
                        slide_designs.design4(presentation.slides, titulo, contenido, imagen_path)
                    elif design == 5:
                        slide_designs.design5(presentation.slides, titulo, contenido, imagen_path)
                    elif design == 6:
                        slide_designs.design6(presentation.slides, titulo, contenido, imagen_path)
                    else:
                        slide_designs.design7(presentation.slides, titulo, contenido, imagen_path)
                
                log_message(f"Diapositiva {i+1} creada con diseño {design if i > 0 else 'portada'}")
                
            except Exception as e:
                log_message(f"Error al aplicar diseño a diapositiva {i+1}: {str(e)}")
                # Intentar con un diseño básico como respaldo
                try:
                    slide_designs.design1(presentation.slides, 
                                         f"Diapositiva {i+1}", 
                                         "Contenido no disponible.", 
                                         imagen_path)
                except:
                    pass
        
        # Guardar la presentación
        log_message(f"\nGuardando presentación en {filename}...")
        presentation.save(filename)
        
        # Limpiar recursos
        for imagen_path in imagenes_generadas:
            try:
                if os.path.exists(imagen_path):
                    pass  # Mantener las imágenes para la vista previa
            except:
                pass
        
        # Retornar éxito y abrir automáticamente si está habilitada esa opción
        return True, auto_open
        
    except Exception as e:
        log_message(f"Error durante la generación de la presentación: {str(e)}")
        return False, False
    finally:
        # Limpiar la memoria
        import gc
        gc.collect() 