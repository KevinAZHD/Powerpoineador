from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout
import requests, sys, os
from PySide6.QtWidgets import QApplication

# Función para manejar rutas de recursos en modo desarrollo y ejecutable
def resource_path(relative_path):
    try:
        # Intenta obtener la ruta base del ejecutable empaquetado
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usa la ruta actual del proyecto
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Clase para la ventana de configuración de la clave API de Replicate
class ReplicateAPIKeyWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # Inicialización de atributos y configuración de la ventana
        self.parent = parent
        self.setWindowTitle('Configuración API Replicate')
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
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
        pixmap = QPixmap(resource_path("iconos/replicate.png"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio)
            logo_label.setPixmap(scaled_pixmap)
            layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        
        # Campo de entrada para la clave API
        layout.addWidget(QLabel('Escriba su clave API de Replicate:'))
        input_layout = QHBoxLayout()
        self.api_input = QLineEdit()
        self.api_input.setMinimumWidth(300)
        self.api_input.textChanged.connect(self.clear_status)

        # Etiqueta para mostrar mensajes de estado
        self.status_label = QLabel('')
        self.status_label.setStyleSheet("color: red; qproperty-alignment: AlignCenter;")

        # Nueva condición para deshabilitar si ya hay clave
        if self.parent and self.parent.api_key:
            self.api_input.setText(self.parent.api_key)
            self.api_input.setDisabled(True)
            self.copy_btn = QPushButton(QIcon(resource_path("iconos/copy.png")), '')
            self.copy_btn.setToolTip('Copiar API al portapapeles')
            self.copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(self.parent.api_key))
            input_layout.addWidget(self.api_input)
            input_layout.addWidget(self.copy_btn)
            self.status_label.setText('Clave válida')
            self.status_label.setStyleSheet("color: green; qproperty-alignment: AlignCenter;")
        else:
            input_layout.addWidget(self.api_input)

        layout.addLayout(input_layout)
        
        # Botón de validación
        validate_btn = QPushButton('Validar y guardar')
        validate_btn.clicked.connect(self.validate_api)
        if self.parent and self.parent.api_key:
            validate_btn.setDisabled(True)
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

    # Función para validar la clave API con el servidor de Replicate
    def validate_api(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            self.show_status('No puede dejar el campo vacío')
            self.status_label.setStyleSheet("color: red; qproperty-alignment: AlignCenter;")
            return
        try:
            # Intenta validar la clave API con una solicitud al servidor
            headers = {"Authorization": f"Token {api_key}"}
            response = requests.get("https://api.replicate.com/v1/models", headers=headers)
            if response.status_code == 200:
                if self.parent:
                    self.parent.set_api_key(api_key)
                self.status_label.setText('Clave válida')
                self.status_label.setStyleSheet("color: green; qproperty-alignment: AlignCenter;")
                self.timer.stop()  # Detener el timer para que el mensaje se mantenga
                self.close()
            else:
                self.show_status('Clave inválida')
                self.status_label.setStyleSheet("color: red; qproperty-alignment: AlignCenter;")
        except Exception as e:
            self.show_status(f'Error de conexión: {str(e)}')
            self.status_label.setStyleSheet("color: red; qproperty-alignment: AlignCenter;")