import sys, os, threading, json
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
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
def get_config_file():
    if sys.platform == 'win32':
        APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
    elif sys.platform == 'darwin':
        APP_DATA_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Powerpoineador')
    else:
        APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.Powerpoineador')
    
    return os.path.join(APP_DATA_DIR, 'config.json')

# Función para cargar el idioma desde la configuración
def load_language_from_config():
    try:
        config_file = get_config_file()
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('language', 'es')
    except Exception as e:
        print(f"Error al cargar el idioma: {str(e)}")
    return 'es'  # Idioma predeterminado si no se puede cargar

# Clase para mostrar el splash de carga
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.hay_actualizacion = False
        self.current_language = load_language_from_config()
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
        container = QWidget()
        container.setObjectName("container")
        container.setStyleSheet("""
            QWidget#container {
                background-color: rgba(255, 255, 255, 255);
                border-radius: 20px;
                border: 2px solid #e0e0e0;
            }
        """)
        container.setCursor(Qt.ArrowCursor)
        
        # Configurar el layout del contenido
        content_layout = QVBoxLayout(container)
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
        title_label = QLabel(obtener_traduccion('app_title', self.current_language))
        title_label.setStyleSheet("""
            QLabel {
                color: #D83B01;
                font-size: 32px;
                font-weight: bold;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        content_layout.addWidget(title_label, alignment=Qt.AlignCenter)

        # Añadir versión del programa
        version_label = QLabel(f"{obtener_version_actual()}")
        version_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 16px;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
        """)
        content_layout.addWidget(version_label, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(container)
        self.setLayout(main_layout)

        # Centrar la ventana en la pantalla
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.center().x() - self.width() // 2,
            screen.center().y() - self.height() // 2
        )

    # Función para verificar si hay una actualización disponible
    def check_version(self):
        self.hay_actualizacion = hay_actualizacion_disponible()
    
    # Función para cerrar el splash de carga
    def closeEvent(self, event):
        QApplication.restoreOverrideCursor()
        super().closeEvent(event)