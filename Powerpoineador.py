import sys, os, requests, json
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, QPushButton,
    QLabel, QMessageBox, QCheckBox, QMainWindow, QLineEdit, QFileDialog)
from Ventana_progreso import LogWindow

# Definir la ruta de la carpeta de datos de la aplicación
APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
# Verificar si la carpeta de datos de la aplicación existe, y si no, crearla
if not os.path.exists(APP_DATA_DIR):
    os.makedirs(APP_DATA_DIR)
# Definir la ruta del archivo de configuración
CONFIG_FILE = os.path.join(APP_DATA_DIR, 'config.json')

# Función para obtener la ruta de un recurso
def resource_path(relative_path):
    try:
        # Obtener la ruta base del ejecutable empaquetado
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usar la ruta actual del proyecto
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Clase para la ventana de configuración de la clave API de Replicate
class APIKeyWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Configuración API Replicate')
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
        self.setWindowModality(Qt.ApplicationModal)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_status)
        
        if self.parent:
            parent_geometry = self.parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2 - (parent_geometry.height() // 8)
            self.move(x, y)
        
        layout = QVBoxLayout()
        
        logo_label = QLabel()
        pixmap = QPixmap(resource_path("iconos/replicate.png"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio)
            logo_label.setPixmap(scaled_pixmap)
            layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        
        layout.addWidget(QLabel('Escriba su clave API de Replicate:'))
        self.api_input = QLineEdit()
        self.api_input.setMinimumWidth(300)
        self.api_input.textChanged.connect(self.clear_status)
        if parent and parent.api_key:
            self.api_input.setText(parent.api_key)
        
        self.status_label = QLabel('')
        self.status_label.setStyleSheet("color: red; qproperty-alignment: AlignCenter;")
        
        validate_btn = QPushButton('Validar y guardar')
        validate_btn.clicked.connect(self.validate_api)
        layout.addWidget(self.api_input)
        layout.addWidget(self.status_label)
        layout.addWidget(validate_btn)
        self.setLayout(layout)

    # Función para limpiar el estado de la ventana
    def clear_status(self):
        if hasattr(self, 'status_label'):
            self.status_label.clear()
            self.timer.stop()
    # Función para mostrar un mensaje de estado
    def show_status(self, message):
        self.status_label.setText(message)
        self.timer.start(2000)

    # Función para validar la clave API de Replicate
    def validate_api(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            self.show_status('No puede dejar el campo vacío')
            return
        try:
            headers = {"Authorization": f"Token {api_key}"}
            response = requests.get("https://api.replicate.com/v1/models", headers=headers)
            if response.status_code == 200:
                if self.parent:
                    self.parent.set_api_key(api_key)
                self.close()
            else:
                self.show_status('Clave inválida')
        except Exception as e:
            self.show_status(f'Error de conexión: {str(e)}')

# Clase para la ventana de configuración de la clave API de xAI
class GrokAPIKeyWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Configuración API xAI')
        self.setFixedSize(650, 300)
        self.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
        self.setWindowModality(Qt.ApplicationModal)
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.clear_status)
        
        if self.parent:
            parent_geometry = self.parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2 - (parent_geometry.height() // 8)
            self.move(x, y)
        
        layout = QVBoxLayout()
        
        logo_label = QLabel()
        pixmap = QPixmap(resource_path("iconos/xai.jpg"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio)
            logo_label.setPixmap(scaled_pixmap)
            layout.addWidget(logo_label, alignment=Qt.AlignCenter)
        
        layout.addWidget(QLabel('Escriba su clave API de xAI:'))
        self.api_input = QLineEdit()
        self.api_input.setMinimumWidth(300)
        self.api_input.textChanged.connect(self.clear_status)
        if parent and parent.grok_api_key:
            self.api_input.setText(parent.grok_api_key)
        
        self.status_label = QLabel('')
        self.status_label.setStyleSheet("color: red; qproperty-alignment: AlignCenter;")
        
        validate_btn = QPushButton('Validar y guardar')
        validate_btn.clicked.connect(self.validate_api)
        layout.addWidget(self.api_input)
        layout.addWidget(self.status_label)
        layout.addWidget(validate_btn)
        self.setLayout(layout)

    # Función para limpiar el estado de la ventana
    def clear_status(self):
        if hasattr(self, 'status_label'):
            self.status_label.clear()
            self.timer.stop()

    # Función para mostrar un mensaje de estado
    def show_status(self, message):
        self.status_label.setText(message)
        self.timer.start(2000)

    # Función para validar la clave API de xAI
    def validate_api(self):
        api_key = self.api_input.text().strip()
        if not api_key:
            self.show_status('No puede dejar el campo vacío')
            return
        
        if not api_key.startswith("xai-"):
            self.show_status('Clave inválida')
            return
        
        try:
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

# Clase para la ventana principal de la aplicación
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.api_key = self.load_api_key()
        self.grok_api_key = self.load_grok_api_key()
        
        if self.api_key:
            os.environ["REPLICATE_API_TOKEN"] = self.api_key
        if self.grok_api_key:
            os.environ["GROK_API_KEY"] = self.grok_api_key
        
        self.widget = None
        self.setup_menu()
        self.setup_main_widget()
        
        self.validate_replicate_api()
        
        self.setAttribute(Qt.WA_DeleteOnClose)

    # Función para cargar la clave API de Replicate
    def load_api_key(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('api_key')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Función para guardar la clave API de Replicate
    def save_api_key(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            config['api_key'] = self.api_key
            config['grok_api_key'] = self.grok_api_key
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error al guardar las claves API: {str(e)}")

    # Función para validar la clave API de Replicate
    def validate_replicate_api(self):
        if self.api_key:
            try:
                headers = {"Authorization": f"Token {self.api_key}"}
                response = requests.get("https://api.replicate.com/v1/models", headers=headers)
                if response.status_code == 200:
                    self.enable_functionality()
                else:
                    self.api_key = None
                    self.save_api_key()
                    if os.environ.get("REPLICATE_API_TOKEN"):
                        del os.environ["REPLICATE_API_TOKEN"]
                    if not self.grok_api_key:
                        self.disable_functionality()
                    else:
                        self.delete_action.setEnabled(False)
                        self.widget.populate_fields()
            except Exception:
                self.api_key = None
                self.save_api_key()
                if os.environ.get("REPLICATE_API_TOKEN"):
                    del os.environ["REPLICATE_API_TOKEN"]
                if not self.grok_api_key:
                    self.disable_functionality()
                else:
                    self.delete_action.setEnabled(False)
                    self.widget.populate_fields()
        elif self.grok_api_key:
            self.validate_grok_api()
        else:
            self.disable_functionality()

    # Función para cargar la clave API de xAI
    def load_grok_api_key(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('grok_api_key')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Función para guardar la clave API de xAI
    def save_grok_api_key(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
        
        config['grok_api_key'] = self.grok_api_key
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)

    # Función para establecer la clave API de xAI
    def set_grok_api_key(self, api_key):
        self.grok_api_key = api_key
        self.save_grok_api_key()
        os.environ["GROK_API_KEY"] = api_key
        self.enable_functionality()

    # Función para configurar el menú de la aplicación
    def setup_menu(self):
        menubar = self.menuBar()
        
        api_menu = menubar.addMenu('Replicate')
        config_action = QAction(QIcon(resource_path("iconos/conf.png")), 'Configurar clave API de Replicate', self)
        config_action.triggered.connect(self.show_api_dialog)
        api_menu.addAction(config_action)
        
        self.delete_action = QAction(QIcon(resource_path("iconos/delete.png")), 'Borrar clave API de Replicate', self)
        self.delete_action.triggered.connect(self.delete_api_key)
        api_menu.addAction(self.delete_action)

        grok_menu = menubar.addMenu('xAI')
        grok_config_action = QAction(QIcon(resource_path("iconos/conf.png")), 'Configurar clave API de xAI', self)
        grok_config_action.triggered.connect(self.show_grok_api_dialog)
        grok_menu.addAction(grok_config_action)
        
        self.grok_delete_action = QAction(QIcon(resource_path("iconos/delete.png")), 'Borrar clave API de xAI', self)
        self.grok_delete_action.triggered.connect(self.delete_grok_api_key)
        grok_menu.addAction(self.grok_delete_action)

    # Función para establecer la clave API de Replicate
    def set_api_key(self, api_key):
        self.api_key = api_key
        self.save_api_key()
        os.environ["REPLICATE_API_TOKEN"] = api_key
        self.enable_functionality()

    # Función para mostrar la ventana de configuración de la clave API de Replicate
    def show_api_dialog(self):
        self.api_window = APIKeyWindow(self)
        self.api_window.show()

    # Función para borrar la clave API de Replicate
    def delete_api_key(self):
        confirm_msg = QMessageBox()
        confirm_msg.setWindowTitle('Confirmar borrado')
        confirm_msg.setText('¿Está seguro de que desea borrar la clave API de Replicate?')
        confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_msg.setDefaultButton(QMessageBox.No)
        confirm_msg.setIcon(QMessageBox.Question)
        confirm_msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
        
        confirm_msg.button(QMessageBox.Yes).setText('Sí')
        confirm_msg.button(QMessageBox.No).setText('No')
        
        if confirm_msg.exec() == QMessageBox.Yes:
            if not self.grok_api_key:
                self.disable_functionality()
                
            self.api_key = None
            self.save_api_key()
            
            if self.grok_api_key:
                self.widget.populate_fields()
                self.delete_action.setEnabled(False)
            
            success_msg = QMessageBox()
            success_msg.setWindowTitle('API borrada')
            success_msg.setText('La clave API de Replicate ha sido borrada correctamente')
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
            success_msg.exec()

    # Función para mostrar la ventana de configuración de la clave API de xAI
    def show_grok_api_dialog(self):
        self.grok_api_window = GrokAPIKeyWindow(self)
        self.grok_api_window.show()

    # Función para borrar la clave API de xAI
    def delete_grok_api_key(self):
        confirm_msg = QMessageBox()
        confirm_msg.setWindowTitle('Confirmar borrado')
        confirm_msg.setText('¿Está seguro de que desea borrar la clave API de xAI?')
        confirm_msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_msg.setDefaultButton(QMessageBox.No)
        confirm_msg.setIcon(QMessageBox.Question)
        confirm_msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
        
        confirm_msg.button(QMessageBox.Yes).setText('Sí')
        confirm_msg.button(QMessageBox.No).setText('No')
        
        if confirm_msg.exec() == QMessageBox.Yes:
            if not self.api_key:
                self.disable_functionality()
            
            self.grok_api_key = None
            self.save_grok_api_key()
            
            if self.api_key:
                self.widget.populate_fields()
                self.grok_delete_action.setEnabled(False)
            
            success_msg = QMessageBox()
            success_msg.setWindowTitle('API borrada')
            success_msg.setText('La clave API de xAI ha sido borrada correctamente')
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
            success_msg.exec()

    # Función para configurar la ventana principal
    def setup_main_widget(self):
        self.widget = PowerpoineatorWidget()
        self.setCentralWidget(self.widget)
        self.setWindowTitle('Powerpoineador v0.1b')
        self.setMinimumSize(700, 400)
        self.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
        
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # Función para deshabilitar la funcionalidad de la aplicación
    def disable_functionality(self):
        if self.widget:
            self.widget.generar_btn.setEnabled(False)
            self.widget.descripcion_text.setEnabled(False)
            self.widget.texto_combo.setEnabled(False)
            self.widget.imagen_combo.setEnabled(False)
            self.widget.auto_open_checkbox.setEnabled(False)
            self.widget.cargar_imagen_btn.setEnabled(False)
            self.widget.ver_imagen_btn.setEnabled(False)
            self.widget.imagen_combo.clear()
            self.widget.texto_combo.clear()
            
            self.widget.descripcion_text.clear()
            self.widget.descripcion_text.setPlaceholderText("Configure una clave API de Replicate o xAI para poder utilizar el programa")
            
            self.widget.clear_fields()
            self.widget.contador_label.hide()
            
            self.delete_action.setEnabled(False)
            self.grok_delete_action.setEnabled(False)
            
            self.widget.cargar_imagen_btn.hide()
            self.widget.ver_imagen_btn.hide()

    # Función para habilitar la funcionalidad de la aplicación
    def enable_functionality(self):
        if self.widget:
            api_available = bool(self.api_key or self.grok_api_key)
            
            if not api_available:
                self.disable_functionality()
                return
                
            self.widget.generar_btn.setEnabled(True)
            self.widget.descripcion_text.setEnabled(True)
            self.widget.texto_combo.setEnabled(True)
            self.widget.auto_open_checkbox.setEnabled(True)
            
            self.widget.descripcion_text.setPlaceholderText("")
            
            self.widget.contador_label.show()
            
            self.widget.imagen_combo.setEnabled(bool(self.api_key))
            
            self.widget.populate_fields()
            
            self.delete_action.setEnabled(bool(self.api_key))
            self.grok_delete_action.setEnabled(bool(self.grok_api_key))

    # Función para manejar el evento de cierre de la ventana
    def closeEvent(self, event):
        if hasattr(self, 'widget') and self.widget:
            if hasattr(self.widget, 'log_window') and self.widget.log_window:
                msg = QMessageBox()
                msg.setWindowTitle('Confirmar salida')
                msg.setText('Hay una generación en proceso. ¿Está seguro de que desea salir?')
                msg.setIcon(QMessageBox.Question)
                msg.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)
                msg.button(QMessageBox.Yes).setText('Sí')
                msg.button(QMessageBox.No).setText('No')
                
                if msg.exec() == QMessageBox.Yes:
                    self.widget.log_window.cancel_generation()
                    self.widget.log_window.close()
                    event.accept()
                else:
                    event.ignore()
                return
        event.accept()

    # Función para validar la clave API de xAI
    def validate_grok_api(self):
        if self.grok_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.grok_api_key}",
                    "Content-Type": "application/json"
                }
                response = requests.get(
                    "https://api.x.ai/v1/models",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code in [200, 403]:
                    self.enable_functionality()
                else:
                    self.grok_api_key = None
                    self.save_grok_api_key()
                    if os.environ.get("GROK_API_KEY"):
                        del os.environ["GROK_API_KEY"]
                    if not self.api_key:
                        self.disable_functionality()
                    else:
                        self.grok_delete_action.setEnabled(False)
                        self.widget.populate_fields()
            except Exception:
                self.grok_api_key = None
                self.save_grok_api_key()
                if os.environ.get("GROK_API_KEY"):
                    del os.environ["GROK_API_KEY"]
                if not self.api_key:
                    self.disable_functionality()
                else:
                    self.grok_delete_action.setEnabled(False)
                    self.widget.populate_fields()

    # Función para actualizar el estado del menú
    def update_menu_state(self):
        self.enable_functionality()

# Clase para la ventana principal de la aplicación
class PowerpoineatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.imagen_personalizada = None
        self.populate_fields()
        self.load_description()

    # Función para configurar la interfaz de usuario
    def setup_ui(self):
        main_layout = QVBoxLayout()
        model_layout = QHBoxLayout()

        texto_layout = QVBoxLayout()
        self.texto_combo = QComboBox()
        self.texto_combo.currentTextChanged.connect(self.on_texto_combo_changed)
        texto_layout.addWidget(QLabel('Modelo de IA de Texto:'))
        texto_layout.addWidget(self.texto_combo)
        model_layout.addLayout(texto_layout)

        imagen_layout = QVBoxLayout()
        imagen_combo_layout = QHBoxLayout()
        self.imagen_combo = QComboBox()
        self.imagen_combo.currentTextChanged.connect(self.on_imagen_combo_changed)
        imagen_layout.addWidget(QLabel('Modelo de IA de Imagen:'))
        imagen_combo_layout.addWidget(self.imagen_combo)
        
        self.cargar_imagen_btn = QPushButton('+')
        self.cargar_imagen_btn.setToolTip('Cargar imagen personalizada')
        self.cargar_imagen_btn.setFixedSize(24, 22.9)
        self.cargar_imagen_btn.clicked.connect(self.cargar_imagen_personalizada)
        self.cargar_imagen_btn.hide()
        imagen_combo_layout.addWidget(self.cargar_imagen_btn)

        self.ver_imagen_btn = QPushButton('Revisar')
        self.ver_imagen_btn.setToolTip('Ver imagen seleccionada')
        self.ver_imagen_btn.setFixedSize(50, 22.9)
        self.ver_imagen_btn.clicked.connect(self.ver_imagen_personalizada)
        self.ver_imagen_btn.hide()
        imagen_combo_layout.addWidget(self.ver_imagen_btn)
        
        imagen_layout.addLayout(imagen_combo_layout)
        model_layout.addLayout(imagen_layout)

        main_layout.addLayout(model_layout)

        main_layout.addWidget(QLabel('Describa su presentación:'))
        self.descripcion_text = QTextEdit()
        font = self.descripcion_text.font()
        font.setPointSize(15)
        self.descripcion_text.setFont(font)
        self.descripcion_text.textChanged.connect(self.on_text_changed)
        self.descripcion_text.textChanged.connect(self.actualizar_contador)
        main_layout.addWidget(self.descripcion_text)

        contador_checkbox_layout = QHBoxLayout()
        
        self.auto_open_checkbox = QCheckBox('Abrir presentación automáticamente')
        self.auto_open_checkbox.setChecked(False)
        contador_checkbox_layout.addWidget(self.auto_open_checkbox)
        
        contador_checkbox_layout.addStretch()
        
        self.contador_label = QLabel('0 palabras')
        self.contador_label.setStyleSheet("color: gray;")
        contador_checkbox_layout.addWidget(self.contador_label)
        
        main_layout.addLayout(contador_checkbox_layout)

        self.generar_btn = QPushButton('Generar PowerPoint')
        self.generar_btn.clicked.connect(self.generar_presentacion_event)
        main_layout.addWidget(self.generar_btn)

        self.setLayout(main_layout)

    # Función para poblar los campos de selección de modelos
    def populate_fields(self):
        self.texto_combo.blockSignals(True)
        self.imagen_combo.blockSignals(True)
        
        self.texto_combo.clear()
        self.imagen_combo.clear()
        
        if hasattr(self.parent(), 'api_key') and self.parent().api_key:
            self.texto_combo.addItems([
                'meta-llama-3.1-405b-instruct (con censura)',
                'dolphin-2.9-llama3-70b-gguf (sin censura)'
            ])
            self.imagen_combo.setEnabled(True)
            self.imagen_combo.addItems([
                'hyper-flux-8step (rápida y muy barata)',
                'photomaker (con caras mejorado)',
                'flux-pulid (con caras)',
                'hyper-flux-16step (rápida y barata)',
                'sdxl-lightning-4step (barata sin censura)',
                'flux-schnell (rápida)',
                'flux-diego (meme)'
            ])
        
        if hasattr(self.parent(), 'grok_api_key') and self.parent().grok_api_key:
            self.texto_combo.addItem('grok-2-1212 (experimental)')
            if not (hasattr(self.parent(), 'api_key') and self.parent().api_key):
                self.imagen_combo.setEnabled(False)
        
        self.load_combo_selection()
        
        self.texto_combo.blockSignals(False)
        self.imagen_combo.blockSignals(False)

    # Función para limpiar los campos de selección de modelos
    def clear_fields(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                config['descripcion'] = ""
                config['texto_modelo'] = ""
                config['imagen_modelo'] = ""
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al limpiar la configuración: {str(e)}")
        
        self.texto_combo.clear()
        self.imagen_combo.clear()
        self.descripcion_text.clear()
        self.imagen_personalizada = None
        self.cargar_imagen_btn.hide()
        self.ver_imagen_btn.hide()

    # Función para generar la presentación
    def generar_presentacion_event(self):
        modelo_texto = self.texto_combo.currentText()
        modelo_imagen = self.imagen_combo.currentText()
        descripcion = self.descripcion_text.toPlainText()
        auto_open = self.auto_open_checkbox.isChecked()

        if modelo_imagen in ['photomaker (con caras mejorado)','flux-pulid (con caras)'] and not self.imagen_personalizada:
            QMessageBox.warning(self, 'Error', 'Debe cargar una imagen para usar este modelo')
            return

        if len(descripcion.split()) < 10 and len(descripcion.split()) > 0:
            QMessageBox.warning(self, 'Error', 'La descripción debe tener al menos 10 palabras')
            return
        elif len(descripcion.split()) == 0:
            QMessageBox.warning(self, 'Error', 'Por favor, escriba una descripción para su presentación')
            return

        if modelo_texto == 'grok-2-1212 (experimental)' and not (hasattr(self.parent(), 'api_key') and self.parent().api_key):
            QMessageBox.warning(self, 'Error', 'Actualmente el modelo de Grok no puede generar imágenes. Por favor, configure una API de Replicate para generar imágenes.')
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Guardar presentación",
            "Presentación_Powerpoineador.pptx",
            "Presentaciones (*.pptx)"
        )

        if file_path:
            self.log_window = LogWindow()
            self.log_window.parent = self
            self.log_window.show()
            self.log_window.start_generation(
                modelo_texto,
                modelo_imagen,
                descripcion,
                auto_open,
                self.imagen_personalizada,
                file_path
            )

    # Función para guardar la descripción
    def save_description(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['descripcion'] = self.descripcion_text.toPlainText()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar la descripción: {str(e)}")

    # Función para cargar la descripción
    def load_description(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    descripcion = config.get('descripcion', '')
                    self.descripcion_text.blockSignals(True)
                    self.descripcion_text.setText(descripcion)
                    self.descripcion_text.blockSignals(False)
                    self.actualizar_contador()
        except Exception as e:
            print(f"Error al cargar la descripción: {str(e)}")

    # Función para actualizar el contador de palabras
    def actualizar_contador(self):
        texto = self.descripcion_text.toPlainText()
        num_palabras = len(texto.split())
        self.contador_label.setText(f'{num_palabras} palabras')
        if num_palabras < 10:
            self.contador_label.setStyleSheet("color: red;")
        else:
            self.contador_label.setStyleSheet("color: green;")

    # Función para cargar una imagen personalizada
    def cargar_imagen_personalizada(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Seleccionar imagen",
            "",
            "Imágenes (*.jpg)"
        )
        if file_path:
            try:
                self.imagen_personalizada = file_path
                QMessageBox.information(self, 'Éxito', 'Imagen cargada correctamente')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Error al cargar la imagen: {str(e)}')

    # Función para manejar el cambio en la selección de modelos de imagen
    def on_imagen_combo_changed(self, texto):
        if texto in ['flux-pulid (con caras)', 'photomaker (con caras mejorado)']:
            self.cargar_imagen_btn.show()
            self.ver_imagen_btn.show()
            self.cargar_imagen_btn.setEnabled(True)
            self.ver_imagen_btn.setEnabled(True)
        else:
            self.cargar_imagen_btn.hide()
            self.ver_imagen_btn.hide()
            self.cargar_imagen_btn.setEnabled(False)
            self.ver_imagen_btn.setEnabled(False)
            self.imagen_personalizada = None
        self.save_combo_selection()

    # Función para ver la imagen personalizada
    def ver_imagen_personalizada(self):
        if hasattr(self, 'imagen_personalizada') and self.imagen_personalizada:
            try:
                os.startfile(self.imagen_personalizada)
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Error al abrir la imagen: {str(e)}')
        else:
            QMessageBox.warning(self, 'Aviso', 'No hay ninguna imagen seleccionada')

    # Función para guardar la descripción cuando cambia el texto
    def on_text_changed(self):
        self.save_description()

    # Función para guardar la selección de modelos
    def save_combo_selection(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if self.texto_combo.currentText():
                config['texto_modelo'] = self.texto_combo.currentText()
            
            if self.imagen_combo.isEnabled() and self.imagen_combo.currentText():
                config['imagen_modelo'] = self.imagen_combo.currentText()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False)
        except Exception as e:
            print(f"Error al guardar la selección de modelos: {str(e)}")

    # Función para cargar la selección de modelos
    def load_combo_selection(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    texto_modelo = config.get('texto_modelo', '')
                    imagen_modelo = config.get('imagen_modelo', '')
                    
                    if texto_modelo and self.texto_combo.count() > 0:
                        index = self.texto_combo.findText(texto_modelo)
                        if index >= 0:
                            self.texto_combo.setCurrentIndex(index)
                    
                    if imagen_modelo and self.imagen_combo.isEnabled() and self.imagen_combo.count() > 0:
                        index = self.imagen_combo.findText(imagen_modelo)
                        if index >= 0:
                            self.imagen_combo.setCurrentIndex(index)
                            if imagen_modelo in ['flux-pulid (con caras)', 'photomaker (con caras mejorado)']:
                                self.cargar_imagen_btn.show()
                                self.ver_imagen_btn.show()
                                self.cargar_imagen_btn.setEnabled(True)
                                self.ver_imagen_btn.setEnabled(True)
                            else:
                                self.cargar_imagen_btn.hide()
                                self.ver_imagen_btn.hide()
                                self.cargar_imagen_btn.setEnabled(False)
                                self.ver_imagen_btn.setEnabled(False)
                                self.imagen_personalizada = None
        except Exception as e:
            print(f"Error al cargar la selección de modelos: {str(e)}")

    # Función para guardar la selección de modelos cuando cambia el texto
    def on_texto_combo_changed(self, texto):
        self.save_combo_selection()

# Función principal para iniciar la aplicación
if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()