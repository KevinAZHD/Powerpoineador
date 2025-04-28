from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QScrollArea, QFrame, QHBoxLayout, QPushButton, QSizePolicy, QApplication, QDialog, QLineEdit, QTextEdit, QFileDialog, QDialogButtonBox, QSpacerItem, QMessageBox
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QFont, QResizeEvent, QIcon
import os, sys
from Traducciones import obtener_traduccion

# Intentar importar python-pptx y manejar el error si no está instalado
try:
    import pptx
    from pptx.dml.color import RGBColor, MSO_COLOR_TYPE
    from pptx.util import Inches, Pt
    from pptx.enum.shapes import MSO_SHAPE_TYPE
    from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False
    # Podrías mostrar un mensaje al usuario aquí si es crucial, 
    # pero por ahora solo desactivaremos la funcionalidad.
    print("ADVERTENCIA: La biblioteca 'python-pptx' no está instalada. La edición directa de PPTX estará deshabilitada.")

# Función para obtener la ruta de un recurso
def resource_path(relative_path):
    try:
        # Intenta obtener la ruta base del ejecutable empaquetado
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usa la ruta actual del proyecto
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# --- Clase para el diálogo de edición de diapositivas ---
class EditSlideDialog(QDialog):
    def __init__(self, current_data, language, parent=None):
        super().__init__(parent)
        self.current_language = language
        self.initial_data = current_data
        self.new_image_path = current_data.get('imagen_path') # Inicializar con la ruta actual

        self.setWindowTitle(obtener_traduccion('edit_slide_dialog_title', self.current_language))
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # --- Campos de Edición ---
        # Título
        title_layout = QHBoxLayout()
        title_label = QLabel(obtener_traduccion('edit_title_label', self.current_language))
        self.title_edit = QLineEdit(current_data.get('titulo', ''))
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.title_edit)
        layout.addLayout(title_layout)

        # Contenido
        content_label = QLabel(obtener_traduccion('edit_content_label', self.current_language))
        layout.addWidget(content_label)
        # --- MODIFICADO: Crear vacío y usar setPlainText --- 
        self.content_edit = QTextEdit() # Crear vacío
        self.content_edit.setPlainText(current_data.get('contenido', '')) # Establecer como texto plano
        # ---------------------------------------------------
        # --- NUEVO: Desactivar rich text para mostrar texto plano ---
        self.content_edit.setAcceptRichText(False) # Mantener esto para evitar pegado de rich text
        # ----------------------------------------------------------
        self.content_edit.setMinimumHeight(100)
        layout.addWidget(self.content_edit)

        # Imagen
        image_layout = QHBoxLayout()
        image_label_text = obtener_traduccion('edit_image_label', self.current_language)
        image_label = QLabel(image_label_text)
        self.current_image_label = QLabel(os.path.basename(self.new_image_path) if self.new_image_path else "N/A")
        self.current_image_label.setWordWrap(True)
        browse_button = QPushButton(obtener_traduccion('edit_browse_button', self.current_language))
        browse_button.clicked.connect(self.browse_new_image)
        image_layout.addWidget(image_label)
        image_layout.addWidget(self.current_image_label, 1) # Darle más espacio
        image_layout.addWidget(browse_button)
        layout.addLayout(image_layout)

        # --- Botones OK/Cancel ---
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        save_button = button_box.button(QDialogButtonBox.Save)
        if save_button:
            save_button.setText(obtener_traduccion('edit_save', self.current_language))
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        if cancel_button:
            cancel_button.setText(obtener_traduccion('edit_cancel', self.current_language))
            
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def browse_new_image(self):
        image_filter_key = 'edit_image_filter'
        image_filter_formats = "*.png *.jpg *.jpeg *.bmp *.gif *.tiff"
        image_filter_text = obtener_traduccion(image_filter_key, self.current_language)
        if image_filter_text == image_filter_key: # Fallback si la traducción no existe
            image_filter_text = f"Imágenes ({image_filter_formats})"
        else:
            try:
                image_filter_text = image_filter_text.format(image_filter_formats)
            except KeyError:
                # Si el formato no funciona (p.ej., {} no presente en la traducción)
                image_filter_text = f"Imágenes ({image_filter_formats})"
                
        select_image_title = obtener_traduccion('edit_select_image', self.current_language)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            select_image_title,
            "", # Directorio inicial
            image_filter_text
        )
        if file_path and os.path.exists(file_path):
            self.new_image_path = file_path
            self.current_image_label.setText(os.path.basename(file_path))

    def get_edited_data(self):
        return {
            'titulo': self.title_edit.text(),
            'contenido': self.content_edit.toPlainText(),
            'imagen_path': self.new_image_path
        }
