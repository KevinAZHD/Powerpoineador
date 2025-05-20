import sys, os, threading, json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QGuiApplication, QPalette, QColor
from Version_checker import hay_actualizacion_disponible, obtener_version_actual
from Traducciones import obtener_traduccion

# Función para obtener la ruta de un recurso
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Obtener la ruta al archivo de configuración
def get_config_file_path():
    if sys.platform == 'win32':
        APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
    elif sys.platform == 'darwin':
        APP_DATA_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Powerpoineador')
    else:
        APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.Powerpoineador')
    
    if not os.path.exists(APP_DATA_DIR):
        try:
            os.makedirs(APP_DATA_DIR)
        except OSError as e:
            print(f"Error al crear el directorio de datos de la aplicación: {e}")
            # Considerar un manejo de error más robusto o un fallback
            # Por ahora, si no se puede crear, no se podrá leer/escribir config.
            return None 
            
    return os.path.join(APP_DATA_DIR, 'config.json')

# Función para cargar la configuración (idioma y tema)
def load_config():
    config_data = {'language': 'es', 'theme_preference': 'system'} # Valores por defecto
    config_file = get_config_file_path()
    
    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
                config_data['language'] = loaded_config.get('language', 'es')
                config_data['theme_preference'] = loaded_config.get('theme_preference', 'system')
        except Exception as e:
            print(f"Error al cargar la configuración: {str(e)}")
    return config_data

# Clase para mostrar el splash de carga
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.hay_actualizacion = False
        
        config = load_config()
        self.current_language = config['language']
        self.theme_preference = config['theme_preference']
        
        self.check_thread = threading.Thread(target=self.check_version)
        self.check_thread.start()
        
        # Configurar la ventana
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )

        # Configurar el fondo transparente y evitar propagación de eventos de ratón
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoMousePropagation)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        # Configurar el tamaño de la ventana (ajustado para mostrar todo el contenido)
        self.setFixedSize(425, 510)
        
        # Configurar el cursor a flecha
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        
        # Configurar el icono y el título de la ventana
        self.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
        self.setWindowTitle(obtener_traduccion('app_title', self.current_language))
        
        # Configurar el layout principal
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Configurar el contenedor
        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setCursor(Qt.ArrowCursor)
        
        # Configurar el layout del contenido
        content_layout = QVBoxLayout(self.container)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(50, 50, 50, 50)
        
        # Configurar el icono
        icon_label = QLabel()
        pixmap = QPixmap(resource_path("iconos/icon.png"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(320, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            content_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        # Añadir título del programa con estilo similar a PowerPoint
        self.title_label = QLabel(obtener_traduccion('app_title', self.current_language))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #D83B01;
                font-size: 32px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        content_layout.addWidget(self.title_label, alignment=Qt.AlignCenter)

        # Añadir versión del programa
        self.version_label = QLabel(f"{obtener_version_actual()}")
        self.version_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        content_layout.addWidget(self.version_label, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(self.container)
        self.setLayout(main_layout)

        # Aplicar tema ANTES de centrar y mostrar
        self.apply_splash_theme()

        # Centrar la ventana en la pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )

    def apply_splash_theme(self):
        effective_theme = self.theme_preference
        if self.theme_preference == 'system':
            # Obtener el tema del sistema operativo
            # Esto necesita que QApplication ya esté instanciada
            # Se llamará desde el if __name__ == "__main__" después de crear app
            # Por ahora, si es system, asumimos claro para el splash inicial
            # o podemos intentar obtenerlo si QGuiApplication está disponible
            try:
                app_instance = QApplication.instance()
                if app_instance:
                    color_scheme = QGuiApplication.styleHints().colorScheme()
                    if color_scheme == Qt.ColorScheme.Dark:
                        effective_theme = 'dark'
                    else:
                        effective_theme = 'light'
                else:
                    # Si QApplication no está lista, usar un default (ej. claro)
                    effective_theme = 'light' 
            except Exception as e:
                print(f"Error detectando tema del sistema para splash: {e}")
                effective_theme = 'light' # Fallback

        if effective_theme == 'dark':
            self.container.setStyleSheet("""
                QWidget#container {
                    background-color: rgba(35, 35, 35, 255); /* Negro/Gris oscuro */
                    border-radius: 20px;
                    border: 2px solid #555555; /* Borde oscuro */
                }
            """)
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #E0E0E0; /* Color de texto claro para tema oscuro */
                    font-size: 32px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
            self.version_label.setStyleSheet("""
                QLabel {
                    color: #AAAAAA; /* Color de texto gris claro para tema oscuro */
                    font-size: 16px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
        else: # Tema claro o default
            self.container.setStyleSheet("""
                QWidget#container {
                    background-color: rgba(255, 255, 255, 255);
                    border-radius: 20px;
                    border: 2px solid #e0e0e0;
                }
            """)
            self.title_label.setStyleSheet("""
                QLabel {
                    color: #D83B01;
                    font-size: 32px;
                    font-weight: bold;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)
            self.version_label.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 16px;
                    font-family: 'Segoe UI', Arial, sans-serif;
                }
            """)

    # Función para verificar si hay una actualización disponible
    def check_version(self):
        self.hay_actualizacion = hay_actualizacion_disponible()
    
    # Función para cerrar el splash de carga
    def closeEvent(self, event):
        QApplication.restoreOverrideCursor()
        super().closeEvent(event)