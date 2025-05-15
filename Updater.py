import sys
import os
import requests
import subprocess
# Asegúrate de que tu aplicación usa PySide6. Si es PyQt5, cambia los imports.
from PySide6.QtWidgets import QProgressDialog, QMessageBox, QDialog
from PySide6.QtCore import QThread, Signal as pyqtSignal, Qt, QTimer # Renombrado Signal a pyqtSignal para evitar conflicto si existe otra variable Signal

# Variable global para el diálogo de progreso, para poder cerrarlo desde el hilo
_progress_dialog = None
_download_thread = None

class DownloadThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str, str)  # downloaded_file_path, error_message (None si éxito)
    
    def __init__(self, download_url, save_path):
        super().__init__()
        self.download_url = download_url
        self.save_path = save_path
        self._is_cancelled = False

    def run(self):
        try:
            response = requests.get(self.download_url, stream=True, timeout=60) # Timeout aumentado
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            # Asegurarse que el directorio de guardado existe
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)

            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        self.finished.emit(self.save_path, "Descarga cancelada por el usuario.")
                        # No eliminar el archivo aquí, podría estar en uso o dar error. El batch lo manejará.
                        return
                    if chunk: # Filtrar keep-alive new chunks
                        f.write(chunk)
                        bytes_downloaded += len(chunk)
                        if total_size > 0:
                            percentage = int((bytes_downloaded / total_size) * 100)
                            self.progress.emit(percentage)
            
            if not self._is_cancelled:
                self.progress.emit(100) 
                self.finished.emit(self.save_path, None) # Éxito
        except requests.exceptions.Timeout:
            self.finished.emit(None, "Error durante la descarga: Timeout (tiempo de espera agotado).")
        except requests.exceptions.RequestException as e:
            self.finished.emit(None, f"Error de red durante la descarga: {str(e)}")
        except IOError as e:
            self.finished.emit(None, f"Error de escritura al guardar el archivo: {str(e)}")
        except Exception as e:
            self.finished.emit(None, f"Error inesperado durante la descarga: {str(e)}")

    def cancel(self):
        self._is_cancelled = True

def _crear_y_ejecutar_batch_actualizador(temp_exe_path, ultima_version_tag, app_instance, parent_window, traduccion_func, current_lang, app_data_dir):
    global _progress_dialog
    try:
        # Cerrar el diálogo de progreso si aún está abierto
        if _progress_dialog and _progress_dialog.isVisible():
            _progress_dialog.close()

        current_exe_dir = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        
        # Nombre base del ejecutable actual (el viejo que se va a reemplazar)
        # Solo tiene sentido si está congelado (compilado)
        nombre_exe_viejo = os.path.basename(sys.executable) if getattr(sys, 'frozen', False) else "Powerpoineador.exe" # Fallback por si no está congelado

        downloaded_file_basename = os.path.basename(temp_exe_path)
        nuevo_exe_nombre_base = f"Powerpoineador_{ultima_version_tag}.exe"
        
        batch_path = os.path.join(app_data_dir, "updater.bat")
        os.makedirs(app_data_dir, exist_ok=True)
        
        batch_content = f"""@echo off
chcp 65001 > nul
echo Realizando CD a {current_exe_dir}
cd /D "{current_exe_dir}"

echo {traduccion_func('waiting_old_program_close', current_lang)}
timeout /t 5 /nobreak > nul

echo Eliminando la versión anterior: {nombre_exe_viejo}
del "{nombre_exe_viejo}" 2>nul

echo {traduccion_func('renaming_new_file', current_lang)} "{downloaded_file_basename}" a "{nuevo_exe_nombre_base}"
del "{nuevo_exe_nombre_base}" 2>nul
ren "{downloaded_file_basename}" "{nuevo_exe_nombre_base}"

echo {traduccion_func('starting_new_version', current_lang)} "{nuevo_exe_nombre_base}"
if exist "{nuevo_exe_nombre_base}" (
    start "" "{nuevo_exe_nombre_base}"
) else (
    echo {traduccion_func('rename_failed_error', current_lang)}
    echo {traduccion_func('file_not_found_error', current_lang).format(file=nuevo_exe_nombre_base)}
    pause
)

REM Eliminar este script de batch de AppData
(goto) 2>nul & del "{batch_path}" 
"""
        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(batch_content)
        
        subprocess.Popen([batch_path], creationflags=0x08000000)
        
        QTimer.singleShot(500, app_instance.quit) # Cierra la aplicación actual

    except Exception as e:
        QMessageBox.critical(parent_window, 
                             traduccion_func('update_script_error_title', current_lang), 
                             f"{traduccion_func('update_script_error_message', current_lang)}: {str(e)}")
        # Intentar limpiar el archivo temporal si la creación del batch falla
        if os.path.exists(temp_exe_path):
            try:
                os.remove(temp_exe_path)
            except OSError:
                pass # No hacer nada si no se puede eliminar

