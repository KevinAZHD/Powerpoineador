from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QPushButton, QSizePolicy, QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QResizeEvent
import os, sys
from Traducciones import obtener_traduccion

# Función para obtener la ruta de un recurso
def resource_path(relative_path):
    try:
        # Intenta obtener la ruta base del ejecutable empaquetado
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usa la ruta actual del proyecto
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Clase para la ventana de vista previa de diapositivas
class VentanaVistaPrevia(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_language = 'es'
        
        # Obtener el idioma del padre si está disponible
        if parent and hasattr(parent, 'current_language'):
            self.current_language = parent.current_language
        elif parent and hasattr(parent, 'parent') and parent.parent and hasattr(parent.parent, 'current_language'):
            self.current_language = parent.parent.current_language
        
        self.setMinimumSize(600, 350)  # Reducir altura mínima
        
        # Inicializar la lista de todas las diapositivas
        self.all_slides_data = []
        self.current_slide_index = -1
        
        # Variable para controlar si el usuario está navegando manualmente
        self.modo_navegacion = False
        
        # Crear layout principal
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)  # Reducir espacio
        
        # Crear área de desplazamiento
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Widget contenedor para la diapositiva actual
        self.contenedor = QWidget()
        self.contenedor.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.contenedor_layout = QVBoxLayout()
        self.contenedor_layout.setAlignment(Qt.AlignCenter)
        self.contenedor_layout.setContentsMargins(5, 5, 5, 5)  # Reducir márgenes
        self.contenedor_layout.setSpacing(5)  # Reducir espaciado
        
        # Añadir mensaje informativo cuando no hay diapositivas
        self.mensaje_vacio = QLabel()
        self.mensaje_vacio.setAlignment(Qt.AlignCenter)
        self.mensaje_vacio.setFont(QFont("Arial", 12))  # Reducir tamaño de fuente
        self.mensaje_vacio.setStyleSheet("color: #888; padding: 50px;")  # Reducir padding
        self.mensaje_vacio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Añadir imagen de previsualización
        self.imagen_preview = QLabel()
        self.imagen_preview.setAlignment(Qt.AlignCenter)
        pixmap = QPixmap(resource_path("iconos/icon.png"))
        if not pixmap.isNull():
            pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.imagen_preview.setPixmap(pixmap)
        self.imagen_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        preview_container = QVBoxLayout()
        preview_container.setAlignment(Qt.AlignCenter)
        preview_container.addWidget(self.imagen_preview)
        preview_container.addWidget(self.mensaje_vacio)
        
        # Contenedor para el mensaje vacío y la imagen
        empty_widget = QWidget()
        empty_widget.setLayout(preview_container)
        empty_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.contenedor_layout.addWidget(empty_widget, 1, Qt.AlignCenter)
        
        self.contenedor.setLayout(self.contenedor_layout)
        
        self.scroll.setWidget(self.contenedor)
        layout.addWidget(self.scroll, 1)
        
        # Añadir botones de navegación
        nav_layout = QHBoxLayout()
        nav_layout.setContentsMargins(5, 0, 5, 0)  # Reducir márgenes
        nav_layout.setSpacing(10)  # Reducir espacio
        
        # Inicializar los botones con texto temporal, se actualizará en actualizar_idioma
        self.prev_button = QPushButton("< Anterior")
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.mostrar_diapositiva_anterior)
        self.prev_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.prev_button.setFixedHeight(25)  # Altura reducida
        
        self.slide_counter_label = QLabel("0/0")
        self.slide_counter_label.setAlignment(Qt.AlignCenter)
        self.slide_counter_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        
        self.next_button = QPushButton("Siguiente >")
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.mostrar_diapositiva_siguiente)
        self.next_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        self.next_button.setFixedHeight(25)  # Altura reducida
        
        nav_layout.addWidget(self.prev_button)
        nav_layout.addWidget(self.slide_counter_label)
        nav_layout.addWidget(self.next_button)
        
        layout.addLayout(nav_layout)
        
        self.setLayout(layout)
        
        # Guardar las proporciones originales para el escalado responsivo
        self.original_width = self.width()
        self.original_height = self.height()
        
        # Conectar evento de redimensionamiento
        self.resized = False
        
        # Aplicar traducciones al iniciar - asegurarnos de que se actualicen todos los textos
        self.actualizar_idioma(self.current_language)
        
        # Habilitar eventos de rueda del mouse para navegación entre diapositivas
        self.setMouseTracking(True)
    
    # Manejar eventos de rueda del mouse para la navegación entre diapositivas
    def wheelEvent(self, event):
        # Solo procesar el evento si hay diapositivas
        if self.all_slides_data and len(self.all_slides_data) > 0:
            # Detectar dirección del scroll
            if event.angleDelta().y() > 0:
                # Scroll hacia arriba - ir a diapositiva anterior
                self.mostrar_diapositiva_anterior()
            else:
                # Scroll hacia abajo - ir a diapositiva siguiente
                self.mostrar_diapositiva_siguiente()
            
            # Consumir el evento para evitar comportamiento estándar
            event.accept()
        else:
            # Si no hay diapositivas, permitir el comportamiento normal de scroll
            super().wheelEvent(event)
    
    # Capturar evento de redimensionamiento
    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        if self.current_slide_index >= 0 and not self.resized:
            # Usar un temporizador para evitar múltiples actualizaciones durante el redimensionamiento
            self.resized = True
            self.mostrar_diapositiva_actual()
            self.resized = False
    
    # Función para actualizar el idioma de la interfaz
    def actualizar_idioma(self, language):
        try:
            # Establecer el idioma actual
            self.current_language = language
            
            # Actualizar título de la ventana de forma segura
            try:
                self.setWindowTitle(obtener_traduccion('vista_previa_title', self.current_language))
            except:
                pass
            
            # Actualizar textos de forma segura sin intentar modificar widgets que puedan estar eliminados
            try:
                # Actualizar solo los textos de los botones
                self.actualizar_textos_botones()
            except Exception as e:
                print(f"Error al actualizar botones: {str(e)}")
            
            # Si no hay diapositivas, forzar una reconstrucción completa de la vista
            if not self.all_slides_data or self.current_slide_index < 0:
                try:
                    # Eliminar completamente el contenido actual y recrearlo
                    self.limpiar_contenedor()
                    
                    # Recrear la vista desde cero
                    self.mostrar_diapositiva_actual()
                except Exception as e:
                    print(f"Error al recrear vista vacía: {str(e)}")
            else:
                # Si hay diapositivas, simplemente actualizar la vista actual
                try:
                    self.mostrar_diapositiva_actual()
                except Exception as e:
                    print(f"Error al actualizar diapositiva actual: {str(e)}")
        except Exception as e:
            print(f"Error en actualizar_idioma: {str(e)}")
    
    # Función para actualizar textos de los botones de navegación
    def actualizar_textos_botones(self):
        try:
            # Obtener traducciones
            texto_anterior = obtener_traduccion('slide_previous', self.current_language)
            if not texto_anterior:
                texto_anterior = "Anterior"
                
            texto_siguiente = obtener_traduccion('slide_next', self.current_language)
            if not texto_siguiente:
                texto_siguiente = "Siguiente"
            
            # Verificar si los botones existen antes de actualizarlos
            if hasattr(self, 'prev_button') and self.prev_button is not None:
                try:
                    self.prev_button.setText("< " + texto_anterior)
                except RuntimeError:
                    # Si el botón ya fue eliminado, recrearlo
                    self.prev_button = QPushButton("< " + texto_anterior)
                    self.prev_button.setEnabled(False)
                    self.prev_button.clicked.connect(self.mostrar_diapositiva_anterior)
                    self.prev_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                    self.prev_button.setFixedHeight(25)
                
            if hasattr(self, 'next_button') and self.next_button is not None:
                try:
                    self.next_button.setText(texto_siguiente + " >")
                except RuntimeError:
                    # Si el botón ya fue eliminado, recrearlo
                    self.next_button = QPushButton(texto_siguiente + " >")
                    self.next_button.setEnabled(False)
                    self.next_button.clicked.connect(self.mostrar_diapositiva_siguiente)
                    self.next_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
                    self.next_button.setFixedHeight(25)
        except Exception as e:
            print(f"Error al actualizar textos de botones: {str(e)}")
    
    # Función para mostrar la diapositiva actual
    def mostrar_diapositiva_actual(self):
        try:
            # Limpiar el contenedor de diapositivas
            self.limpiar_contenedor()
            
            # Verificar que hay diapositivas y que el índice es válido
            if not self.all_slides_data or self.current_slide_index < 0:
                # Recrear el mensaje vacío para asegurar que no haya problemas con objetos eliminados
                empty_widget = QWidget()
                preview_container = QVBoxLayout(empty_widget)
                preview_container.setAlignment(Qt.AlignCenter)
                
                # Recrear la imagen de previsualización
                imagen_preview = QLabel()
                imagen_preview.setAlignment(Qt.AlignCenter)
                pixmap = QPixmap(resource_path("iconos/icon.png"))
                if not pixmap.isNull():
                    pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    imagen_preview.setPixmap(pixmap)
                imagen_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                # Recrear el mensaje vacío - IMPORTANTE: siempre usar el idioma actual
                mensaje_vacio = QLabel()
                mensaje_vacio.setAlignment(Qt.AlignCenter)
                mensaje_vacio.setFont(QFont("Arial", 12))
                mensaje_vacio.setStyleSheet("color: #888; padding: 50px;")
                mensaje_vacio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
                # Obtener el texto traducido con manejo de errores
                try:
                    mensaje = obtener_traduccion('vista_previa_empty_message', self.current_language)
                    if not mensaje:
                        mensaje = "Aquí aparecerán las diapositivas generadas"
                except Exception:
                    mensaje = "Aquí aparecerán las diapositivas generadas"
                
                mensaje_vacio.setText(mensaje)
                
                # Guardar referencia al mensaje vacío nuevo
                self.mensaje_vacio = mensaje_vacio
                
                preview_container.addWidget(imagen_preview)
                preview_container.addWidget(mensaje_vacio)
                self.contenedor_layout.addWidget(empty_widget, 1, Qt.AlignCenter)
                return
            
            # Obtener datos de la diapositiva actual
            datos = self.all_slides_data[self.current_slide_index]
            
            # Crear frame para la diapositiva
            slide_frame = QFrame()
            slide_frame.setFrameStyle(QFrame.Box)
            slide_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            slide_layout = QVBoxLayout()
            slide_layout.setSpacing(8)
            slide_layout.setContentsMargins(8, 8, 8, 8)
            
            # Calcular tamaños responsivos basados en el tamaño disponible
            available_width = self.scroll.width() - 30  # Reducir márgenes para dar más espacio
            available_height = self.scroll.height() - 100  # Reducir espacio reservado para texto
            
            # Agregar título
            titulo_label = QLabel(datos['titulo'])
            titulo_label.setAlignment(Qt.AlignCenter)
            titulo_label.setWordWrap(True)
            titulo_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            
            # Calcular tamaño de fuente responsivo para el título
            font_size = max(10, min(14, int(available_width / 55)))
            font = QFont("Arial", font_size, QFont.Bold)
            titulo_label.setFont(font)
            titulo_label.setMaximumHeight(int(available_height * 0.15))
            
            slide_layout.addWidget(titulo_label)
            
            # Agregar imagen con mayor prioridad
            imagen_label = QLabel()
            imagen_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            imagen_label.setAlignment(Qt.AlignCenter)
            
            # Cargar y escalar la imagen de forma responsiva con mayores proporciones
            pixmap = QPixmap(datos['imagen_path'])
            max_img_width = int(available_width * 0.95)  # Aumentar ancho al 95%
            max_img_height = int(available_height * 0.85)  # Aumentar altura al 85%
            
            # Verificar que la imagen no sea demasiado pequeña
            min_width = 400
            if max_img_width < min_width and available_width >= min_width:
                max_img_width = min_width
            
            scaled_pixmap = pixmap.scaled(
                max_img_width, 
                max_img_height,
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            )
            imagen_label.setPixmap(scaled_pixmap)
            imagen_label.setMinimumHeight(int(available_height * 0.6))  # Garantizar altura mínima
            
            # Dar más espacio a la imagen (factor 3 en vez de 1)
            slide_layout.addWidget(imagen_label, 3)
            
            # Agregar contenido con menos espacio
            contenido_label = QLabel(datos['contenido'])
            contenido_label.setAlignment(Qt.AlignLeft)
            contenido_label.setWordWrap(True)
            contenido_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            
            # Calcular tamaño de fuente responsivo para el contenido (más pequeño)
            content_font_size = max(8, min(11, int(available_width / 75)))
            content_font = QFont("Arial", content_font_size)
            contenido_label.setFont(content_font)
            contenido_label.setStyleSheet(f"padding: {int(available_width/120)}px;")
            contenido_label.setMaximumHeight(int(available_height * 0.25))  # Limitar altura máxima
            
            slide_layout.addWidget(contenido_label)
            
            slide_frame.setLayout(slide_layout)
            self.contenedor_layout.addWidget(slide_frame)
            
            # Actualizar el contador de diapositivas
            self.slide_counter_label.setText(f"{self.current_slide_index + 1}/{len(self.all_slides_data)}")
            
            # Si estamos viendo la última diapositiva, desactivar el modo navegación
            if self.current_slide_index == len(self.all_slides_data) - 1:
                self.modo_navegacion = False
            
            # Asegurar que la diapositiva sea visible
            self.contenedor.adjustSize()
        except Exception as e:
            print(f"Error en mostrar_diapositiva_actual: {str(e)}")

    # Función para limpiar el contenedor de diapositivas
    def limpiar_contenedor(self):
        # Eliminar todos los widgets del contenedor
        while self.contenedor_layout.count():
            item = self.contenedor_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    # Función para mostrar la diapositiva anterior
    def mostrar_diapositiva_anterior(self):
        if self.current_slide_index > 0:
            # Activar el modo navegación
            self.modo_navegacion = True
            self.current_slide_index -= 1
            self.mostrar_diapositiva_actual()
            self.actualizar_botones_navegacion()

    # Función para mostrar la diapositiva siguiente
    def mostrar_diapositiva_siguiente(self):
        if self.current_slide_index < len(self.all_slides_data) - 1:
            # Activar el modo navegación si no estamos en la última
            if self.current_slide_index < len(self.all_slides_data) - 2:
                self.modo_navegacion = True
            else:
                # Si vamos a la última, desactivar modo navegación
                self.modo_navegacion = False
                
            self.current_slide_index += 1
            self.mostrar_diapositiva_actual()
            self.actualizar_botones_navegacion()

    # Función para actualizar el estado de los botones de navegación
    def actualizar_botones_navegacion(self):
        # Activar/desactivar botones según la posición actual
        self.prev_button.setEnabled(self.current_slide_index > 0)
        self.next_button.setEnabled(self.current_slide_index < len(self.all_slides_data) - 1) 
        
    # Función para resetear completamente la vista previa
    def reset_completo(self):
        try:
            # Limpiar la lista de diapositivas
            self.all_slides_data = []
            # Reiniciar el índice
            self.current_slide_index = -1
            # Desactivar botones de navegación
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            # Resetear contador
            self.slide_counter_label.setText("0/0")
            # Desactivar modo navegación
            self.modo_navegacion = False
            
            # Limpiar el contenedor y mostrar mensaje vacío
            self.limpiar_contenedor()
            
            # Recrear el mensaje vacío para asegurar que no haya problemas con objetos eliminados
            empty_widget = QWidget()
            empty_widget.setStyleSheet("background-color: transparent;")
            preview_container = QVBoxLayout(empty_widget)
            preview_container.setAlignment(Qt.AlignCenter)
            preview_container.setContentsMargins(0, 0, 0, 0)
            preview_container.setSpacing(10)
            
            # Recrear la imagen de previsualización
            imagen_preview = QLabel()
            imagen_preview.setAlignment(Qt.AlignCenter)
            pixmap = QPixmap(resource_path("iconos/icon.png"))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(128, 128, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                imagen_preview.setPixmap(pixmap)
            imagen_preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            imagen_preview.setStyleSheet("background-color: transparent;")
            
            # Recrear el mensaje vacío - IMPORTANTE: siempre usar el idioma actual
            mensaje_vacio = QLabel()
            mensaje_vacio.setAlignment(Qt.AlignCenter)
            mensaje_vacio.setFont(QFont("Arial", 12))
            mensaje_vacio.setStyleSheet("color: #888; padding: 50px; background-color: transparent;")
            mensaje_vacio.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # Obtener el texto traducido con manejo de errores
            try:
                mensaje = obtener_traduccion('vista_previa_empty_message', self.current_language)
                if not mensaje:
                    mensaje = "Aquí aparecerán las diapositivas generadas"
            except Exception:
                mensaje = "Aquí aparecerán las diapositivas generadas"
            
            mensaje_vacio.setText(mensaje)
            
            # Guardar referencia al nuevo mensaje vacío
            self.mensaje_vacio = mensaje_vacio
            
            preview_container.addWidget(imagen_preview)
            preview_container.addWidget(mensaje_vacio)
            
            # Limpiar el layout anterior si existe
            while self.contenedor_layout.count():
                item = self.contenedor_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            
            # Agregar el nuevo widget al contenedor
            self.contenedor_layout.addWidget(empty_widget, 1, Qt.AlignCenter)
            
            # Forzar actualización visual
            empty_widget.update()
            self.update()
            QApplication.processEvents()
            
        except Exception as e:
            print(f"Error en reset_completo: {str(e)}")

    # Función para actualizar el mensaje cuando no hay diapositivas
    def actualizar_mensaje_vacio(self):
        try:
            mensaje = obtener_traduccion('vista_previa_empty_message', self.current_language)
            if not mensaje:
                mensaje = "Aquí aparecerán las diapositivas generadas"
            
            # Actualizar SOLO el objeto mensaje_vacio principal
            if hasattr(self, 'mensaje_vacio') and self.mensaje_vacio is not None:
                try:
                    self.mensaje_vacio.setText(mensaje)
                except RuntimeError:
                    # Ignorar si el objeto ya ha sido eliminado
                    pass
                
            # No intentar buscar en la jerarquía de widgets para evitar
            # acceder a widgets que puedan haber sido eliminados
        except Exception as e:
            print(f"Error en actualizar_mensaje_vacio: {str(e)}")

    # Función para agregar una nueva diapositiva a la vista previa  
    def agregar_diapositiva(self, imagen_path, titulo, contenido):
        # Guardar datos de la diapositiva
        if os.path.exists(imagen_path):
            self.all_slides_data.append({
                'imagen_path': imagen_path,
                'titulo': titulo,
                'contenido': contenido
            })
            
            # Solo actualizar a la última si no estamos en modo navegación
            if not self.modo_navegacion:
                self.current_slide_index = len(self.all_slides_data) - 1
                self.mostrar_diapositiva_actual()
            else:
                # Si estamos en modo navegación, solo actualizar el contador
                # con el total actualizado pero manteniendo la diapositiva actual
                self.slide_counter_label.setText(f"{self.current_slide_index + 1}/{len(self.all_slides_data)}")
            
            # Actualizar botones de navegación
            self.actualizar_botones_navegacion() 