import sys, os
from PySide6.QtCore import Signal, QObject, QThread

# Función para manejar rutas de recursos tanto en modo desarrollo como en modo ejecutable
def resource_path(relative_path):
    try:
        # Intenta obtener la ruta base del ejecutable empaquetado
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usa la ruta actual del proyecto
        base_path = os.path.abspath(".")
    
    # Combina la ruta base con la ruta relativa del recurso
    return os.path.join(base_path, relative_path)

# Clase para manejar las señales de la ventana de log
class LogSignals(QObject):
    # Señal para actualizar el texto del log
    update_log = Signal(str)
    # Señal para indicar que el proceso terminó
    finished = Signal()
    # Señal para manejar errores
    error = Signal(str)
    # Señal para indicar que se cerró la ventana
    closed = Signal()
    # Señal para actualizar la barra de progreso
    update_progress = Signal(int, int)
    # Señal para agregar una nueva diapositiva
    nueva_diapositiva = Signal(str, str, str)
    
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        # Inicializar con español por defecto
        self.current_language = 'es'
        
        # Intentar obtener el idioma del padre
        if parent and hasattr(parent, 'current_language'):
            self.current_language = parent.current_language
        # Si no, intentar obtener el idioma del abuelo
        elif parent and hasattr(parent, 'parent') and parent.parent() and hasattr(parent.parent(), 'current_language'):
            self.current_language = parent.parent().current_language
        
        print(f"LogSignals inicializado con idioma: {self.current_language}")

# Clase worker para ejecutar la generación en un hilo separado
class GenerationWorker(QThread):
    def __init__(self, modelo_texto, modelo_imagen, descripcion, auto_open, imagen_personalizada, filename, signals, title_font_name='Calibri', content_font_name='Calibri', title_font_size=16, content_font_size=10, title_bold=False, title_italic=False, title_underline=False, content_bold=False, content_italic=False, content_underline=False, disenos_aleatorios=True, selected_layout_index=1):
        super().__init__()
        # Inicialización de variables necesarias para la generación
        self.modelo_texto = modelo_texto
        self.modelo_imagen = modelo_imagen
        self.descripcion = descripcion
        self.auto_open = auto_open
        self.imagen_personalizada = imagen_personalizada
        self.filename = filename
        self.signals = signals
        self.title_font_name = title_font_name
        self.content_font_name = content_font_name
        self.title_font_size = title_font_size
        self.content_font_size = content_font_size
        self.title_bold = title_bold
        self.title_italic = title_italic
        self.title_underline = title_underline
        # Bandera para saber si el proceso debe continuar
        self.running = True
        # Nuevas variables para formato de contenido
        self.content_bold = content_bold
        self.content_italic = content_italic
        self.content_underline = content_underline
        # Variable para determinar si los diseños son aleatorios
        self.disenos_aleatorios = disenos_aleatorios
        self.selected_layout_index = selected_layout_index

    # Función para ejecutar la generación de la presentación
    def run(self):
        try:
            # Importa e inicia la generación de la presentación
            from Logica_diapositivas import generar_presentacion
            generar_presentacion(
                self.modelo_texto,
                self.modelo_imagen,
                self.descripcion,
                self.auto_open,
                self.imagen_personalizada,
                self.filename,
                self.signals,
                self.title_font_name,
                self.content_font_name,
                self.title_font_size,
                self.content_font_size,
                self.title_bold,
                self.title_italic,
                self.title_underline,
                self.content_bold,
                self.content_italic,
                self.content_underline,
                self.disenos_aleatorios,
                self.selected_layout_index
            )
        except InterruptedError:
            # Obtener idioma para mensaje de cancelación
            current_language = 'es'
            if self.signals and hasattr(self.signals, 'current_language'):
                current_language = self.signals.current_language
            # No emitir error si fue cancelado intencionalmente
            from Traducciones import obtener_traduccion
            print(obtener_traduccion('generation_cancelled', current_language))
        except Exception as e:
            # Emite señal de error si algo falla
            if not self.isInterruptionRequested():
                self.signals.error.emit(str(e)) 