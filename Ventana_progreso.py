import sys, os
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QProgressBar, QMessageBox, QApplication, QHBoxLayout, QGridLayout
from PySide6.QtCore import Qt, Signal, QObject, QThread, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QIcon
from Vista_previa import VentanaVistaPrevia

# Función para manejar rutas de recursos tanto en modo desarrollo como en modo ejecutable
def resource_path(relative_path):
    try:
        # Intenta obtener la ruta base del ejecutable empaquetado
        base_path = sys._MEIPASS
    except Exception:
        # Si no está empaquetado, usa la ruta actual del proyecto
        base_path = os.path.abspath(".")
    
    # Combina la ruta base con la ruta relativa del recurso
    return os.path.join(base_path, relative_path)

# Clase para manejar las señales de la ventana de log
class LogSignals(QObject):
    # Señal para actualizar el texto del log
    update_log = Signal(str)
    # Señal para indicar que el proceso terminó
    finished = Signal()
    # Señal para manejar errores
    error = Signal(str)
    # Señal para indicar que se cerró la ventana
    closed = Signal()
    # Señal para actualizar la barra de progreso
    update_progress = Signal(int, int)
    # Señal para agregar una nueva diapositiva
    nueva_diapositiva = Signal(str, str, str)

# Clase worker para ejecutar la generación en un hilo separado
class GenerationWorker(QThread):
    def __init__(self, modelo_texto, modelo_imagen, descripcion, auto_open, imagen_personalizada, filename, signals):
        super().__init__()
        # Inicialización de variables necesarias para la generación
        self.modelo_texto = modelo_texto
        self.modelo_imagen = modelo_imagen
        self.descripcion = descripcion
        self.auto_open = auto_open
        self.imagen_personalizada = imagen_personalizada
        self.filename = filename
        self.signals = signals

    # Función para ejecutar la generación de la presentación
    def run(self):
        try:
            # Importa e inicia la generación de la presentación
            from Logica_diapositivas import generar_presentacion
            generar_presentacion(
                self.modelo_texto,
                self.modelo_imagen,
                self.descripcion,
                self.auto_open,
                self.imagen_personalizada,
                self.filename,
                self.signals
            )
        except Exception as e:
            # Emite señal de error si algo falla
            self.signals.error.emit(str(e))

