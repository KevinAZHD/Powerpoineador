import sys
import os
import requests
import subprocess
import shutil
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
            # Asegurarse que el directorio de guardado existe
            os.makedirs(os.path.dirname(self.save_path), exist_ok=True)
            
            response = requests.get(self.download_url, stream=True, timeout=60) # Timeout aumentado
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            bytes_downloaded = 0
            
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._is_cancelled:
                        self.finished.emit(self.save_path, "Descarga cancelada por el usuario.")
                        # No eliminar el archivo aquí, podría estar en uso o dar error. El batch lo manejará si es necesario.
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
            # Emitir save_path como None porque el archivo podría no haberse creado o estar incompleto
            self.finished.emit(None, f"Error de escritura al guardar el archivo: {str(e)}")
        except Exception as e:
            self.finished.emit(None, f"Error inesperado durante la descarga: {str(e)}")

    def cancel(self):
        self._is_cancelled = True

def _crear_y_ejecutar_batch_actualizador(downloaded_temp_exe_path, app_instance, parent_window, traduccion_func, current_lang, app_data_dir):
    global _progress_dialog
    try:
        # Cerrar el diálogo de progreso si aún está abierto
        if _progress_dialog and _progress_dialog.isVisible():
            _progress_dialog.close()

        is_frozen = getattr(sys, 'frozen', False)
        
        if is_frozen:
            current_exe_full_path = sys.executable
            current_exe_dir = os.path.dirname(current_exe_full_path)
            nombre_exe_a_reemplazar = os.path.basename(current_exe_full_path)
        else:
            current_exe_dir = os.path.dirname(os.path.abspath(__file__))
            nombre_exe_a_reemplazar = "Powerpoineador.exe" # Nombre por defecto si no está congelado
            current_exe_full_path = os.path.join(current_exe_dir, nombre_exe_a_reemplazar)
        
        batch_path = os.path.join(app_data_dir, "updater.bat")
        os.makedirs(app_data_dir, exist_ok=True)
        
        # Obtenemos el directorio base de la descarga temporal para pasarlo al batch
        temp_download_base_dir_for_batch = os.path.dirname(downloaded_temp_exe_path)

        batch_content = f"""@echo off
chcp 65001 > nul
echo {traduccion_func('update_starting', current_lang)}
echo.

set "EXE_A_REEMPLAZAR={current_exe_full_path}"
set "NOMBRE_EXE_BASE={nombre_exe_a_reemplazar}"
set "EXE_NUEVO_TEMPORAL={downloaded_temp_exe_path}"
set "DIR_EXE={current_exe_dir}"
set "TEMP_DOWNLOAD_DIR_BATCH={temp_download_base_dir_for_batch}"

echo {traduccion_func('update_closing_app', current_lang)}
taskkill /F /IM "%NOMBRE_EXE_BASE%" > nul 2>&1
timeout /t 3 /nobreak > nul

set INTENTOS=0
:LOOP_CIERRE
set /a INTENTOS+=1
if %INTENTOS% gtr 5 (
    echo {traduccion_func('update_close_failed_critical', current_lang)}
    goto CLEANUP_ERROR_AND_TEMP
)
tasklist /FI "IMAGENAME eq %NOMBRE_EXE_BASE%" 2>nul | find /i "%NOMBRE_EXE_BASE%" >nul
if not errorlevel 1 (
    echo {traduccion_func('update_waiting_close_retry', current_lang)} [%INTENTOS%/5]
    taskkill /F /IM "%NOMBRE_EXE_BASE%" > nul 2>&1
    timeout /t 2 /nobreak > nul
    goto LOOP_CIERRE
)
echo {traduccion_func('update_app_closed', current_lang)}
echo.

if not exist "%EXE_NUEVO_TEMPORAL%" (
    echo {traduccion_func('update_new_file_not_found_error', current_lang).format(file="%EXE_NUEVO_TEMPORAL%")}
    pause
    goto END_BATCH_NO_TEMP_CLEANUP
)
echo {traduccion_func('update_replacing_files', current_lang)}

if exist "%EXE_A_REEMPLAZAR%" (
    echo {traduccion_func('update_deleting_old_version', current_lang).format(file="%NOMBRE_EXE_BASE%")}
    del /F /Q "%EXE_A_REEMPLAZAR%"
    timeout /t 1 /nobreak > nul
    if exist "%EXE_A_REEMPLAZAR%" (
        echo {traduccion_func('update_delete_old_failed_error', current_lang).format(file="%NOMBRE_EXE_BASE%")}
    )
)

echo {traduccion_func('update_copying_new_version', current_lang)}
copy /Y "%EXE_NUEVO_TEMPORAL%" "%EXE_A_REEMPLAZAR%"
if errorlevel 1 (
    echo {traduccion_func('update_copy_failed_error', current_lang)}
    echo {traduccion_func('source_colon', current_lang)} "%EXE_NUEVO_TEMPORAL%"
    echo {traduccion_func('destination_colon', current_lang)} "%EXE_A_REEMPLAZAR%"
    pause
    goto CLEANUP_ERROR_AND_TEMP
)

if not exist "%EXE_A_REEMPLAZAR%" (
    echo {traduccion_func('update_copy_verify_failed_error', current_lang).format(file="%NOMBRE_EXE_BASE%")}
    pause
    goto CLEANUP_ERROR_AND_TEMP
)

echo {traduccion_func('update_completed_successfully', current_lang)}
echo {traduccion_func('update_starting_new_version', current_lang).format(file="%NOMBRE_EXE_BASE%")}
cd /D "%DIR_EXE%"
start "" "%EXE_A_REEMPLAZAR%"
if errorlevel 1 (
    echo {traduccion_func('update_start_new_failed_error', current_lang).format(file="%NOMBRE_EXE_BASE%")}
    pause
)

:CLEANUP_ERROR_AND_TEMP
if exist "%EXE_NUEVO_TEMPORAL%" (
    echo {traduccion_func('update_cleaning_temp_files', current_lang)}
    del /F /Q "%EXE_NUEVO_TEMPORAL%"
)
if exist "%TEMP_DOWNLOAD_DIR_BATCH%" (
    echo {traduccion_func('update_cleaning_temp_folder', current_lang)}
    rd /s /q "%TEMP_DOWNLOAD_DIR_BATCH%"
)

:END_BATCH_NO_TEMP_CLEANUP
echo {traduccion_func('update_deleting_batch', current_lang)}
(goto) 2>nul & del "%~f0"
"""
        with open(batch_path, "w", encoding="utf-8") as f:
            f.write(batch_content)
        
        subprocess.Popen([batch_path], creationflags=0x08000000, cwd=app_data_dir) # CREATE_NO_WINDOW
        
        QTimer.singleShot(1000, app_instance.quit) # Dar tiempo para que el batch se inicie

    except Exception as e:
        QMessageBox.critical(parent_window, 
                             traduccion_func('update_script_error_title', current_lang), 
                             f"{traduccion_func('update_script_error_message', current_lang)}: {str(e)}")
        # Intentar limpiar el archivo temporal si la creación del batch falla y el archivo existe
        if os.path.exists(downloaded_temp_exe_path):
            try:
                os.remove(downloaded_temp_exe_path)
            except OSError:
                pass # No hacer nada si no se puede eliminar