def iniciar_actualizacion_automatica(ultima_version_tag, parent_window, app_instance, traduccion_func, current_lang, url_exe, app_data_dir):
    global _progress_dialog, _download_thread

    if not url_exe:
        QMessageBox.critical(parent_window, 
                             traduccion_func('error_title', current_lang), 
                             traduccion_func('update_url_error_message', current_lang)) # Nueva key
        return

    current_exe_dir_for_download = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    temp_download_name = "Powerpoineador_temp_download.exe" # Nombre temporal para la descarga
    save_path = os.path.join(current_exe_dir_for_download, temp_download_name)

    _progress_dialog = QProgressDialog(
        traduccion_func('downloading_update_message', current_lang), # Nueva key
        traduccion_func('cancel', current_lang), 0, 100, parent_window
    )
    _progress_dialog.setWindowTitle(traduccion_func('downloading_update_title', current_lang))
    _progress_dialog.setWindowModality(Qt.WindowModal)
    _progress_dialog.setAutoClose(False) 
    _progress_dialog.setAutoReset(False)
    _progress_dialog.setMinimumWidth(450) # Hacer el diálogo un poco más ancho

    _download_thread = DownloadThread(url_exe, save_path)
    _download_thread.progress.connect(_progress_dialog.setValue)
    
    def on_download_finished(downloaded_file_path, error_message):
        global _progress_dialog # Necesario para modificar la variable global
        
        if _progress_dialog and not _progress_dialog.wasCanceled() and _progress_dialog.value() < 100 and not error_message:
             _progress_dialog.setValue(100) # Asegurar que llega al 100% si todo OK

        # Cerrar el diálogo si aún está visible y no fue una cancelación manejada por el propio diálogo cerrándose
        # (por ejemplo, si la descarga termina muy rápido o con error antes de que el usuario interactúe)
        if _progress_dialog and _progress_dialog.isVisible():
             _progress_dialog.close()


        if error_message:
            # No mostrar mensaje de error si la descarga fue explícitamente cancelada por el usuario.
            if error_message != "Descarga cancelada por el usuario.":
                 QMessageBox.critical(parent_window, 
                                     traduccion_func('download_error_title', current_lang), 
                                     error_message)
            # Intentar eliminar el archivo temporal en caso de error o cancelación.
            if downloaded_file_path and os.path.exists(downloaded_file_path): 
                try:
                    os.remove(downloaded_file_path)
                except Exception as e:
                    print(f"No se pudo eliminar el archivo temporal {downloaded_file_path}: {e}")
            return

        if downloaded_file_path and not error_message:
            _crear_y_ejecutar_batch_actualizador(downloaded_file_path, ultima_version_tag, app_instance, parent_window, traduccion_func, current_lang, app_data_dir)
    
    _download_thread.finished.connect(on_download_finished)
    
    def on_dialog_canceled():
        global _download_thread
        if _download_thread and _download_thread.isRunning():
            _download_thread.cancel()

    _progress_dialog.canceled.connect(on_dialog_canceled)
    
    # Manejar cierre del diálogo por 'X' o Esc
    def handle_dialog_rejection(result_code):
        global _download_thread, _progress_dialog
        # result_code es QDialog.Accepted o QDialog.Rejected (0)
        # Esta función se llama cuando exec() termina.
        if result_code == QDialog.Rejected:
            # Si el diálogo fue rechazado (ej. por 'X' o Esc) y no fue
            # a través del botón "Cancelar" (que ya establece wasCanceled a True).
            if _progress_dialog and not _progress_dialog.wasCanceled():
                if _download_thread and _download_thread.isRunning():
                    _download_thread.cancel() # Cancelar la descarga

    _progress_dialog.finished[int].connect(handle_dialog_rejection)

    _download_thread.start()
    _progress_dialog.setValue(0)
    _progress_dialog.exec()
