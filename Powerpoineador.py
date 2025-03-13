import sys, os, requests, json, webbrowser
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap, QAction
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, QPushButton,
    QLabel, QMessageBox, QCheckBox, QMainWindow, QFileDialog, QMenuBar)
from Ventana_progreso import LogWindow
from Version_checker import obtener_url_descarga, obtener_ultima_version, obtener_version_actual
from apis.Replicate import ReplicateAPIKeyWindow
from apis.xAI import GrokAPIKeyWindow

# Definir la ruta de la carpeta de datos de la aplicación según el sistema operativo
if sys.platform == 'win32':
    APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
else:
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), '.Powerpoineador')

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

# Función para verificar la conexión a Internet
def verificar_conexion_internet():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True
    except requests.RequestException:
        return False

# Función para mostrar el mensaje de error de conexión
def mostrar_error_conexion():
    msg = QMessageBox()
    msg.setWindowTitle('Error de conexión')
    msg.setText('No se detectó conexión a Internet.\nPowerpoineador necesita una conexión a Internet para funcionar.')
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
    msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
    msg.button(QMessageBox.Retry).setText('Reintentar')
    msg.button(QMessageBox.Cancel).setText('Salir')
    
    msg.show()
    msg.hide()
    
    screen = QApplication.primaryScreen().geometry()
    msg_pos = screen.center() - msg.rect().center()
    msg.move(msg_pos)
    
    return msg.exec()

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
        
        if not (self.api_key or self.grok_api_key):
            self.disable_functionality()
        else:
            self.validate_replicate_api()
        
        if not self.load_window_position():
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.width()) // 2
            y = (screen.height() - self.height()) // 2
            self.move(x, y)
        
        self.setAttribute(Qt.WA_DeleteOnClose)

    # Función para cargar la clave API de Replicate
    def load_api_key(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('api_key')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Función para guardar la clave API de Replicate
    def save_api_key(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['api_key'] = self.api_key
            config['grok_api_key'] = self.grok_api_key
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar las claves API: {str(e)}")

    # Función para validar la clave API de Replicate
    def validate_replicate_api(self):
        replicate_invalid = False
        grok_invalid = False
        has_saved_replicate = bool(self.load_api_key())
        has_saved_grok = bool(self.load_grok_api_key())
        
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
                    replicate_invalid = True
                    if not self.grok_api_key:
                        self.disable_functionality()
                
            except Exception:
                self.api_key = None
                self.save_api_key()
                if os.environ.get("REPLICATE_API_TOKEN"):
                    del os.environ["REPLICATE_API_TOKEN"]
                replicate_invalid = True
                if not self.grok_api_key:
                    self.disable_functionality()
        else:
            replicate_invalid = has_saved_replicate

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
                    grok_invalid = True
                    if not self.api_key:
                        self.disable_functionality()
                
            except Exception:
                self.grok_api_key = None
                self.save_grok_api_key()
                if os.environ.get("GROK_API_KEY"):
                    del os.environ["GROK_API_KEY"]
                grok_invalid = True
                if not self.api_key:
                    self.disable_functionality()
        else:
            grok_invalid = has_saved_grok

        if replicate_invalid and grok_invalid and (has_saved_replicate or has_saved_grok):
            self.disable_functionality()
            QTimer.singleShot(100, lambda: self.show_all_apis_invalid_message())
        elif replicate_invalid and has_saved_replicate:
            if not self.grok_api_key:
                self.disable_functionality()
            self.delete_action.setEnabled(False)
            QTimer.singleShot(100, lambda: self.show_invalid_api_message())
        elif grok_invalid and has_saved_grok:
            if not self.api_key:
                self.disable_functionality()
            self.grok_delete_action.setEnabled(False)
            QTimer.singleShot(100, lambda: self.show_invalid_grok_api_message())
        
        self.initial_validation = False

    # Función para cargar la clave API de xAI
    def load_grok_api_key(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('grok_api_key')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Función para guardar la clave API de xAI
    def save_grok_api_key(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
        
        config['grok_api_key'] = self.grok_api_key
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    # Función para establecer la clave API de xAI
    def set_grok_api_key(self, api_key):
        self.grok_api_key = api_key
        self.save_grok_api_key()
        os.environ["GROK_API_KEY"] = api_key
        self.enable_functionality()

        self.get_grok_api_action.setEnabled(False)

    # Función para configurar el menú de la aplicación
    def setup_menu(self):
        menubar = self.menuBar()
        
        left_menubar = QMenuBar(menubar)
        
        api_menu = left_menubar.addMenu('Replicate')
        self.get_api_action = QAction(QIcon(resource_path("iconos/web.png")), 'Obtener clave API de Replicate', self)
        self.get_api_action.triggered.connect(lambda: webbrowser.open('https://replicate.com/account/api-tokens'))
        self.get_api_action.setEnabled(not bool(self.api_key))
        api_menu.addAction(self.get_api_action)
        
        config_action = QAction(QIcon(resource_path("iconos/conf.png")), 'Configurar clave API de Replicate', self)
        config_action.triggered.connect(self.show_api_dialog)
        api_menu.addAction(config_action)
        
        self.delete_action = QAction(QIcon(resource_path("iconos/delete.png")), 'Borrar clave API de Replicate', self)
        self.delete_action.triggered.connect(self.delete_api_key)
        api_menu.addAction(self.delete_action)

        grok_menu = left_menubar.addMenu('xAI')
        self.get_grok_api_action = QAction(QIcon(resource_path("iconos/web.png")), 'Obtener clave API de xAI', self)
        self.get_grok_api_action.triggered.connect(lambda: webbrowser.open('https://console.x.ai/team/default/api-keys'))
        self.get_grok_api_action.setEnabled(not bool(self.grok_api_key))
        grok_menu.addAction(self.get_grok_api_action)
        
        grok_config_action = QAction(QIcon(resource_path("iconos/conf.png")), 'Configurar clave API de xAI', self)
        grok_config_action.triggered.connect(self.show_grok_api_dialog)
        grok_menu.addAction(grok_config_action)
        
        self.grok_delete_action = QAction(QIcon(resource_path("iconos/delete.png")), 'Borrar clave API de xAI', self)
        self.grok_delete_action.triggered.connect(self.delete_grok_api_key)
        grok_menu.addAction(self.grok_delete_action)

        menubar.setCornerWidget(left_menubar, Qt.TopLeftCorner)

        right_menubar = QMenuBar(menubar)

        balance_action = QAction(QIcon(resource_path("iconos/coin.png")), '', self)
        balance_action.setStatusTip('Consultar costos totales aproximados acumulados')
        balance_action.triggered.connect(self.calcular_costos_totales)
        balance_action.setEnabled(bool(self.api_key or self.grok_api_key))
        right_menubar.addAction(balance_action)
        self.balance_action = balance_action

        donate_action = QAction(QIcon(resource_path("iconos/paypal.png")), '', self)
        donate_action.setStatusTip('Apoyar el desarrollo con una donación')
        donate_action.triggered.connect(lambda: webbrowser.open('https://paypal.me/KevinAZHD'))
        right_menubar.addAction(donate_action)
        
        github_action = QAction(QIcon(resource_path("iconos/github.png")), '', self)
        github_action.setStatusTip('Visitar el repositorio')
        github_action.triggered.connect(lambda: webbrowser.open('https://github.com/KevinAZHD/Powerpoineador'))
        right_menubar.addAction(github_action)

        menubar.setCornerWidget(right_menubar, Qt.TopRightCorner)

    # Función para establecer la clave API de Replicate
    def set_api_key(self, api_key):
        self.api_key = api_key
        self.save_api_key()
        os.environ["REPLICATE_API_TOKEN"] = api_key
        self.enable_functionality()
        self.get_api_action.setEnabled(False)

    # Función para mostrar la ventana de configuración de la clave API de Replicate
    def show_api_dialog(self):
        self.api_window = ReplicateAPIKeyWindow(self)
        self.api_window.show()

    # Función para borrar la clave API de Replicate
    def delete_api_key(self):
        msg = QMessageBox()
        msg.setWindowTitle('Confirmar borrado API')
        msg.setText('¿Está seguro de que desea borrar la clave API de Replicate?')
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText('Sí')
        msg.button(QMessageBox.No).setText('No')
        
        QApplication.beep()
        
        msg.show()
        msg.hide()
        
        msg_pos = self.geometry().center() - msg.rect().center()
        msg.move(msg_pos)
        
        if msg.exec() == QMessageBox.Yes:
            self.api_key = None
            self.save_api_key()
            if os.environ.get("REPLICATE_API_TOKEN"):
                del os.environ["REPLICATE_API_TOKEN"]

            self.get_api_action.setEnabled(True)
            
            if not self.grok_api_key:
                self.disable_functionality()
                try:
                    if os.path.exists(CONFIG_FILE):
                        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        if 'costos_totales' in config:
                            del config['costos_totales']
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    print(f"Error al borrar costos totales: {str(e)}")
            else:
                self.delete_action.setEnabled(False)
                if self.widget:
                    self.widget.populate_fields()
            
            self.balance_action.setEnabled(bool(self.grok_api_key))
            
            success_msg = QMessageBox()
            success_msg.setWindowTitle('Clave API borrada')
            success_msg.setText('La clave API de Replicate ha sido borrada correctamente.')
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
            
            success_msg.show()
            success_msg.hide()
            
            success_pos = self.geometry().center() - success_msg.rect().center()
            success_msg.move(success_pos)
            
            success_msg.exec()

    # Función para mostrar la ventana de configuración de la clave API de xAI
    def show_grok_api_dialog(self):
        self.grok_api_window = GrokAPIKeyWindow(self)
        self.grok_api_window.show()

    # Función para borrar la clave API de xAI
    def delete_grok_api_key(self):
        msg = QMessageBox()
        msg.setWindowTitle('Confirmar borrado API')
        msg.setText('¿Está seguro de que desea borrar la clave API de xAI?')
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText('Sí')
        msg.button(QMessageBox.No).setText('No')
        
        QApplication.beep()
        
        msg.show()
        msg.hide()
        
        msg_pos = self.geometry().center() - msg.rect().center()
        msg.move(msg_pos)
        
        if msg.exec() == QMessageBox.Yes:
            self.grok_api_key = None
            self.save_grok_api_key()
            if os.environ.get("GROK_API_KEY"):
                del os.environ["GROK_API_KEY"]
            
            self.get_grok_api_action.setEnabled(True)
            
            if not self.api_key:
                self.disable_functionality()
                # Borrar los costos totales cuando no hay ninguna API
                try:
                    if os.path.exists(CONFIG_FILE):
                        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        if 'costos_totales' in config:
                            del config['costos_totales']
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    print(f"Error al borrar costos totales: {str(e)}")
            else:
                self.grok_delete_action.setEnabled(False)
                if self.widget:
                    self.widget.populate_fields()
            
            self.balance_action.setEnabled(bool(self.api_key))
            
            success_msg = QMessageBox()
            success_msg.setWindowTitle('Clave API borrada')
            success_msg.setText('La clave API de xAI ha sido borrada correctamente.')
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
            
            success_msg.show()
            success_msg.hide()
            
            success_pos = self.geometry().center() - success_msg.rect().center()
            success_msg.move(success_pos)
            
            success_msg.exec()

    # Función para configurar la ventana principal
    def setup_main_widget(self):
        self.widget = PowerpoineatorWidget()
        self.setCentralWidget(self.widget)
        self.setWindowTitle('Powerpoineador')
        self.setMinimumSize(833, 400)
        self.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
        
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    # Función para deshabilitar la funcionalidad de la aplicación
    def disable_functionality(self):
        if hasattr(self, 'balance_action'):
            self.balance_action.setEnabled(False)
            # Borrar los costos totales cuando se deshabilita
            try:
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    if 'costos_totales' in config:
                        del config['costos_totales']
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Error al borrar costos totales: {str(e)}")
        
        if self.widget:
            self.widget.generar_btn.setEnabled(False)
            self.widget.descripcion_text.setEnabled(False)
            self.widget.texto_combo.setEnabled(False)
            self.widget.imagen_combo.setEnabled(False)
            self.widget.auto_open_checkbox.setEnabled(False)
            self.widget.cargar_imagen_btn.setEnabled(False)
            self.widget.ver_imagen_btn.setEnabled(False)
            self.widget.imagen_combo.setEnabled(False)
            self.widget.texto_combo.setEnabled(False)
            
            self.widget.descripcion_text.clear()
            self.widget.descripcion_text.setPlaceholderText("Configura una clave API de Replicate o xAI para poder utilizar el programa")
            
            self.widget.clear_fields()
            self.widget.contador_label.hide()
            
            self.delete_action.setEnabled(False)
            self.grok_delete_action.setEnabled(False)
            
            self.widget.cargar_imagen_btn.hide()
            self.widget.ver_imagen_btn.hide()

    # Función para habilitar la funcionalidad de la aplicación
    def enable_functionality(self):
        if hasattr(self, 'balance_action'):
            self.balance_action.setEnabled(True)
        
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
        self.save_window_position()
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

    # Función para mostrar el mensaje de clave API inválida de Replicate
    def show_invalid_api_message(self):
        msg = QMessageBox()
        msg.setWindowTitle('API Replicate inválida')
        msg.setText('La clave API de Replicate no es válida. Escribe una nueva clave API de Replicate.')
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
        msg.exec()

    # Función para mostrar el mensaje de error de conexión con Replicate
    def show_connection_error_message(self):
        msg = QMessageBox()
        msg.setWindowTitle('Error de conexión con Replicate')
        msg.setText('No se pudo validar la clave API de Replicate. Verifica tu conexión a internet.')
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
        msg.exec()

    # Función para mostrar el mensaje de clave API inválida de xAI
    def show_invalid_grok_api_message(self):
        msg = QMessageBox()
        msg.setWindowTitle('API xAI inválida')
        msg.setText('La clave API de xAI no es válida. Escribe una nueva clave API de xAI.')
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
        msg.exec()

    # Función para mostrar el mensaje de error de conexión con xAI
    def show_grok_connection_error_message(self):
        msg = QMessageBox()
        msg.setWindowTitle('Error de conexión con xAI')
        msg.setText('No se pudo validar la clave API de xAI. Verifica tu conexión a internet.')
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
        msg.exec()

    # Función para mostrar el mensaje de claves API inválidas
    def show_all_apis_invalid_message(self):
        msg = QMessageBox()
        msg.setWindowTitle('Claves API inválidas')
        msg.setText('No hay ninguna clave API válida configurada. Escriba al menos una clave API válida para usar el programa.')
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
        msg.exec()

    # Función para validar la clave API de xAI
    def validate_grok_api(self):
        if not self.grok_api_key:
            return False
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
            return response.status_code in [200, 403]
        except:
            return False

    # Función para guardar la posición de la ventana
    def save_window_position(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            is_maximized = self.isMaximized()
            config['window_maximized'] = is_maximized
            
            if not is_maximized:
                geometry = self.geometry()
                config['window_position'] = {
                    'x': geometry.x(),
                    'y': geometry.y(),
                    'width': geometry.width(),
                    'height': geometry.height()
                }
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar la posición de la ventana: {str(e)}")

    # Función para cargar la posición de la ventana
    def load_window_position(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    
                    if config.get('window_maximized', False):
                        QTimer.singleShot(0, self.showMaximized)
                        return True
                    
                    position = config.get('window_position')
                    if position:
                        self.setGeometry(
                            position['x'],
                            position['y'],
                            position['width'],
                            position['height']
                        )
                        return True
        except Exception as e:
            print(f"Error al cargar la posición de la ventana: {str(e)}")
        return False

    # Función para calcular los costos totales
    def calcular_costos_totales(self):
        self.balance_window = BalanceWindow(self)
        self.balance_window.show()

# Clase para la ventana de saldo total
class BalanceWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.setWindowTitle('Saldo total')
        self.setFixedSize(400, 300)
        self.setWindowIcon(QIcon(resource_path("iconos/coin.png")))
        self.setWindowModality(Qt.ApplicationModal)
        
        if self.parent:
            parent_geometry = self.parent.geometry()
            x = parent_geometry.x() + (parent_geometry.width() - self.width()) // 2
            y = parent_geometry.y() + (parent_geometry.height() - self.height()) // 2 - (parent_geometry.height() // 8)
            self.move(x, y)
        
        self.setup_ui()

    # Función para configurar la interfaz de usuario
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        icon_label = QLabel()
        pixmap = QPixmap(resource_path("iconos/coin.png"))
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(scaled_pixmap)
            layout.addWidget(icon_label, alignment=Qt.AlignCenter)
        
        titulo = QLabel('Costos totales aproximados acumulados')
        font_titulo = titulo.font()
        font_titulo.setPointSize(11)
        font_titulo.setBold(True)
        titulo.setFont(font_titulo)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        config = self.load_costs()
        
        label_texto = QLabel(f'Texto: ${config["costos_totales"]["texto"]:.5f}')
        font_normal = label_texto.font()
        font_normal.setPointSize(10)
        label_texto.setFont(font_normal)
        label_texto.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_texto)
        
        label_imagenes = QLabel(f'Imágenes: ${config["costos_totales"]["imagen"]:.5f}')
        label_imagenes.setFont(font_normal)
        label_imagenes.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_imagenes)
        
        total = config["costos_totales"]["texto"] + config["costos_totales"]["imagen"]
        label_total = QLabel(f'Total: ${total:.5f}')
        font_total = label_total.font()
        font_total.setPointSize(11)
        font_total.setBold(True)
        label_total.setFont(font_total)
        label_total.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_total)
        
        btn_xai = QPushButton('Revisar en xAI')
        btn_xai.setFixedWidth(120)
        btn_xai.clicked.connect(self.abrir_saldo_xai)

        if self.parent and hasattr(self.parent, 'grok_api_key') and self.parent.grok_api_key:
            btn_xai.setEnabled(True)
        else:
            btn_xai.setEnabled(False)
        
        btn_replicate = QPushButton('Revisar en Replicate')
        btn_replicate.setFixedWidth(120)
        btn_replicate.clicked.connect(self.abrir_saldo_replicate)

        if self.parent and hasattr(self.parent, 'api_key') and self.parent.api_key:
            btn_replicate.setEnabled(True)
        else:
            btn_replicate.setEnabled(False)
        
        btn_reset = QPushButton('Reiniciar los costes')
        btn_reset.setFixedWidth(120)
        btn_reset.clicked.connect(self.confirmar_reinicio_costes)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_replicate)
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_xai)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # Función para cargar los costos
    def load_costs(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if 'costos_totales' not in config:
                config['costos_totales'] = {
                    'texto': 0.0,
                    'imagen': 0.0
                }
            return config
        except Exception as e:
            print(f"Error al cargar costos: {str(e)}")
            return {'costos_totales': {'texto': 0.0, 'imagen': 0.0}}

    # Función para confirmar el reinicio de los costos
    def confirmar_reinicio_costes(self):
        msg = QMessageBox(self)
        msg.setWindowTitle('Confirmar reinicio')
        msg.setText('¿Está seguro de que desea reiniciar los costes a cero?')
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon(resource_path("iconos/coin.png")))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText('Sí')
        msg.button(QMessageBox.No).setText('No')
        
        QApplication.beep()
        
        if msg.exec() == QMessageBox.Yes:
            try:
                config = self.load_costs()
                config['costos_totales'] = {'texto': 0.0, 'imagen': 0.0}
                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                self.close()
            except Exception as e:
                print(f"Error al reiniciar costos: {str(e)}")

    # Función para ver el saldo de Replicate
    def abrir_saldo_replicate(self):
        webbrowser.open("https://replicate.com")

    # Función para ver el saldo de xAI
    def abrir_saldo_xai(self):
        webbrowser.open("https://console.x.ai/team/default/usage")

# Clase para la ventana principal de la aplicación
class PowerpoineatorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.imagen_personalizada = None
        self.populate_fields()
        self.load_description()
        self.load_auto_open_state()

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
        self.auto_open_checkbox.stateChanged.connect(self.save_auto_open_state)
        contador_checkbox_layout.addWidget(self.auto_open_checkbox)
        
        contador_checkbox_layout.addStretch()
        
        self.contador_label = QLabel('0 palabras')
        self.contador_label.setStyleSheet("color: gray;")
        contador_checkbox_layout.addWidget(self.contador_label)
        
        main_layout.addLayout(contador_checkbox_layout)

        self.generar_btn = QPushButton('POWERPOINEAR')
        self.generar_btn.setMinimumWidth(200)
        self.generar_btn.setFixedHeight(40)

        font = self.generar_btn.font()
        font.setPointSize(13)
        font.setBold(True)
        self.generar_btn.setFont(font)

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
            self.texto_combo.addItem(QIcon(resource_path("iconos/deepseek.png")), 'deepseek-r1 (razonador) [$0.007]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/claude.png")), 'claude-3.7-sonnet (más inteligente) [$0.0105]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/claude.png")), 'claude-3.5-sonnet (inteligente) [$0.0131]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/claude.png")), 'claude-3.5-haiku (económico) [$0.0035]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/meta.png")), 'meta-llama-3.1-405b-instruct (con censura) [$0.0067]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/dolphin.png")), 'dolphin-2.9-llama3-70b-gguf (sin censura) [$0.0086]')
            
            self.imagen_combo.setEnabled(True)
            self.imagen_combo.addItem(QIcon(resource_path("iconos/fluxschnell.png")), 'flux-schnell (rápida) [$0.003]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/google.png")), 'imagen-3 (mejor calidad) [$0.05]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/google.png")), 'imagen-3-fast (barata y rápida) [$0.025]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/nvidia.png")), 'sana (calidad-precio) [$0.0042]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/photomaker.png")), 'photomaker (con caras mejorado) [$0.0069]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'flux-pulid (con caras) [$0.037]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'hyper-flux-8step (rápida y muy barata) [$0.0063]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'hyper-flux-16step (rápida y barata) [$0.0667]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'sdxl-lightning-4step (barata sin censura) [$0.0014]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/lightweight.png")), 'model3_4 (muy económico y sin censura) [$0.00098]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/dgmtnzflux.png")), 'dgmtnzflux (meme) [$0.03]')
        
        if hasattr(self.parent(), 'grok_api_key') and self.parent().grok_api_key and self.parent().validate_grok_api():
            self.texto_combo.addItem(QIcon(resource_path("iconos/grok.png")), 'grok-2-1212 (experimental)')
            if not (hasattr(self.parent(), 'api_key') and self.parent().api_key):
                self.imagen_combo.setEnabled(False)
        
        self.load_combo_selection()
        
        self.texto_combo.setMaxVisibleItems(self.texto_combo.count())
        self.imagen_combo.setMaxVisibleItems(self.imagen_combo.count())
        
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

        if modelo_imagen in ['photomaker (con caras mejorado) [$0.0069]', 'flux-pulid (con caras) [$0.037]'] and not self.imagen_personalizada:
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
            self.log_window = LogWindow(self.parent())
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
        if texto in ['flux-pulid (con caras) [$0.037]', 'photomaker (con caras mejorado) [$0.0069]']:
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
                json.dump(config, f, ensure_ascii=False, indent=4)
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
                    
                    parent = self.parent()
                    if texto_modelo and self.texto_combo.count() > 0:
                        if texto_modelo == 'grok-2-1212 (experimental)':
                            if parent and parent.grok_api_key and parent.validate_grok_api():
                                index = self.texto_combo.findText(texto_modelo)
                                if index >= 0:
                                    self.texto_combo.setCurrentIndex(index)
                            else:
                                self.texto_combo.setCurrentIndex(0)
                                config['texto_modelo'] = self.texto_combo.currentText()
                                with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                                    json.dump(config, f, ensure_ascii=False, indent=4)
                        else:
                            if parent.api_key:
                                index = self.texto_combo.findText(texto_modelo)
                                if index >= 0:
                                    self.texto_combo.setCurrentIndex(index)
                            else:
                                self.texto_combo.setCurrentIndex(0)
                    
                    if imagen_modelo and self.imagen_combo.isEnabled() and self.imagen_combo.count() > 0:
                        index = self.imagen_combo.findText(imagen_modelo)
                        if index >= 0:
                            self.imagen_combo.setCurrentIndex(index)
                            if imagen_modelo in ['flux-pulid (con caras) [$0.037]', 'photomaker (con caras mejorado) [$0.0069]']:
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

    # Función para guardar el estado de auto-abrir
    def save_auto_open_state(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['auto_open'] = self.auto_open_checkbox.isChecked()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar el estado de auto-abrir: {str(e)}")

    # Función para cargar el estado de auto-abrir
    def load_auto_open_state(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    auto_open = config.get('auto_open', False)
                    self.auto_open_checkbox.setChecked(auto_open)
        except Exception as e:
            print(f"Error al cargar el estado de auto-abrir: {str(e)}")

    def extraer_precio_modelo(self, texto_modelo):
        try:
            inicio = texto_modelo.find('[$')
            fin = texto_modelo.find(']')
            if inicio != -1 and fin != -1:
                precio = float(texto_modelo[inicio+2:fin])
                return precio
            return 0.0
        except:
            return 0.0

    def registrar_costos(self, modelo_texto=None, modelo_imagen=None, num_imagenes=1):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            if 'costos_totales' not in config:
                config['costos_totales'] = {
                    'texto': 0.0,
                    'imagen': 0.0
                }
            
            if modelo_texto:
                precio_texto = self.extraer_precio_modelo(modelo_texto)
                config['costos_totales']['texto'] += precio_texto
            
            if modelo_imagen:
                precio_imagen = self.extraer_precio_modelo(modelo_imagen)
                if hasattr(self, 'log_window') and self.log_window:
                    num_imagenes = self.log_window.total_images
                config['costos_totales']['imagen'] += precio_imagen * num_imagenes
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al registrar costos: {str(e)}")

    def registrar_costos_finales(self):
        self.registrar_costos(modelo_texto=self.texto_combo.currentText())
        self.registrar_costos(modelo_imagen=self.imagen_combo.currentText(), num_imagenes=1)

# Función principal para iniciar la aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
    
    while not verificar_conexion_internet():
        if mostrar_error_conexion() == QMessageBox.Cancel:
            sys.exit()
    
    from Splash_carga import SplashScreen
    from Version_checker import obtener_url_descarga
    
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    window = MainWindow()
    
    # Función para verificar y mostrar la ventana principal
    def check_and_show_main_window():
        if not verificar_conexion_internet():
            window.close()
            if mostrar_error_conexion() == QMessageBox.Cancel:
                app.quit()
            else:
                QTimer.singleShot(100, check_and_show_main_window)
            return
        
        if not splash.check_thread.is_alive():
            window.show()
            splash.close()
            
            if splash.hay_actualizacion:
                ultima_version = obtener_ultima_version()
                version_actual = obtener_version_actual()
                msg = QMessageBox()
                msg.setWindowTitle('Actualización disponible')
                msg.setText(f'Hay una nueva versión de Powerpoineador disponible.\n\nVersión actual: {version_actual}\nNueva versión: {ultima_version}\n\n¿Desea descargarla?')
                msg.setIcon(QMessageBox.Information)
                msg.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.Yes)
                msg.button(QMessageBox.Yes).setText('Sí')
                msg.button(QMessageBox.No).setText('No')
                
                msg.show()
                msg.hide()
                
                msg_pos = window.geometry().center() - msg.rect().center()
                msg.move(msg_pos)
                
                if msg.exec() == QMessageBox.Yes:
                    webbrowser.open(obtener_url_descarga())
                    window.close()
                    app.quit()
                    sys.exit()
        else:
            QTimer.singleShot(100, check_and_show_main_window)
    
    check_and_show_main_window()
    app.exec()