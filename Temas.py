import sys, platform
from PySide6.QtCore import Qt
from PySide6.QtGui import QPalette, QColor, QGuiApplication
from PySide6.QtWidgets import QApplication, QStyleFactory, QWidget

# Clase para gestionar el tema de la aplicación
class ThemeManager:
    def __init__(self, main_window_instance):
        self.main_window_instance = main_window_instance
        self.system_highlight_color = None
        self.system_highlighted_text_color = None
        self.actualizar_colores_resaltado_del_sistema()
        self.is_generating = False  # Nuevo flag para controlar si hay una generación en curso

    def actualizar_colores_resaltado_del_sistema(self):
        system_palette = QPalette() 
        self.system_highlight_color = system_palette.color(QPalette.ColorRole.Highlight)
        self.system_highlighted_text_color = system_palette.color(QPalette.ColorRole.HighlightedText)

    @staticmethod
    def _crear_paleta_clara():
        light_palette = QPalette()
        light_palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ColorRole.WindowText, Qt.black)
        light_palette.setColor(QPalette.ColorRole.Base, Qt.white)
        light_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(233, 233, 233))
        light_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 220))
        light_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.black)
        light_palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(160, 160, 160))
        light_palette.setColor(QPalette.ColorRole.Text, Qt.black)
        light_palette.setColor(QPalette.ColorRole.Button, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ColorRole.ButtonText, Qt.black)
        light_palette.setColor(QPalette.ColorRole.BrightText, Qt.red)
        light_palette.setColor(QPalette.ColorRole.Link, QColor(0, 0, 255))
        light_palette.setColor(QPalette.ColorRole.Light, QColor(240, 240, 240))
        light_palette.setColor(QPalette.ColorRole.Dark, QColor(160, 160, 160))
        light_palette.setColor(QPalette.ColorRole.Mid, QColor(200, 200, 200))
        light_palette.setColor(QPalette.ColorRole.Shadow, QColor(100, 100, 100))
        light_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        light_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.white)
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(120, 120, 120))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(120, 120, 120))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(120, 120, 120))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(220, 220, 220))
        light_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, QColor(220, 220, 220))
        return light_palette

    @staticmethod
    def _crear_paleta_oscura():
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.ColorRole.Window, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.WindowText, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ColorRole.AlternateBase, QColor(45, 45, 45))
        dark_palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.ColorRole.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.Text, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.Button, QColor(50, 50, 50))
        dark_palette.setColor(QPalette.ColorRole.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.ColorRole.BrightText, Qt.red)
        dark_palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.ColorRole.HighlightedText, Qt.white)
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(127, 127, 127))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Base, QColor(30, 30, 30))
        dark_palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.AlternateBase, QColor(30, 30, 30))
        return dark_palette

    def aplicar_paleta_y_actualizar_ui(self, tema_nombre, chosen_palette):
        # Aplicar la paleta a la aplicación
        app = QApplication.instance()
        if app:
            app.setPalette(chosen_palette)
            
            # Obtener los colores de resaltado del sistema como strings hexadecimales
            highlight_color_hex = self.system_highlight_color.name()
            highlighted_text_color_hex = self.system_highlighted_text_color.name()
            
            # Aplicar estilos específicos para submenús según el tema
            if tema_nombre == "light":
                # Determinar si es Windows 10
                is_win10 = False
                if sys.platform == "win32":
                    try:
                        release, version, csd, ptype = platform.win32_ver()
                        build_number_str = version.split('.')[2] if len(version.split('.')) > 2 else version.split('.')[0]
                        build_number = int(build_number_str)
                        if build_number < 22000: # Windows 10 o anterior
                            is_win10 = True
                    except Exception:
                        pass # Fallback, no se pudo determinar, is_win10 permanece False

                # Definir el estilo base para el tema claro
                light_style = f"""
                    QMenuBar::item:selected {{ /* Cuando se pasa el cursor sobre un elemento de la barra de menú */
                        /* background-color: {highlight_color_hex}; No cambiamos el fondo */
                        /* color: {highlighted_text_color_hex}; No cambiamos el color del texto */
                        border: 1px solid #BBBBBB; /* Borde para mejorar la visibilidad */
                    }}
                    QMenu {{
                        background-color: #F0F0F0; /* Fondo general del menú claro */
                        color: black;
                        border: 1px solid #CCCCCC;
                    }}
                    QMenu::item {{
                        /* padding: top, right, bottom, left */
                        padding: 4px 20px 4px 5px; /* Espacio para consistencia y futuro indicador */
                        background-color: transparent; /* Items sin fondo por defecto */
                    }}
                    QMenu::item:selected {{ /* Para el hover del ratón o selección con teclado */
                        background-color: {highlight_color_hex}; /* Fondo con color de resaltado del sistema */
                        color: {highlighted_text_color_hex}; /* Texto con color de resaltado del sistema */
                    }}
                    QMenu::item:checked {{ /* Para el item que está marcado/activo */
                        background-color: #DCDCDC; /* Un gris claro, ligeramente más oscuro que el fondo del menú */
                        font-weight: bold; /* Texto en negrita */
                        color: black; /* Texto negro para contraste */
                    }}
                    QPushButton {{
                        border: 1px solid #AAAAAA;
                        border-radius: 2px;
                        padding: 3px;
                        background-color: #E8E8E8;
                    }}
                    QPushButton:hover {{
                        background-color: #E5E5E5;
                    }}
                    QPushButton:pressed {{
                        background-color: #D0D0D0;
                    }}
                    QPushButton:disabled {{
                        color: #555555;
                        background-color: #F2F2F2;
                        border: 1px solid #CCCCCC;
                    }}
                    
                    /* Estilo específico para botones en diálogos */
                    QDialog QPushButton {{
                        min-width: 100px;
                        padding: 5px 15px;
                        margin: 2px 5px;
                    }}
                    
                    /* Estilo para QMessageBox que muestra diálogos de alerta/confirmación */
                    QMessageBox QPushButton {{
                        min-width: 100px;
                        padding: 5px 15px;
                        margin: 2px 5px;
                    }}
                    
                    /* Estilo para los botones estándar en diálogos (Aceptar, Cancelar, etc.) */
                    QDialogButtonBox QPushButton {{
                        min-width: 100px;
                        padding: 5px 15px;
                        margin: 2px 5px;
                    }}
                    
                    /* Estilo para QFileDialog */
                    QFileDialog QPushButton {{
                        min-width: 90px;
                    }}
                    
                    /* Estilo para botones por defecto en diálogos - Tema claro */
                    QPushButton:default {{
                        border: 2px solid #FF6E00;  /* Borde naranja para los botones por defecto */
                        font-weight: bold;          /* Texto en negrita */
                        background-color: #FFE6CC;  /* Fondo ligeramente naranja */
                    }}
                    
                    /* Estilo para el hover en botones por defecto */
                    QPushButton:default:hover {{
                        background-color: #FFD6AA;  /* Un tono más intenso al pasar el ratón */
                    }}
                    
                    /* Estilo para cuando se pulsa un botón por defecto */
                    QPushButton:default:pressed {{
                        background-color: #FFBF80;  /* Aún más intenso al pulsar */
                    }}
                """

                # Estilos para QProgressBar según el sistema operativo y estado
                # Aplicar estilos para todas las versiones de Windows
                light_style += f"""
                QProgressBar {{
                    border: 1px solid #AAAAAA;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #F0F0F0;
                    height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: {highlight_color_hex}; /* Usar el color de resaltado del sistema */
                }}
                """
                
                # Añadir el estilo de checkbox según si hay generación o no
                if self.is_generating:
                    # Estilo para checkboxes durante la generación (aspecto desactivado)
                    light_style += """
                    QCheckBox::indicator {
                        width: 15px;
                        height: 15px;
                        border: 1px solid #BBBBBB; /* Borde más claro */
                        border-radius: 2px;
                        background-color: #F2F2F2; /* Fondo más claro */
                    }
                    QCheckBox::indicator:checked {
                        background-color: #C0C0C0; /* Color gris claro en lugar del color de resaltado */
                        border: 1px solid #BBBBBB;
                        image: url(iconos/tick.png);
                    }
                    QCheckBox::indicator:hover {
                        border: 1px solid #BBBBBB; /* Sin efecto hover */
                    }
                    """
                else: # No se está generando
                    if is_win10:
                        # Para Windows 10 con tema claro, no aplicar estilo personalizado de QCheckBox::indicator
                        # para usar los checkboxes predeterminados del sistema.
                        pass # No se añade nada a light_style para los checkboxes
                    else:
                        # Estilo normal para checkboxes en otros SO o Win11+ con tema claro
                        light_style += f"""
                        QCheckBox::indicator {{
                            width: 15px;
                            height: 15px;
                            border: 1px solid #888888;
                            border-radius: 2px;
                            background-color: white;
                        }}
                        QCheckBox::indicator:checked {{
                            background-color: {highlight_color_hex}; /* Usar color de resaltado del sistema */
                            border: 1px solid #555555;
                            image: url(iconos/tick.png);
                        }}
                        QCheckBox::indicator:hover {{
                            border: 1px solid #555555;
                        }}
                        """
                
                # Aplicar el estilo completo
                app.setStyleSheet(light_style)
            elif tema_nombre == "dark":
                # También aplicar la misma lógica para el tema oscuro
                is_win10 = False
                if sys.platform == "win32":
                    try:
                        release, version, csd, ptype = platform.win32_ver()
                        build_number_str = version.split('.')[2] if len(version.split('.')) > 2 else version.split('.')[0]
                        build_number = int(build_number_str)
                        if build_number < 22000: # Windows 10 o anterior
                            is_win10 = True
                    except Exception:
                        pass # Fallback, no se pudo determinar, is_win10 permanece False
                
                dark_style = f"""
                    QMenu {{
                        background-color: #333333;
                        color: white;
                        border: 1px solid #555555;
                    }}
                    QMenu::item {{
                        padding: 4px 20px 4px 5px;
                        background-color: transparent;
                    }}
                    QMenu::item:selected {{
                        background-color: {highlight_color_hex}; /* Fondo con color de resaltado del sistema */
                        color: {highlighted_text_color_hex}; /* Texto con color de resaltado del sistema */
                    }}
                    QMenu::item:checked {{
                        background-color: #4A4A4A;
                        font-weight: bold;
                        color: white;
                    }}
                    
                    /* Estilo de botones para el tema oscuro */
                    QPushButton {{
                        border: 1px solid #666666;
                        border-radius: 2px;
                        padding: 3px;
                        background-color: #444444;
                        color: white;
                    }}
                    QPushButton:hover {{
                        background-color: #505050;
                    }}
                    QPushButton:pressed {{
                        background-color: #353535;
                    }}
                    QPushButton:disabled {{
                        color: #888888;
                        background-color: #333333;
                        border: 1px solid #555555;
                    }}
                    
                    /* Estilo específico para botones en diálogos */
                    QDialog QPushButton {{
                        min-width: 100px;
                        padding: 5px 15px;
                        margin: 2px 5px;
                    }}
                    
                    /* Estilo para QMessageBox */
                    QMessageBox QPushButton {{
                        min-width: 100px;
                        padding: 5px 15px;
                        margin: 2px 5px;
                    }}
                    
                    /* Estilo para los botones estándar en diálogos */
                    QDialogButtonBox QPushButton {{
                        min-width: 100px;
                        padding: 5px 15px;
                        margin: 2px 5px;
                    }}
                    
                    /* Estilo para QFileDialog */
                    QFileDialog QPushButton {{
                        min-width: 90px;
                    }}
                    
                    /* Estilo para botones por defecto en diálogos - Tema oscuro */
                    QPushButton:default {{
                        border: 2px solid #FF6E00;  /* Borde naranja para los botones por defecto */
                        font-weight: bold;          /* Texto en negrita */
                        background-color: #553019;  /* Fondo oscuro con tinte naranja */
                        color: #FFFFFF;             /* Texto blanco para mejor contraste */
                    }}
                    
                    /* Estilo para el hover en botones por defecto */
                    QPushButton:default:hover {{
                        background-color: #6B3D1F;  /* Un tono más claro al pasar el ratón */
                    }}
                    
                    /* Estilo para cuando se pulsa un botón por defecto */
                    QPushButton:default:pressed {{
                        background-color: #432712;  /* Más oscuro al pulsar */
                    }}
                """
                
                # Aplicar estilos para QProgressBar en tema oscuro para todas las versiones de Windows
                dark_style += f"""
                QProgressBar {{
                    border: 1px solid #555555;
                    border-radius: 4px;
                    text-align: center;
                    background-color: #303030;
                    color: white;
                    height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: {highlight_color_hex}; /* Usar color de resaltado del sistema */
                }}
                """
                
                app.setStyleSheet(dark_style)

        # Actualizar la interfaz de la ventana principal
        if self.main_window_instance:
            self.main_window_instance.update()
            
            # Actualizar también los menús específicamente
            if hasattr(self.main_window_instance, 'menuBar'):
                menu_bar = self.main_window_instance.menuBar()
                if menu_bar:
                    menu_bar.update()

    def gestionar_tema_aplicacion(self, tema_nombre): # Se elimina guardar_preferencia
        """Gestiona y aplica el tema de la aplicación (claro, oscuro)."""
        # print(f"Gestionando tema: {tema_nombre}")
        
        if tema_nombre == "dark":
            palette = self._crear_paleta_oscura()
            self.aplicar_paleta_y_actualizar_ui("dark", palette)
        elif tema_nombre == "light":
            palette = self._crear_paleta_clara()
            self.aplicar_paleta_y_actualizar_ui("light", palette)
        else: # Por defecto o si es 'system' (aunque no lo usaremos para auto-detección ahora)
            # Podríamos optar por un tema por defecto (ej. claro) si tema_nombre es None o inválido
            # print(f"Tema '{tema_nombre}' no reconocido o no especificado, aplicando claro por defecto.")
            palette = self._crear_paleta_clara()
            self.aplicar_paleta_y_actualizar_ui("light", palette)

        # Actualizar el borde de la vista previa en el widget principal si existe
        if self.main_window_instance and hasattr(self.main_window_instance, 'widget'):
            widget = self.main_window_instance.widget
            if widget and hasattr(widget, 'vista_previa') and widget.vista_previa:
                # Actualizar el borde según el tema
                widget.vista_previa.actualizar_borde_tema(tema_nombre)

    # Nuevos métodos para cambiar el aspecto durante la generación
    def set_generating_state(self, is_generating):
        """Establece el estado de generación y actualiza los estilos."""
        self.is_generating = is_generating
        
        # Obtener el tema actual para volver a aplicarlo con los nuevos estilos
        current_theme = "light"  # Por defecto asumimos tema claro
        
        # Intentar detectar el tema actual desde la ventana principal
        if self.main_window_instance and hasattr(self.main_window_instance, 'current_app_theme'):
            theme_preference = self.main_window_instance.current_app_theme
            if theme_preference == 'dark':
                current_theme = "dark"
            elif theme_preference == 'system':
                # Si es 'system', verificar el tema actual del sistema
                color_scheme = QGuiApplication.styleHints().colorScheme()
                if color_scheme == Qt.ColorScheme.Dark:
                    current_theme = "dark"
        
        # Re-aplicar el tema con el nuevo estado de generación
        if current_theme == "dark":
            palette = self._crear_paleta_oscura()
        else:
            palette = self._crear_paleta_clara()
        
        self.aplicar_paleta_y_actualizar_ui(current_theme, palette)