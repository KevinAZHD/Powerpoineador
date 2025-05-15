import requests, os, time
from PIL import Image
from io import BytesIO
from Traducciones import obtener_traduccion

# Función para generar una imagen basada en la sección, contenido y descripción del usuario
def generar_imagen(section, content, nuevo_string, signals=None):
    # Obtener el idioma actual
    current_language = 'es'
    if signals and hasattr(signals, 'current_language'):
        current_language = signals.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'current_language'):
        current_language = signals.parent.current_language
    elif signals and hasattr(signals, 'parent') and hasattr(signals.parent, 'parent') and hasattr(signals.parent.parent, 'current_language'):
        current_language = signals.parent.parent.current_language
    
    # Definir los encabezados para la solicitud HTTP
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
    }
    
    # Definir los datos para la solicitud HTTP
    data = {
        "model": "grok-2-image-1212",
        "prompt": f"a photo in the context of the PowerPoint of {content} {section}",
        "n": 1,
        "response_format": "url"
    }
    
    max_retries = 10
    retry_delay = 5
    retries = 0

    while retries < max_retries:
        try:
            # Realizar la solicitud HTTP
            response = requests.post(
                "https://api.x.ai/v1/images/generations",
                headers=headers,
                json=data,
                timeout=30 # Add a timeout to the request itself
            )
            
            # Verificar si la solicitud fue exitosa
            if response.status_code == 200:
                # Obtener la URL de la imagen generada
                image_url = response.json()['data'][0]['url']
                
                # Realizar una solicitud HTTP para obtener la imagen
                img_response = requests.get(image_url, timeout=30) # Add timeout here too
                img_response.raise_for_status() # Check image download success
                
                # Abrir la imagen generada en formato PIL
                img = Image.open(BytesIO(img_response.content))
                
                return img # Return the successful image

            # Check for the specific timeout error
            elif response.status_code == 400 and "Timeout expired" in response.text:
                retries += 1
                error_msg = f"Error 400 (Timeout): {response.text}"
                print(error_msg)
                if signals:
                    retry_msg = obtener_traduccion('retry_image_generation', current_language).format(
                        attempt=retries,
                        max_attempts=max_retries,
                        delay=retry_delay
                    )
                    signals.update_log.emit(retry_msg)

                if retries < max_retries:
                    time.sleep(retry_delay)
                    continue # Go to the next iteration
                else:
                    # Max retries reached for timeout
                    final_error_msg = obtener_traduccion('max_retries_reached', current_language).format(error=error_msg)
                    if signals:
                        signals.update_log.emit(final_error_msg)
                    raise Exception(final_error_msg)
            else:
                # Handle other non-200 status codes immediately
                error_msg = f"Error: {response.status_code}\nResponse: {response.text}"
                print(error_msg)
                if signals:
                    signals.update_log.emit(obtener_traduccion('error_generacion_imagen', current_language).format(error=error_msg))
                raise Exception(error_msg)

        except requests.exceptions.Timeout as timeout_err:
            retries += 1
            error_message = f"Request Timeout: {str(timeout_err)}"
            print(error_message)
            if signals:
                retry_msg = obtener_traduccion('retry_image_generation', current_language).format(
                    attempt=retries,
                    max_attempts=max_retries,
                    delay=retry_delay
                ) + f" ({obtener_traduccion('request_timeout', current_language)})"
                signals.update_log.emit(retry_msg)

            if retries < max_retries:
                time.sleep(retry_delay)
                continue # Go to the next iteration
            else:
                final_error_msg = obtener_traduccion('max_retries_reached', current_language).format(error=error_message)
                if signals:
                    signals.update_log.emit(final_error_msg)
                raise Exception(final_error_msg) from timeout_err

        except requests.exceptions.RequestException as req_err:
            # Handle other potential request errors (connection, etc.)
            retries += 1
            error_message = f"Request Exception: {str(req_err)}"
            print(error_message)
            if signals:
                 retry_msg = obtener_traduccion('retry_image_generation', current_language).format(
                    attempt=retries,
                    max_attempts=max_retries,
                    delay=retry_delay
                ) + f" ({obtener_traduccion('connection_error_details', current_language)}: {str(req_err)})"
                 signals.update_log.emit(retry_msg)

            if retries < max_retries:
                time.sleep(retry_delay)
                continue # Go to the next iteration
            else:
                final_error_msg = obtener_traduccion('max_retries_reached', current_language).format(error=error_message)
                if signals:
                    signals.update_log.emit(final_error_msg)
                raise Exception(final_error_msg) from req_err

        except Exception as e:
            # Catch any other unexpected errors during the process
            error_message = str(e)
            print(obtener_traduccion('error_generacion_imagen', current_language).format(error=error_message))
            if signals:
                signals.update_log.emit(obtener_traduccion('error_generacion_imagen', current_language).format(error=error_message))
            raise # Re-raise the caught exception

    # This part should theoretically not be reached if exceptions are raised correctly
    # but serves as a fallback.
    final_fallback_error = obtener_traduccion('error_generacion_imagen_unknown', current_language)
    if signals:
        signals.update_log.emit(final_fallback_error)
    raise Exception(final_fallback_error)