# --- Fin Clase EditSlideDialog ---

# Clase para la ventana de vista previa de diapositivas
class VentanaVistaPrevia(QWidget):
    # --- MODIFICADO: Añadir parámetros de formato y valores predeterminados ---
    def __init__(self, parent=None, 
                 title_font_name='Calibri', content_font_name='Calibri', 
                 title_font_size=16, content_font_size=10, 
                 title_bold=False, title_italic=False, title_underline=False, 
                 content_bold=False, content_italic=False, content_underline=False):
        super().__init__(parent)
        self.current_language = 'es'
        self.pptx_path = None # Ruta al archivo PPTX generado
        
        # --- NUEVO: Almacenar configuración de formato global ---
        self.title_font_name = title_font_name
        self.content_font_name = content_font_name
        self.title_font_size = title_font_size
        self.content_font_size = content_font_size
        self.title_bold = title_bold
        self.title_italic = title_italic
        self.title_underline = title_underline
        self.content_bold = content_bold
        self.content_italic = content_italic
        self.content_underline = content_underline
        # -------------------------------------------------------
        
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
        
        # Variable para almacenar el botón de edición (se crea/destruye dinámicamente)
        self.edit_button = None
    
    # --- NUEVO: Método para actualizar la configuración de formato ---
    def update_format_settings(self, title_font_name, content_font_name, 
                               title_font_size, content_font_size, 
                               title_bold, title_italic, title_underline, 
                               content_bold, content_italic, content_underline):
        self.title_font_name = title_font_name
        self.content_font_name = content_font_name
        self.title_font_size = title_font_size
        self.content_font_size = content_font_size
        self.title_bold = title_bold
        self.title_italic = title_italic
        self.title_underline = title_underline
        self.content_bold = content_bold
        self.content_italic = content_italic
        self.content_underline = content_underline
        print("Configuración de formato de VistaPrevia actualizada.") # Debug
    # -------------------------------------------------------------

    # --- Nueva función para establecer la ruta del PPTX ---
    def set_pptx_path(self, path):
        if os.path.exists(path):
            self.pptx_path = path
        else:
            self.pptx_path = None
            print(f"Advertencia: La ruta del PPTX proporcionada no existe: {path}")
            
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
                    # Actualizar texto del botón editar si existe
                    if self.edit_button:
                         self.edit_button.setToolTip(obtener_traduccion('edit_slide', self.current_language))
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
            self.edit_button = None # Resetear referencia al botón
            
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
            
            # --- Layout Superior (Título y Botón Editar) ---
            top_layout = QHBoxLayout()
            top_layout.setContentsMargins(0,0,0,0)
            top_layout.setSpacing(5)
            
            # --- Añadir espaciador izquierdo para compensar botón --- 
            button_width = 47 # Ancho del botón de edición
            left_spacer = QSpacerItem(button_width, 20, QSizePolicy.Fixed, QSizePolicy.Minimum)
            top_layout.addSpacerItem(left_spacer)
            # -----------------------------------------------------
            
            titulo_label = QLabel(datos['titulo'])
            titulo_label.setAlignment(Qt.AlignCenter)
            titulo_label.setWordWrap(True)
            # --- MODIFICADO: Usar config + cálculo dinámico responsivo ---
            # Calcular tamaño dinámico basado en ancho disponible
            available_width_title = self.scroll.width() - 80 # Ancho disponible (menos botón y márgenes)
            dynamic_title_size = max(10, int(available_width_title / 50)) # Tamaño basado en ancho, mínimo 10
            # Usar el menor entre el tamaño configurado y el dinámico calculado
            final_title_size = min(self.title_font_size, dynamic_title_size)
            
            title_font = QFont(self.title_font_name, final_title_size) # Usar tamaño final
            title_font.setBold(self.title_bold)
            title_font.setItalic(self.title_italic)
            title_font.setUnderline(self.title_underline)
            titulo_label.setFont(title_font)
            # ----------------------------------------------------------
            
            # Crear Botón Editar
            self.edit_button = QPushButton()
            icon_path = resource_path("iconos/editar.png")
            if os.path.exists(icon_path):
                self.edit_button.setIcon(QIcon(icon_path))
                self.edit_button.setIconSize(QSize(24, 24))
                self.edit_button.setFixedSize(QSize(32, 32))
            else:
                self.edit_button.setText("E") # Texto fallback si no hay icono
                self.edit_button.setFixedSize(QSize(32, 32))
                
            self.edit_button.setToolTip(obtener_traduccion('edit_slide', self.current_language))
            self.edit_button.setStyleSheet("QPushButton { border: none; background-color: transparent; padding: 2px; }")
            self.edit_button.setCursor(Qt.PointingHandCursor)
            self.edit_button.clicked.connect(self.editar_diapositiva_actual)
            # Deshabilitar si python-pptx no está disponible o no hay ruta PPTX
            self.edit_button.setEnabled(PPTX_AVAILABLE and self.pptx_path is not None) 
            
            top_layout.addWidget(titulo_label, 1) # Título toma el espacio extra
            top_layout.addWidget(self.edit_button, 0, Qt.AlignRight | Qt.AlignTop)
            
            slide_layout.addLayout(top_layout)
            # --- Fin Layout Superior ---
            
            # Calcular tamaños responsivos basados en el tamaño disponible
            available_width = self.scroll.width() - 30  # Reducir márgenes para dar más espacio
            available_height = self.scroll.height() - 100  # Reducir espacio reservado para texto y botón
            
            # Agregar imagen con mayor prioridad
            imagen_label = QLabel()
            imagen_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            imagen_label.setAlignment(Qt.AlignCenter)
            
            # Cargar y escalar la imagen de forma responsiva con mayores proporciones
            pixmap = QPixmap(datos['imagen_path'])
            if not pixmap.isNull(): # Comprobar si la imagen se cargó correctamente
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
            else:
                 imagen_label.setText(f"Error al cargar: {os.path.basename(datos['imagen_path'])}")
                 imagen_label.setStyleSheet("color: red;")
                 
            imagen_label.setMinimumHeight(int(available_height * 0.6))  # Garantizar altura mínima
            
            # Dar más espacio a la imagen (factor 3 en vez de 1)
            slide_layout.addWidget(imagen_label, 3)
            
            # Agregar contenido con menos espacio
            contenido_label = QLabel()
            # --- NUEVO: Forzar texto plano para evitar interpretación HTML ---
            contenido_label.setTextFormat(Qt.PlainText) 
            # -------------------------------------------------------------
            contenido_label.setText(datos['contenido']) # Establecer el texto DESPUÉS de fijar el formato
            contenido_label.setAlignment(Qt.AlignLeft)
            contenido_label.setWordWrap(True)
            contenido_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            
            # --- MODIFICADO: Usar config + cálculo dinámico responsivo ---
             # Calcular tamaño dinámico basado en ancho disponible
            available_width_content = self.scroll.width() - 40 # Ancho disponible (menos márgenes)
            dynamic_content_size = max(8, int(available_width_content / 70)) # Tamaño basado en ancho, mínimo 8
            # Usar el menor entre el tamaño configurado y el dinámico calculado
            final_content_size = min(self.content_font_size, dynamic_content_size)

            content_font = QFont(self.content_font_name, final_content_size) # Usar tamaño final
            content_font.setBold(self.content_bold)
            content_font.setItalic(self.content_italic)
            content_font.setUnderline(self.content_underline)
            contenido_label.setFont(content_font)
            # ---------------------------------------------------------------
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
            # Resetear botón editar
            self.edit_button = None 
            
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
            
            self.pptx_path = None # Olvidar la ruta del PPTX al resetear
            
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

    # --- Función modificada para manejar la edición y guardar en PPTX ---
    def editar_diapositiva_actual(self):
        if not PPTX_AVAILABLE:
             # Opcional: Mostrar mensaje al usuario informando que la función no está disponible
             QMessageBox.warning(self, "Función no disponible", "La biblioteca 'python-pptx' es necesaria para editar el archivo PPTX directamente. Por favor, instálala.")
             return
             
        if self.current_slide_index < 0 or self.current_slide_index >= len(self.all_slides_data):
            return # No hay diapositiva válida para editar
            
        current_data = self.all_slides_data[self.current_slide_index]
        
        # Crear y mostrar el diálogo de edición
        dialog = EditSlideDialog(current_data, self.current_language, self)
        if dialog.exec() == QDialog.Accepted:
            # Obtener los datos editados
            edited_data = dialog.get_edited_data()
            
            # 1. Actualizar los datos en la lista interna
            self.all_slides_data[self.current_slide_index] = edited_data
            
            # 2. Refrescar la vista previa para mostrar los cambios inmediatamente
            self.mostrar_diapositiva_actual()
            
            # 3. Aplicar los cambios al archivo PPTX
            # Pasar los datos originales también para poder encontrar las shapes correctas
            self._apply_changes_to_pptx(self.current_slide_index, edited_data, current_data)
            
    # --- Nueva función para aplicar cambios al archivo PPTX ---
    # Se añade 'original_data' para buscar las shapes por contenido original
    def _apply_changes_to_pptx(self, slide_index, edited_data, original_data):
        if not self.pptx_path or not os.path.exists(self.pptx_path):
            QMessageBox.warning(self,
                                obtener_traduccion('edit_save_pptx_error_title', self.current_language),
                                obtener_traduccion('edit_save_pptx_not_found_message', self.current_language))
            return

        try:
            prs = pptx.Presentation(self.pptx_path)

            # Asegurarse que el índice es válido para la presentación
            if slide_index < 0 or slide_index >= len(prs.slides):
                 raise ValueError(f"Índice de diapositiva ({slide_index}) fuera de rango.")

            slide = prs.slides[slide_index]

            # --- Actualizar Texto ---
            title_shape = None
            content_shape = None
            original_title = original_data.get('titulo', '').strip()
            original_content = original_data.get('contenido', '').strip()

            # Buscar shapes (sin cambios)
            for shape in slide.shapes:
                if shape.has_text_frame:
                    shape_text = shape.text_frame.text.strip()
                    if not title_shape and shape_text == original_title:
                        title_shape = shape
                        print(f"Shape de título encontrada por texto: '{original_title}'")
                    elif not content_shape and shape_text == original_content:
                        content_shape = shape
                        print(f"Shape de contenido encontrada por texto: '{original_content[:50]}...'")
                if title_shape and content_shape:
                    break
            
            # --- Actualizar Título (Lógica simplificada similar a la anterior, suele ser menos complejo) ---
            if title_shape:
                print(f"Actualizando título en shape: {title_shape.name if hasattr(title_shape, 'name') else 'N/A'}")
                original_alignment = PP_ALIGN.LEFT # Default
                original_color_rgb = RGBColor(255, 255, 255) # Default white
                try:
                    if title_shape.text_frame and title_shape.text_frame.paragraphs:
                        first_para = title_shape.text_frame.paragraphs[0]
                        original_alignment = first_para.alignment or PP_ALIGN.LEFT
                        if first_para.runs and hasattr(first_para.runs[0].font.color, 'type') and first_para.runs[0].font.color.type == MSO_COLOR_TYPE.RGB:
                            original_color_rgb = first_para.runs[0].font.color.rgb
                    print(f"Título original detectado - Alineación: {original_alignment}, Color RGB: {original_color_rgb}")
                except Exception as e:
                    print(f"WARN: No se pudo obtener formato original título: {e}, usando defaults.")

                try:
                    nuevo_titulo = edited_data['titulo']
                    tf = title_shape.text_frame
                    tf.clear()
                    lines = nuevo_titulo.split('\n')
                    p = tf.add_paragraph()
                    p.text = lines[0] if lines else ""
                    for line in lines[1:]:
                        p = tf.add_paragraph()
                        p.text = line
                    
                    for para in tf.paragraphs:
                        para.alignment = original_alignment
                        for run in para.runs:
                            run.font.name = self.title_font_name
                            run.font.size = Pt(self.title_font_size)
                            run.font.bold = self.title_bold
                            run.font.italic = self.title_italic
                            run.font.underline = self.title_underline
                            run.font.color.rgb = original_color_rgb
                    print(f"Título actualizado a: '{nuevo_titulo}'")
                except Exception as e:
                    print(f"Error fatal al procesar título: {e}")
                    QMessageBox.critical(self, "Error PPTX", f"Error al actualizar el título: {e}")
            else:
                print("ERROR: No se encontró la shape del título para actualizar.")

            # --- Actualizar Contenido (Lógica Mejorada) ---
            if content_shape:
                print(f"Actualizando contenido en shape: {content_shape.name if hasattr(content_shape, 'name') else 'N/A'}")
                original_alignments = []
                original_colors_rgb = []
                original_margins = { "left": None, "right": None, "top": None, "bottom": None }
                original_vertical_anchor = MSO_ANCHOR.TOP # Default
                
                # --- 1. Guardar formato original detallado --- 
                try:
                    original_tf = content_shape.text_frame
                    # Guardar márgenes y anclaje del text_frame
                    original_margins["left"] = original_tf.margin_left
                    original_margins["right"] = original_tf.margin_right
                    original_margins["top"] = original_tf.margin_top
                    original_margins["bottom"] = original_tf.margin_bottom
                    original_vertical_anchor = original_tf.vertical_anchor or MSO_ANCHOR.TOP
                    print(f"Contenido original - Márgenes: {original_margins}, Anclaje: {original_vertical_anchor}")

                    # Guardar formato de cada párrafo original
                    for p_idx, para in enumerate(original_tf.paragraphs):
                        # Guardar alineación
                        alignment = para.alignment or PP_ALIGN.LEFT # Default a Izquierda si no está definida
                        original_alignments.append(alignment)
                        
                        # --- Guardar color (REFINADO) --- 
                        color_rgb = None
                        # Intentar obtener del primer run con color RGB explícito
                        found_run_color = False
                        if para.runs:
                            for run in para.runs:
                                try:
                                    if hasattr(run.font.color, 'type') and run.font.color.type == MSO_COLOR_TYPE.RGB:
                                        color_rgb = run.font.color.rgb
                                        found_run_color = True
                                        # print(f"DEBUG: Color RGB encontrado en run: {color_rgb}")
                                        break # Usar el primer color RGB encontrado en los runs
                                except AttributeError:
                                    # Puede que el run no tenga font o color definidos
                                    continue 
                        
                        # Si no se encontró en los runs, intentar obtener del párrafo
                        if not found_run_color:
                            try:
                                if hasattr(para.font.color, 'type') and para.font.color.type == MSO_COLOR_TYPE.RGB:
                                    color_rgb = para.font.color.rgb
                                    # print(f"DEBUG: Color RGB encontrado en párrafo: {color_rgb}")
                                else:
                                    # Opcional: Comprobar si es color de tema, aunque no podamos usarlo directamente
                                    if hasattr(para.font.color, 'type') and para.font.color.type == MSO_COLOR_TYPE.THEME:
                                         print(f"WARN: Contenido Para {p_idx} - Color es de TEMA, no RGB. No se puede preservar directamente.")
                                    else:
                                         print(f"WARN: Contenido Para {p_idx} - No se pudo obtener color RGB (ni runs ni párrafo). Tipo: {getattr(para.font.color, 'type', 'N/A')}")
                            except AttributeError:
                                print(f"WARN: Contenido Para {p_idx} - Atributo de color no encontrado en párrafo.")
                        
                        original_colors_rgb.append(color_rgb) # Puede ser None
                        # print(f"Contenido Para {p_idx} original - Alineación: {alignment}, Color Guardado: {color_rgb}")
                        
                except Exception as e:
                    print(f"WARN: No se pudo obtener el formato original completo del contenido: {e}")
                    import traceback
                    traceback.print_exc()

                # --- 2. Limpiar y recrear párrafos --- 
                try:
                    nuevo_contenido = edited_data['contenido']
                    tf = content_shape.text_frame
                    tf.clear()
                    lines = nuevo_contenido.split('\n')
                    # Crear los párrafos nuevos
                    new_paragraphs = []
                    p = tf.add_paragraph()
                    p.text = lines[0] if lines else ""
                    new_paragraphs.append(p)
                    for line in lines[1:]:
                        p = tf.add_paragraph()
                        p.text = line
                        new_paragraphs.append(p)

                    # --- 3. Reaplicar formato específico --- 
                    # Reaplicar márgenes y anclaje al text_frame
                    if original_margins["left"] is not None: tf.margin_left = original_margins["left"]
                    if original_margins["right"] is not None: tf.margin_right = original_margins["right"]
                    if original_margins["top"] is not None: tf.margin_top = original_margins["top"]
                    if original_margins["bottom"] is not None: tf.margin_bottom = original_margins["bottom"]
                    tf.vertical_anchor = original_vertical_anchor
                    print(f"Márgenes y anclaje reaplicados al TextFrame.")

                    # Aplicar formato a cada párrafo nuevo
                    num_original_paras = len(original_alignments)
                    default_color = RGBColor(0, 0, 0) # Negro por defecto
                    
                    for para_idx, para in enumerate(new_paragraphs):
                        # --- Determinar Alineación y Color a Aplicar ---
                        alignment_to_apply = PP_ALIGN.LEFT # Default
                        if para_idx < num_original_paras:
                            alignment_to_apply = original_alignments[para_idx]
                        elif num_original_paras > 0:
                            alignment_to_apply = original_alignments[-1]

                        color_to_apply = default_color # Default
                        # Usar color detectado si existe y no es None
                        if para_idx < len(original_colors_rgb) and original_colors_rgb[para_idx] is not None:
                            color_to_apply = original_colors_rgb[para_idx]
                        elif original_colors_rgb and original_colors_rgb[-1] is not None:
                             color_to_apply = original_colors_rgb[-1]
                             if para_idx >= len(original_colors_rgb): # Informar si se usa fallback del último párrafo
                                 print(f"WARN: Contenido Para {para_idx} - Usando color del último párrafo original como fallback.")
                        elif color_to_apply == default_color:
                             print(f"WARN: Contenido Para {para_idx} - Usando color NEGRO de fallback (no se detectó RGB original).")

                        # --- Aplicar Formato a Nivel de Párrafo --- 
                        para.alignment = alignment_to_apply
                        # Aplicar propiedades de fuente directamente al párrafo
                        para.font.name = self.content_font_name
                        para.font.size = Pt(self.content_font_size)
                        para.font.bold = self.content_bold
                        para.font.italic = self.content_italic
                        para.font.underline = self.content_underline
                        para.font.color.rgb = color_to_apply
                        # print(f"Contenido Para {para_idx}: Align={alignment_to_apply}, Color={color_to_apply}, Font={para.font.name}, Size={para.font.size}pt")
                        
                        # --- Ya no se itera sobre runs para aplicar formato base ---
                        # for run in para.runs:
                        #     run.font.name = self.content_font_name
                        #     run.font.size = Pt(self.content_font_size)
                        #     run.font.bold = self.content_bold
                        #     run.font.italic = self.content_italic
                        #     run.font.underline = self.content_underline
                        #     run.font.color.rgb = color_to_apply
                        #     # print(f"  Run: Color aplicado {color_to_apply}")

                    # Optional: Adjust text frame shape to fit text?
                    # Considerar si MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT es deseable aquí
                    # tf.auto_size = MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT 
                    print(f"Contenido actualizado y formato reaplicado para: '{nuevo_contenido[:50]}...'")

                except Exception as e:
                    print(f"Error fatal al procesar contenido: {e}")
                    import traceback
                    traceback.print_exc() # Imprimir stack trace para depuración
                    QMessageBox.critical(self, "Error PPTX", f"Error al actualizar el contenido: {e}")
            else:
                print("ERROR: No se encontró la shape del contenido para actualizar.")


            # --- Actualizar Imagen (Lógica sin cambios respecto a la versión anterior) ---
            pic_shape = None
            for shp in slide.shapes:
                # Asegurarse de que no sea un placeholder de imagen vacío
                if shp.shape_type == MSO_SHAPE_TYPE.PICTURE:
                    pic_shape = shp
                    print(f"Shape de imagen encontrada: {pic_shape.name if hasattr(pic_shape, 'name') else 'N/A'}") # Debug
                    break # Usar la primera que se encuentre
                elif shp.shape_type == MSO_SHAPE_TYPE.PLACEHOLDER and hasattr(shp, 'placeholder_format') and shp.placeholder_format.type == MSO_SHAPE_TYPE.PICTURE:
                     # Podría ser un placeholder de imagen, verificar si tiene imagen
                     if hasattr(shp, 'image'):
                         pic_shape = shp
                         print(f"Shape de imagen (placeholder) encontrada: {pic_shape.name if hasattr(pic_shape, 'name') else 'N/A'}") # Debug
                         break

            if pic_shape:
                new_image_path = edited_data['imagen_path']
                original_image_path = original_data.get('imagen_path')

                # ---- SOLO REEMPLAZAR SI LA IMAGEN CAMBIÓ Y ES VÁLIDA ----
                if os.path.exists(new_image_path) and new_image_path != original_image_path:
                    print(f"La ruta de la imagen cambió a: {new_image_path}. Reemplazando...") # Debug
                    # Obtener posición y tamaño de la imagen original ANTES de borrarla
                    left, top, width, height = pic_shape.left, pic_shape.top, pic_shape.width, pic_shape.height

                    # Eliminar la shape de imagen antigua
                    # Comprobar si es un placeholder antes de intentar eliminarlo de la forma estándar
                    if pic_shape.shape_type != MSO_SHAPE_TYPE.PLACEHOLDER:
                        try:
                            sp = pic_shape._element
                            sp.getparent().remove(sp)
                            print("Shape de imagen anterior eliminada.") # Debug
                        except Exception as e_rem:
                            print(f"WARN: No se pudo eliminar la shape de imagen anterior directamente: {e_rem}")
                            # Podría ser necesario manejar placeholders de imagen de forma diferente si la eliminación directa falla
                    else:
                         print("INFO: La imagen original es un placeholder, no se elimina directamente.")

                    # Añadir la nueva imagen en la misma posición/tamaño
                    try:
                        print(f"Añadiendo nueva imagen: {new_image_path}") # Debug
                        # Asegurarse de que el tamaño no sea inválido
                        if width is not None and height is not None and width > 0 and height > 0:
                           slide.shapes.add_picture(new_image_path, left, top, width, height)
                        elif width is not None and width > 0:
                             print(f"WARN: Altura de imagen original inválida (H:{height}). Añadiendo con ancho fijo.")
                             slide.shapes.add_picture(new_image_path, left, top, width=width)
                        elif height is not None and height > 0:
                             print(f"WARN: Ancho de imagen original inválido (W:{width}). Añadiendo con altura fija.")
                             slide.shapes.add_picture(new_image_path, left, top, height=height)
                        else:
                             print(f"WARN: Dimensiones de imagen original inválidas (W:{width}, H:{height}). Añadiendo con tamaño por defecto.")
                             slide.shapes.add_picture(new_image_path, left, top)
                    except Exception as e_add:
                         print(f"ERROR: No se pudo añadir la nueva imagen: {e_add}")
                         QMessageBox.warning(self, "Error Imagen", f"No se pudo reemplazar la imagen: {e_add}")

                elif not os.path.exists(new_image_path):
                    print(f"Error: La nueva imagen no existe en la ruta: {new_image_path}")
                    QMessageBox.warning(self, "Error Imagen", f"La ruta de la nueva imagen no es válida:\n{new_image_path}")
                else:
                    # La ruta es la misma o la nueva no existe pero es igual a la original
                    print("La imagen no ha cambiado o la nueva ruta no es válida y es igual a la original. No se reemplaza.") # Debug
                # ---- FIN DEL BLOQUE DE REEMPLAZO ----
            else:
                print("WARN: No se encontró ninguna shape de imagen para actualizar.")

            # --- Guardar la presentación ---
            prs.save(self.pptx_path)
            print("Presentación guardada con éxito.") # Debug

        except Exception as e:
            print(f"Error general al guardar cambios en PPTX: {e}")
            import traceback
            traceback.print_exc() # Imprimir stack trace completo
            QMessageBox.critical(self,
                               obtener_traduccion('edit_save_pptx_error_title', self.current_language),
                               obtener_traduccion('edit_save_pptx_error_message', self.current_language).format(error=e)) 