from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QFrame
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont
import os

# Clase para la ventana de vista previa de diapositivas
class VentanaVistaPrevia(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Vista previa de diapositivas')
        self.setMinimumSize(800, 600)
        
        # Inicializar la lista de diapositivas
        self.slides = []
        
        # Crear layout principal con margen superior reducido
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Crear área de desplazamiento
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Widget contenedor para las diapositivas
        self.contenedor = QWidget()
        self.contenedor_layout = QVBoxLayout()
        self.contenedor_layout.setAlignment(Qt.AlignTop)
        
        # Añadir mensaje informativo cuando no hay diapositivas
        self.mensaje_vacio = QLabel("Aquí se mostrarán las vistas previas\nde las diapositivas conforme\nse vayan generando.")
        self.mensaje_vacio.setAlignment(Qt.AlignCenter)
        self.mensaje_vacio.setFont(QFont("Arial", 14))
        self.mensaje_vacio.setStyleSheet("color: #888; padding: 100px;")
        self.contenedor_layout.addWidget(self.mensaje_vacio, 1, Qt.AlignCenter)
        
        self.contenedor.setLayout(self.contenedor_layout)
        
        
        scroll.setWidget(self.contenedor)
        layout.addWidget(scroll)
        
        self.setLayout(layout)

    # Función para agregar una nueva diapositiva a la vista previa  
    def agregar_diapositiva(self, imagen_path, titulo, contenido):
        # Si es la primera diapositiva, ocultar el mensaje
        if not self.slides and hasattr(self, 'mensaje_vacio'):
            self.mensaje_vacio.hide()
        
        if os.path.exists(imagen_path):
            # Crear un frame para contener la diapositiva
            slide_frame = QFrame()
            slide_frame.setFrameStyle(QFrame.Box)
            slide_layout = QVBoxLayout()
            
            # Agregar título
            titulo_label = QLabel(titulo)
            titulo_label.setAlignment(Qt.AlignCenter)
            titulo_label.setFont(QFont("Arial", 12, QFont.Bold))
            titulo_label.setWordWrap(True)
            slide_layout.addWidget(titulo_label)
            
            # Agregar imagen
            imagen_label = QLabel()
            pixmap = QPixmap(imagen_path)
            pixmap = pixmap.scaled(700, 525, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            imagen_label.setPixmap(pixmap)
            imagen_label.setAlignment(Qt.AlignCenter)
            slide_layout.addWidget(imagen_label)
            
            # Agregar contenido
            contenido_label = QLabel(contenido)
            contenido_label.setAlignment(Qt.AlignLeft)
            contenido_label.setWordWrap(True)
            contenido_label.setFont(QFont("Arial", 10))
            contenido_label.setStyleSheet("padding: 10px;")
            slide_layout.addWidget(contenido_label)
            
            # Agregar separador
            separador = QFrame()
            separador.setFrameShape(QFrame.HLine)
            separador.setFrameShadow(QFrame.Sunken)
            
            slide_frame.setLayout(slide_layout)
            self.contenedor_layout.addWidget(slide_frame)
            self.contenedor_layout.addWidget(separador)
            
            self.slides.append(slide_frame)
            
            # Asegurar que la última diapositiva sea visible
            self.contenedor.adjustSize() 