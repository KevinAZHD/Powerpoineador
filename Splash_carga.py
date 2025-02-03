import sys, os, threading
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from Version_checker import hay_actualizacion_disponible

# Función para obtener la ruta de un recurso
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Clase para mostrar el splash de carga
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.hay_actualizacion = False
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
        
        # Configurar el tamaño fijo de la ventana
        self.setFixedSize(400, 400)
        
        # Configurar el cursor a flecha
        QApplication.setOverrideCursor(Qt.ArrowCursor)
        
        # Configurar el icono y el título de la ventana
        self.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
        self.setWindowTitle('Powerpoineador')
        
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
                border: none;
            }
        """)
        container.setCursor(Qt.ArrowCursor)
        
        # Configurar el layout del contenido
        content_layout = QVBoxLayout(container)
        content_layout.setSpacing(25)
        content_layout.setContentsMargins(30, 30, 30, 30)
        
        # Configurar el icono
        icon_label = QLabel()
        pixmap = QPixmap(resource_path("iconos/icon.jpg"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            content_layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        # Configurar el widget para mostrar el progreso
        loading_label = QLabel("Iniciando Powerpoineador")
        loading_label.setStyleSheet("""
            QLabel {
                color: #333333;
                font-size: 18px;
                font-weight: bold;
            }
        """)
        loading_label.setCursor(Qt.ArrowCursor)
        content_layout.addWidget(loading_label, alignment=Qt.AlignCenter)
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