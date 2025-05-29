import sys, os, requests, json, webbrowser, platform
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from PySide6.QtGui import QIcon, QPixmap, QAction, QFont, QFontDatabase, QActionGroup, QTextCursor, QGuiApplication
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QTextEdit, QPushButton,
    QLabel, QMessageBox, QCheckBox, QMainWindow, QFileDialog, QMenuBar, QSpinBox, QProgressBar,
    QMenu, QSizePolicy, QGridLayout, QStyleFactory
    )
from Version_checker import obtener_url_descarga, obtener_ultima_version, obtener_version_actual
from apis.Replicate import ReplicateAPIKeyWindow
from apis.xAI import GrokAPIKeyWindow
from apis.Google import GoogleAPIKeyWindow
from Cifrado import GestorCifrado
from Traducciones import obtener_traduccion
from PyPDF2 import PdfReader
from Vista_previa import PPTX_AVAILABLE
from Plantillas import StyleSelectionDialog
from Temas import ThemeManager
import subprocess

# Definir la ruta de la carpeta de datos de la aplicación según el sistema operativo
if sys.platform == 'win32':
    APP_DATA_DIR = os.path.join(os.getenv('APPDATA'), 'Powerpoineador')
elif sys.platform == 'darwin':
    APP_DATA_DIR = os.path.join(os.path.expanduser('~'), 'Library', 'Application Support', 'Powerpoineador')
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
    # Obtener el idioma guardado
    current_language = 'es'
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                current_language = config.get('language', 'es')
    except Exception as e:
        print(f"Error al cargar el idioma: {str(e)}")
    
    msg = QMessageBox()
    msg.setWindowTitle(obtener_traduccion('connection_error_title', current_language))
    msg.setText(obtener_traduccion('connection_error_message', current_language))
    msg.setIcon(QMessageBox.Critical)
    msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
    msg.setStandardButtons(QMessageBox.Retry | QMessageBox.Cancel)
    msg.button(QMessageBox.Retry).setText(obtener_traduccion('retry', current_language))
    msg.button(QMessageBox.Cancel).setText(obtener_traduccion('exit', current_language))
    
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
        GestorCifrado.migrar_claves_antiguas(CONFIG_FILE)
        self.api_key = self.load_api_key()
        self.grok_api_key = self.load_grok_api_key()
        self.google_api_key = self.load_google_api_key()
        
        self.current_language = 'es'
        self.load_language()
        
        # Configuración del tema de apariencia
        self.current_app_theme = 'system' # Default antes de cargar, podría ser 'system', 'light', or 'dark'
        self.theme_manager = ThemeManager(self)
        self.load_app_theme_preference() # Carga la preferencia guardada

        # Conectar la señal de cambio de tema del SO
        QGuiApplication.styleHints().colorSchemeChanged.connect(self._handle_system_theme_change)
        
        # Aplicar tema DESPUÉS de que QApplication.setStyle se llame en if __name__ == "__main__"
        # pero antes de setup_ui para que los menús se creen con el tema correcto.
        # Lo moveremos a después de QApplication.setStyle. Por ahora, solo cargamos la preferencia.
        
        if self.api_key:
            os.environ["REPLICATE_API_TOKEN"] = self.api_key
        if self.grok_api_key:
            os.environ["GROK_API_KEY"] = self.grok_api_key
        if self.google_api_key:
            os.environ["GOOGLE_API_KEY"] = self.google_api_key
        
        self.widget = None
        self.setup_menu()
        self.setup_main_widget()
        
        if not (self.api_key or self.grok_api_key or self.google_api_key):
            self.disable_functionality()
        else:
            self.validate_replicate_api()
        
        # Siempre iniciar maximizado
        self.showMaximized()
        
        self.setAttribute(Qt.WA_DeleteOnClose)

    # Función para migrar claves antiguas
    def migrar_claves_antiguas(self):
        GestorCifrado.migrar_claves_antiguas(CONFIG_FILE)

    # Función para cargar la clave API de Replicate
    def load_api_key(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    encrypted_key = config.get('api_key')
                    return GestorCifrado.decrypt_text(encrypted_key) if encrypted_key else None
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Función para guardar la clave API de Replicate
    def save_api_key(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['api_key'] = GestorCifrado.encrypt_text(self.api_key) if self.api_key else None
            config['grok_api_key'] = GestorCifrado.encrypt_text(self.grok_api_key) if self.grok_api_key else None
            config['google_api_key'] = GestorCifrado.encrypt_text(self.google_api_key) if self.google_api_key else None
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar las claves API: {str(e)}")

    # Función para validar la clave API de Replicate
    def validate_replicate_api(self):
        replicate_invalid = False
        grok_invalid = False
        google_invalid = False
        has_saved_replicate = bool(self.load_api_key())
        has_saved_grok = bool(self.load_grok_api_key())
        has_saved_google = bool(self.load_google_api_key())
        
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
                    self.get_api_action.setEnabled(True)
                    if not (self.grok_api_key or self.google_api_key):
                        self.disable_functionality()
                
            except Exception:
                self.api_key = None
                self.save_api_key()
                if os.environ.get("REPLICATE_API_TOKEN"):
                    del os.environ["REPLICATE_API_TOKEN"]
                replicate_invalid = True
                self.get_api_action.setEnabled(True)
                if not (self.grok_api_key or self.google_api_key):
                    self.disable_functionality()
        else:
            replicate_invalid = has_saved_replicate
            self.get_api_action.setEnabled(True)

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
                    self.get_grok_api_action.setEnabled(True)
                    if not (self.api_key or self.google_api_key):
                        self.disable_functionality()
                
            except Exception:
                self.grok_api_key = None
                self.save_grok_api_key()
                if os.environ.get("GROK_API_KEY"):
                    del os.environ["GROK_API_KEY"]
                grok_invalid = True
                self.get_grok_api_action.setEnabled(True)
                if not (self.api_key or self.google_api_key):
                    self.disable_functionality()
        else:
            grok_invalid = has_saved_grok
            self.get_grok_api_action.setEnabled(True)

        if self.google_api_key:
            try:
                headers = {
                    "Content-Type": "application/json"
                }
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.google_api_key}"
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    self.enable_functionality()
                else:
                    self.google_api_key = None
                    self.save_google_api_key()
                    if os.environ.get("GOOGLE_API_KEY"):
                        del os.environ["GOOGLE_API_KEY"]
                    google_invalid = True
                    self.get_google_api_action.setEnabled(True)
                    if not (self.api_key or self.grok_api_key):
                        self.disable_functionality()
            
            except Exception:
                self.google_api_key = None
                self.save_google_api_key()
                if os.environ.get("GOOGLE_API_KEY"):
                    del os.environ["GOOGLE_API_KEY"]
                google_invalid = True
                self.get_google_api_action.setEnabled(True)
                if not (self.api_key or self.grok_api_key):
                    self.disable_functionality()
        else:
            google_invalid = has_saved_google
            self.get_google_api_action.setEnabled(True)

        if replicate_invalid and grok_invalid and google_invalid and (has_saved_replicate or has_saved_grok or has_saved_google):
            self.disable_functionality()
            QTimer.singleShot(100, lambda: self.show_all_apis_invalid_message())
        elif google_invalid and has_saved_google:
            if not (self.api_key or self.grok_api_key):
                self.disable_functionality()
            QTimer.singleShot(100, lambda: self.show_invalid_google_api_message())
        elif replicate_invalid and grok_invalid and has_saved_replicate:
            if not self.grok_api_key:
                self.disable_functionality()
            self.delete_action.setEnabled(False)
            QTimer.singleShot(100, lambda: self.show_invalid_api_message())
        elif grok_invalid and has_saved_grok:
            if not (self.api_key or self.google_api_key):
                self.disable_functionality()
            self.grok_delete_action.setEnabled(False)
            QTimer.singleShot(100, lambda: self.show_invalid_grok_api_message())
        
        self.initial_validation = False

    # Función para cargar la clave API de xAI
    def load_grok_api_key(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                encrypted_key = config.get('grok_api_key')
                return GestorCifrado.decrypt_text(encrypted_key) if encrypted_key else None
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Función para guardar la clave API de xAI
    def save_grok_api_key(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
        
        config['grok_api_key'] = GestorCifrado.encrypt_text(self.grok_api_key) if self.grok_api_key else None
        
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

        # Determinar si es macOS (Darwin) para aplicar configuraciones específicas
        is_darwin = platform.system() == 'Darwin'

        if is_darwin:
            # Forzar la barra de menú a estar dentro de la ventana en macOS
            menubar.setNativeMenuBar(False)

            # --- Configuración para Darwin: Añadir todo directamente a menubar ---
            # Google Menu
            self.google_menu = menubar.addMenu('Google')
            self.get_google_api_action = QAction(QIcon(resource_path("iconos/web.png")), obtener_traduccion('obtener_google_api', self.current_language), self)
            self.get_google_api_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.get_google_api_action.setObjectName('get_google_api_action')
            self.get_google_api_action.triggered.connect(lambda: webbrowser.open('https://aistudio.google.com/app/apikey'))
            self.get_google_api_action.setEnabled(not bool(self.google_api_key))
            self.google_menu.addAction(self.get_google_api_action)
            
            google_config_action = QAction(QIcon(resource_path("iconos/conf.png")), obtener_traduccion('configurar_google_api', self.current_language), self)
            google_config_action.setMenuRole(QAction.NoRole) # is_darwin es True
            google_config_action.setObjectName('google_config_action')
            google_config_action.triggered.connect(self.show_google_api_dialog)
            self.google_menu.addAction(google_config_action)
            
            self.google_delete_action = QAction(QIcon(resource_path("iconos/delete.png")), obtener_traduccion('borrar_google_api', self.current_language), self)
            self.google_delete_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.google_delete_action.setObjectName('google_delete_action')
            self.google_delete_action.triggered.connect(self.delete_google_api_key)
            self.google_menu.addAction(self.google_delete_action)

            # Replicate Menu
            self.replicate_menu = menubar.addMenu('Replicate') 
            self.get_api_action = QAction(QIcon(resource_path("iconos/web.png")), obtener_traduccion('obtener_replicate_api', self.current_language), self)
            self.get_api_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.get_api_action.setObjectName('get_replicate_api_action')
            self.get_api_action.triggered.connect(lambda: webbrowser.open('https://replicate.com/account/api-tokens'))
            self.get_api_action.setEnabled(not bool(self.api_key))
            self.replicate_menu.addAction(self.get_api_action)
            
            config_action = QAction(QIcon(resource_path("iconos/conf.png")), obtener_traduccion('configurar_replicate_api', self.current_language), self)
            config_action.setMenuRole(QAction.NoRole) # is_darwin es True
            config_action.setObjectName('replicate_config_action')
            config_action.triggered.connect(self.show_api_dialog)
            self.replicate_menu.addAction(config_action)
            
            self.delete_action = QAction(QIcon(resource_path("iconos/delete.png")), obtener_traduccion('borrar_replicate_api', self.current_language), self)
            self.delete_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.delete_action.setObjectName('replicate_delete_action')
            self.delete_action.triggered.connect(self.delete_api_key)
            self.replicate_menu.addAction(self.delete_action)

            # xAI Menu
            self.grok_menu = menubar.addMenu('xAI')
            self.get_grok_api_action = QAction(QIcon(resource_path("iconos/web.png")), obtener_traduccion('obtener_xai_api', self.current_language), self)
            self.get_grok_api_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.get_grok_api_action.setObjectName('get_xai_api_action')
            self.get_grok_api_action.triggered.connect(lambda: webbrowser.open('https://console.x.ai/team/default/api-keys'))
            self.get_grok_api_action.setEnabled(not bool(self.grok_api_key))
            self.grok_menu.addAction(self.get_grok_api_action)
            
            grok_config_action = QAction(QIcon(resource_path("iconos/conf.png")), obtener_traduccion('configurar_xai_api', self.current_language), self)
            grok_config_action.setMenuRole(QAction.NoRole) # is_darwin es True
            grok_config_action.setObjectName('xai_config_action')
            grok_config_action.triggered.connect(self.show_grok_api_dialog)
            self.grok_menu.addAction(grok_config_action)
            
            self.grok_delete_action = QAction(QIcon(resource_path("iconos/delete.png")), obtener_traduccion('borrar_xai_api', self.current_language), self)
            self.grok_delete_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.grok_delete_action.setObjectName('xai_delete_action')
            self.grok_delete_action.triggered.connect(self.delete_grok_api_key)
            self.grok_menu.addAction(self.grok_delete_action)

            # Acciones de la "derecha" directamente en menubar
            balance_action = QAction(QIcon(resource_path("iconos/coin.png")), '', self)
            balance_action.setMenuRole(QAction.NoRole) # is_darwin es True
            balance_action.setStatusTip('Consultar costos totales aproximados acumulados')
            balance_action.triggered.connect(self.calcular_costos_totales)
            balance_action.setEnabled(bool(self.api_key or self.grok_api_key))
            menubar.addAction(balance_action)
            self.balance_action = balance_action

            donate_action = QAction(QIcon(resource_path("iconos/paypal.png")), '', self)
            donate_action.setMenuRole(QAction.NoRole) # is_darwin es True
            donate_action.setStatusTip('Apoyar el desarrollo con una donación')
            donate_action.triggered.connect(lambda: webbrowser.open('https://paypal.me/KevinAZHD'))
            menubar.addAction(donate_action)
            self.paypal_action = donate_action
            
            github_action = QAction(QIcon(resource_path("iconos/github.png")), '', self)
            github_action.setMenuRole(QAction.NoRole) # is_darwin es True
            github_action.setStatusTip('Visitar el repositorio')
            github_action.triggered.connect(lambda: webbrowser.open('https://github.com/KevinAZHD/Powerpoineador'))
            menubar.addAction(github_action)
            self.github_action = github_action

            # Menú de Idioma directamente en menubar
            self.language_menu = QMenu(self)
            self.language_menu_action = QAction(QIcon(resource_path("iconos/languages.png")), '', self)
            self.language_menu_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.language_menu_action.setMenu(self.language_menu)

            self.language_group = QActionGroup(self)
            self.language_group.setExclusive(True)

            self.es_action = QAction(QIcon(resource_path("iconos/es.png")), obtener_traduccion('language_option_es', self.current_language), self)
            self.es_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.es_action.setCheckable(True)
            self.es_action.triggered.connect(lambda: self.change_language('es'))
            self.language_menu.addAction(self.es_action)
            self.language_group.addAction(self.es_action)

            self.en_action = QAction(QIcon(resource_path("iconos/en.png")), obtener_traduccion('language_option_en', self.current_language), self)
            self.en_action.setMenuRole(QAction.NoRole) # is_darwin es True
            self.en_action.setCheckable(True)
            self.en_action.triggered.connect(lambda: self.change_language('en'))
            self.language_menu.addAction(self.en_action)
            self.language_group.addAction(self.en_action)
            
            self.fr_action = QAction(QIcon(resource_path("iconos/fr.png")), obtener_traduccion('language_option_fr', self.current_language), self)
            self.fr_action.setMenuRole(QAction.NoRole); self.fr_action.setCheckable(True)
            self.fr_action.triggered.connect(lambda: self.change_language('fr'))
            self.language_menu.addAction(self.fr_action); self.language_group.addAction(self.fr_action)

            self.pt_action = QAction(QIcon(resource_path("iconos/pt.png")), obtener_traduccion('language_option_pt', self.current_language), self)
            self.pt_action.setMenuRole(QAction.NoRole); self.pt_action.setCheckable(True)
            self.pt_action.triggered.connect(lambda: self.change_language('pt'))
            self.language_menu.addAction(self.pt_action); self.language_group.addAction(self.pt_action)

            self.it_action = QAction(QIcon(resource_path("iconos/it.png")), obtener_traduccion('language_option_it', self.current_language), self)
            self.it_action.setMenuRole(QAction.NoRole); self.it_action.setCheckable(True)
            self.it_action.triggered.connect(lambda: self.change_language('it'))
            self.language_menu.addAction(self.it_action); self.language_group.addAction(self.it_action)

            self.de_action = QAction(QIcon(resource_path("iconos/de.png")), obtener_traduccion('language_option_de', self.current_language), self)
            self.de_action.setMenuRole(QAction.NoRole); self.de_action.setCheckable(True)
            self.de_action.triggered.connect(lambda: self.change_language('de'))
            self.language_menu.addAction(self.de_action); self.language_group.addAction(self.de_action)

            self.tl_action = QAction(QIcon(resource_path("iconos/tl.png")), obtener_traduccion('language_option_tl', self.current_language), self)
            self.tl_action.setMenuRole(QAction.NoRole); self.tl_action.setCheckable(True)
            self.tl_action.triggered.connect(lambda: self.change_language('tl'))
            self.language_menu.addAction(self.tl_action); self.language_group.addAction(self.tl_action)

            self.ar_action = QAction(QIcon(resource_path("iconos/ar.png")), obtener_traduccion('language_option_ar', self.current_language), self)
            self.ar_action.setMenuRole(QAction.NoRole); self.ar_action.setCheckable(True)
            self.ar_action.triggered.connect(lambda: self.change_language('ar'))
            self.language_menu.addAction(self.ar_action); self.language_group.addAction(self.ar_action)

            self.ru_action = QAction(QIcon(resource_path("iconos/ru.png")), obtener_traduccion('language_option_ru', self.current_language), self)
            self.ru_action.setMenuRole(QAction.NoRole); self.ru_action.setCheckable(True)
            self.ru_action.triggered.connect(lambda: self.change_language('ru'))
            self.language_menu.addAction(self.ru_action); self.language_group.addAction(self.ru_action)

            self.cn_action = QAction(QIcon(resource_path("iconos/cn.png")), obtener_traduccion('language_option_cn', self.current_language), self)
            self.cn_action.setMenuRole(QAction.NoRole); self.cn_action.setCheckable(True)
            self.cn_action.triggered.connect(lambda: self.change_language('cn'))
            self.language_menu.addAction(self.cn_action); self.language_group.addAction(self.cn_action)

            self.jp_action = QAction(QIcon(resource_path("iconos/jp.png")), obtener_traduccion('language_option_jp', self.current_language), self)
            self.jp_action.setMenuRole(QAction.NoRole); self.jp_action.setCheckable(True)
            self.jp_action.triggered.connect(lambda: self.change_language('jp'))
            self.language_menu.addAction(self.jp_action); self.language_group.addAction(self.jp_action)

            self.kr_action = QAction(QIcon(resource_path("iconos/kr.png")), obtener_traduccion('language_option_kr', self.current_language), self)
            self.kr_action.setMenuRole(QAction.NoRole); self.kr_action.setCheckable(True)
            self.kr_action.triggered.connect(lambda: self.change_language('kr'))
            self.language_menu.addAction(self.kr_action); self.language_group.addAction(self.kr_action)
            
            menubar.addAction(self.language_menu_action)

            # --- MENÚ DE APARIENCIA PARA DARWIN ---
            self.appearance_menu_action = QAction(QIcon(resource_path("iconos/theme.png")), '', self) # ICONO theme.png
            self.appearance_menu_action.setMenuRole(QAction.NoRole)
            self.appearance_menu = QMenu(self)
            self.appearance_menu_action.setMenu(self.appearance_menu)
            self.appearance_menu_action.setToolTip(obtener_traduccion('appearance_menu_title', self.current_language))

            self.theme_action_group = QActionGroup(self)
            self.theme_action_group.setExclusive(True)

            self.system_theme_action = QAction(QIcon(resource_path("iconos/system.png")), obtener_traduccion('system_theme_action_text', self.current_language), self) # ICONO system.png
            self.system_theme_action.setCheckable(True)
            self.system_theme_action.setMenuRole(QAction.NoRole)
            self.system_theme_action.triggered.connect(lambda: self.cambiar_tema_apariencia('system'))
            self.appearance_menu.addAction(self.system_theme_action)
            self.theme_action_group.addAction(self.system_theme_action)

            self.light_theme_action = QAction(QIcon(resource_path("iconos/light.png")), obtener_traduccion('light_theme_action_text', self.current_language), self) # ICONO light.png
            self.light_theme_action.setCheckable(True)
            self.light_theme_action.setMenuRole(QAction.NoRole)
            self.light_theme_action.triggered.connect(lambda: self.cambiar_tema_apariencia('light'))
            self.appearance_menu.addAction(self.light_theme_action)
            self.theme_action_group.addAction(self.light_theme_action)

            self.dark_theme_action = QAction(QIcon(resource_path("iconos/dark.png")), obtener_traduccion('dark_theme_action_text', self.current_language), self) # ICONO dark.png
            self.dark_theme_action.setCheckable(True)
            self.dark_theme_action.setMenuRole(QAction.NoRole)
            self.dark_theme_action.triggered.connect(lambda: self.cambiar_tema_apariencia('dark'))
            self.appearance_menu.addAction(self.dark_theme_action)
            self.theme_action_group.addAction(self.dark_theme_action)
            
            menubar.addAction(self.appearance_menu_action)
            menubar.addAction(self.language_menu_action)
            # --- FIN MENÚ DE APARIENCIA PARA DARWIN ---

        else:
            # --- Configuración para otras plataformas (original con left/right menubars) ---
            if is_darwin: # Esta condición es redundante aquí, ya que estamos en el 'else'
                menubar.setNativeMenuBar(False) # Ya estaba en el código original con la condición

            left_menubar = QMenuBar(menubar)
            
            # Google Menu
            self.google_menu = left_menubar.addMenu('Google')
            self.get_google_api_action = QAction(QIcon(resource_path("iconos/web.png")), obtener_traduccion('obtener_google_api', self.current_language), self)
            if is_darwin: self.get_google_api_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.get_google_api_action.setObjectName('get_google_api_action')
            self.get_google_api_action.triggered.connect(lambda: webbrowser.open('https://aistudio.google.com/app/apikey'))
            self.get_google_api_action.setEnabled(not bool(self.google_api_key))
            self.google_menu.addAction(self.get_google_api_action)
            
            google_config_action = QAction(QIcon(resource_path("iconos/conf.png")), obtener_traduccion('configurar_google_api', self.current_language), self)
            if is_darwin: google_config_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            google_config_action.setObjectName('google_config_action')
            google_config_action.triggered.connect(self.show_google_api_dialog)
            self.google_menu.addAction(google_config_action)
            
            self.google_delete_action = QAction(QIcon(resource_path("iconos/delete.png")), obtener_traduccion('borrar_google_api', self.current_language), self)
            if is_darwin: self.google_delete_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.google_delete_action.setObjectName('google_delete_action')
            self.google_delete_action.triggered.connect(self.delete_google_api_key)
            self.google_menu.addAction(self.google_delete_action)
            
            # Replicate Menu
            self.replicate_menu = left_menubar.addMenu('Replicate') 
            self.get_api_action = QAction(QIcon(resource_path("iconos/web.png")), obtener_traduccion('obtener_replicate_api', self.current_language), self)
            if is_darwin: self.get_api_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.get_api_action.setObjectName('get_replicate_api_action')
            self.get_api_action.triggered.connect(lambda: webbrowser.open('https://replicate.com/account/api-tokens'))
            self.get_api_action.setEnabled(not bool(self.api_key))
            self.replicate_menu.addAction(self.get_api_action)
            
            config_action = QAction(QIcon(resource_path("iconos/conf.png")), obtener_traduccion('configurar_replicate_api', self.current_language), self)
            if is_darwin: config_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            config_action.setObjectName('replicate_config_action')
            config_action.triggered.connect(self.show_api_dialog)
            self.replicate_menu.addAction(config_action)
            
            self.delete_action = QAction(QIcon(resource_path("iconos/delete.png")), obtener_traduccion('borrar_replicate_api', self.current_language), self)
            if is_darwin: self.delete_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.delete_action.setObjectName('replicate_delete_action')
            self.delete_action.triggered.connect(self.delete_api_key)
            self.replicate_menu.addAction(self.delete_action)

            # xAI Menu
            self.grok_menu = left_menubar.addMenu('xAI')
            self.get_grok_api_action = QAction(QIcon(resource_path("iconos/web.png")), obtener_traduccion('obtener_xai_api', self.current_language), self)
            if is_darwin: self.get_grok_api_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.get_grok_api_action.setObjectName('get_xai_api_action')
            self.get_grok_api_action.triggered.connect(lambda: webbrowser.open('https://console.x.ai/team/default/api-keys'))
            self.get_grok_api_action.setEnabled(not bool(self.grok_api_key))
            self.grok_menu.addAction(self.get_grok_api_action)
            
            grok_config_action = QAction(QIcon(resource_path("iconos/conf.png")), obtener_traduccion('configurar_xai_api', self.current_language), self)
            if is_darwin: grok_config_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            grok_config_action.setObjectName('xai_config_action')
            grok_config_action.triggered.connect(self.show_grok_api_dialog)
            self.grok_menu.addAction(grok_config_action)
            
            self.grok_delete_action = QAction(QIcon(resource_path("iconos/delete.png")), obtener_traduccion('borrar_xai_api', self.current_language), self)
            if is_darwin: self.grok_delete_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.grok_delete_action.setObjectName('xai_delete_action')
            self.grok_delete_action.triggered.connect(self.delete_grok_api_key)
            self.grok_menu.addAction(self.grok_delete_action)

            menubar.setCornerWidget(left_menubar, Qt.TopLeftCorner)

            right_menubar = QMenuBar(menubar)

            balance_action = QAction(QIcon(resource_path("iconos/coin.png")), '', self)
            if is_darwin: balance_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            balance_action.setStatusTip('Consultar costos totales aproximados acumulados')
            balance_action.triggered.connect(self.calcular_costos_totales)
            balance_action.setEnabled(bool(self.api_key or self.grok_api_key))
            right_menubar.addAction(balance_action)
            self.balance_action = balance_action

            donate_action = QAction(QIcon(resource_path("iconos/paypal.png")), '', self)
            if is_darwin: donate_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            donate_action.setStatusTip('Apoyar el desarrollo con una donación')
            donate_action.triggered.connect(lambda: webbrowser.open('https://paypal.me/KevinAZHD'))
            right_menubar.addAction(donate_action)
            self.paypal_action = donate_action
            
            github_action = QAction(QIcon(resource_path("iconos/github.png")), '', self)
            if is_darwin: github_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            github_action.setStatusTip('Visitar el repositorio')
            github_action.triggered.connect(lambda: webbrowser.open('https://github.com/KevinAZHD/Powerpoineador'))
            right_menubar.addAction(github_action)
            self.github_action = github_action

            self.language_menu = QMenu(self)
            self.language_menu_action = QAction(QIcon(resource_path("iconos/languages.png")), '', self)
            if is_darwin: self.language_menu_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.language_menu_action.setMenu(self.language_menu)

            self.language_group = QActionGroup(self)
            self.language_group.setExclusive(True)

            self.es_action = QAction(QIcon(resource_path("iconos/es.png")), obtener_traduccion('language_option_es', self.current_language), self)
            if is_darwin: self.es_action.setMenuRole(QAction.NoRole) # is_darwin es False aquí
            self.es_action.setCheckable(True)
            # ... (resto de la configuración y adición de acciones de idioma a self.language_menu y self.language_group) ...
            # Copiar el bloque completo de acciones de idioma como está en el original.
            self.es_action.triggered.connect(lambda: self.change_language('es'))
            self.language_menu.addAction(self.es_action)
            self.language_group.addAction(self.es_action)

            self.en_action = QAction(QIcon(resource_path("iconos/en.png")), obtener_traduccion('language_option_en', self.current_language), self)
            if is_darwin: self.en_action.setMenuRole(QAction.NoRole)
            self.en_action.setCheckable(True)
            self.en_action.triggered.connect(lambda: self.change_language('en'))
            self.language_menu.addAction(self.en_action)
            self.language_group.addAction(self.en_action)

            self.fr_action = QAction(QIcon(resource_path("iconos/fr.png")), obtener_traduccion('language_option_fr', self.current_language), self)
            if is_darwin: self.fr_action.setMenuRole(QAction.NoRole)
            self.fr_action.setCheckable(True)
            self.fr_action.triggered.connect(lambda: self.change_language('fr'))
            self.language_menu.addAction(self.fr_action)
            self.language_group.addAction(self.fr_action)

            self.pt_action = QAction(QIcon(resource_path("iconos/pt.png")), obtener_traduccion('language_option_pt', self.current_language), self)
            if is_darwin: self.pt_action.setMenuRole(QAction.NoRole)
            self.pt_action.setCheckable(True)
            self.pt_action.triggered.connect(lambda: self.change_language('pt'))
            self.language_menu.addAction(self.pt_action)
            self.language_group.addAction(self.pt_action)

            self.it_action = QAction(QIcon(resource_path("iconos/it.png")), obtener_traduccion('language_option_it', self.current_language), self)
            if is_darwin: self.it_action.setMenuRole(QAction.NoRole)
            self.it_action.setCheckable(True)
            self.it_action.triggered.connect(lambda: self.change_language('it'))
            self.language_menu.addAction(self.it_action)
            self.language_group.addAction(self.it_action)

            self.de_action = QAction(QIcon(resource_path("iconos/de.png")), obtener_traduccion('language_option_de', self.current_language), self)
            if is_darwin: self.de_action.setMenuRole(QAction.NoRole)
            self.de_action.setCheckable(True)
            self.de_action.triggered.connect(lambda: self.change_language('de'))
            self.language_menu.addAction(self.de_action)
            self.language_group.addAction(self.de_action)

            self.tl_action = QAction(QIcon(resource_path("iconos/tl.png")), obtener_traduccion('language_option_tl', self.current_language), self)
            if is_darwin: self.tl_action.setMenuRole(QAction.NoRole)
            self.tl_action.setCheckable(True)
            self.tl_action.triggered.connect(lambda: self.change_language('tl'))
            self.language_menu.addAction(self.tl_action)
            self.language_group.addAction(self.tl_action)

            self.ar_action = QAction(QIcon(resource_path("iconos/ar.png")), obtener_traduccion('language_option_ar', self.current_language), self)
            if is_darwin: self.ar_action.setMenuRole(QAction.NoRole)
            self.ar_action.setCheckable(True)
            self.ar_action.triggered.connect(lambda: self.change_language('ar'))
            self.language_menu.addAction(self.ar_action)
            self.language_group.addAction(self.ar_action)

            self.ru_action = QAction(QIcon(resource_path("iconos/ru.png")), obtener_traduccion('language_option_ru', self.current_language), self)
            if is_darwin: self.ru_action.setMenuRole(QAction.NoRole)
            self.ru_action.setCheckable(True)
            self.ru_action.triggered.connect(lambda: self.change_language('ru'))
            self.language_menu.addAction(self.ru_action)
            self.language_group.addAction(self.ru_action)

            self.cn_action = QAction(QIcon(resource_path("iconos/cn.png")), obtener_traduccion('language_option_cn', self.current_language), self)
            if is_darwin: self.cn_action.setMenuRole(QAction.NoRole)
            self.cn_action.setCheckable(True)
            self.cn_action.triggered.connect(lambda: self.change_language('cn'))
            self.language_menu.addAction(self.cn_action)
            self.language_group.addAction(self.cn_action)

            self.jp_action = QAction(QIcon(resource_path("iconos/jp.png")), obtener_traduccion('language_option_jp', self.current_language), self)
            if is_darwin: self.jp_action.setMenuRole(QAction.NoRole)
            self.jp_action.setCheckable(True)
            self.jp_action.triggered.connect(lambda: self.change_language('jp'))
            self.language_menu.addAction(self.jp_action)
            self.language_group.addAction(self.jp_action)

            self.kr_action = QAction(QIcon(resource_path("iconos/kr.png")), obtener_traduccion('language_option_kr', self.current_language), self)
            if is_darwin: self.kr_action.setMenuRole(QAction.NoRole)
            self.kr_action.setCheckable(True)
            self.kr_action.triggered.connect(lambda: self.change_language('kr'))
            self.language_menu.addAction(self.kr_action)
            self.language_group.addAction(self.kr_action)
            
            right_menubar.addAction(self.language_menu_action)
            menubar.setCornerWidget(right_menubar, Qt.TopRightCorner)

            # --- MENÚ DE APARIENCIA PARA OTRAS PLATAFORMAS (EN RIGHT_MENUBAR) ---
            self.appearance_menu_action = QAction(QIcon(resource_path("iconos/theme.png")), '', self) # ICONO theme.png
            self.appearance_menu = QMenu(self)
            self.appearance_menu_action.setMenu(self.appearance_menu)
            self.appearance_menu_action.setToolTip(obtener_traduccion('appearance_menu_title', self.current_language))

            self.theme_action_group = QActionGroup(self)
            self.theme_action_group.setExclusive(True)

            self.system_theme_action = QAction(QIcon(resource_path("iconos/system.png")), obtener_traduccion('system_theme_action_text', self.current_language), self) # ICONO system.png
            self.system_theme_action.setCheckable(True)
            self.system_theme_action.triggered.connect(lambda: self.cambiar_tema_apariencia('system'))
            self.appearance_menu.addAction(self.system_theme_action)
            self.theme_action_group.addAction(self.system_theme_action)

            self.light_theme_action = QAction(QIcon(resource_path("iconos/light.png")), obtener_traduccion('light_theme_action_text', self.current_language), self) # ICONO light.png
            self.light_theme_action.setCheckable(True)
            self.light_theme_action.triggered.connect(lambda: self.cambiar_tema_apariencia('light'))
            self.appearance_menu.addAction(self.light_theme_action)
            self.theme_action_group.addAction(self.light_theme_action)

            self.dark_theme_action = QAction(QIcon(resource_path("iconos/dark.png")), obtener_traduccion('dark_theme_action_text', self.current_language), self) # ICONO dark.png
            self.dark_theme_action.setCheckable(True)
            self.dark_theme_action.triggered.connect(lambda: self.cambiar_tema_apariencia('dark'))
            self.appearance_menu.addAction(self.dark_theme_action)
            self.theme_action_group.addAction(self.dark_theme_action)
            
            right_menubar.addAction(self.appearance_menu_action) # Añadido a right_menubar
            right_menubar.addAction(self.language_menu_action)
            # --- FIN MENÚ DE APARIENCIA PARA OTRAS PLATAFORMAS ---

        # >>> LLAMAR después de configurar las acciones <<<
        self.update_language_menu_state()
        self.update_theme_menu_state() # <--- LLAMAR PARA ACTUALIZAR ESTADO DEL MENÚ DE TEMA

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
        msg.setWindowTitle(obtener_traduccion('replicate_delete_confirm_title', self.current_language))
        msg.setText(obtener_traduccion('replicate_delete_confirm_message', self.current_language))
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', self.current_language))
        msg.button(QMessageBox.No).setText(obtener_traduccion('no', self.current_language))
        
        QApplication.beep()
        
        msg.adjustSize()
        msg_pos = self.geometry().center() - msg.rect().center()
        msg.move(msg_pos)
        dialog_pos = msg.pos()
        
        if msg.exec() == QMessageBox.Yes:
            self.api_key = None
            self.save_api_key()
            if os.environ.get("REPLICATE_API_TOKEN"):
                del os.environ["REPLICATE_API_TOKEN"]

            self.get_api_action.setEnabled(True)
            
            # Solo limpiamos el log siempre
            if hasattr(self, 'widget') and hasattr(self.widget, 'log_text'):
                self.widget.log_text.clear()
                QApplication.processEvents()
            
            # Limpiar vista previa solo cuando no quedan más APIs
            if not (self.grok_api_key or self.google_api_key):
                if hasattr(self, 'widget'):
                    # Solución radical: reemplazar completamente el objeto vista_previa
                    if hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                        try:
                            # Obtener el parent y el layout donde está la vista previa
                            parent_widget = self.widget.right_panel
                            right_layout = parent_widget.layout()
                            
                            # Eliminar la vista previa antigua
                            if self.widget.vista_previa:
                                old_vista_previa = self.widget.vista_previa
                                right_layout.removeWidget(old_vista_previa)
                                old_vista_previa.setParent(None)
                                old_vista_previa.deleteLater()
                                QApplication.processEvents()
                            
                            # Crear una nueva vista previa
                            from Vista_previa import VentanaVistaPrevia
                            self.widget.vista_previa = VentanaVistaPrevia(self.widget)
                            self.widget.vista_previa.current_language = self.current_language
                            self.widget.vista_previa.actualizar_idioma(self.current_language)
                            
                            # Agregar la nueva vista previa al layout
                            right_layout.insertWidget(0, self.widget.vista_previa, 3)
                            QApplication.processEvents()
                        except Exception as e:
                            print(f"Error al recrear vista previa: {str(e)}")
                            # Si falla, intentar el método anterior
                            if hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                                self.widget.vista_previa.limpiar_contenedor()
                                QApplication.processEvents()
                                self.widget.vista_previa.reset_completo()
                                self.widget.vista_previa.update()
                    
                    # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                    QApplication.processEvents()
                
                self.disable_functionality()
                # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                QApplication.processEvents()
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
                    # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                    QApplication.processEvents()
            
            self.balance_action.setEnabled(bool(self.grok_api_key))
            
            # Forzar actualización de la interfaz antes de mostrar el mensaje
            QApplication.processEvents()
            
            success_msg = QMessageBox()
            success_msg.setWindowTitle(obtener_traduccion('replicate_api_deleted_title', self.current_language))
            success_msg.setText(obtener_traduccion('replicate_api_deleted_message', self.current_language))
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowIcon(QIcon(resource_path("iconos/replicate.png")))
            
            success_msg.move(dialog_pos)
            
            success_msg.exec()

    # Función para mostrar la ventana de configuración de la clave API de xAI
    def show_grok_api_dialog(self):
        self.grok_api_window = GrokAPIKeyWindow(self)
        self.grok_api_window.show()

    # Función para borrar la clave API de xAI
    def delete_grok_api_key(self):
        msg = QMessageBox()
        msg.setWindowTitle(obtener_traduccion('xai_delete_confirm_title', self.current_language))
        msg.setText(obtener_traduccion('xai_delete_confirm_message', self.current_language))
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', self.current_language))
        msg.button(QMessageBox.No).setText(obtener_traduccion('no', self.current_language))
        
        QApplication.beep()
        
        msg.adjustSize()
        msg_pos = self.geometry().center() - msg.rect().center()
        msg.move(msg_pos)
        dialog_pos = msg.pos()
        
        if msg.exec() == QMessageBox.Yes:
            self.grok_api_key = None
            self.save_grok_api_key()
            if os.environ.get("GROK_API_KEY"):
                del os.environ["GROK_API_KEY"]
            
            self.get_grok_api_action.setEnabled(True)
            
            # Solo limpiamos el log siempre
            if hasattr(self, 'widget') and hasattr(self.widget, 'log_text'):
                self.widget.log_text.clear()
                QApplication.processEvents()
            
            # Limpiar vista previa solo cuando no quedan más APIs
            if not (self.api_key or self.google_api_key):
                if hasattr(self, 'widget'):
                    # Solución radical: reemplazar completamente el objeto vista_previa
                    if hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                        try:
                            # Obtener el parent y el layout donde está la vista previa
                            parent_widget = self.widget.right_panel
                            right_layout = parent_widget.layout()
                            
                            # Eliminar la vista previa antigua
                            if self.widget.vista_previa:
                                old_vista_previa = self.widget.vista_previa
                                right_layout.removeWidget(old_vista_previa)
                                old_vista_previa.setParent(None)
                                old_vista_previa.deleteLater()
                                QApplication.processEvents()
                            
                            # Crear una nueva vista previa
                            from Vista_previa import VentanaVistaPrevia
                            self.widget.vista_previa = VentanaVistaPrevia(self.widget)
                            self.widget.vista_previa.current_language = self.current_language
                            self.widget.vista_previa.actualizar_idioma(self.current_language)
                            
                            # Agregar la nueva vista previa al layout
                            right_layout.insertWidget(0, self.widget.vista_previa, 3)
                            QApplication.processEvents()
                        except Exception as e:
                            print(f"Error al recrear vista previa: {str(e)}")
                            # Si falla, intentar el método anterior
                            if hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                                self.widget.vista_previa.limpiar_contenedor()
                                QApplication.processEvents()
                                self.widget.vista_previa.reset_completo()
                                self.widget.vista_previa.update()
                    
                    # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                    QApplication.processEvents()
                
                self.disable_functionality()
                # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                QApplication.processEvents()
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
                    # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                    QApplication.processEvents()
            
            self.balance_action.setEnabled(bool(self.api_key))
            
            # Forzar actualización de la interfaz antes de mostrar el mensaje
            QApplication.processEvents()
            
            success_msg = QMessageBox()
            success_msg.setWindowTitle(obtener_traduccion('xai_api_deleted_title', self.current_language))
            success_msg.setText(obtener_traduccion('xai_api_deleted_message', self.current_language))
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowIcon(QIcon(resource_path("iconos/xai.jpg")))
            
            success_msg.move(dialog_pos)
            
            success_msg.exec()

    # Función para borrar la clave API de Google
    def delete_google_api_key(self):
        msg = QMessageBox()
        msg.setWindowTitle(obtener_traduccion('google_delete_confirm_title', self.current_language))
        msg.setText(obtener_traduccion('google_delete_confirm_message', self.current_language))
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon(resource_path("iconos/google.png")))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', self.current_language))
        msg.button(QMessageBox.No).setText(obtener_traduccion('no', self.current_language))
        
        QApplication.beep()
        
        msg.adjustSize()
        msg_pos = self.geometry().center() - msg.rect().center()
        msg.move(msg_pos)
        dialog_pos = msg.pos()
        
        if msg.exec() == QMessageBox.Yes:
            self.google_api_key = None
            self.save_google_api_key()
            if os.environ.get("GOOGLE_API_KEY"):
                del os.environ["GOOGLE_API_KEY"]
            
            self.get_google_api_action.setEnabled(True)
            
            # Solo limpiamos el log siempre
            if hasattr(self, 'widget') and hasattr(self.widget, 'log_text'):
                self.widget.log_text.clear()
                QApplication.processEvents()
            
            # Limpiar vista previa solo cuando no quedan más APIs
            if not (self.api_key or self.grok_api_key):
                if hasattr(self, 'widget'):
                    # Solución radical: reemplazar completamente el objeto vista_previa
                    if hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                        try:
                            # Obtener el parent y el layout donde está la vista previa
                            parent_widget = self.widget.right_panel
                            right_layout = parent_widget.layout()
                            
                            # Eliminar la vista previa antigua
                            if self.widget.vista_previa:
                                old_vista_previa = self.widget.vista_previa
                                right_layout.removeWidget(old_vista_previa)
                                old_vista_previa.setParent(None)
                                old_vista_previa.deleteLater()
                                QApplication.processEvents()
                            
                            # Crear una nueva vista previa
                            from Vista_previa import VentanaVistaPrevia
                            self.widget.vista_previa = VentanaVistaPrevia(self.widget)
                            self.widget.vista_previa.current_language = self.current_language
                            self.widget.vista_previa.actualizar_idioma(self.current_language)
                            
                            # Agregar la nueva vista previa al layout
                            right_layout.insertWidget(0, self.widget.vista_previa, 3)
                            QApplication.processEvents()
                        except Exception as e:
                            print(f"Error al recrear vista previa: {str(e)}")
                            # Si falla, intentar el método anterior
                            if hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                                self.widget.vista_previa.limpiar_contenedor()
                                QApplication.processEvents()
                                self.widget.vista_previa.reset_completo()
                                self.widget.vista_previa.update()
                    
                    # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                    QApplication.processEvents()
                
                self.disable_functionality()
                # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                QApplication.processEvents()
                try:
                    if os.path.exists(CONFIG_FILE):
                        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        if 'costos_totales' in config:
                            del config['costos_totales']
                        if 'num_diapositivas' in config:
                            del config['num_diapositivas']
                        if 'pdf_path' in config: # <--- Añadir esta línea
                            del config['pdf_path'] # <--- Añadir esta línea
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    print(f"Error al borrar costos totales: {str(e)}")
            else:
                self.google_delete_action.setEnabled(False)
                if self.widget:
                    self.widget.populate_fields()
                    # Forzar procesamiento de eventos para asegurar la actualización visual inmediata
                    QApplication.processEvents()
            
            self.balance_action.setEnabled(bool(self.api_key or self.grok_api_key))
            
            # Forzar actualización de la interfaz antes de mostrar el mensaje
            QApplication.processEvents()
            
            success_msg = QMessageBox()
            success_msg.setWindowTitle(obtener_traduccion('google_api_deleted_title', self.current_language))
            success_msg.setText(obtener_traduccion('google_api_deleted_message', self.current_language))
            success_msg.setIcon(QMessageBox.Information)
            success_msg.setWindowIcon(QIcon(resource_path("iconos/google.png")))
            
            success_msg.move(dialog_pos)
            
            success_msg.exec()

    # Método para deshabilitar elementos del menú durante la generación
    def disable_menu_during_generation(self):
        try:
            # Deshabilitar menús completos
            self.replicate_menu.setEnabled(False)
            self.grok_menu.setEnabled(False)
            self.google_menu.setEnabled(False)
            
            # Deshabilitar acciones específicas
            self.balance_action.setEnabled(False)
            self.github_action.setEnabled(False)
            self.language_menu_action.setEnabled(False) # <-- Deshabilitar el nuevo menú
            self.paypal_action.setEnabled(False)
            self.appearance_menu_action.setEnabled(False) # <-- AÑADIR ESTA LÍNEA
            
            # Actualizar estilo de checkboxes en modo claro
            if hasattr(self, 'theme_manager'):
                self.theme_manager.set_generating_state(True)
        except Exception as e:
            print(f"Error al deshabilitar menús: {str(e)}")

    # Método para habilitar elementos del menú después de la generación
    def enable_menu_after_generation(self):
        try:
            # Habilitar menús completos siempre
            self.replicate_menu.setEnabled(True)
            self.grok_menu.setEnabled(True)
            self.google_menu.setEnabled(True)
            
            # Habilitar acciones específicas
            self.balance_action.setEnabled(bool(self.api_key or self.grok_api_key))
            self.github_action.setEnabled(True)
            self.language_menu_action.setEnabled(True) # <-- Habilitar el nuevo menú
            self.paypal_action.setEnabled(True)
            self.appearance_menu_action.setEnabled(True) # <-- AÑADIR ESTA LÍNEA
            
            # Restaurar estilo normal de checkboxes
            if hasattr(self, 'theme_manager'):
                self.theme_manager.set_generating_state(False)
        except Exception as e:
            print(f"Error al habilitar menús: {str(e)}")

    # Función para configurar la ventana principal
    def setup_main_widget(self):
        # --- MODIFICADO: Pasar idioma al crear el widget ---
        self.widget = PowerpoineatorWidget(self.current_language)
        # -------------------------------------------------
        self.setCentralWidget(self.widget)
        self.setWindowTitle(obtener_traduccion('app_title', self.current_language))
        self.setMinimumSize(1485, 700)
        self.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
        
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        # --- AÑADIDO: Llamar a actualizar_traducciones DESPUÉS de setCentralWidget y configurar ventana ---
        # Esto asegura que la jerarquía de padres esté establecida y que PowerpoineatorWidget
        # pueda actualizar sus propios elementos y propagar la actualización a VistaPrevia si es necesario.
        self.widget.actualizar_traducciones(self.current_language)
        # --------------------------------------------------------------------------------------------

    # Función para deshabilitar la funcionalidad de la aplicación
    def disable_functionality(self):
        if hasattr(self, 'balance_action'):
            self.balance_action.setEnabled(False)
            try:
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    if 'costos_totales' in config:
                        del config['costos_totales']
                    if 'num_diapositivas' in config:
                        del config['num_diapositivas']
                    if 'pdf_path' in config: # <--- Añadir esta línea
                        del config['pdf_path'] # <--- Añadir esta línea
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"Error al borrar costos totales: {str(e)}")
        
        if self.widget:
            self.widget.generar_btn.setStyleSheet("")
            
            self.widget.generar_btn.setEnabled(False)
            self.widget.descripcion_text.setEnabled(False)
            
            self.widget.texto_label.setEnabled(False)
            self.widget.texto_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.widget.imagen_label.setEnabled(False)
            self.widget.imagen_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.widget.descripcion_label.setEnabled(False)
            self.widget.descripcion_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            
            self.widget.texto_combo.setEnabled(False)
            self.widget.texto_combo.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.widget.imagen_combo.setEnabled(False)
            self.widget.imagen_combo.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.widget.auto_open_checkbox.setEnabled(False)

            self.widget.diapositivas_label.setEnabled(False)
            self.widget.diapositivas_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.widget.cargar_imagen_btn.setEnabled(False)
            self.widget.ver_imagen_btn.setEnabled(False)
            self.widget.num_diapositivas_spin.setEnabled(False)
            self.widget.num_diapositivas_spin.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            self.widget.num_diapositivas_spin.setValue(8)
            self.widget.num_diapositivas_spin.setStyleSheet("QSpinBox:disabled { color: transparent; }")
            
            # Deshabilitar selección de fuente
            if hasattr(self.widget, 'title_font_label'):
                self.widget.title_font_label.setEnabled(False)
                self.widget.title_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            if hasattr(self.widget, 'font_combo'):
                self.widget.font_combo.setEnabled(False)
                self.widget.font_combo.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                self.widget.font_combo.setCurrentIndex(-1)  # Nueva línea añadida
            
            # Deshabilitar selección de tamaño de fuente
            if hasattr(self.widget, 'title_font_size_label'):
                self.widget.title_font_size_label.setEnabled(False)
                self.widget.title_font_size_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            if hasattr(self.widget, 'title_font_size_spin'):
                self.widget.title_font_size_spin.setEnabled(False)
                self.widget.title_font_size_spin.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                self.widget.title_font_size_spin.setStyleSheet("QSpinBox:disabled { color: transparent; }") # Ocultar valor
            if hasattr(self.widget, 'content_font_size_label'):
                self.widget.content_font_size_label.setEnabled(False)
                self.widget.content_font_size_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            if hasattr(self.widget, 'content_font_size_spin'):
                self.widget.content_font_size_spin.setEnabled(False)
                self.widget.content_font_size_spin.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                self.widget.content_font_size_spin.setStyleSheet("QSpinBox:disabled { color: transparent; }") # Ocultar valor

            # Deshabilitar selección de fuente de contenido
            if hasattr(self.widget, 'content_font_label'):
                self.widget.content_font_label.setEnabled(False)
                self.widget.content_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            if hasattr(self.widget, 'content_font_combo'):
                self.widget.content_font_combo.setEnabled(False)
                self.widget.content_font_combo.setAttribute(Qt.WA_TransparentForMouseEvents, True)
                self.widget.content_font_combo.setCurrentIndex(-1)

            # Deshabilitar checkboxes de formato de título
            if hasattr(self.widget, 'title_bold_checkbox'):
                 self.widget.title_bold_checkbox.setEnabled(False)
                 self.widget.title_bold_checkbox.setChecked(False)
            if hasattr(self.widget, 'title_italic_checkbox'):
                 self.widget.title_italic_checkbox.setEnabled(False)
                 self.widget.title_italic_checkbox.setChecked(False)
            if hasattr(self.widget, 'title_underline_checkbox'):
                 self.widget.title_underline_checkbox.setEnabled(False)
                 self.widget.title_underline_checkbox.setChecked(False)

            # >>> AÑADIR Deshabilitar checkboxes de formato de contenido <<<
            if hasattr(self.widget, 'content_bold_checkbox'):
                 self.widget.content_bold_checkbox.setEnabled(False)
                 self.widget.content_bold_checkbox.setChecked(False)
            if hasattr(self.widget, 'content_italic_checkbox'):
                 self.widget.content_italic_checkbox.setEnabled(False)
                 self.widget.content_italic_checkbox.setChecked(False)
            if hasattr(self.widget, 'content_underline_checkbox'):
                 self.widget.content_underline_checkbox.setEnabled(False)
                 self.widget.content_underline_checkbox.setChecked(False)

            # Limpiar la vista previa y resetearla
            if hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                self.widget.vista_previa.reset_completo()
            
            # Deshabilitar botones de PDF
            if hasattr(self.widget, 'cargar_pdf_btn'):
                self.widget.cargar_pdf_btn.setEnabled(False)
            if hasattr(self.widget, 'eliminar_pdf_btn'):
                self.widget.eliminar_pdf_btn.setEnabled(False)
                self.widget.eliminar_pdf_btn.hide() # <--- Añadir esta línea
            if hasattr(self.widget, 'revisar_pdf_btn'):
                self.widget.revisar_pdf_btn.setEnabled(False)
                self.widget.revisar_pdf_btn.hide() # <--- Añadir esta línea
            if hasattr(self.widget, 'pdf_label'): # <--- Añadir bloque
                self.widget.pdf_label.setText("") # <--- Añadir esta línea
            if hasattr(self.widget, 'pdf_cargado'): # <--- Añadir bloque
                self.widget.pdf_cargado = None # <--- Añadir esta línea
            
            # Deshabilitar el botón de ocultar/mostrar log
            if hasattr(self.widget, 'log_toggle_btn'):
                # Guardar las dimensiones originales
                original_height = self.widget.log_toggle_btn.height()
                self.widget.log_toggle_btn.setEnabled(False)
                # Aplicar estilo para el estado deshabilitado que mantenga las mismas dimensiones
                self.widget.log_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #7C7C7C;
                        color: #C1C1C1;
                        border: none;
                        border-radius: 3px;
                        padding: 2px 10px;
                        min-width: 60px;
                    }
                    QPushButton:disabled {
                        background-color: #7C7C7C;
                        color: #C1C1C1;
                        border: none;
                        border-radius: 3px;
                        padding: 2px 10px;
                        min-width: 60px;
                    }
                """)
                # Asegurar la altura correcta
                self.widget.log_toggle_btn.setFixedHeight(original_height)
            
            self.widget.descripcion_text.clear()
            self.widget.descripcion_text.setPlaceholderText(obtener_traduccion('description_text', self.current_language))
            
            self.widget.clear_fields()
            self.widget.contador_label.hide()
            
            self.delete_action.setEnabled(False)
            self.grok_delete_action.setEnabled(False)
            self.google_delete_action.setEnabled(bool(self.google_api_key))
            
            self.widget.cargar_imagen_btn.hide()
            self.widget.ver_imagen_btn.hide()

            # >>> AÑADIR Deshabilitar botón de selección de estilo <<<
            if hasattr(self.widget, 'select_style_btn'):
                self.widget.select_style_btn.setEnabled(False)
                
            # >>> AÑADIR Ocultar etiqueta de estilo actual <<<
            if hasattr(self.widget, 'current_style_label'):
                self.widget.current_style_label.setText("")
                self.widget.current_style_label.hide()

    # Función para habilitar la funcionalidad de la aplicación
    def enable_functionality(self):
        if hasattr(self, 'balance_action'):
            self.balance_action.setEnabled(bool(self.api_key or self.grok_api_key))
        
        if self.widget:
            api_available = bool(self.api_key or self.grok_api_key or self.google_api_key)
            
            if not api_available:
                self.disable_functionality()
                return
            
            self.widget.generar_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6E00;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #FF8C32;
                }
                QPushButton:pressed {
                    background-color: #E56200;
                }
            """)
            
            # Habilitar el botón de ocultar/mostrar log
            if hasattr(self.widget, 'log_toggle_btn'):
                self.widget.log_toggle_btn.setEnabled(True)
                # Mantener solo el estilo
                self.widget.log_toggle_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF8C32;
                        color: white;
                        border: none;
                        border-radius: 3px;
                        padding: 2px 10px;
                        min-width: 60px;
                    }
                    QPushButton:hover {
                        background-color: #FFA559;
                    }
                    QPushButton:pressed {
                        background-color: #E56200;
                    }
                """)
                
            self.widget.generar_btn.setEnabled(True)
            self.widget.descripcion_text.setEnabled(True)
            
            self.widget.texto_label.setEnabled(True)
            self.widget.texto_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.widget.imagen_label.setEnabled(True)
            self.widget.imagen_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.widget.descripcion_label.setEnabled(True)
            self.widget.descripcion_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            
            self.widget.texto_combo.setEnabled(True)
            self.widget.texto_combo.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            
            # Habilitar selección de fuente
            if hasattr(self.widget, 'title_font_label'):
                self.widget.title_font_label.setEnabled(True)
                self.widget.title_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                self.widget.load_font_selection()
            if hasattr(self.widget, 'font_combo'):
                self.widget.font_combo.setEnabled(True)
                self.widget.font_combo.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                self.widget.load_font_selection()  # Modificado: llamar al método del widget
            
            # Habilitar selección de tamaño de fuente
            if hasattr(self.widget, 'title_font_size_label'):
                self.widget.title_font_size_label.setEnabled(True)
                self.widget.title_font_size_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            if hasattr(self.widget, 'title_font_size_spin'):
                self.widget.title_font_size_spin.setEnabled(True)
                self.widget.title_font_size_spin.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            if hasattr(self.widget, 'content_font_size_label'):
                self.widget.content_font_size_label.setEnabled(True)
                self.widget.content_font_size_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            if hasattr(self.widget, 'content_font_size_spin'):
                self.widget.content_font_size_spin.setEnabled(True)
                self.widget.content_font_size_spin.setAttribute(Qt.WA_TransparentForMouseEvents, False)

            self.widget.auto_open_checkbox.setEnabled(True)
            self.widget.diapositivas_label.setEnabled(True)
            self.widget.diapositivas_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.widget.num_diapositivas_spin.setEnabled(True)
            self.widget.num_diapositivas_spin.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            
            # Habilitar botones de PDF
            if hasattr(self.widget, 'cargar_pdf_btn'):
                self.widget.cargar_pdf_btn.setEnabled(True)
            
            # Verificar si hay un PDF cargado y mostrar/habilitar los botones correspondientes
            if hasattr(self.widget, 'pdf_cargado') and self.widget.pdf_cargado:
                if hasattr(self.widget, 'eliminar_pdf_btn'):
                    self.widget.eliminar_pdf_btn.show()
                    self.widget.eliminar_pdf_btn.setEnabled(True)
                if hasattr(self.widget, 'revisar_pdf_btn'):
                    self.widget.revisar_pdf_btn.show()
                    self.widget.revisar_pdf_btn.setEnabled(True)
                if hasattr(self.widget, 'pdf_label') and hasattr(self.widget.pdf_label, 'text') and not self.widget.pdf_label.text():
                    # Restaurar la etiqueta del PDF si está vacía pero hay PDF cargado
                    current_language = getattr(self, 'current_language', 'es')
                    self.widget.pdf_label.setText(obtener_traduccion('pdf_cargado', current_language).format(os.path.basename(self.widget.pdf_cargado)))
            
            self.widget.descripcion_text.setPlaceholderText("")
            
            self.widget.contador_label.show()
            
            # Siempre habilitar el combo de imágenes
            self.widget.imagen_combo.setEnabled(True)
            self.widget.imagen_combo.setAttribute(Qt.WA_TransparentForMouseEvents, False)

            self.widget.populate_fields()
            
            self.delete_action.setEnabled(bool(self.api_key))
            self.grok_delete_action.setEnabled(bool(self.grok_api_key))
            self.google_delete_action.setEnabled(bool(self.google_api_key))

            # Habilitar selección de fuente de contenido
            if hasattr(self.widget, 'content_font_label'):
                self.widget.content_font_label.setEnabled(True)
                self.widget.content_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            if hasattr(self.widget, 'content_font_combo'):
                self.widget.content_font_combo.setEnabled(True)
                self.widget.content_font_combo.setAttribute(Qt.WA_TransparentForMouseEvents, False)
                self.widget.load_content_font_selection() # Recargar selección

            # Habilitar checkboxes de formato de título
            if hasattr(self.widget, 'title_bold_checkbox'):
                 self.widget.title_bold_checkbox.setEnabled(True)
            if hasattr(self.widget, 'title_italic_checkbox'):
                 self.widget.title_italic_checkbox.setEnabled(True)
            if hasattr(self.widget, 'title_underline_checkbox'):
                 self.widget.title_underline_checkbox.setEnabled(True)
            # Recargar estado guardado de formato
            if hasattr(self.widget, 'load_format_settings'):
                 self.widget.load_format_settings()

            # >>> AÑADIR Habilitar checkboxes de formato de contenido <<<
            if hasattr(self.widget, 'content_bold_checkbox'):
                 self.widget.content_bold_checkbox.setEnabled(True)
            if hasattr(self.widget, 'content_italic_checkbox'):
                 self.widget.content_italic_checkbox.setEnabled(True)
            if hasattr(self.widget, 'content_underline_checkbox'):
                 self.widget.content_underline_checkbox.setEnabled(True)

            # >>> AÑADIR Habilitar botón de selección de estilo <<<
            if hasattr(self.widget, 'select_style_btn'):
                self.widget.select_style_btn.setEnabled(True)
                
            # >>> AÑADIR Mostrar etiqueta de estilo actual <<<
            if hasattr(self.widget, 'current_style_label'):
                self.widget.current_style_label.show()
                self.widget.update_style_label() # Actualizar el texto

    # Función para manejar el evento de cierre de la ventana
    def closeEvent(self, event):
        self.save_window_position()
        if hasattr(self, 'widget') and self.widget:
            if hasattr(self.widget, 'worker') and self.widget.worker and self.widget.worker.isRunning():
                msg = QMessageBox()
                msg.setWindowTitle(obtener_traduccion('confirm_exit', self.current_language))
                msg.setText(obtener_traduccion('generation_in_progress', self.current_language))
                msg.setIcon(QMessageBox.Question)
                msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.No)
                msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', self.current_language))
                msg.button(QMessageBox.No).setText(obtener_traduccion('no', self.current_language))
                
                if msg.exec() == QMessageBox.Yes:
                    if self.widget.worker:
                        self.widget.worker.requestInterruption()
                        self.widget.worker.terminate()
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
        msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
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
                    
                    # Siempre maximizar la ventana, independientemente de la configuración guardada
                    QTimer.singleShot(0, self.showMaximized)
                    return True
                    
        except Exception as e:
            print(f"Error al cargar la posición de la ventana: {str(e)}")
        
        # Siempre maximizar la ventana si no hay configuración
        QTimer.singleShot(0, self.showMaximized)
        return True

    # Función para calcular los costos totales
    def calcular_costos_totales(self):
        self.balance_window = BalanceWindow(self)
        self.balance_window.show()

    # Función para cargar la clave API de Google
    def load_google_api_key(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                encrypted_key = config.get('google_api_key')
                return GestorCifrado.decrypt_text(encrypted_key) if encrypted_key else None
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    # Función para guardar la clave API de Google
    def save_google_api_key(self):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            config = {}
        
        config['google_api_key'] = GestorCifrado.encrypt_text(self.google_api_key) if self.google_api_key else None
        
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    # Función para establecer la clave API de Google
    def set_google_api_key(self, api_key):
        self.google_api_key = api_key
        self.save_google_api_key()
        os.environ["GOOGLE_API_KEY"] = api_key
        self.enable_functionality()
        self.get_google_api_action.setEnabled(False)

    # Función para mostrar la ventana de configuración de la clave API de Google
    def show_google_api_dialog(self):
        self.google_api_window = GoogleAPIKeyWindow(self)
        self.google_api_window.show()

    # Función para mostrar el mensaje de clave API inválida de Google
    def show_invalid_google_api_message(self):
        msg = QMessageBox()
        msg.setWindowTitle(obtener_traduccion('google_invalid_api_title', self.current_language))
        msg.setText(obtener_traduccion('google_invalid_api_message', self.current_language))
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(resource_path("iconos/google.png")))
        msg.exec()

    # Función para mostrar el mensaje de error de conexión con Google
    def show_google_connection_error_message(self):
        msg = QMessageBox()
        msg.setWindowTitle(obtener_traduccion('google_connection_error_title', self.current_language))
        msg.setText(obtener_traduccion('google_connection_error_message', self.current_language))
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowIcon(QIcon(resource_path("iconos/google.png")))
        msg.exec()

    # Función para validar la clave API de Google
    def validate_google_api(self):
        if not self.google_api_key:
            return False
        try:
            headers = {
                "Content-Type": "application/json"
            }
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.google_api_key}"
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except:
            return False

    # Función para cambiar el idioma
    def change_language(self, language_code):
        self.current_language = language_code
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            config['language'] = language_code

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)

            # >>> Actualizar texto de las opciones del menú <<<
            self.es_action.setText(obtener_traduccion('language_option_es', language_code))
            self.en_action.setText(obtener_traduccion('language_option_en', language_code))
            # >>> AÑADIR texto para Francés <<<
            self.fr_action.setText(obtener_traduccion('language_option_fr', language_code))
            # >>> AÑADIR texto para Portugués <<<
            self.pt_action.setText(obtener_traduccion('language_option_pt', language_code))
            # >>> AÑADIR texto para Italiano <<<
            self.it_action.setText(obtener_traduccion('language_option_it', language_code))
            # >>> AÑADIR texto para Alemán <<<
            self.de_action.setText(obtener_traduccion('language_option_de', language_code))
            # >>> AÑADIR texto para Ruso <<<
            self.ru_action.setText(obtener_traduccion('language_option_ru', language_code))
            # >>> AÑADIR texto para Chino <<<
            self.cn_action.setText(obtener_traduccion('language_option_cn', language_code))
            # >>> AÑADIR texto para Japonés <<<
            self.jp_action.setText(obtener_traduccion('language_option_jp', language_code))
            # >>> AÑADIR texto para Coreano <<<
            self.kr_action.setText(obtener_traduccion('language_option_kr', language_code))
            # >>> AÑADIR texto para Árabe <<<
            self.ar_action.setText(obtener_traduccion('language_option_ar', language_code))
            # >>> AÑADIR texto para Filipino <<<
            self.tl_action.setText(obtener_traduccion('language_option_tl', language_code))
            # >>> Actualizar estado y etiqueta principal del menú <<<
            self.update_language_menu_state()

            self.setWindowTitle(obtener_traduccion('app_title', language_code))

            # Actualizar el widget principal
            if hasattr(self, 'widget') and self.widget and not self.widget.isHidden():
                self.widget.actualizar_traducciones(language_code)

            # Actualizar directamente la vista previa principal (para los botones y textos)
            try:
                if hasattr(self, 'widget') and self.widget and hasattr(self.widget, 'vista_previa') and self.widget.vista_previa:
                    # Actualizar la vista previa completamente con el nuevo idioma
                    self.widget.vista_previa.current_language = language_code
                    self.widget.vista_previa.actualizar_idioma(language_code)
            except Exception as e:
                print(f"Error al actualizar vista previa: {str(e)}")

            # Actualizar menús (traducciones de otras acciones)
            try:
                for action in self.findChildren(QAction):
                    if hasattr(action, 'objectName'):
                        if action.objectName() == 'get_google_api_action':
                            action.setText(obtener_traduccion('obtener_google_api', language_code))
                        elif action.objectName() == 'google_config_action':
                            action.setText(obtener_traduccion('configurar_google_api', language_code))
                        elif action.objectName() == 'google_delete_action':
                            action.setText(obtener_traduccion('borrar_google_api', language_code))
                        elif action.objectName() == 'get_replicate_api_action':
                            action.setText(obtener_traduccion('obtener_replicate_api', language_code))
                        elif action.objectName() == 'replicate_config_action':
                            action.setText(obtener_traduccion('configurar_replicate_api', language_code))
                        elif action.objectName() == 'replicate_delete_action':
                            action.setText(obtener_traduccion('borrar_replicate_api', language_code))
                        elif action.objectName() == 'get_xai_api_action':
                            action.setText(obtener_traduccion('obtener_xai_api', language_code))
                        elif action.objectName() == 'xai_config_action':
                            action.setText(obtener_traduccion('configurar_xai_api', language_code))
                        elif action.objectName() == 'xai_delete_action':
                            action.setText(obtener_traduccion('borrar_xai_api', language_code))
            except Exception as e:
                print(f"Error al actualizar menús: {str(e)}")

            # Actualizar textos del menú de apariencia directamente
            if hasattr(self, 'system_theme_action'):
                self.system_theme_action.setText(obtener_traduccion('system_theme_action_text', language_code))
            if hasattr(self, 'light_theme_action'):
                self.light_theme_action.setText(obtener_traduccion('light_theme_action_text', language_code))
            if hasattr(self, 'dark_theme_action'):
                self.dark_theme_action.setText(obtener_traduccion('dark_theme_action_text', language_code))
            if hasattr(self, 'appearance_menu_action'): # Esta es la acción que CONTIENE el menú de apariencia
                self.appearance_menu_action.setToolTip(obtener_traduccion('appearance_menu_title', language_code))
                # Si el menú en sí tiene un título que se muestra (depende de la plataforma y estilo),
                # y si self.appearance_menu es un QMenu directamente añadido a la barra, también se podría actualizar su título si es visible.
                # Sin embargo, el QAction self.appearance_menu_action es el que tiene el tooltip y el icono visible en la barra.

        except Exception as e:
            print(f"Error al guardar el idioma: {str(e)}")

    def load_language(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_language = config.get('language', 'es')
            # >>> Actualizar estado del menú después de cargar <<<
            if hasattr(self, 'language_menu_action'): # Asegurarse de que el menú existe
                 self.update_language_menu_state()
        except Exception as e:
            print(f"Error al cargar el idioma: {str(e)}")
            self.current_language = 'es'
            # >>> Actualizar estado del menú incluso en error <<<
            if hasattr(self, 'language_menu_action'):
                 self.update_language_menu_state()

    # Agregar el evento keyPressEvent para detectar la tecla Escape
    def keyPressEvent(self, event):
        # Si se presiona Escape y hay una generación en curso, preguntar si desea cancelar
        if event.key() == Qt.Key_Escape and hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            self.confirm_cancel_generation()
        else:
            # Pasar el evento a la implementación base
            super().keyPressEvent(event)

    # Método para confirmar la cancelación de la generación
    def confirm_cancel_generation(self):
        # Obtener el idioma actual
        current_language = 'es'
        if self.parent() and hasattr(self.parent(), 'current_language'):
            current_language = self.parent().current_language
        
        # Crear el cuadro de diálogo de confirmación
        msg = QMessageBox(self)
        msg.setWindowTitle(obtener_traduccion('confirm_cancellation', current_language))
        msg.setText(obtener_traduccion('cancel_generation_confirm', current_language))
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
        
        # Ajustar botones con traducciones
        msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', current_language))
        msg.button(QMessageBox.No).setText(obtener_traduccion('no', current_language))
        
        # Ajustar posición
        msg.adjustSize()
        msg_pos = self.geometry().center() - msg.rect().center()
        msg.move(msg_pos)
        
        # Mostrar el cuadro de diálogo y obtener la respuesta del usuario
        response = msg.exec()
        
        # Si el usuario confirma la cancelación, detener la generación
        if response == QMessageBox.Yes:
            # Detener el timer de inmediato para evitar animación
            if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
                self.loading_timer.stop()
                
            # Mostrar mensaje de cancelación inmediatamente
            self.log_text.append("\n" + obtener_traduccion('generation_cancelled', current_language))
            
            # Resetear la barra de progreso inmediatamente
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            
            # Habilitar la interfaz inmediatamente
            self.enable_ui_after_generation()
            
            # Detener el worker después de habilitar la interfaz
            if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
                self.worker.requestInterruption()
                # Reducir el tiempo de espera a 500ms
                if not self.worker.wait(500):
                    self.worker.terminate()
                    # No esperar más después de terminate
                self.worker = None

    # >>> AÑADIR NUEVA FUNCIÓN <<<
    def update_language_menu_state(self):
        """Actualiza el texto del botón del menú de idioma y marca la opción correcta."""
        if self.current_language == 'es':
            self.language_menu_action.setText(obtener_traduccion('language_option_es', self.current_language))
            self.es_action.setChecked(True)
        elif self.current_language == 'en': # Corregir 'else' por 'elif' y la condición
            self.language_menu_action.setText(obtener_traduccion('language_option_en', self.current_language))
            self.en_action.setChecked(True)
        elif self.current_language == 'fr': # Mantener elif para francés
            self.language_menu_action.setText(obtener_traduccion('language_option_fr', self.current_language))
            self.fr_action.setChecked(True)
        elif self.current_language == 'pt': # >>> AÑADIR caso para Portugués <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_pt', self.current_language))
            self.pt_action.setChecked(True)
        elif self.current_language == 'it': # >>> AÑADIR caso para Italiano <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_it', self.current_language))
            self.it_action.setChecked(True)
        elif self.current_language == 'de': # >>> AÑADIR caso para Alemán <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_de', self.current_language))
            self.de_action.setChecked(True)
        elif self.current_language == 'ru': # >>> AÑADIR caso para Ruso <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_ru', self.current_language))
            self.ru_action.setChecked(True)
        elif self.current_language == 'cn': # >>> AÑADIR caso para Chino <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_cn', self.current_language))
            self.cn_action.setChecked(True)
        elif self.current_language == 'jp': # >>> AÑADIR caso para Japonés <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_jp', self.current_language))
            self.jp_action.setChecked(True)
        elif self.current_language == 'kr': # >>> AÑADIR caso para Coreano <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_kr', self.current_language))
            self.kr_action.setChecked(True)
        elif self.current_language == 'ar': # >>> AÑADIR caso para Árabe <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_ar', self.current_language))
            self.ar_action.setChecked(True)
        elif self.current_language == 'tl': # >>> AÑADIR caso para Filipino <<<
            self.language_menu_action.setText(obtener_traduccion('language_option_tl', self.current_language))
            self.tl_action.setChecked(True)
        else: # Añadir un caso por defecto para volver a español si el idioma es desconocido
            self.current_language = 'es' # Asegurar que el idioma actual sea válido
            self.language_menu_action.setText(obtener_traduccion('language_option_es', self.current_language))
            self.es_action.setChecked(True)

    # --- INICIO NUEVAS FUNCIONES PARA TEMA ---
    def load_app_theme_preference(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.current_app_theme = config.get('theme_preference', 'system') # Leer 'theme_preference'
            else:
                self.current_app_theme = 'system' # Default si no hay config
        except Exception as e:
            print(f"Error al cargar la preferencia de tema: {str(e)}")
            self.current_app_theme = 'system'

    def save_app_theme_preference(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            config['theme_preference'] = self.current_app_theme # Guardar como 'theme_preference'
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar la preferencia de tema: {str(e)}")

    def cambiar_tema_apariencia(self, theme_choice): # theme_choice puede ser 'system', 'light', o 'dark'
        self.current_app_theme = theme_choice # Guardamos la elección directa del usuario
        
        theme_to_apply = theme_choice
        if theme_choice == 'system':
            color_scheme = QGuiApplication.styleHints().colorScheme()
            if color_scheme == Qt.ColorScheme.Dark:
                theme_to_apply = 'dark'
            else: # Incluye Qt.ColorScheme.Light y Qt.ColorScheme.Unknown (default a light)
                theme_to_apply = 'light'
        
        if hasattr(self, 'theme_manager') and self.theme_manager:
            self.theme_manager.gestionar_tema_aplicacion(theme_to_apply)
           
        self.save_app_theme_preference() # Guardar la elección del usuario (system, light, dark)
        if hasattr(self, 'update_theme_menu_state'):
            self.update_theme_menu_state()
        # Forzar actualización de la UI de widgets principales
        if self.widget:
            self.widget.update()
        self.update()


    def update_theme_menu_state(self):
        if not hasattr(self, 'light_theme_action') or not hasattr(self, 'dark_theme_action') or not hasattr(self, 'system_theme_action'):
            return # Menú aún no creado
            
        # self.current_app_theme guarda la elección del usuario: 'system', 'light', o 'dark'
        if self.current_app_theme == 'system':
            self.system_theme_action.setChecked(True)
        elif self.current_app_theme == 'light':
            self.light_theme_action.setChecked(True)
        elif self.current_app_theme == 'dark':
            self.dark_theme_action.setChecked(True)
    # --- FIN NUEVAS FUNCIONES PARA TEMA ---

    # --- NUEVO MÉTODO PARA MANEJAR CAMBIOS DE TEMA DEL SO EN TIEMPO REAL ---
    def _handle_system_theme_change(self, color_scheme):
        # Este slot se activa cuando el esquema de color del sistema operativo cambia.
        # Solo actuamos si la preferencia del usuario está configurada en 'system'.
        if self.current_app_theme == 'system':
            theme_to_apply = 'light' # Default a light
            if color_scheme == Qt.ColorScheme.Dark:
                theme_to_apply = 'dark'
            
            # Aplicar el tema detectado
            if hasattr(self, 'theme_manager') and self.theme_manager:
                self.theme_manager.gestionar_tema_aplicacion(theme_to_apply)
            
            # No guardamos la preferencia aquí, porque la elección del usuario sigue siendo 'system'.
            # No es necesario actualizar el menú, 'System Theme' debe permanecer marcado.
            
            # Forzar actualización de la UI de widgets principales
            if self.widget:
                self.widget.update()
            self.update()
    # --- FIN NUEVO MÉTODO ---

# Clase para la ventana de saldo total
class BalanceWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        self.current_language = 'es'
        
        if self.parent and hasattr(self.parent, 'current_language'):
            self.current_language = self.parent.current_language
            
        self.setWindowTitle(obtener_traduccion('balance_window_title', self.current_language))
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
        
        titulo = QLabel(obtener_traduccion('accumulated_costs_title', self.current_language))
        font_titulo = titulo.font()
        font_titulo.setPointSize(11)
        font_titulo.setBold(True)
        titulo.setFont(font_titulo)
        titulo.setAlignment(Qt.AlignCenter)
        layout.addWidget(titulo)
        
        config = self.load_costs()
        
        label_texto = QLabel(obtener_traduccion('text_costs', self.current_language).format(config["costos_totales"]["texto"]))
        font_normal = label_texto.font()
        font_normal.setPointSize(10)
        label_texto.setFont(font_normal)
        label_texto.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_texto)
        
        label_imagenes = QLabel(obtener_traduccion('image_costs', self.current_language).format(config["costos_totales"]["imagen"]))
        label_imagenes.setFont(font_normal)
        label_imagenes.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_imagenes)
        
        total = config["costos_totales"]["texto"] + config["costos_totales"]["imagen"]
        label_total = QLabel(obtener_traduccion('total_costs', self.current_language).format(total))
        font_total = label_total.font()
        font_total.setPointSize(11)
        font_total.setBold(True)
        label_total.setFont(font_total)
        label_total.setAlignment(Qt.AlignCenter)
        layout.addWidget(label_total)
        
        btn_xai = QPushButton(obtener_traduccion('check_xai_balance', self.current_language))
        btn_xai.setFixedWidth(120)
        btn_xai.clicked.connect(self.abrir_saldo_xai)

        if self.parent and hasattr(self.parent, 'grok_api_key') and self.parent.grok_api_key:
            btn_xai.setEnabled(True)
        else:
            btn_xai.setEnabled(False)
        
        btn_replicate = QPushButton(obtener_traduccion('check_replicate_balance', self.current_language))
        btn_replicate.setFixedWidth(120)
        btn_replicate.clicked.connect(self.abrir_saldo_replicate)

        if self.parent and hasattr(self.parent, 'api_key') and self.parent.api_key:
            btn_replicate.setEnabled(True)
        else:
            btn_replicate.setEnabled(False)
        
        btn_reset = QPushButton(obtener_traduccion('reset_costs', self.current_language))
        btn_reset.setFixedWidth(120)
        btn_reset.clicked.connect(self.confirmar_reinicio_costes)
        
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_replicate)
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_xai)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    # Función para confirmar el reinicio de los costos
    def confirmar_reinicio_costes(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(obtener_traduccion('confirm_reset_title', self.current_language))
        msg.setText(obtener_traduccion('confirm_reset_message', self.current_language))
        msg.setIcon(QMessageBox.Question)
        msg.setWindowIcon(QIcon(resource_path("iconos/coin.png")))
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', self.current_language))
        msg.button(QMessageBox.No).setText(obtener_traduccion('no', self.current_language))
        
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

# Clase para la ventana principal de la aplicación
class PowerpoineatorWidget(QWidget):
    # --- MODIFICADO: Aceptar idioma inicial ---
    def __init__(self, initial_language='es'):
    # ----------------------------------------
        super().__init__()
        # Señales para la lógica de generación de presentación
        self.signals = None
        self.worker = None
        self.vista_previa = None
        self.total_images = 0
        self.current_image = 0
        self.generation_completed = False
        # --- MODIFICADO: Usar idioma inicial ---
        # Establecer el idioma por defecto
        self.current_language = initial_language
        # Ya no es necesario buscar en el padre aquí
        # if self.parent() and hasattr(self.parent(), 'current_language'):
        #     self.current_language = self.parent().current_language
        # -------------------------------------
        
        # Obtener fuentes del sistema
        # font_db = QFontDatabase()
        self.system_fonts = QFontDatabase.families() # Usar método estático
        if not self.system_fonts: # Fallback por si no se encuentran fuentes
            self.system_fonts = ["Arial", "Calibri", "Times New Roman"] 

        # Eliminar la lista hardcodeada y el default font
        # self.available_fonts = ["Arial", "Calibri", "Times New Roman", "Verdana", "Tahoma", "Georgia", "Comic Sans MS"]
        # self.selected_font = "Calibri" 

        self.selected_layout_index = 1 # <--- AÑADIR Inicializar índice de estilo seleccionado

        self.setup_ui()
        self.load_log_visibility_state()
        self.imagen_personalizada = None
        self.pdf_cargado = None
        self.populate_fields()
        self.load_description()
        self.load_auto_open_state()
        self.load_num_diapositivas()
        self.load_pdf_path()
        self.load_font_selection() # Cargar fuente guardada después de setup_ui
        self.load_content_font_selection()
        self.load_font_sizes()
        self.load_format_settings()
        self.load_selected_style() # Importante: cargar índice de estilo antes de actualizar la etiqueta
        self.update_style_label() # Actualizar la etiqueta con el estilo seleccionado
        # --- MODIFICADO: Eliminar esta línea, ya se estableció con initial_language ---
        # self.current_language = 'es'
        # ----------------------------------------------------------------------------
        self.generated_pptx_path = None # Ruta del último PPTX generado

    def actualizar_traducciones(self, idioma):
        try:
            self.current_language = idioma
            
            # Actualizar textos principales
            self.auto_open_checkbox.setText(obtener_traduccion('auto_open', idioma))
            self.diapositivas_label.setText(obtener_traduccion('num_diapositivas', idioma))
            self.descripcion_label.setText(obtener_traduccion('descripcion_presentacion', idioma))
            self.texto_label.setText(obtener_traduccion('texto_modelo', idioma))
            self.imagen_label.setText(obtener_traduccion('imagen_modelo', idioma))
            # self.font_label.setText(obtener_traduccion('font_label', idioma)) # Traducir etiqueta de fuente
            self.title_font_label.setText(obtener_traduccion('title_font_label', idioma)) # <-- Cambiar etiqueta título
            self.content_font_label.setText(obtener_traduccion('content_font_label', idioma)) # <-- Añadir etiqueta contenido
            self.title_font_size_label.setText(obtener_traduccion('title_font_size_label', idioma)) # Traducir etiqueta tamaño título
            self.content_font_size_label.setText(obtener_traduccion('content_font_size_label', idioma)) # Traducir etiqueta tamaño contenido
            
            # Actualizar checkboxes de formato
            self.title_bold_checkbox.setText(obtener_traduccion('title_bold', idioma))
            self.title_italic_checkbox.setText(obtener_traduccion('title_italic', idioma))
            self.title_underline_checkbox.setText(obtener_traduccion('title_underline', idioma))
            # >>> Añadir actualizaciones para los checkboxes de contenido <<<
            self.content_bold_checkbox.setText(obtener_traduccion('content_bold', idioma))
            self.content_italic_checkbox.setText(obtener_traduccion('content_italic', idioma))
            self.content_underline_checkbox.setText(obtener_traduccion('content_underline', idioma))
            
            # Actualizar botones de documentos
            self.cargar_pdf_btn.setText(obtener_traduccion('cargar_pdf', idioma))
            
            # Actualizar mensajes de estado del PDF
            if self.pdf_cargado and os.path.exists(self.pdf_cargado):
                self.pdf_label.setText(obtener_traduccion('pdf_cargado', idioma).format(os.path.basename(self.pdf_cargado)))
            
            # Actualizar el texto del botón de cargar PDF
            self.cargar_pdf_btn.setText(obtener_traduccion('cargar_pdf', idioma))
            if hasattr(self, 'eliminar_pdf_btn') and self.eliminar_pdf_btn.isVisible():
                self.eliminar_pdf_btn.setText(obtener_traduccion('eliminar_pdf', idioma))
            # >>> Añadir la traducción para el botón revisar_pdf_btn <<<
            if hasattr(self, 'revisar_pdf_btn') and self.revisar_pdf_btn.isVisible():
                self.revisar_pdf_btn.setText(obtener_traduccion('revisar_pdf', idioma))
            
            # Actualizar el texto del label de PDF cargado
            if self.pdf_cargado and os.path.exists(self.pdf_cargado):
                self.pdf_label.setText(obtener_traduccion('pdf_cargado', idioma).format(os.path.basename(self.pdf_cargado)))
            
            # Actualizar el texto del botón de ocultar/mostrar log
            if hasattr(self, 'log_toggle_btn'):
                if self.log_text.isVisible():
                    self.log_toggle_btn.setText(obtener_traduccion('ocultar_log', idioma))
                else:
                    self.log_toggle_btn.setText(obtener_traduccion('mostrar_log', idioma))
            
            # Actualizar los tooltips y texto del botón para cargar y ver imágenes
            if hasattr(self, 'cargar_imagen_btn'):
                self.cargar_imagen_btn.setToolTip(obtener_traduccion('cargar_imagen_personalizada_tooltip', idioma))
            if hasattr(self, 'ver_imagen_btn'):
                self.ver_imagen_btn.setToolTip(obtener_traduccion('ver_imagen_personalizada_tooltip', idioma))
                self.ver_imagen_btn.setText(obtener_traduccion('revisar_pdf', idioma))
                    
            # Actualizar el texto del botón de generar si está en modo cancelar
            if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
                self.generar_btn.setText(obtener_traduccion('cancel_generation', idioma))
            if not self.descripcion_text.isEnabled():
                self.descripcion_text.setPlaceholderText(obtener_traduccion('description_text', idioma))
            self.actualizar_contador()
            
            # Actualizar la vista previa si existe
            if hasattr(self, 'vista_previa') and self.vista_previa:
                try:
                    # Establecer el idioma y actualizar completamente
                    self.vista_previa.current_language = idioma
                    self.vista_previa.actualizar_idioma(idioma)
                except Exception as e:
                    print(f"Error al actualizar vista previa: {str(e)}")
            
            # Auto open checkbox
            self.auto_open_checkbox.setText(obtener_traduccion('auto_open', idioma))

            # >>> AÑADIR ACTUALIZACIÓN PARA BOTÓN ESTILO <<<
            self.select_style_btn.setText(obtener_traduccion('select_style', idioma))
            self.select_style_btn.setToolTip(obtener_traduccion('select_style_tooltip', idioma))
            
            # >>> ACTUALIZAR LA ETIQUETA DEL ESTILO SELECCIONADO <<<
            self.update_style_label()
            
        except Exception as e:
            print(f"Error general al actualizar traducciones: {str(e)}")

    # Función para configurar la interfaz de usuario
    def setup_ui(self):
        current_language = 'es'
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    current_language = config.get('language', 'es')
        except Exception as e:
            print(f"Error al cargar el idioma: {str(e)}")

        # Layout principal dividido en izquierda y derecha
        main_layout = QHBoxLayout()
        
        # Panel izquierdo (elementos originales)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        model_layout = QHBoxLayout()

        # Verificar si estamos en macOS para ajustar el layout
        is_macos = sys.platform == 'darwin'

        if is_macos:
            # Para macOS, usar un layout de grid para alinear mejor las etiquetas y comboboxes
            model_grid = QGridLayout()
            
            # Primera columna: Modelo de texto
            self.texto_label = QLabel(obtener_traduccion('texto_modelo', current_language))
            model_grid.addWidget(self.texto_label, 0, 0)
            
            self.texto_combo = QComboBox()
            self.texto_combo.currentTextChanged.connect(self.on_texto_combo_changed)
            model_grid.addWidget(self.texto_combo, 1, 0)
            
            # Segunda columna: Modelo de imagen
            self.imagen_label = QLabel(obtener_traduccion('imagen_modelo', current_language))
            model_grid.addWidget(self.imagen_label, 0, 1)
            
            # Crear el combobox de imagen directamente sin layout adicional
            self.imagen_combo = QComboBox()
            self.imagen_combo.currentTextChanged.connect(self.on_imagen_combo_changed)
            model_grid.addWidget(self.imagen_combo, 1, 1)
            
            # Crear un layout separado solo para los botones
            botones_layout = QHBoxLayout()
            botones_layout.setContentsMargins(0, 0, 0, 0)
            botones_layout.setSpacing(5)  # Aumentar espacio entre botones
            
            self.cargar_imagen_btn = QPushButton('+')
            self.cargar_imagen_btn.setToolTip(obtener_traduccion('cargar_imagen_personalizada_tooltip', current_language))
            self.cargar_imagen_btn.setFixedSize(30, 24)  # Aumentar tamaño del botón +
            self.cargar_imagen_btn.clicked.connect(self.cargar_imagen_personalizada)
            self.cargar_imagen_btn.hide()
            
            self.ver_imagen_btn = QPushButton(obtener_traduccion('revisar_pdf', current_language))
            self.ver_imagen_btn.setToolTip(obtener_traduccion('ver_imagen_personalizada_tooltip', current_language))
            self.ver_imagen_btn.setFixedSize(70, 24)  # Aumentar ancho para que quepa todo el texto
            self.ver_imagen_btn.clicked.connect(self.ver_imagen_personalizada)
            self.ver_imagen_btn.hide()
            
            # Añadir los botones en una tercera columna SIN verificar visibilidad
            botones_layout.addWidget(self.cargar_imagen_btn)
            botones_layout.addWidget(self.ver_imagen_btn)
            botones_container = QWidget()
            botones_container.setLayout(botones_layout)
            model_grid.addWidget(botones_container, 1, 2)
            
            # Establecer las columnas para que tengan el mismo ancho
            model_grid.setColumnStretch(0, 1)
            model_grid.setColumnStretch(1, 1)
            model_grid.setColumnStretch(2, 0)
            
            # Añadir el grid al layout principal
            left_layout.addLayout(model_grid)
        else:
            # Código original para otras plataformas
            texto_layout = QVBoxLayout()
            self.texto_combo = QComboBox()
            self.texto_combo.currentTextChanged.connect(self.on_texto_combo_changed)
            self.texto_label = QLabel(obtener_traduccion('texto_modelo', current_language))
            texto_layout.addWidget(self.texto_label)
            texto_layout.addWidget(self.texto_combo)
            model_layout.addLayout(texto_layout)

            imagen_layout = QVBoxLayout()
            imagen_combo_layout = QHBoxLayout()
            self.imagen_combo = QComboBox()
            self.imagen_combo.currentTextChanged.connect(self.on_imagen_combo_changed)
            self.imagen_label = QLabel(obtener_traduccion('imagen_modelo', current_language))
            imagen_layout.addWidget(self.imagen_label)
            imagen_combo_layout.addWidget(self.imagen_combo)
            
            self.cargar_imagen_btn = QPushButton('+')
            self.cargar_imagen_btn.setToolTip(obtener_traduccion('cargar_imagen_personalizada_tooltip', current_language))
            self.cargar_imagen_btn.setFixedSize(30, 24)  # Aumentar tamaño del botón +
            self.cargar_imagen_btn.clicked.connect(self.cargar_imagen_personalizada)
            self.cargar_imagen_btn.hide()
            imagen_combo_layout.addWidget(self.cargar_imagen_btn)

            self.ver_imagen_btn = QPushButton(obtener_traduccion('revisar_pdf', current_language))
            self.ver_imagen_btn.setToolTip(obtener_traduccion('ver_imagen_personalizada_tooltip', current_language))
            self.ver_imagen_btn.setFixedSize(70, 24)  # Aumentar ancho para que quepa todo el texto
            self.ver_imagen_btn.clicked.connect(self.ver_imagen_personalizada)
            self.ver_imagen_btn.hide()
            imagen_combo_layout.addWidget(self.ver_imagen_btn)
            
            imagen_layout.addLayout(imagen_combo_layout)
            model_layout.addLayout(imagen_layout)

            left_layout.addLayout(model_layout)
        
        # Crear layout para descripción y contador
        descripcion_y_contador_layout = QHBoxLayout()
        self.descripcion_label = QLabel(obtener_traduccion('descripcion_presentacion', current_language))
        descripcion_y_contador_layout.addWidget(self.descripcion_label)
        descripcion_y_contador_layout.addStretch(1) # Empujar contador a la derecha
        self.contador_label = QLabel(obtener_traduccion('contador_label', current_language)) # Crear contador aquí
        self.contador_label.setStyleSheet("color: gray;") # Aplicar estilo aquí
        descripcion_y_contador_layout.addWidget(self.contador_label)

        # Añadir el layout combinado
        left_layout.addLayout(descripcion_y_contador_layout)

        self.descripcion_text = QTextEdit()
        font = self.descripcion_text.font()
        font.setPointSize(15)
        self.descripcion_text.setFont(font)
        self.descripcion_text.textChanged.connect(self.on_text_changed)
        self.descripcion_text.textChanged.connect(self.actualizar_contador)
        left_layout.addWidget(self.descripcion_text)
        
        # Nuevo layout para fuentes (Título y Contenido)
        fonts_layout = QHBoxLayout()

        # Fuente Título
        title_font_layout = QVBoxLayout()
        self.title_font_label = QLabel(obtener_traduccion('title_font_label', current_language))
        self.font_combo = QComboBox() # Mantenemos el nombre font_combo para el título
        for font_name in self.system_fonts:
            self.font_combo.addItem(font_name)
            index = self.font_combo.count() - 1
            font = QFont(font_name, 10)
            self.font_combo.setItemData(index, font, Qt.FontRole)
        self.font_combo.currentTextChanged.connect(self.save_font_selection) # Guardar fuente TÍTULO
        self.font_combo.currentTextChanged.connect(lambda text: self.update_font_combo_style(self.font_combo, text)) # Actualizar estilo
        title_font_layout.addWidget(self.title_font_label)
        title_font_layout.addWidget(self.font_combo)

        # Tamaño Título (Movido aquí)
        self.title_font_size_label = QLabel(obtener_traduccion('title_font_size_label', current_language))
        self.title_font_size_spin = QSpinBox()
        self.title_font_size_spin.setRange(1, 30)
        self.title_font_size_spin.setValue(20) # Default title size
        self.title_font_size_spin.valueChanged.connect(self.save_font_sizes)
        title_font_layout.addWidget(self.title_font_size_label)
        title_font_layout.addWidget(self.title_font_size_spin)

        # Checkboxes para formateo de título
        self.title_format_layout = QHBoxLayout()
        self.title_bold_checkbox = QCheckBox(obtener_traduccion('title_bold', current_language))
        self.title_italic_checkbox = QCheckBox(obtener_traduccion('title_italic', current_language))
        self.title_underline_checkbox = QCheckBox(obtener_traduccion('title_underline', current_language))
        
        self.title_bold_checkbox.stateChanged.connect(self.save_format_settings)
        self.title_italic_checkbox.stateChanged.connect(self.save_format_settings)
        self.title_underline_checkbox.stateChanged.connect(self.save_format_settings)
        
        self.title_format_layout.addWidget(self.title_bold_checkbox)
        self.title_format_layout.addStretch(1) # Añadir espacio flexible entre Negrita y Cursiva
        self.title_format_layout.addWidget(self.title_italic_checkbox)
        self.title_format_layout.addStretch(1) # Añadir espacio flexible entre Cursiva y Subrayado
        self.title_format_layout.addWidget(self.title_underline_checkbox)
        
        title_font_layout.addLayout(self.title_format_layout)

        fonts_layout.addLayout(title_font_layout, 1) # Añadir factor de estiramiento 1

        # Fuente Contenido
        content_font_layout = QVBoxLayout()
        self.content_font_label = QLabel(obtener_traduccion('content_font_label', current_language))
        self.content_font_combo = QComboBox()
        for font_name in self.system_fonts:
            self.content_font_combo.addItem(font_name)
            index = self.content_font_combo.count() - 1
            font = QFont(font_name, 10)
            self.content_font_combo.setItemData(index, font, Qt.FontRole)
        self.content_font_combo.currentTextChanged.connect(self.save_content_font_selection) # Guardar fuente CONTENIDO
        self.content_font_combo.currentTextChanged.connect(lambda text: self.update_font_combo_style(self.content_font_combo, text)) # Actualizar estilo
        content_font_layout.addWidget(self.content_font_label)
        content_font_layout.addWidget(self.content_font_combo)

        # Tamaño Contenido (Movido aquí)
        self.content_font_size_label = QLabel(obtener_traduccion('content_font_size_label', current_language))
        self.content_font_size_spin = QSpinBox()
        self.content_font_size_spin.setRange(1, 20)
        self.content_font_size_spin.setValue(15) # Default content size
        self.content_font_size_spin.valueChanged.connect(self.save_font_sizes)
        content_font_layout.addWidget(self.content_font_size_label)
        content_font_layout.addWidget(self.content_font_size_spin)

        # Checkboxes para formateo de contenido
        self.content_format_layout = QHBoxLayout()
        self.content_bold_checkbox = QCheckBox(obtener_traduccion('content_bold', current_language))
        self.content_italic_checkbox = QCheckBox(obtener_traduccion('content_italic', current_language))
        self.content_underline_checkbox = QCheckBox(obtener_traduccion('content_underline', current_language))

        self.content_bold_checkbox.stateChanged.connect(self.save_format_settings)
        self.content_italic_checkbox.stateChanged.connect(self.save_format_settings)
        self.content_underline_checkbox.stateChanged.connect(self.save_format_settings)

        self.content_format_layout.addWidget(self.content_bold_checkbox)
        self.content_format_layout.addStretch(1)
        self.content_format_layout.addWidget(self.content_italic_checkbox)
        self.content_format_layout.addStretch(1)
        self.content_format_layout.addWidget(self.content_underline_checkbox)

        content_font_layout.addLayout(self.content_format_layout) # Añadir layout de formato de contenido

        fonts_layout.addLayout(content_font_layout, 1) # Añadir factor de estiramiento 1

        left_layout.addLayout(fonts_layout) # Añadir el layout general de fuentes
        
        # Layout para los botones de PDF
        pdf_layout = QHBoxLayout()
        # Crear un contenedor central para los botones de PDF y alinearlo al centro
        pdf_buttons_layout = QHBoxLayout()
        pdf_buttons_layout.setContentsMargins(0, 0, 0, 0)
        pdf_buttons_layout.setSpacing(5)
        
        self.cargar_pdf_btn = QPushButton(obtener_traduccion('cargar_pdf', current_language))
        pdf_buttons_layout.addWidget(self.cargar_pdf_btn)
        self.cargar_pdf_btn.clicked.connect(self.cargar_pdf)
        
        self.pdf_label = QLabel("")
        self.pdf_label.setStyleSheet("color: gray;")
        self.pdf_label.hide()
        pdf_buttons_layout.addWidget(self.pdf_label)
        
        # Nuevo botón para revisar documento
        self.revisar_pdf_btn = QPushButton(obtener_traduccion('revisar_pdf', current_language))
        self.revisar_pdf_btn.setFixedWidth(100)
        self.revisar_pdf_btn.clicked.connect(self.revisar_pdf)
        self.revisar_pdf_btn.hide()
        pdf_buttons_layout.addWidget(self.revisar_pdf_btn)
        
        self.eliminar_pdf_btn = QPushButton(obtener_traduccion('eliminar_pdf', current_language))
        self.eliminar_pdf_btn.setFixedWidth(100)
        self.eliminar_pdf_btn.clicked.connect(self.eliminar_pdf)
        self.eliminar_pdf_btn.hide()
        pdf_buttons_layout.addWidget(self.eliminar_pdf_btn)
        
        # Añadir espaciado flexible izquierdo y derecho para centrar el layout de botones
        pdf_layout.addStretch(1)
        pdf_layout.addLayout(pdf_buttons_layout)
        pdf_layout.addStretch(1)
        
        left_layout.addLayout(pdf_layout)

        # Reorganizar el contador_checkbox_layout con tres secciones equilibradas
        self.contador_checkbox_layout = QHBoxLayout()
        
        # Sección izquierda - Checkbox auto abrir
        left_section = QHBoxLayout()
        self.auto_open_checkbox = QCheckBox(obtener_traduccion('auto_open', current_language))
        self.auto_open_checkbox.setChecked(False)
        self.auto_open_checkbox.stateChanged.connect(self.save_auto_open_state)
        left_section.addWidget(self.auto_open_checkbox)
        left_section.addStretch(1)
        
        # Sección central - Botón y etiqueta de estilos
        center_section = QHBoxLayout()
        center_section.setAlignment(Qt.AlignCenter)
        self.select_style_btn = QPushButton(obtener_traduccion('select_style', current_language))
        self.select_style_btn.setToolTip(obtener_traduccion('select_style_tooltip', current_language))
        self.select_style_btn.clicked.connect(self.select_slide_style)
        center_section.addWidget(self.select_style_btn)
        
        self.current_style_label = QLabel("")
        self.current_style_label.setStyleSheet("color: gray;")
        center_section.addWidget(self.current_style_label)
        
        # Sección derecha - Controles de diapositivas
        right_section = QHBoxLayout()
        right_section.addStretch(1)  # Añadir stretch al inicio empuja los widgets a la derecha
        self.diapositivas_label = QLabel(obtener_traduccion('num_diapositivas', current_language))
        right_section.addWidget(self.diapositivas_label)
        
        self.num_diapositivas_spin = QSpinBox()
        self.num_diapositivas_spin.setRange(3, 30)
        self.num_diapositivas_spin.setValue(8)
        self.num_diapositivas_spin.valueChanged.connect(self.save_num_diapositivas)
        self.num_diapositivas_spin.setReadOnly(False)
        self.num_diapositivas_spin.setButtonSymbols(QSpinBox.UpDownArrows)
        self.num_diapositivas_spin.setKeyboardTracking(False)
        right_section.addWidget(self.num_diapositivas_spin)
        # Eliminar el stretch final que empuja los widgets a la izquierda

        # Añadir las tres secciones al layout principal con proporciones iguales
        self.contador_checkbox_layout.addLayout(left_section, 1)
        self.contador_checkbox_layout.addLayout(center_section, 1)
        self.contador_checkbox_layout.addLayout(right_section, 1)
        
        left_layout.addLayout(self.contador_checkbox_layout)

        self.generar_btn = QPushButton('POWERPOINEAR')
        self.generar_btn.setMinimumWidth(200)
        self.generar_btn.setFixedHeight(40)

        font = self.generar_btn.font()
        font.setPointSize(13)
        font.setBold(True)
        self.generar_btn.setFont(font)

        self.generar_btn.clicked.connect(self.generar_presentacion_event)
        left_layout.addWidget(self.generar_btn)
        
        # Panel derecho (elementos de progreso)
        right_panel = QWidget()
        right_panel.setVisible(True)  # Siempre visible
        self.right_panel = right_panel
        right_layout = QVBoxLayout(right_panel)
        
        # Crear la vista previa como el primer elemento del panel derecho
        try:
            from Vista_previa import VentanaVistaPrevia
            # --- MODIFICACIÓN: Pasar parámetros de formato al crear VentanaVistaPrevia ---
            self.vista_previa = VentanaVistaPrevia(
                parent=self,
                title_font_name=self.font_combo.currentText(), # CORREGIDO
                content_font_name=self.content_font_combo.currentText(), # CORREGIDO
                title_font_size=self.title_font_size_spin.value(),
                content_font_size=self.content_font_size_spin.value(),
                title_bold=self.title_bold_checkbox.isChecked(),
                title_italic=self.title_italic_checkbox.isChecked(),
                title_underline=self.title_underline_checkbox.isChecked(),
                content_bold=self.content_bold_checkbox.isChecked(),
                content_italic=self.content_italic_checkbox.isChecked(),
                content_underline=self.content_underline_checkbox.isChecked()
            )
            # -------------------------------------------------------------------------
            self.vista_previa.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            # Añadir al layout derecho con un factor de estiramiento mayor
            right_layout.addWidget(self.vista_previa, 3) # Darle más peso vertical
        except ImportError:
            print("Error al importar VentanaVistaPrevia")
            self.vista_previa = QLabel("Error al cargar la vista previa.")
            right_layout.addWidget(self.vista_previa)
        
        # Contenedor para centrar el botón
        log_btn_container = QHBoxLayout()
        log_btn_container.setAlignment(Qt.AlignCenter)
        
        # Botón para ocultar/mostrar el log
        self.log_toggle_btn = QPushButton(obtener_traduccion('mostrar_log', current_language))
        self.log_toggle_btn.setFixedHeight(20)
        # Eliminar el ancho fijo y añadir un padding horizontal adecuado
        self.log_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF8C32;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 10px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #FFA559;
            }
            QPushButton:pressed {
                background-color: #E56200;
            }
        """)
        self.log_toggle_btn.clicked.connect(self.toggle_log_visibility)
        
        # Añadir el botón al contenedor centrado
        log_btn_container.addWidget(self.log_toggle_btn)
        
        # Añadir el contenedor al layout principal
        right_layout.addLayout(log_btn_container)
        
        # Log de texto (ahora segundo)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)  # Limitar altura
        right_layout.addWidget(self.log_text, 1)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        right_layout.addWidget(self.progress_bar)
        
        # Configurar anchos de los paneles
        left_panel.setMinimumWidth(400)
        right_panel.setMinimumWidth(600)
        
        # Añadir ambos paneles al layout principal
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)
        
        # Configurar layout principal
        self.setLayout(main_layout)
        
        # Configuración para animación de carga
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self.update_loading_animation)

        # Asegurarse que la instancia de VentanaVistaPrevia se guarda
        # self.preview_window = VentanaVistaPrevia(self.parent()) # O self si no tiene padre específico <---- Eliminada esta línea

        # Mostrar advertencia si python-pptx no está disponible
        if not PPTX_AVAILABLE:
            # Usar QTimer para mostrar el mensaje después de que la ventana principal sea visible
            QTimer.singleShot(100, lambda: QMessageBox.warning(self, 
                                                        "Advertencia", 
                                                        "La biblioteca 'python-pptx' no está instalada.\\nLa función de editar diapositivas directamente en el archivo PPTX estará deshabilitada.\\nInstálala con: pip install python-pptx"))

    # Función para poblar los campos de selección de modelos
    def populate_fields(self):

        self.texto_combo.blockSignals(True)
        self.imagen_combo.blockSignals(True)
        
        self.texto_combo.clear()
        self.imagen_combo.clear()

        if hasattr(self.parent(), 'google_api_key') and self.parent().google_api_key and self.parent().validate_google_api():
            self.texto_combo.addItem(QIcon(resource_path("iconos/gemini.png")), 'gemini-2.5-flash-preview-05-20')
            self.texto_combo.addItem(QIcon(resource_path("iconos/gemini.png")), 'gemini-2.0-flash')
            self.texto_combo.addItem(QIcon(resource_path("iconos/gemini.png")), 'gemini-2.0-flash-thinking-exp-01-21')
            
            self.imagen_combo.addItem(QIcon(resource_path("iconos/gemini.png")), 'gemini-2.0-flash-preview-image-generation')
            
            if not (hasattr(self.parent(), 'api_key') and self.parent().api_key) and not (hasattr(self.parent(), 'grok_api_key') and self.parent().grok_api_key):
                self.imagen_combo.setEnabled(True)
                self.imagen_combo.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        if hasattr(self.parent(), 'api_key') and self.parent().api_key:
            self.texto_combo.addItem(QIcon(resource_path("iconos/openai.png")), 'gpt-4.1 [$0.0056]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/openai.png")), 'gpt-4.1-nano [$0.00028]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/openai.png")), 'o4-mini [$0.0028]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/openai.png")), 'gpt-4o [$0.00112]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/openai.png")), 'gpt-4o-mini [$0.00042]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/deepseek.png")), 'deepseek-r1 [$0.007]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/claude.png")), 'claude-4-sonnet [$0.0105]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/claude.png")), 'claude-3.7-sonnet [$0.0105]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/claude.png")), 'claude-3.5-sonnet [$0.01312]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/claude.png")), 'claude-3.5-haiku [$0.0035]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/meta.png")), 'meta-llama-4-scout-instruct [$0.00046]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/meta.png")), 'meta-llama-4-maverick-instruct [$0.00067]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/meta.png")), 'meta-llama-3.1-405b-instruct [$0.0067]')
            self.texto_combo.addItem(QIcon(resource_path("iconos/dolphin.png")), 'dolphin-2.9-llama3-70b-gguf [$0.050]')
            
            self.imagen_combo.setEnabled(True)
            self.imagen_combo.setAttribute(Qt.WA_TransparentForMouseEvents, False)
            self.imagen_combo.addItem(QIcon(resource_path("iconos/openai.png")), 'dall-e-3 [$0.12]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/openai.png")), 'dall-e-2 [$0.02]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/fluxschnell.png")), 'flux-schnell [$0.003]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/google.png")), 'imagen-4 [$0.05]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/google.png")), 'imagen-3 [$0.05]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/google.png")), 'imagen-3-fast [$0.025]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/nvidia.png")), 'sana [$0.0067]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/nvidia.png")), 'sana-sprint-1.6b [$0.0015]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/photomaker.png")), 'photomaker [$0.0070]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'flux-pulid [$0.032]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'hyper-flux-8step [$0.045]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'hyper-flux-16step [$0.047]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/bytedance.png")), 'sdxl-lightning-4step [$0.0037]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/lightweight.png")), 'model3_4 [$0.00098]')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/dgmtnzflux.png")), 'dgmtnzflux [$0.03]')
        
        if hasattr(self.parent(), 'grok_api_key') and self.parent().grok_api_key and self.parent().validate_grok_api():
            self.texto_combo.addItem(QIcon(resource_path("iconos/grok.jpg")), 'grok-3')
            self.texto_combo.addItem(QIcon(resource_path("iconos/grok.jpg")), 'grok-3-mini')
            self.texto_combo.addItem(QIcon(resource_path("iconos/grok.jpg")), 'grok-3-mini-fast')
            self.texto_combo.addItem(QIcon(resource_path("iconos/grok.jpg")), 'grok-2-1212')
            self.imagen_combo.addItem(QIcon(resource_path("iconos/grok.jpg")), 'grok-2-image-1212')
            if not (hasattr(self.parent(), 'api_key') and self.parent().api_key):
                self.imagen_combo.setEnabled(True)
                self.imagen_combo.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        
        self.load_combo_selection()
        self.load_font_selection()
        self.load_content_font_selection()
        self.load_font_sizes()
        self.load_description()
        self.load_auto_open_state()
        self.load_num_diapositivas()
        self.load_format_settings()
        self.load_selected_style() 
        self.update_style_label()
        self.actualizar_contador()
        
        self.texto_combo.setMaxVisibleItems(self.texto_combo.count())
        self.imagen_combo.setMaxVisibleItems(self.imagen_combo.count())
        
        self.texto_combo.blockSignals(False)
        self.imagen_combo.blockSignals(False)

    # Método para ocultar/mostrar el log
    def toggle_log_visibility(self):
        if self.log_text.isVisible():
            self.log_text.setVisible(False)
            self.log_toggle_btn.setText(obtener_traduccion('mostrar_log', self.current_language))
        else:
            self.log_text.setVisible(True)
            self.log_toggle_btn.setText(obtener_traduccion('ocultar_log', self.current_language))
        
        # Guardar el estado actual de visibilidad
        self.save_log_visibility_state()
    
    def save_log_visibility_state(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['log_visible'] = self.log_text.isVisible()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar el estado de visibilidad del log: {str(e)}")
    
    def load_log_visibility_state(self):
        try:
            log_visible = False
            config_language = 'es'
            
            # 1. Leer archivo de configuración
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    log_visible = config.get('log_visible', False)
                    config_language = config.get('language', 'es')  # Idioma del archivo
            
            # 2. Aplicar visibilidad ANTES de cualquier otra configuración
            self.log_text.setVisible(log_visible)
            
            # 3. Traducir el botón con el idioma del archivo
            texto_boton = obtener_traduccion('ocultar_log' if log_visible else 'mostrar_log', config_language)
            self.log_toggle_btn.setText(texto_boton)
            
            # 4. Sincronizar el idioma del widget (sin afectar otras partes)
            self.current_language = config_language
            
        except Exception as e:
            self.log_text.setVisible(False)
            self.log_toggle_btn.setText(obtener_traduccion('mostrar_log', 'es'))
            print(f"Error al cargar el estado de visibilidad del log: {str(e)}")

    # Añadir funciones de Ventana_progreso.py
    def update_loading_animation(self):
        # Verificar que la barra de progreso existe y está configurada correctamente
        if hasattr(self, 'progress_bar') and self.progress_bar and self.progress_bar.maximum() == 0:
            self.progress_bar.setValue(0)
            
    def update_log(self, text):
        # --- MODIFICACIÓN: Usar insertPlainText ---
        # Mover cursor al final antes de insertar
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_text.setTextCursor(cursor)
        # Insertar el texto como plano, añadiendo un salto de línea
        self.log_text.insertPlainText(text + "\n")
        # -----------------------------------------
        # Asegurar que la barra de scroll baja (esto ya estaba y es correcto)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

        # Detectar cuando comienza la generación de imágenes y obtener el total
        current_language = self.current_language # Usar el idioma actual del widget

        # Obtener la traducción del mensaje clave en el idioma actual
        generando_key = 'generando_imagen'
        generando_base_text = obtener_traduccion(generando_key, current_language)
        # Formatear para eliminar placeholders y espacios
        generando_check_text = generando_base_text.format(numero=1, total='').strip()

        # Comprobar si el texto formateado está en el log recibido
        # Asegurarse que generango_check_text no está vacío antes de la comprobación
        if generando_check_text and generando_check_text in text:
            self.loading_timer.stop()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            # Extraer el número total de imágenes
            try:
                # Intenta extraer el total asumiendo el formato "... X/Y ..."
                parts = text.split('/')
                if len(parts) > 1:
                    # Intentar obtener el número después de la barra, limpiando espacios/caracteres no numéricos
                    total_str_part = parts[-1].strip().split()[0]
                    # Filtrar solo dígitos
                    total_str = ''.join(filter(str.isdigit, total_str_part))
                    if total_str: # Asegurarse que hay dígitos
                        self.total_images = int(total_str)
                    else: # Si no se encontraron dígitos después de la limpieza
                        print(f"Advertencia: No se pudieron extraer dígitos del total de imágenes de: {parts[-1]}")
                        self.total_images = 1 # Fallback
                else: # Si no hay '/', asumir 1 imagen (fallback)
                     self.total_images = 1
            except ValueError:
                print(f"Advertencia: No se pudo convertir a entero el número total de imágenes del texto: {text}")
                self.total_images = 1 # Fallback si la conversión falla
            except Exception as e:
                 print(f"Error inesperado extrayendo total de imágenes: {e}")
                 self.total_images = 1 # Fallback general
        
    def update_progress(self, current, total):
        # Detener la animación de carga inicial
        if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
            self.loading_timer.stop()
        self.progress_bar.setRange(0, 100)
        
        # Continuar con la animación normal de progreso
        target_percentage = int((current / total) * 100)
        current_percentage = self.progress_bar.value()
        
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(500)
        self.progress_animation.setStartValue(current_percentage)
        self.progress_animation.setEndValue(target_percentage)
        self.progress_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.progress_animation.start()
        
    def agregar_diapositiva(self, imagen_path, titulo, contenido):
        if self.vista_previa:
            self.vista_previa.agregar_diapositiva(imagen_path, titulo, contenido)
            
    def on_generation_finished(self):
        try:
            # Asegurarse de que el timer se detiene
            if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
                self.loading_timer.stop()
            
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)
            
            current_language = 'es'
            if self.parent() and hasattr(self.parent(), 'current_language'):
                current_language = self.parent().current_language
                
            self.log_text.append("\n" + obtener_traduccion('generation_successful', current_language))
            self.generation_completed = True
            
            # Guardamos los datos del worker antes de limpiarlo
            filename = None
            auto_open = False
            if self.worker:
                filename = self.worker.filename # <- Esta es la ruta del archivo generado
                auto_open = self.worker.auto_open
                
                # Limpieza del worker de manera segura
                if self.worker.isRunning():
                    self.worker.requestInterruption()
                    if not self.worker.wait(3000):  # Esperar hasta 3 segundos
                        self.worker.terminate()
                        self.worker.wait()
                self.worker = None
            
            # Registrar los costos
            self.registrar_costos_finales()
            
            # Habilitar la interfaz ANTES de intentar abrir/mostrar mensaje
            self.enable_ui_after_generation()
            
            if filename:
                # --- Guardar y pasar la ruta a la ventana de vista previa --- 
                self.generated_pptx_path = os.path.abspath(filename) # Guardar ruta absoluta
                if hasattr(self, 'vista_previa') and self.vista_previa: # <--- Cambiado de preview_window a vista_previa
                    self.vista_previa.set_pptx_path(self.generated_pptx_path)
                    # Forzar la actualización de la vista previa para habilitar el botón
                    if self.vista_previa.current_slide_index >= 0: # <--- Añadida comprobación
                        self.vista_previa.mostrar_diapositiva_actual() # <--- Añadida llamada
                # ------------------------------------------------------------
                
                if auto_open:
                    # Abrir el archivo automáticamente
                    # Usar QDesktopServices para una mejor compatibilidad multiplataforma
                    try:
                        from PySide6.QtGui import QDesktopServices
                        from PySide6.QtCore import QUrl
                        QDesktopServices.openUrl(QUrl.fromLocalFile(self.generated_pptx_path))
                    except Exception as open_err:
                        print(f"Error al abrir archivo automáticamente: {open_err}")
                        # Fallback a os.startfile si existe (Windows)
                        try:
                           os.startfile(self.generated_pptx_path)
                        except AttributeError:
                           pass # No disponible en otras plataformas
                           
                else:
                    # Mostrar mensaje de éxito
                    nombre_archivo = os.path.basename(self.generated_pptx_path)
                    ruta_completa = self.generated_pptx_path # Ya es absoluta
                    
                    msg = QMessageBox(self)
                    msg.setWindowTitle(obtener_traduccion('presentation_ready', current_language))
                    msg.setText(obtener_traduccion('presentation_generated_successfully', current_language).format(nombre_archivo=nombre_archivo, ruta_completa=ruta_completa))
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
                    
                    # Ajustar posición
                    msg.adjustSize()
                    msg_pos = self.geometry().center() - msg.rect().center()
                    msg.move(msg_pos)
                    
                    msg.exec()
            else:
                 # Si no hay 'filename', asegurarse que la ruta PPTX está limpia
                 self.generated_pptx_path = None
                 if hasattr(self, 'vista_previa') and self.vista_previa: # <--- Cambiado de preview_window a vista_previa
                      self.vista_previa.set_pptx_path(None)
                      
        except Exception as e:
            print(f"Error en on_generation_finished: {str(e)}")
            # Asegurar que la interfaz se habilite incluso en caso de error
            self.enable_ui_after_generation()
            # Limpiar la ruta PPTX en caso de error también
            self.generated_pptx_path = None
            if hasattr(self, 'vista_previa') and self.vista_previa:
                 self.vista_previa.set_pptx_path(None)

    def show_error(self, error_msg):
        try:
            current_language = 'es'
            if self.parent() and hasattr(self.parent(), 'current_language'):
                current_language = self.parent().current_language
            
            # Detener el timer de animación si está activo
            if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
                self.loading_timer.stop()
            
            # Habilitar nuevamente la interfaz en caso de error
            self.enable_ui_after_generation()
            
            msg = QMessageBox(self)
            msg.setWindowTitle(obtener_traduccion('error', current_language))
            msg.setText(obtener_traduccion('generation_error', current_language).format(error=error_msg))
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
            
            # Reproducir sonido de sistema
            QApplication.beep()
            
            # Ajustar posición
            msg.adjustSize()
            msg_pos = self.geometry().center() - msg.rect().center()
            msg.move(msg_pos)
            
            msg.exec()
            
            # Resetear la barra de progreso
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
        except Exception as e:
            print(f"Error al mostrar error: {str(e)}")

    # Función para deshabilitar la interfaz durante la generación
    def disable_ui_during_generation(self):
        # Deshabilitar selección de modelos
        self.texto_combo.setEnabled(False)
        self.imagen_combo.setEnabled(False)

        self.font_combo.setEnabled(False)
        self.title_font_label.setEnabled(False)
        self.title_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, True) # Añadido para consistencia
        self.content_font_combo.setEnabled(False)
        self.content_font_label.setEnabled(False)
        self.content_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, True) # Añadido para consistencia

        # Deshabilitar los labels solicitados
        self.texto_label.setEnabled(False)
        self.texto_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.imagen_label.setEnabled(False)
        self.imagen_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.descripcion_label.setEnabled(False)
        self.descripcion_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Deshabilitar spinboxes de tamaño de fuente
        if hasattr(self, 'title_font_size_label'):
            self.title_font_size_label.setEnabled(False)
        if hasattr(self, 'title_font_size_spin'):
            self.title_font_size_spin.setEnabled(False)
        if hasattr(self, 'content_font_size_label'):
            self.content_font_size_label.setEnabled(False)
        if hasattr(self, 'content_font_size_spin'):
            self.content_font_size_spin.setEnabled(False)

        # Deshabilitar checkboxes de formato de título
        self.title_bold_checkbox.setEnabled(False)
        self.title_italic_checkbox.setEnabled(False)
        self.title_underline_checkbox.setEnabled(False)

        # >>> AÑADIR Deshabilitar checkboxes de formato de contenido <<<
        self.content_bold_checkbox.setEnabled(False)
        self.content_italic_checkbox.setEnabled(False)
        self.content_underline_checkbox.setEnabled(False)
        
        # Deshabilitar botón de selección de estilo
        self.select_style_btn.setEnabled(False)

        # Deshabilitar área de descripción
        self.descripcion_text.setEnabled(False)

        # Deshabilitar controles auxiliares
        self.auto_open_checkbox.setEnabled(False)
        self.num_diapositivas_spin.setEnabled(False)
        self.diapositivas_label.setEnabled(False)

        # Deshabilitar botones de PDF
        self.cargar_pdf_btn.setEnabled(False)
        if self.eliminar_pdf_btn.isVisible():
            self.eliminar_pdf_btn.setEnabled(False)
        if self.revisar_pdf_btn.isVisible():
            self.revisar_pdf_btn.setEnabled(False)

        # Deshabilitar botones adicionales
        if hasattr(self, 'cargar_imagen_btn') and self.cargar_imagen_btn.isVisible():
            self.cargar_imagen_btn.setEnabled(False)
        if hasattr(self, 'ver_imagen_btn') and self.ver_imagen_btn.isVisible():
            self.ver_imagen_btn.setEnabled(False)

        # Cambiar el estilo del botón de generar a modo "cancelar"
        self.generar_btn.setText(obtener_traduccion('cancel_generation', self.current_language))
        self.generar_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #FF6259;
            }
            QPushButton:pressed {
                background-color: #CC2F26;
            }
        """)
        # Desconectar el evento anterior y conectar al evento de cancelación
        try:
            self.generar_btn.clicked.disconnect()
        except:
            pass
        self.generar_btn.clicked.connect(self.confirm_cancel_generation)
        self.generar_btn.setEnabled(True)

        # Asegurarse de que los botones de navegación de la vista previa estén habilitados según corresponda
        if self.vista_previa:
            self.vista_previa.actualizar_botones_navegacion()

        # Deshabilitar elementos del menú si la ventana principal está disponible
        if self.parent() and hasattr(self.parent(), 'disable_menu_during_generation'):
            self.parent().disable_menu_during_generation()
        # También actualizar el estilo de los checkboxes directamente desde el widget si es necesario
        elif self.parent() and hasattr(self.parent(), 'theme_manager'):
            self.parent().theme_manager.set_generating_state(True)

    # Método para habilitar la interfaz después de la generación
    def enable_ui_after_generation(self):
        # Cambiar el estilo del botón de generar y habilitarlo
        self.generar_btn.setText('POWERPOINEAR')
        self.generar_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF6E00;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #FF8C32;
                }
                QPushButton:pressed {
                    background-color: #E56200;
                }
            """)
        # Desconectar el evento de cancel
        try:
            self.generar_btn.clicked.disconnect()
        except:
            pass
        self.generar_btn.clicked.connect(self.generar_presentacion_event)
        self.generar_btn.setEnabled(True)
        
        # Habilitar selección de modelos
        self.texto_combo.setEnabled(True)
        self.imagen_combo.setEnabled(True)
        
        self.font_combo.setEnabled(True)
        self.title_font_label.setEnabled(True)
        self.title_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, False) # Añadido para consistencia
        self.content_font_combo.setEnabled(True)
        self.content_font_label.setEnabled(True)
        self.content_font_label.setAttribute(Qt.WA_TransparentForMouseEvents, False) # Añadido para consistencia
        self.load_font_selection()
        self.load_content_font_selection()

        # Habilitar los labels solicitados
        self.texto_label.setEnabled(True)
        self.texto_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.imagen_label.setEnabled(True)
        self.imagen_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.descripcion_label.setEnabled(True)
        self.descripcion_label.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        # Habilitar spinboxes de tamaño de fuente
        if hasattr(self, 'title_font_size_label'):
            self.title_font_size_label.setEnabled(True)
        if hasattr(self, 'title_font_size_spin'):
            self.title_font_size_spin.setEnabled(True)
        if hasattr(self, 'content_font_size_label'):
            self.content_font_size_label.setEnabled(True)
        if hasattr(self, 'content_font_size_spin'):
            self.content_font_size_spin.setEnabled(True)
            
        # Habilitar checkboxes de formato de título
        self.title_bold_checkbox.setEnabled(True)
        self.title_italic_checkbox.setEnabled(True)
        self.title_underline_checkbox.setEnabled(True)

        # Habilitar checkboxes de formato de contenido
        self.content_bold_checkbox.setEnabled(True)
        self.content_italic_checkbox.setEnabled(True)
        self.content_underline_checkbox.setEnabled(True)

        # Habilitar botón de selección de estilo
        self.select_style_btn.setEnabled(True)
        
        # Habilitar área de descripción
        self.descripcion_text.setEnabled(True)
        
        # Habilitar controles auxiliares
        self.auto_open_checkbox.setEnabled(True)
        self.num_diapositivas_spin.setEnabled(True)
        self.diapositivas_label.setEnabled(True)
        
        # Habilitar botones de documentos
        self.cargar_pdf_btn.setEnabled(True)
        if self.eliminar_pdf_btn.isVisible():
            self.eliminar_pdf_btn.setEnabled(True)
        if self.revisar_pdf_btn.isVisible():
            self.revisar_pdf_btn.setEnabled(True)
        
        # Habilitar botones adicionales
        if hasattr(self, 'cargar_imagen_btn') and self.cargar_imagen_btn.isVisible():
            self.cargar_imagen_btn.setEnabled(True)
        if hasattr(self, 'ver_imagen_btn') and self.ver_imagen_btn.isVisible():
            self.ver_imagen_btn.setEnabled(True)
        
        # Habilitar elementos del menú si la ventana principal está disponible
        if self.parent() and hasattr(self.parent(), 'enable_menu_after_generation'):
            self.parent().enable_menu_after_generation()
        # También actualizar el estilo de los checkboxes directamente desde el widget si es necesario  
        elif self.parent() and hasattr(self.parent(), 'theme_manager'):
            self.parent().theme_manager.set_generating_state(False)

    # Modificación del método de generación de presentación para usar la lógica integrada
    def generar_presentacion_event(self):
        # --- Resetear ruta PPTX y estado de edición antes de generar --- 
        self.generated_pptx_path = None
        if hasattr(self, 'preview_window') and self.preview_window:
            # Resetear la vista previa (esto también limpia su pptx_path y deshabilita el botón)
            self.preview_window.reset_completo()
            # Alternativamente, solo limpiar la ruta: self.preview_window.set_pptx_path(None)
        # --------------------------------------------------------------
        
        modelo_texto = self.texto_combo.currentText()
        modelo_imagen = self.imagen_combo.currentText()
        descripcion = self.descripcion_text.toPlainText()
        auto_open = self.auto_open_checkbox.isChecked()
        num_diapositivas = self.num_diapositivas_spin.value()
        # selected_font = self.font_combo.currentText() # Obtener fuente seleccionada
        title_font = self.font_combo.currentText() # <-- Fuente Título
        content_font = self.content_font_combo.currentText() # <-- Fuente Contenido
        title_font_size = self.title_font_size_spin.value() # Obtener tamaño título
        content_font_size = self.content_font_size_spin.value() # Obtener tamaño contenido
        
        # Obtener opciones de formato de título
        title_bold = self.title_bold_checkbox.isChecked()
        title_italic = self.title_italic_checkbox.isChecked()
        title_underline = self.title_underline_checkbox.isChecked()

        # Obtener opciones de formato de contenido
        content_bold = self.content_bold_checkbox.isChecked()
        content_italic = self.content_italic_checkbox.isChecked()
        content_underline = self.content_underline_checkbox.isChecked()

        # Obtener el idioma actual desde el padre (MainWindow) o usar default
        current_language = 'es'
        if self.parent() and hasattr(self.parent(), 'current_language'):
            current_language = self.parent().current_language
        
        # Guardar el idioma actual en la instancia para propagar a través de signals
        self.current_language = current_language
        
        num_palabras = len(descripcion.split())
        if num_palabras >= 200:
            QMessageBox.warning(self, obtener_traduccion('error', current_language), 
                               obtener_traduccion('too_many_words', current_language))
            return

        if len(descripcion.split()) < 10 and len(descripcion.split()) > 0:
            QMessageBox.warning(self, obtener_traduccion('error', current_language), 
                               obtener_traduccion('too_few_words', current_language))
            return
        elif len(descripcion.split()) == 0:
            QMessageBox.warning(self, obtener_traduccion('error', current_language), 
                               obtener_traduccion('empty_description', current_language))
            return
        
        if modelo_imagen in ['photomaker [$0.0070]', 'flux-pulid [$0.032]']:
            if not self.imagen_personalizada or not os.path.exists(self.imagen_personalizada):
                QMessageBox.warning(self, obtener_traduccion('error', current_language), 
                                   obtener_traduccion('image_required', current_language))
                return

        default_filename = obtener_traduccion('default_filename', current_language)
        file_filter = obtener_traduccion('pptx_filter', current_language)
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            obtener_traduccion('save_presentation', current_language),
            default_filename,
            file_filter
        )

        if file_path:
            # Limpiar el log y la vista previa
            self.log_text.clear()
            self.resetear_vista_previa()
            
            # Configurar barra de progreso
            self.progress_bar.setRange(0, 0)
            self.progress_bar.setValue(0)
            
            # Deshabilitar la interfaz durante la generación
            self.disable_ui_during_generation()
            
            # Crear signals para la comunicación
            from Ventana_progreso import LogSignals
            self.signals = LogSignals(self)
            # Explícitamente establecer el idioma actual en signals
            self.signals.current_language = current_language
            self.signals.update_log.connect(self.update_log)
            self.signals.finished.connect(self.on_generation_finished)
            self.signals.error.connect(self.show_error)
            self.signals.update_progress.connect(self.update_progress)
            self.signals.nueva_diapositiva.connect(self.agregar_diapositiva)
            
            # Iniciar el timer de animación de carga
            self.loading_timer.start(50)
            
            # Modificar la descripción si hay un PDF cargado
            nuevo_string = descripcion
            if self.pdf_cargado and os.path.exists(self.pdf_cargado):
                try:
                    # Determinar el tipo de archivo por su extensión
                    if self.pdf_cargado.lower().endswith('.pdf'):
                        texto_doc = self.extraer_texto_pdf(self.pdf_cargado)
                    elif self.pdf_cargado.lower().endswith('.txt'):
                        texto_doc = self.extraer_texto_txt(self.pdf_cargado)
                    else:
                        texto_doc = ""
                        
                    if texto_doc.strip():
                        nuevo_string += f"\n\nContenido del documento para tener en cuenta:\n{texto_doc}"
                except Exception as e:
                    print(f"Error al procesar el documento para la presentación: {str(e)}")
            
            # Crear worker e iniciar generación
            from Ventana_progreso import GenerationWorker
            idioma = current_language  # Usar la variable current_language en lugar de self.parent().current_language
            instruccion_idioma = obtener_traduccion('language_instruction', idioma)
            selected_layout_index = self.selected_layout_index # <-- Obtener el índice seleccionado

            self.worker = GenerationWorker(
                modelo_texto,
                modelo_imagen,
                nuevo_string + f" hazlo OBLIGATORIAMENTE en {num_diapositivas} claves-valores (diapositivas) y en {instruccion_idioma}, tal que los títulos de la tupla NO superen 4 palabras y del contenido NO superen 69 palabras",
                auto_open,
                self.imagen_personalizada,
                file_path,
                self.signals,
                title_font, # <-- Pasar fuente título
                content_font, # <-- Pasar fuente contenido
                title_font_size, # Pasar tamaño de fuente de título
                content_font_size, # Pasar tamaño de fuente de contenido
                title_bold, # Pasar opción de negrita para título
                title_italic, # Pasar opción de cursiva para título
                title_underline, # Pasar opción de subrayado para título
                content_bold, # Pasar opción de negrita para contenido
                content_italic, # Pasar opción de cursiva para contenido
                content_underline, # Pasar opción de subrayado para contenido
                selected_layout_index=selected_layout_index # Pasar el índice seleccionado (se usará si aleatorio es False)
            )
            self.worker.start()

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
        current_language = 'es'
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    current_language = config.get('language', 'es')
        except Exception as e:
            print(f"Error al cargar el idioma: {str(e)}")
            
        texto = self.descripcion_text.toPlainText()
        num_palabras = len(texto.split())
        
        if num_palabras > 200:
            cursor = self.descripcion_text.textCursor()
            pos = cursor.position()
            
            palabras = texto.split()[:200]
            texto_truncado = ' '.join(palabras)
            
            self.descripcion_text.blockSignals(True)
            self.descripcion_text.setPlainText(texto_truncado)
            
            cursor = self.descripcion_text.textCursor()
            pos = min(pos, len(texto_truncado))
            cursor.setPosition(pos)
            self.descripcion_text.setTextCursor(cursor)
            
            self.descripcion_text.blockSignals(False)
            num_palabras = 200
            
        self.contador_label.setText(obtener_traduccion('contador_label', current_language).format(num_palabras))
        
        if num_palabras < 10:
            self.contador_label.setStyleSheet("color: red;")
        elif num_palabras >= 175 and num_palabras < 200:
            self.contador_label.setStyleSheet("color: yellow;")
        elif num_palabras >= 200:
            self.contador_label.setStyleSheet("color: red;")
        else:
            self.contador_label.setStyleSheet("color: green;")

    # Función para cargar una imagen personalizada
    def cargar_imagen_personalizada(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            obtener_traduccion('seleccionar_imagen_personalizada', self.current_language),
            "",
            obtener_traduccion('imagen_filter', self.current_language) + " (*.jpg)"
        )
        if file_path:
            self.imagen_personalizada_path = file_path # Guardar la ruta en una variable temporal
            try:
                # Verificar que la ruta existe y es un archivo
                if os.path.exists(self.imagen_personalizada_path) and os.path.isfile(self.imagen_personalizada_path):
                    self.imagen_personalizada = self.imagen_personalizada_path # Guardar la ruta si es válida
                    QMessageBox.information(self, obtener_traduccion('edit_save_pptx_success_title', self.current_language),
                                            obtener_traduccion('imagen_cargada_exito_mensaje', self.current_language))
                else:
                    QMessageBox.critical(self, obtener_traduccion('error', self.current_language),
                                         obtener_traduccion('ruta_imagen_invalida_mensaje', self.current_language))
                    self.imagen_personalizada = None
            except Exception as e:
                self.imagen_personalizada = None
                QMessageBox.critical(self, obtener_traduccion('error', self.current_language),
                                     obtener_traduccion('error_cargar_imagen_mensaje', self.current_language).format(str(e)))

    # Función para manejar el cambio en la selección de modelos de imagen
    def on_imagen_combo_changed(self, texto):
        if texto in ['flux-pulid [$0.032]', 'photomaker [$0.0070]']:
            self.cargar_imagen_btn.show()
            self.ver_imagen_btn.show()
            self.cargar_imagen_btn.setEnabled(True)
            self.ver_imagen_btn.setEnabled(True)
            
            if hasattr(self, 'imagen_personalizada') and self.imagen_personalizada:
                if not os.path.exists(self.imagen_personalizada):
                    self.imagen_personalizada = None
        else:
            self.cargar_imagen_btn.hide()
            self.ver_imagen_btn.hide()
            self.cargar_imagen_btn.setEnabled(False)
            self.ver_imagen_btn.setEnabled(False)
            self.imagen_personalizada = None
        self.save_combo_selection()

    # Función para ver la imagen personalizada
    def ver_imagen_personalizada(self):
        # Verificar que hay una imagen seleccionada y que existe
        if hasattr(self, 'imagen_personalizada') and self.imagen_personalizada and os.path.exists(self.imagen_personalizada):
            # Abrir la imagen con el visor predeterminado del sistema
            try:
                # Usar QDesktopServices.openUrl para compatibilidad multiplataforma
                from PySide6.QtGui import QDesktopServices
                from PySide6.QtCore import QUrl
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.imagen_personalizada))
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Error al abrir la imagen: {str(e)}')
        else:
            # Usar las traducciones para el mensaje de error
            idioma_actual = self.current_language if hasattr(self, 'current_language') else 'es'
            QMessageBox.warning(self, obtener_traduccion('no_imagen_seleccionada_titulo', idioma_actual), 
                                obtener_traduccion('no_imagen_seleccionada_mensaje', idioma_actual))
            self.imagen_personalizada = None

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
            config = {}
            # Intentar cargar la configuración existente
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            texto_modelo_guardado = config.get('texto_modelo', '')
            imagen_modelo_guardado = config.get('imagen_modelo', '')
            # parent = self.parent() # No se necesita parent aquí ya que populate_fields ya filtró

            # --- Manejo de texto_combo ---
            if self.texto_combo.count() > 0: # Solo proceder si el combo tiene items
                if texto_modelo_guardado:
                    index = self.texto_combo.findText(texto_modelo_guardado)
                    if index >= 0:
                        # El modelo guardado existe en el combo actual
                        self.texto_combo.setCurrentIndex(index)
                    else:
                        # El modelo guardado no está en el combo actual (API desactivada o modelo ya no existe)
                        # Seleccionar el primer modelo disponible y actualizar la configuración.
                        self.texto_combo.setCurrentIndex(0)
                        config['texto_modelo'] = self.texto_combo.currentText()
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                else:
                    # No hay modelo guardado, o el combo estaba vacío pero ahora tiene items.
                    # Seleccionar el primero por defecto y guardarlo.
                    self.texto_combo.setCurrentIndex(0)
                    config['texto_modelo'] = self.texto_combo.currentText()
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=4)
            
            # --- Manejo de imagen_combo ---
            if self.imagen_combo.isEnabled() and self.imagen_combo.count() > 0: # Solo proceder si el combo está habilitado y tiene items
                if imagen_modelo_guardado:
                    index = self.imagen_combo.findText(imagen_modelo_guardado)
                    if index >= 0:
                        self.imagen_combo.setCurrentIndex(index)
                        # Re-aplicar lógica de mostrar/ocultar botones para modelos específicos
                        if imagen_modelo_guardado in ['flux-pulid [$0.032]', 'photomaker [$0.0070]']:
                            self.cargar_imagen_btn.show()
                            self.ver_imagen_btn.show()
                            self.cargar_imagen_btn.setEnabled(True)
                            self.ver_imagen_btn.setEnabled(True)
                        else:
                            self.cargar_imagen_btn.hide()
                            self.ver_imagen_btn.hide()
                            # self.imagen_personalizada = None # on_imagen_combo_changed se encarga de esto
                    else:
                        # El modelo guardado no está en el combo actual
                        self.imagen_combo.setCurrentIndex(0)
                        config['imagen_modelo'] = self.imagen_combo.currentText()
                        # Re-aplicar lógica de botones para el nuevo modelo seleccionado (índice 0)
                        current_img_model_at_0 = self.imagen_combo.currentText()
                        if current_img_model_at_0 in ['flux-pulid [$0.032]', 'photomaker [$0.0070]']:
                             self.cargar_imagen_btn.show(); self.ver_imagen_btn.show()
                             self.cargar_imagen_btn.setEnabled(True); self.ver_imagen_btn.setEnabled(True)
                        else:
                             self.cargar_imagen_btn.hide(); self.ver_imagen_btn.hide()
                             # self.imagen_personalizada = None
                        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                            json.dump(config, f, ensure_ascii=False, indent=4)
                else:
                    # No hay modelo de imagen guardado. Seleccionar el primero y guardarlo.
                    self.imagen_combo.setCurrentIndex(0)
                    config['imagen_modelo'] = self.imagen_combo.currentText()
                    current_img_model_at_0 = self.imagen_combo.currentText()
                    if current_img_model_at_0 in ['flux-pulid [$0.032]', 'photomaker [$0.0070]']:
                            self.cargar_imagen_btn.show(); self.ver_imagen_btn.show()
                            self.cargar_imagen_btn.setEnabled(True); self.ver_imagen_btn.setEnabled(True)
                    else:
                            self.cargar_imagen_btn.hide(); self.ver_imagen_btn.hide()
                            # self.imagen_personalizada = None
                    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=4)
                        
        except (FileNotFoundError, json.JSONDecodeError):
            # Archivo de configuración no existe o está corrupto.
            # Si los combos tienen items, seleccionar el primero. save_combo_selection se llamará después si es necesario.
            if self.texto_combo.count() > 0:
                self.texto_combo.setCurrentIndex(0)
            if self.imagen_combo.isEnabled() and self.imagen_combo.count() > 0:
                self.imagen_combo.setCurrentIndex(0)
                # Actualizar botones para el modelo en el índice 0 de imagen_combo
                current_img_model_at_0 = self.imagen_combo.currentText()
                if current_img_model_at_0 in ['flux-pulid [$0.032]', 'photomaker [$0.0070]']:
                        self.cargar_imagen_btn.show(); self.ver_imagen_btn.show()
                        self.cargar_imagen_btn.setEnabled(True); self.ver_imagen_btn.setEnabled(True)
                else:
                        self.cargar_imagen_btn.hide(); self.ver_imagen_btn.hide()
        except Exception as e:
            print(f"Error al cargar la selección de modelos: {str(e)}")
            # Fallback: seleccionar el primer item si hay alguno
            if self.texto_combo.count() > 0:
                self.texto_combo.setCurrentIndex(0)
            if self.imagen_combo.isEnabled() and self.imagen_combo.count() > 0:
                self.imagen_combo.setCurrentIndex(0)
                # Actualizar botones para el modelo en el índice 0 de imagen_combo
                current_img_model_at_0 = self.imagen_combo.currentText()
                if current_img_model_at_0 in ['flux-pulid [$0.032]', 'photomaker [$0.0070]']:
                        self.cargar_imagen_btn.show(); self.ver_imagen_btn.show()
                        self.cargar_imagen_btn.setEnabled(True); self.ver_imagen_btn.setEnabled(True)
                else:
                        self.cargar_imagen_btn.hide(); self.ver_imagen_btn.hide()

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
                # Eliminar la siguiente línea, ya que num_imagenes se pasará correctamente
                # if hasattr(self, 'log_window') and self.log_window:
                #     num_imagenes = self.log_window.total_images
                config['costos_totales']['imagen'] += precio_imagen * num_imagenes
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al registrar costos: {str(e)}")

    def registrar_costos_finales(self):
        self.registrar_costos(modelo_texto=self.texto_combo.currentText())
        # Usar self.total_images que se obtiene de update_log.
        # Si self.total_images no se actualizó (por ejemplo, si no hubo mensajes de 'generando_imagen'),
        # su valor por defecto es 0, pero update_log tiene fallbacks a 1.
        # Para mayor seguridad, si self.total_images es 0, usar 1.
        num_imagenes_a_registrar = self.total_images if self.total_images > 0 else 1
        self.registrar_costos(modelo_imagen=self.imagen_combo.currentText(), num_imagenes=num_imagenes_a_registrar)

    def save_num_diapositivas(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['num_diapositivas'] = self.num_diapositivas_spin.value()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar el número de diapositivas: {str(e)}")

    def load_num_diapositivas(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    num_diapositivas = config.get('num_diapositivas', 5)
                    self.num_diapositivas_spin.setValue(num_diapositivas)
        except Exception as e:
            print(f"Error al cargar el número de diapositivas: {str(e)}")

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

    # Función para limpiar y resetear la vista previa
    def resetear_vista_previa(self):
        if hasattr(self, 'vista_previa') and self.vista_previa:
            self.vista_previa.reset_completo()

    # Redefinir el método closeEvent para manejar cierre durante la generación
    def closeEvent(self, event):
        # Si hay una generación en curso, preguntar si desea cancelar
        if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
            # No cerrar el widget directamente, sino mostrar un diálogo de confirmación
            event.ignore()
            self.confirm_cancel_generation()
        else:
            # Si no hay generación en curso, comportamiento normal
            event.accept()

    # Método para confirmar la cancelación de la generación
    def confirm_cancel_generation(self):
        # Obtener el idioma actual
        current_language = 'es'
        if self.parent() and hasattr(self.parent(), 'current_language'):
            current_language = self.parent().current_language
        
        # Crear el cuadro de diálogo de confirmación
        msg = QMessageBox(self)
        msg.setWindowTitle(obtener_traduccion('confirm_cancellation', current_language))
        msg.setText(obtener_traduccion('cancel_generation_confirm', current_language))
        msg.setIcon(QMessageBox.Question)
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.No)
        msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
        
        # Ajustar botones con traducciones
        msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', current_language))
        msg.button(QMessageBox.No).setText(obtener_traduccion('no', current_language))
        
        # Ajustar posición
        msg.adjustSize()
        msg_pos = self.geometry().center() - msg.rect().center()
        msg.move(msg_pos)
        
        # Mostrar el cuadro de diálogo y obtener la respuesta del usuario
        response = msg.exec()
        
        # Si el usuario confirma la cancelación, detener la generación
        if response == QMessageBox.Yes:
            # Detener el timer de inmediato para evitar animación
            if hasattr(self, 'loading_timer') and self.loading_timer.isActive():
                self.loading_timer.stop()
                
            # Mostrar mensaje de cancelación inmediatamente
            self.log_text.append("\n" + obtener_traduccion('generation_cancelled', current_language))
            
            # Resetear la barra de progreso inmediatamente
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            
            # Habilitar la interfaz inmediatamente
            self.enable_ui_after_generation()
            
            # Detener el worker después de habilitar la interfaz
            if hasattr(self, 'worker') and self.worker and self.worker.isRunning():
                self.worker.requestInterruption()
                # Reducir el tiempo de espera a 500ms
                if not self.worker.wait(500):
                    self.worker.terminate()
                    # No esperar más después de terminate
                self.worker = None

    # Función para cargar un archivo PDF o TXT
    def cargar_pdf(self):
        current_language = 'es'
        if self.parent() and hasattr(self.parent(), 'current_language'):
            current_language = self.parent().current_language
        
        file_filter = obtener_traduccion('pdf_filter', current_language)
        doc_path, _ = QFileDialog.getOpenFileName(
            self,
            obtener_traduccion('seleccionar_pdf', current_language),
            "",
            file_filter
        )
        
        if doc_path:
            try:
                # Determinar el tipo de archivo por su extensión
                if doc_path.lower().endswith('.pdf'):
                    texto_doc = self.extraer_texto_pdf(doc_path)
                elif doc_path.lower().endswith('.txt'):
                    texto_doc = self.extraer_texto_txt(doc_path)
                else:
                    raise Exception("Formato de archivo no soportado")
                
                if not texto_doc.strip():
                    QMessageBox.warning(self, obtener_traduccion('error_cargar_pdf', current_language), 
                                    obtener_traduccion('error_pdf_vacio', current_language))
                    return
                
                self.pdf_cargado = doc_path
                self.pdf_label.setText(obtener_traduccion('pdf_cargado', current_language).format(os.path.basename(doc_path)))
                self.pdf_label.show() # <--- Mostrar la etiqueta
                
                # Mostrar y habilitar los botones
                self.eliminar_pdf_btn.show()
                self.eliminar_pdf_btn.setEnabled(True)
                self.revisar_pdf_btn.show()
                self.revisar_pdf_btn.setEnabled(True)
                
                # Guardar la ruta del PDF
                self.save_pdf_path()
            except Exception as e:
                print(f"Error al cargar el documento: {str(e)}")
                QMessageBox.warning(self, obtener_traduccion('error_cargar_pdf', current_language), str(e))
    
    # Función para extraer texto de un PDF
    def extraer_texto_pdf(self, pdf_path):
        try:
            reader = PdfReader(pdf_path)
            texto = ""
            for pagina in reader.pages:
                texto += pagina.extract_text() + "\n"
            return texto
        except Exception as e:
            print(f"Error al extraer texto del PDF: {str(e)}")
            raise
    
    # Función para extraer texto de un archivo TXT
    def extraer_texto_txt(self, txt_path):
        try:
            with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                texto = f.read()
            return texto
        except Exception as e:
            print(f"Error al extraer texto del TXT: {str(e)}")
            raise
    
    # Función para eliminar el PDF cargado
    def eliminar_pdf(self):
        self.pdf_cargado = None
        self.pdf_label.setText("")
        self.pdf_label.hide() # <--- Ocultar la etiqueta
        self.eliminar_pdf_btn.hide()
        self.save_pdf_path()
        self.revisar_pdf_btn.hide()
    
    # Guardar la ruta del PDF en la configuración
    def save_pdf_path(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['pdf_path'] = self.pdf_cargado if self.pdf_cargado else ""
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar la ruta del PDF: {str(e)}")
    
    # Cargar la ruta del PDF desde la configuración
    def load_pdf_path(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    pdf_path = config.get('pdf_path', "")
                    if pdf_path and os.path.exists(pdf_path):
                        self.pdf_cargado = pdf_path
                        if hasattr(self, 'pdf_label'):
                            # Obtener el idioma del archivo de configuración para asegurar coherencia
                            current_language = config.get('language', 'es')
                            self.pdf_label.setText(obtener_traduccion('pdf_cargado', current_language).format(os.path.basename(pdf_path)))
                            self.pdf_label.show() # <--- Mostrar la etiqueta
                            # Mostrar y habilitar los botones
                            self.eliminar_pdf_btn.show()
                            self.eliminar_pdf_btn.setEnabled(True)
                            self.revisar_pdf_btn.show()
                            self.revisar_pdf_btn.setEnabled(True)
                    else:
                        self.pdf_cargado = None
                        if hasattr(self, 'pdf_label'): # <--- Asegurarse de que existe antes de ocultar
                            self.pdf_label.setText("")
                            self.pdf_label.hide()
        except Exception as e:
            print(f"Error al cargar la ruta del PDF: {str(e)}")
            self.pdf_cargado = None
            if hasattr(self, 'pdf_label'): # <--- Asegurarse de que existe antes de ocultar
                self.pdf_label.setText("")
                self.pdf_label.hide()

    def revisar_pdf(self):
        if self.pdf_cargado and os.path.exists(self.pdf_cargado):
            try:
                os.startfile(self.pdf_cargado)
            except Exception as e:
                current_language = 'es'
                if self.parent() and hasattr(self.parent(), 'current_language'):
                    current_language = self.parent().current_language
                QMessageBox.critical(self, obtener_traduccion('error', current_language), 
                                   obtener_traduccion('error_abrir_pdf', current_language).format(error=str(e)))
        else:
            current_language = 'es'
            if self.parent() and hasattr(self.parent(), 'current_language'):
                current_language = self.parent().current_language
            QMessageBox.warning(self, obtener_traduccion('aviso', current_language), 
                              obtener_traduccion('ningun_documento', current_language))

    # Función para guardar la selección de fuente
    def save_font_selection(self, font_name):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            config['title_font'] = font_name # <-- Guardar como title_font

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar la fuente del título: {str(e)}")
            
        # --- NUEVO: Actualizar vista previa ---
        if hasattr(self, 'vista_previa') and self.vista_previa:
            self.vista_previa.update_format_settings(
                title_font_name=self.font_combo.currentText(), # CORREGIDO
                content_font_name=self.content_font_combo.currentText(), # CORREGIDO
                title_font_size=self.title_font_size_spin.value(),
                content_font_size=self.content_font_size_spin.value(),
                title_bold=self.title_bold_checkbox.isChecked(),
                title_italic=self.title_italic_checkbox.isChecked(),
                title_underline=self.title_underline_checkbox.isChecked(),
                content_bold=self.content_bold_checkbox.isChecked(),
                content_italic=self.content_italic_checkbox.isChecked(),
                content_underline=self.content_underline_checkbox.isChecked()
            )
        # ---------------------------------------
        # ... (código existente de manejo de errores)
    # --- Fin Función para guardar selección de fuente ---

    # --- Nueva función para guardar la fuente del contenido ---
    def save_content_font_selection(self, font_name):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['content_font'] = font_name
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar la fuente del contenido: {str(e)}")
        # --- NUEVO: Actualizar vista previa ---
        if hasattr(self, 'vista_previa') and self.vista_previa:
            self.vista_previa.update_format_settings(
                title_font_name=self.font_combo.currentText(), # CORREGIDO
                content_font_name=self.content_font_combo.currentText(), # CORREGIDO
                title_font_size=self.title_font_size_spin.value(),
                content_font_size=self.content_font_size_spin.value(),
                title_bold=self.title_bold_checkbox.isChecked(),
                title_italic=self.title_italic_checkbox.isChecked(),
                title_underline=self.title_underline_checkbox.isChecked(),
                content_bold=self.content_bold_checkbox.isChecked(),
                content_italic=self.content_italic_checkbox.isChecked(),
                content_underline=self.content_underline_checkbox.isChecked()
            )
        # ---------------------------------------
        # ... (código existente de manejo de errores)
    # --- Fin Función para guardar selección de fuente de CONTENIDO ---

    def load_font_selection(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Cargar fuente de título (anteriormente 'font')
                    title_font = config.get('title_font', config.get('font', 'Calibri')) 
                    if title_font in self.system_fonts:
                        self.font_combo.blockSignals(True)
                        self.font_combo.setCurrentText(title_font)
                        self.update_font_combo_style(self.font_combo, title_font) # Aplicar estilo al cargar
                        self.font_combo.blockSignals(False)
                    else:
                        print(f"Fuente de título guardada '{title_font}' no encontrada. Usando Calibri.")
                        self.font_combo.blockSignals(True)
                        self.font_combo.setCurrentText('Calibri')
                        self.update_font_combo_style(self.font_combo, 'Calibri')
                        self.font_combo.blockSignals(False)
                        self.save_font_selection('Calibri') # Guardar valor por defecto
        except Exception as e:
            print(f"Error al cargar la fuente del título: {str(e)}")
            self.font_combo.setCurrentText('Calibri') # Fallback
            self.update_font_combo_style(self.font_combo, 'Calibri')

    # Nueva función para cargar la fuente del contenido
    def load_content_font_selection(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    content_font = config.get('content_font', 'Calibri')
                    if content_font in self.system_fonts:
                        self.content_font_combo.blockSignals(True)
                        self.content_font_combo.setCurrentText(content_font)
                        self.update_font_combo_style(self.content_font_combo, content_font)
                        self.content_font_combo.blockSignals(False)
                    else:
                        print(f"Fuente de contenido guardada '{content_font}' no encontrada. Usando Calibri.")
                        self.content_font_combo.blockSignals(True)
                        self.content_font_combo.setCurrentText('Calibri')
                        self.update_font_combo_style(self.content_font_combo, 'Calibri')
                        self.content_font_combo.blockSignals(False)
                        self.save_content_font_selection('Calibri')
        except Exception as e:
            print(f"Error al cargar la fuente del contenido: {str(e)}")
            self.content_font_combo.setCurrentText('Calibri') # Fallback
            self.update_font_combo_style(self.content_font_combo, 'Calibri')

    # Modificar para aceptar el combobox como argumento
    def update_font_combo_style(self, combo_box, font_name):
        if font_name in self.system_fonts:
            font = QFont(font_name, 10)
            combo_box.setFont(font)
        else:
            combo_box.setFont(QFont("Calibri", 10)) # Fallback

    def save_font_sizes(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['title_font_size'] = self.title_font_size_spin.value()
            config['content_font_size'] = self.content_font_size_spin.value()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            # --- NUEVO: Actualizar vista previa ---
            if hasattr(self, 'vista_previa') and self.vista_previa:
                self.vista_previa.update_format_settings(
                    title_font_name=self.font_combo.currentText(), # CORREGIDO
                    content_font_name=self.content_font_combo.currentText(), # CORREGIDO
                    title_font_size=self.title_font_size_spin.value(),
                    content_font_size=self.content_font_size_spin.value(),
                    title_bold=self.title_bold_checkbox.isChecked(),
                    title_italic=self.title_italic_checkbox.isChecked(),
                    title_underline=self.title_underline_checkbox.isChecked(),
                    content_bold=self.content_bold_checkbox.isChecked(),
                    content_italic=self.content_italic_checkbox.isChecked(),
                    content_underline=self.content_underline_checkbox.isChecked()
                )
            # ---------------------------------------
        except Exception as e:
            print(f"Error al guardar tamaños de fuente: {str(e)}")

    def load_font_sizes(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    title_font_size = config.get('title_font_size', 24)
                    content_font_size = config.get('content_font_size', 18)
                    self.title_font_size_spin.setValue(title_font_size)
                    self.content_font_size_spin.setValue(content_font_size)
        except Exception as e:
            print(f"Error al cargar los tamaños de fuente: {str(e)}")

    # Función para guardar los tamaños de fuente
    def save_font_sizes(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            config['title_font_size'] = self.title_font_size_spin.value()
            config['content_font_size'] = self.content_font_size_spin.value()

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            # --- NUEVO: Actualizar vista previa ---
            if hasattr(self, 'vista_previa') and self.vista_previa:
                self.vista_previa.update_format_settings(
                    title_font_name=self.font_combo.currentText(), # CORREGIDO
                    content_font_name=self.content_font_combo.currentText(), # CORREGIDO
                    title_font_size=self.title_font_size_spin.value(),
                    content_font_size=self.content_font_size_spin.value(),
                    title_bold=self.title_bold_checkbox.isChecked(),
                    title_italic=self.title_italic_checkbox.isChecked(),
                    title_underline=self.title_underline_checkbox.isChecked(),
                    content_bold=self.content_bold_checkbox.isChecked(),
                    content_italic=self.content_italic_checkbox.isChecked(),
                    content_underline=self.content_underline_checkbox.isChecked()
                )
            # ---------------------------------------
        except Exception as e:
            print(f"Error al guardar los tamaños de fuente: {str(e)}")

    # Función para cargar los tamaños de fuente
    def load_font_sizes(self):
        try:
            title_size = 16 # Default
            content_size = 10 # Default
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    title_size = config.get('title_font_size', 16)
                    content_size = config.get('content_font_size', 10)

            # Validar rangos
            if not (1 <= title_size <= 72): # Ajustado el límite superior a 72
                title_size = 16
            if not (1 <= content_size <= 72): # Ajustado el límite superior a 72 (opcional, pero consistente)
                content_size = 10

            # Setear valores en los spin boxes
            if hasattr(self, 'title_font_size_spin') and self.title_font_size_spin:
                self.title_font_size_spin.blockSignals(True)
                self.title_font_size_spin.setValue(title_size)
                self.title_font_size_spin.blockSignals(False)
            if hasattr(self, 'content_font_size_spin') and self.content_font_size_spin:
                self.content_font_size_spin.blockSignals(True)
                self.content_font_size_spin.setValue(content_size)
                self.content_font_size_spin.blockSignals(False)

        except Exception as e:
            print(f"Error al cargar los tamaños de fuente: {str(e)}")
            # En caso de error, aplicar defaults
            if hasattr(self, 'title_font_size_spin') and self.title_font_size_spin:
                self.title_font_size_spin.setValue(16)
            if hasattr(self, 'content_font_size_spin') and self.content_font_size_spin:
                self.content_font_size_spin.setValue(10)

    # Función para guardar el formato de título
    def save_format_settings(self):
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['title_bold'] = self.title_bold_checkbox.isChecked()
            config['title_italic'] = self.title_italic_checkbox.isChecked()
            config['title_underline'] = self.title_underline_checkbox.isChecked()
            config['content_bold'] = self.content_bold_checkbox.isChecked()
            config['content_italic'] = self.content_italic_checkbox.isChecked()
            config['content_underline'] = self.content_underline_checkbox.isChecked()
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
            
            # --- NUEVO: Actualizar vista previa ---
            if hasattr(self, 'vista_previa') and self.vista_previa:
                self.vista_previa.update_format_settings(
                    title_font_name=self.font_combo.currentText(), # CORREGIDO
                    content_font_name=self.content_font_combo.currentText(), # CORREGIDO
                    title_font_size=self.title_font_size_spin.value(),
                    content_font_size=self.content_font_size_spin.value(),
                    title_bold=self.title_bold_checkbox.isChecked(),
                    title_italic=self.title_italic_checkbox.isChecked(),
                    title_underline=self.title_underline_checkbox.isChecked(),
                    content_bold=self.content_bold_checkbox.isChecked(),
                    content_italic=self.content_italic_checkbox.isChecked(),
                    content_underline=self.content_underline_checkbox.isChecked()
                )
            # ---------------------------------------
        except Exception as e:
            print(f"Error al guardar configuración de formato: {str(e)}")

    def load_format_settings(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.title_bold_checkbox.setChecked(config.get('title_bold', False))
                    self.title_italic_checkbox.setChecked(config.get('title_italic', False))
                    self.title_underline_checkbox.setChecked(config.get('title_underline', False))
                    # Cargar formato de contenido
                    self.content_bold_checkbox.setChecked(config.get('content_bold', False))
                    self.content_italic_checkbox.setChecked(config.get('content_italic', False))
                    self.content_underline_checkbox.setChecked(config.get('content_underline', False))
        except Exception as e:
            print(f"Error al cargar las configuraciones de formato: {str(e)}")

    # >>> NUEVA FUNCIÓN PLACEHOLDER <<<
    def select_slide_style(self):
        # --- MODIFICADO: Implementar lógica del diálogo ---
        # Asegurarse de tener el idioma actual
        current_language = 'es'
        if self.parent() and hasattr(self.parent(), 'current_language'):
            current_language = self.parent().current_language
        else:
            current_language = self.current_language # Usar el del widget si no hay padre

        # Crear y mostrar el diálogo
        dialog = StyleSelectionDialog(
            current_language=current_language,
            current_selection_index=self.selected_layout_index,
            parent=self # Pasar el widget como padre
        )

        if dialog.exec(): # Si el usuario hace clic en OK
            self.selected_layout_index = dialog.get_selected_index()
            self.save_selected_style() # Guardar la nueva selección
            self.update_style_label() # Actualizar la etiqueta con el estilo seleccionado
            print(f"Estilo de diseño seleccionado: {self.selected_layout_index}") # Opcional: para depuración
        # ----------------------------------------------------
        # pass # <-- Eliminar el placeholder pass

    # >>> AÑADIR NUEVAS FUNCIONES PARA GUARDAR/CARGAR ESTILO <<<
    def save_selected_style(self):
        """Guarda el índice del estilo de diseño seleccionado en config.json."""
        try:
            config = {}
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)

            config['selected_layout_index'] = self.selected_layout_index

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error al guardar el índice de estilo seleccionado: {str(e)}")

    def load_selected_style(self):
        """Carga el índice del estilo de diseño seleccionado desde config.json."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Obtener el índice guardado, usar 1 (Formal) si no existe
                    self.selected_layout_index = config.get('selected_layout_index', 0)
            else:
                self.selected_layout_index = 1 # Default si no existe config.json
        except Exception as e:
            print(f"Error al cargar el índice de estilo seleccionado: {str(e)}")
            self.selected_layout_index = 1 # Default en caso de error

    # >>> AÑADIR NUEVA FUNCIÓN PARA ACTUALIZAR LA ETIQUETA <<<
    def update_style_label(self):
        """Actualiza la etiqueta que muestra el estilo actual seleccionado."""
        try:
            # Mapeo de índices de estilo a nombres traducidos
            style_names = {
                0: obtener_traduccion('style_random', self.current_language),  # <-- AÑADIR ESTA LÍNEA
                1: obtener_traduccion('style_formal', self.current_language),
                5: obtener_traduccion('style_minimalist', self.current_language),
                6: obtener_traduccion('style_free', self.current_language),
                3: obtener_traduccion('style_comparison', self.current_language),
                8: obtener_traduccion('style_visual', self.current_language),
            }
            
            # Obtener el nombre del estilo según el índice seleccionado
            style_name = style_names.get(self.selected_layout_index, obtener_traduccion('style_formal', self.current_language))
            
            # Actualizar el texto de la etiqueta
            self.current_style_label.setText(f"({style_name})")
        except Exception as e:
            print(f"Error al actualizar la etiqueta de estilo: {str(e)}")

# Función principal para iniciar la aplicación
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(resource_path("iconos/icon.png")))

    # Importar platform para la detección del SO
    import platform

    # Establecer el estilo globalmente al inicio según la versión de Windows
    if sys.platform == "win32":
        try:
            release, version, csd, ptype = platform.win32_ver()
            # Extraer el build number. El formato es 'X.Y.BUILD.Z' o 'X.Y.BUILD'
            build_number_str = version.split('.')[2] if len(version.split('.')) > 2 else version.split('.')[0] 
            build_number = int(build_number_str)
            
            if build_number < 22000: # Es Windows 10 o anterior
                QApplication.setStyle(QStyleFactory.create('windows'))
            else: # Es Windows 11 o posterior
                QApplication.setStyle(QStyleFactory.create('Plastique'))
        except (IndexError, ValueError, TypeError):
            # Fallback si no se puede determinar la versión correctamente
            QApplication.setStyle(QStyleFactory.create('Plastique'))
    else:
        # Para otros sistemas operativos (Linux, macOS, etc.)
        QApplication.setStyle(QStyleFactory.create('Plastique'))

    while not verificar_conexion_internet():
        if mostrar_error_conexion() == QMessageBox.Cancel:
            sys.exit()
    
    from Splash_carga import SplashScreen
    from Version_checker import obtener_url_descarga
    
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    window = MainWindow() # MainWindow.__init__ carga la preferencia de tema
    
    # Aplicar el tema cargado ANTES de mostrar la ventana y DESPUÉS de QApplication.setStyle
    theme_to_apply_on_startup = window.current_app_theme
    if window.current_app_theme == 'system':
        color_scheme = QGuiApplication.styleHints().colorScheme()
        if color_scheme == Qt.ColorScheme.Dark:
            theme_to_apply_on_startup = 'dark'
        else: # Incluye Qt.ColorScheme.Light y Qt.ColorScheme.Unknown (default a light)
            theme_to_apply_on_startup = 'light'

    if hasattr(window, 'theme_manager'):
        window.theme_manager.gestionar_tema_aplicacion(theme_to_apply_on_startup) # USAR theme_to_apply_on_startup
    
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
            # Preparar la ventana principal antes de mostrarla
            window.activateWindow()
            
            # Mostrar la ventana principal después de que todo esté listo
            window.show()
            
            # Cerrar la pantalla de splash después de mostrar la ventana principal
            splash.close()
            
            if splash.hay_actualizacion:
                ultima_version = obtener_ultima_version()
                version_actual = obtener_version_actual()
                msg = QMessageBox()
                msg.setWindowTitle(obtener_traduccion('update_available_title', window.current_language))
                msg.setText(obtener_traduccion('update_available_message', window.current_language).format(
                    version_actual=version_actual, 
                    version_nueva=ultima_version
                ))
                msg.setIcon(QMessageBox.Information)
                msg.setWindowIcon(QIcon(resource_path("iconos/icon.png")))
                msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                msg.setDefaultButton(QMessageBox.Yes)
                msg.button(QMessageBox.Yes).setText(obtener_traduccion('yes', window.current_language))
                msg.button(QMessageBox.No).setText(obtener_traduccion('no', window.current_language))
                
                # Ajustar tamaño y centrar correctamente en la pantalla
                msg.adjustSize()
                
                # Centrar en la pantalla principal en lugar de relativo a la ventana
                screen_geometry = QApplication.primaryScreen().geometry()
                x = (screen_geometry.width() - msg.width()) // 2
                y = (screen_geometry.height() - msg.height()) // 2
                msg.move(QPoint(x, y))
                
                # Asegurar que la interfaz esté completamente actualizada antes de mostrar el diálogo
                app.processEvents()
                
                if msg.exec() == QMessageBox.Yes:
                    # ---------- INICIO DE LA NUEVA LÓGICA DE ACTUALIZACIÓN ----------
                    # Comprobar si es Windows y está compilado con PyInstaller
                    is_windows = sys.platform == "win32"
                    is_frozen = getattr(sys, 'frozen', False)

                    if is_windows and is_frozen:
                        try:
                            from Updater import iniciar_actualizacion_automatica
                            from Version_checker import obtener_url_descarga_exe # Importar la nueva función

                            url_exe_descarga = obtener_url_descarga_exe(ultima_version)

                            iniciar_actualizacion_automatica(
                                ultima_version, # Pasar el tag de la última versión
                                window,  # Ventana principal como padre para los diálogos
                                app,     # Instancia de QApplication
                                obtener_traduccion, # Tu función de traducción
                                window.current_language,
                                url_exe_descarga,
                                APP_DATA_DIR  # <--- AÑADIR APP_DATA_DIR aquí
                            )
                            # Nota: iniciar_actualizacion_automatica se encargará de cerrar la app si la actualización procede.
                        except ImportError:
                            QMessageBox.critical(window, 
                                                 obtener_traduccion('error_title', window.current_language), 
                                                 obtener_traduccion('updater_module_not_found_error', window.current_language))
                            webbrowser.open(obtener_url_descarga()) # Fallback al método antiguo
                            window.close()
                            app.quit()
                            # sys.exit() # app.quit() debería ser suficiente
                        except Exception as e_update:
                            QMessageBox.critical(window, 
                                                 obtener_traduccion('update_error_title', window.current_language),
                                                 f"{obtener_traduccion('unexpected_update_error_message', window.current_language)}: {str(e_update)}")
                            webbrowser.open(obtener_url_descarga()) # Fallback
                            window.close()
                            app.quit()
                            # sys.exit()
                    else:
                        # Si no es Windows compilado, o si la condición no se cumple, usar el método antiguo
                        webbrowser.open(obtener_url_descarga())
                        window.close()
                        app.quit()
                        sys.exit() # <--- DESCOMENTAR ESTA LÍNEA
                    # ---------- FIN DE LA NUEVA LÓGICA DE ACTUALIZACIÓN ----------
        else:
            QTimer.singleShot(100, check_and_show_main_window)
    
    check_and_show_main_window()
    app.exec()