def iniciar_actualizacion_automatica(ultima_version_tag, parent_window, app_instance, traduccion_func, current_lang, url_exe, app_data_dir):
    global _progress_dialog, _download_thread

    if not url_exe:
        QMessageBox.critical(parent_window, 
                             traduccion_func('error_title', current_lang), 
                             traduccion_func('update_url_error_message', current_lang))
        return

    temp_download_base_dir = os.path.join(app_data_dir, "temp_download_Powerpoineador")
    try:
        os.makedirs(temp_download_base_dir, exist_ok=True)
    except OSError as e:
        QMessageBox.critical(parent_window,
                             traduccion_func('error_title', current_lang),
                             f"{traduccion_func('create_temp_dir_error', current_lang)}: {str(e)}") # Nueva key: 'create_temp_dir_error'
        return

    safe_version_tag = "".join(c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in ultima_version_tag)
    temp_download_filename = f"Powerpoineador_new_{safe_version_tag}.exe"
    save_path = os.path.join(temp_download_base_dir, temp_download_filename)

    _progress_dialog = QProgressDialog(
        traduccion_func('downloading_update_message', current_lang), 
        traduccion_func('cancel', current_lang), 0, 100, parent_window
    )
    _progress_dialog.setWindowTitle(traduccion_func('downloading_update_title', current_lang))
    _progress_dialog.setWindowModality(Qt.WindowModal)
    _progress_dialog.setAutoClose(False) 
    _progress_dialog.setAutoReset(False)
    _progress_dialog.setMinimumWidth(450)

    _download_thread = DownloadThread(url_exe, save_path)
    _download_thread.progress.connect(_progress_dialog.setValue)
    
    def on_download_finished(downloaded_file_path, error_message):
        global _progress_dialog
        
        if _progress_dialog and not _progress_dialog.wasCanceled() and _progress_dialog.value() < 100 and not error_message:
             _progress_dialog.setValue(100)

        if _progress_dialog and _progress_dialog.isVisible():
             _progress_dialog.close()


        if error_message:
            if error_message != "Descarga cancelada por el usuario.":
                 QMessageBox.critical(parent_window, 
                                     traduccion_func('download_error_title', current_lang), 
                                     error_message)
            # Intentar eliminar el archivo temporal y su carpeta en caso de error o cancelación.
            if os.path.exists(temp_download_base_dir): # temp_download_base_dir es del scope de iniciar_actualizacion_automatica
                try:
                    shutil.rmtree(temp_download_base_dir) # Eliminar toda la carpeta
                    print(f"Directorio de descarga temporal {temp_download_base_dir} eliminado tras error/cancelación.")
                except Exception as e_shutil:
                    print(f"Error al eliminar el directorio de descarga temporal {temp_download_base_dir}: {e_shutil}")
            return

        if downloaded_file_path and not error_message:
            _crear_y_ejecutar_batch_actualizador(downloaded_file_path, app_instance, parent_window, traduccion_func, current_lang, app_data_dir)
    
    _download_thread.finished.connect(on_download_finished)
    
    def on_dialog_canceled():
        global _download_thread
        if _download_thread and _download_thread.isRunning():
            _download_thread.cancel()

    _progress_dialog.canceled.connect(on_dialog_canceled)
    
    def handle_dialog_rejection(result_code):
        global _download_thread, _progress_dialog
        if result_code == QDialog.Rejected: # 0
            if _progress_dialog and not _progress_dialog.wasCanceled():
                if _download_thread and _download_thread.isRunning():
                    _download_thread.cancel()

    _progress_dialog.finished[int].connect(handle_dialog_rejection)

    _download_thread.start()
    _progress_dialog.setValue(0)
    _progress_dialog.exec()