# Clase principal de la ventana de log
class LogWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent
        # Configuración inicial de la ventana
        self.setWindowTitle('Generando PowerPoint...')
        self.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
        self.setMinimumSize(1200, 600)
        self.setWindowModality(Qt.ApplicationModal)
        self.generation_completed = False
        
        # Crear layout de cuadrícula para mejor alineación
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # Crear widget para el panel izquierdo con el log
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Área de texto para el log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        left_layout.addWidget(self.log_text)
        
        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setRange(0, 0)
        left_layout.addWidget(self.progress_bar)
        
        # Configuración del timer para la animación inicial
        self.loading_timer = QTimer()
        self.loading_timer.timeout.connect(self.update_loading_animation)
        self.loading_timer.start(50)
        
        # Agregar panel izquierdo y vista previa al grid
        grid_layout.addWidget(left_widget, 0, 0)
        
        # Crear vista previa
        self.vista_previa = VentanaVistaPrevia()
        grid_layout.addWidget(self.vista_previa, 0, 1)
        
        # Establecer proporciones de columna
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        
        self.setLayout(grid_layout)
        
        # Configuración de señales
        self.signals = LogSignals()
        self.signals.update_log.connect(self.update_log)
        self.signals.finished.connect(self.generation_finished)
        self.signals.error.connect(self.show_error)
        self.signals.closed.connect(self.on_window_closed)
        self.signals.update_progress.connect(self.update_progress)
        self.signals.nueva_diapositiva.connect(self.agregar_diapositiva)
        
        # Variables de control
        self.closed_by_user = False
        self.worker = None
        
        # Centrar la ventana en la pantalla
        self.center_window()
        
        # Contadores para el progreso
        self.total_images = 0
        self.current_image = 0
        
        # Iniciar el contador de imágenes totales
        self.total_images = 0
    
    # Función para centrar la ventana en la pantalla independientemente del padre
    def center_window(self):
        # Calcular el tamaño de la ventana
        self.adjustSize()
        
        # Obtener la geometría de la pantalla principal
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Calcular las coordenadas para centrar la ventana
        x = screen.center().x() - self.width() // 2
        y = screen.center().y() - self.height() // 2
        
        # Mover la ventana al centro de la pantalla
        self.move(x, y)

    # Función para mostrar errores
    def show_error(self, error_msg):
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.critical(self, 'Error', f'Error al generar la presentación: {error_msg}')
        self.close()

    # Función para iniciar la generación
    def start_generation(self, modelo_texto, modelo_imagen, descripcion, auto_open, imagen_personalizada, filename):
        self.worker = GenerationWorker(
            modelo_texto, modelo_imagen, descripcion, 
            auto_open, imagen_personalizada, filename, 
            self.signals
        )
        self.worker.start()
    
    # Función para actualizar el log
    def update_log(self, text):
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
        
        # Detectar cuando comienza la generación de imágenes y obtener el total
        if "Generando imagen 1/" in text:
            self.loading_timer.stop()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            # Extraer el número total de imágenes
            try:
                total_images = int(text.split('/')[-1].split()[0])
                self.total_images = total_images
            except:
                self.total_images = 1
    
    # Función llamada cuando termina la generación
    def generation_finished(self):
        self.loading_timer.stop()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.log_text.append("\n¡Presentación generada exitosamente!")
        self.generation_completed = True
        
        filename = self.worker.filename if self.worker else None
        auto_open = self.worker.auto_open if self.worker else False
        
        # Registrar los costos solo cuando la presentación se ha generado exitosamente
        if hasattr(self.parent, 'widget') and self.parent.widget:
            self.parent.widget.registrar_costos_finales()
        
        # Limpieza del worker
        if self.worker:
            self.worker.quit()
            self.worker.wait()
            self.worker = None
        
        try:
            if filename:
                if auto_open:
                    # Abrir el archivo automáticamente
                    os.startfile(filename)
                    self.close()
                else:
                    # Mostrar mensaje de éxito
                    nombre_archivo = filename.split('/')[-1] if '/' in filename else filename.split('\\')[-1]
                    ruta_completa = os.path.abspath(filename)
                    
                    msg = QMessageBox(self)
                    msg.setWindowTitle('Presentación lista')
                    msg.setText(f'Su presentación "{nombre_archivo}" ha sido generada correctamente en:\n{ruta_completa}')
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
                    
                    # Forzar el cálculo del tamaño del mensaje
                    msg.show()
                    msg.hide()
                    
                    # Centrar el mensaje en la ventana del log
                    msg_pos = self.geometry().center() - msg.rect().center()
                    msg.move(msg_pos)
                    
                    msg.exec()
                    
                    self.close()
        except Exception as e:
            print(f"Error en generation_finished: {str(e)}")
            QMessageBox.critical(self, 'Error', f'Error al finalizar la generación: {str(e)}')
    
    # Función para cancelar la generación
    def cancel_generation(self):
        self.loading_timer.stop()
        try:
            if self.worker and self.worker.isRunning():
                self.worker.terminate()
                self.worker.wait()
                self.log_text.append("\nGeneración cancelada por el usuario.")
                
                self.worker = None
                
                self.signals.closed.emit()
                
                # Intentar eliminar el archivo si existe
                if hasattr(self.worker, 'filename') and os.path.exists(self.worker.filename):
                    try:
                        os.remove(self.worker.filename)
                    except:
                        pass
        except Exception as e:
            print(f"Error al cancelar la generación: {str(e)}")
        finally:
            self.close()

    # Función llamada al cerrar la ventana
    def closeEvent(self, event):
        if self.worker and self.worker.isRunning() and not self.generation_completed:
            # Mostrar diálogo de confirmación
            msg = QMessageBox()
            msg.setWindowTitle('Confirmar cancelación')
            msg.setText('¿Está seguro de que desea cancelar la generación?')
            msg.setIcon(QMessageBox.Question)
            msg.setWindowIcon(QIcon(resource_path("iconos/icon.jpg")))
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg.setDefaultButton(QMessageBox.No)
            msg.button(QMessageBox.Yes).setText('Sí')
            msg.button(QMessageBox.No).setText('No')
            
            # Forzar el cálculo del tamaño del mensaje
            msg.show()
            msg.hide()
            
            # Centrar el mensaje en la ventana del log
            msg_pos = self.geometry().center() - msg.rect().center()
            msg.move(msg_pos)
            
            # Reproducir sonido de sistema
            QApplication.beep()
            
            if msg.exec() == QMessageBox.Yes:
                self.cancel_generation()
                event.accept()
            else:
                event.ignore()
        else:
            if self.worker:
                self.worker.quit()
                self.worker.wait()
                self.worker = None
            self.signals.closed.emit()
            event.accept()
            
    # Función llamada cuando se cierra la ventana
    def on_window_closed(self):
        if hasattr(self, 'parent') and self.parent:
            if hasattr(self.parent, 'widget') and self.parent.widget:
                self.parent.widget.log_window = None
    
    # Función para actualizar la barra de progreso
    def update_progress(self, current, total):
        # Detener la animación de carga inicial
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

    # Función para actualizar la animación de carga
    def update_loading_animation(self):
        if self.progress_bar.maximum() == 0:
            self.progress_bar.setValue(0)

    # Función para agregar una nueva diapositiva a la vista previa
    def agregar_diapositiva(self, imagen_path, titulo, contenido):
        self.vista_previa.agregar_diapositiva(imagen_path, titulo, contenido)