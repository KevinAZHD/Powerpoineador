from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton
import requests, sys, os

# Función para manejar rutas de recursos en modo desarrollo y ejecutable
def resource_path(relative_path):
    try:
        # Intenta obtener la ruta base del ejecutable empaquetado
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usa la ruta actual del proyecto
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Clase para la ventana de configuración de la clave API de xAI
class GrokAPIKeyWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # Inicialización de atributos y configuración de la ventana
        self.parent = parent
        self.setWindowTitle('Configuración API xAI')
        self.setFixedSize(650, 300)
        self.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
        self.setWindowModality(Qt.ApplicationModal)
        
        # Timer para limpiar mensajes de estado
        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_status)
        
        # Centrar la ventana respecto al padre si existe
        if self.parent:
            parent_geometry = self.parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2 - (parent_geometry.height() // 8)
            self.move(x, y)
        
        self.setup_ui()

    # Función para configurar la interfaz de usuario
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Configuración del logo
        logo_label = QLabel()
        pixmap = QPixmap(resource_path("iconos/xai.jpg"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio)
            logo_label.setPixmap(scaled_pixmap)
            layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        
        # Campo de entrada para la clave API
        layout.addWidget(QLabel('Escriba su clave API de xAI:'))
        self.api_input = QLineEdit()
        self.api_input.setMinimumWidth(300)
        self.api_input.textChanged.connect(self.clear_status)
        if self.parent and self.parent.grok_api_key:
            self.api_input.setText(self.parent.grok_api_key)
        
        # Etiqueta para mostrar mensajes de estado
        self.status_label = QLabel('')
        self.status_label.setStyleSheet("color: red; qproperty-alignment: AlignCenter;")
        
        # Botón de validación
        validate_btn = QPushButton('Validar y guardar')
        validate_btn.clicked.connect(self.validate_api)
        layout.addWidget(self.api_input)
        layout.addWidget(self.status_label)
        layout.addWidget(validate_btn)
        self.setLayout(layout)

    # Función para limpiar el mensaje de estado
    def clear_status(self):
        if hasattr(self, 'status_label'):
            self.status_label.clear()
            self.timer.stop()

    # Función para mostrar mensajes de estado temporales
    def show_status(self, message):
        self.status_label.setText(message)
        self.timer.start(2000)

    # Función para validar la clave API con el servidor de xAI
    def validate_api(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            self.show_status('No puede dejar el campo vacío')
            return
        
        # Validar el formato de la clave API
        if not api_key.startswith("xai-"):
            self.show_status('Clave inválida')
            return
        
        try:
            # Intenta validar la clave API con una solicitud al servidor
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            response = requests.get(
                "https://api.x.ai/v1/models",
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 403]:
                if self.parent:
                    self.parent.set_grok_api_key(api_key)
                self.close()
            else:
                self.show_status('Clave inválida')
                
        except requests.exceptions.Timeout:
            self.show_status('Error de conexión: Timeout')
        except requests.exceptions.ConnectionError:
            self.show_status('Error de conexión: No se pudo conectar al servidor')
        except Exception as e:
            self.show_status(f'Error de conexión: {str(e)}')