import os
import concurrent.futures
import replicate
import requests
import time
from PIL import Image
from io import BytesIO
from deep_translator import GoogleTranslator

def test_model_availability(modelo, tipo="texto", signals=None):
    """
    Función que realiza una llamada de prueba a un modelo para verificar su disponibilidad
    y evitar errores de timeout en la generación paralela.
    
    Args:
        modelo (str): Modelo de IA a probar.
        tipo (str): Tipo de modelo ("texto" o "imagen").
        signals: Señales para actualizar la interfaz gráfica.
        
    Returns:
        bool: True si el modelo está disponible, False en caso contrario.
    """
    def log_message(msg):
        print(msg)
        if signals:
            signals.update_log.emit(str(msg))
    
    log_message(f"Verificando disponibilidad del modelo: {modelo}")
    
    try:
        if tipo == "texto":
            # Prueba sencilla de modelos de texto
            prompt = "Genera una palabra."
            
            if "claude-3.7-sonnet" in modelo:
                # Basado en IA_sonnet_3_7.py
                replicate.run(
                    "anthropic/claude-3.7-sonnet",
                    input={
                        "prompt": prompt,
                        "max_tokens": 10,
                        "system_prompt": "Responde de forma breve.",
                        "max_image_resolution": 0.5
                    }
                )
            elif "claude-3.5-sonnet" in modelo:
                # Basado en IA_sonnet_3_5.py
                replicate.run(
                    "anthropic/claude-3.5-sonnet",
                    input={
                        "prompt": prompt,
                        "max_tokens": 10,
                        "system_prompt": "Responde de forma breve.",
                        "max_image_resolution": 0.5
                    }
                )
            elif "haiku" in modelo:
                # Basado en IA_haiku.py
                replicate.run(
                    "anthropic/claude-3.5-haiku",
                    input={
                        "prompt": prompt,
                        "max_tokens": 10,
                        "system_prompt": "Responde de forma breve."
                    }
                )
            elif "deepseek-r1" in modelo:
                # Basado en IA_deepseek.py
                replicate.run(
                    "deepseek-ai/deepseek-r1",
                    input={
                        "prompt": prompt,
                        "max_tokens": 10,
                        "system_prompt": "Responde de forma breve.",
                        "top_p": 1,
                        "temperature": 0.1,
                        "presence_penalty": 0,
                        "frequency_penalty": 0
                    }
                )
            elif "dolphin" in modelo:
                # Basado en IA_dolphin.py
                replicate.run(
                    "mikeei/dolphin-2.9-llama3-70b-gguf:7cd1882cb3ea90756d09decf4bc8a259353354703f8f385ce588b71f7946f0aa",
                    input={
                        "prompt": prompt,
                        "max_new_tokens": 10,
                        "system_prompt": "Responde de forma breve.",
                        "temperature": 0.6,
                        "repeat_penalty": 1.1,
                        "prompt_template": "<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
                    }
                )
            elif "grok" in modelo:
                # Basado en IA_grok_2.py
                if not os.environ.get('GROK_API_KEY'):
                    log_message("Error: GROK_API_KEY no está configurada en el entorno")
                    return False
                    
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
                }
                
                data = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Responde de forma breve."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "model": "grok-2-1212",
                    "stream": False,
                    "temperature": 0.6,
                    "max_tokens": 10
                }
                
                response = requests.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    log_message(f"Error al verificar Grok: {response.status_code}")
                    return False
            else:  # Modelo por defecto (meta-llama o similar)
                # Basado en IA_llama.py
                replicate.run(
                    "meta/meta-llama-3.1-405b-instruct",
                    input={
                        "prompt": prompt,
                        "max_tokens": 10,
                        "system_prompt": "Responde de forma breve.",
                        "top_k": 50,
                        "top_p": 0.9,
                        "temperature": 0.6,
                        "presence_penalty": 0,
                        "frequency_penalty": 0
                    }
                )
        
        elif tipo == "imagen":
            # Prueba sencilla de modelos de imagen
            prompt = "a simple circle"
            
            if 'sdxl-lightning-4step' in modelo:
                # Basado en IA_sdxl.py
                replicate.run(
                    "bytedance/sdxl-lightning-4step:727e49a643e999d602a896c774a0658ffefea21465756a6ce24b7ea4165eba6a",
                    input={
                        "prompt": prompt,
                        "width": 512,
                        "height": 512,
                        "num_inference_steps": 4,
                        "scheduler": "K_EULER",
                        "guidance_scale": 0,
                        "negative_prompt": "worst quality, low quality",
                        "disable_safety_checker": True
                    }
                )
            elif 'flux-schnell' in modelo:
                # Basado en IA_fluxschnell.py
                replicate.run(
                    "black-forest-labs/flux-schnell",
                    input={
                        "prompt": prompt,
                        "go_fast": True,
                        "megapixels": "1",
                        "num_outputs": 1,
                        "aspect_ratio": "1:1",
                        "output_format": "webp",
                        "output_quality": 80,
                        "num_inference_steps": 4,
                        "disable_safety_checker": True
                    }
                )
            elif 'hyper-flux-8step' in modelo:
                # Basado en IA_flux8.py
                replicate.run(
                    "bytedance/hyper-flux-8step:81946b1e09b256c543b35f37333a30d0d02ee2cd8c4f77cd915873a1ca622bad",
                    input={
                        "prompt": prompt,
                        "num_outputs": 1,
                        "aspect_ratio": "1:1",
                        "output_format": "webp",
                        "guidance_scale": 3.5,
                        "output_quality": 80,
                        "num_inference_steps": 4,
                        "disable_safety_checker": True
                    }
                )
            elif 'hyper-flux-16step' in modelo:
                # Basado en IA_flux16.py
                replicate.run(
                    "bytedance/hyper-flux-16step:382cf8959fb0f0d665b26e7e80b8d6dc3faaef1510f14ce017e8c732bb3d1eb7",
                    input={
                        "prompt": prompt,
                        "num_outputs": 1,
                        "aspect_ratio": "1:1",
                        "output_format": "webp",
                        "guidance_scale": 3.5,
                        "output_quality": 80,
                        "num_inference_steps": 4,
                        "disable_safety_checker": True
                    }
                )
            elif 'dgmtnzflux' in modelo:
                # Basado en IA_dgmtnzflux.py
                replicate.run(
                    "dgmtnz/dgmtnzflux:2df4f3bc8070ddda1854e25218cf5ac159cc0d51c9fcfdd08447712075807e8b",
                    input={
                        "prompt": prompt,
                        "model": "dev",
                        "lora_scale": 1,
                        "num_outputs": 1,
                        "aspect_ratio": "1:1",
                        "output_format": "webp",
                        "guidance_scale": 3.5,
                        "output_quality": 90,
                        "prompt_strength": 0.8,
                        "extra_lora_scale": 1,
                        "num_inference_steps": 4,
                        "disable_safety_checker": True
                    }
                )
            elif 'sana' in modelo:
                # Basado en IA_sana.py
                replicate.run(
                    "nvidia/sana:c6b5d2b7459910fec94432e9e1203c3cdce92d6db20f714f1355747990b52fa6",
                    input={
                        "prompt": prompt,
                        "width": 512,
                        "height": 512,
                        "model_variant": "1600M-1024px",
                        "guidance_scale": 5,
                        "negative_prompt": "bad quality, worst quality, text, signature, watermark",
                        "pag_guidance_scale": 2,
                        "num_inference_steps": 4,
                        "disable_safety_checker": True
                    }
                )
            elif 'imagen-3' in modelo:
                # Basado en IA_imagen3.py
                replicate.run(
                    "google/imagen-3",
                    input={
                        "prompt": prompt,
                        "aspect_ratio": "1:1"
                    }
                )
            elif 'imagen-3-fast' in modelo:
                # Basado en IA_imagen3fast.py
                replicate.run(
                    "google/imagen-3-fast",
                    input={
                        "prompt": prompt,
                        "aspect_ratio": "1:1"
                    }
                )
            elif 'model3_4' in modelo:
                # Basado en IA_model3_4.py
                replicate.run(
                    "lightweight-ai/model3_4:3db8401934ab8847047c76cce766bc7390a54ae0a5342e42da8b27098b78f5ca",
                    input={
                        "prompt": prompt,
                        "width": 512,
                        "height": 512,
                        "scheduler": "K_EULER",
                        "num_outputs": 1,
                        "guidance_scale": 3.5,
                        "negative_prompt": "bad quality, worst quality",
                        "num_inference_steps": 4,
                        "nsfw_chekcer": False,
                        "output_format": "png",
                        "output_quality": 100
                    }
                )
            elif 'grok' in modelo:
                # Basado en IA_grok_2_image.py
                if not os.environ.get('GROK_API_KEY'):
                    log_message("Error: GROK_API_KEY no está configurada en el entorno")
                    return False
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
                }
                
                data = {
                    "model": "grok-2-image-1212",
                    "prompt": prompt,
                    "n": 1,
                    "response_format": "url"
                }
                
                response = requests.post(
                    "https://api.x.ai/v1/images/generations",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code != 200:
                    log_message(f"Error al verificar Grok Image: {response.status_code}")
                    return False
            else:
                # Modelo por defecto - hyper-flux-16step
                log_message(f"Modelo {modelo} no reconocido, usando hyper-flux-16step para la prueba")
                replicate.run(
                    "bytedance/hyper-flux-16step:382cf8959fb0f0d665b26e7e80b8d6dc3faaef1510f14ce017e8c732bb3d1eb7",
                    input={
                        "prompt": prompt,
                        "num_outputs": 1,
                        "aspect_ratio": "1:1",
                        "output_format": "webp",
                        "guidance_scale": 3.5,
                        "output_quality": 80,
                        "num_inference_steps": 4,
                        "disable_safety_checker": True
                    }
                )
                
        log_message(f"Modelo {modelo} disponible y funcionando correctamente")
        return True
        
    except Exception as e:
        log_message(f"Error al verificar el modelo {modelo}: {str(e)}")
        return False

class AgenteOrganizador:
    """
    Agente encargado de organizar la estructura general de la presentación
    basándose en el tema proporcionado por el usuario y el número de diapositivas deseado.
    """
    def __init__(self, signals=None):
        self.signals = signals
        
    def log_message(self, msg):
        print(msg)
        if self.signals:
            self.signals.update_log.emit(str(msg))
    
    def generar_estructura(self, tema, num_diapositivas, modelo):
        """
        Genera una estructura para la presentación, creando prompts específicos
        para cada diapositiva.
        
        Args:
            tema (str): El tema general de la presentación.
            num_diapositivas (int): Número de diapositivas a generar.
            modelo (str): Modelo de IA a utilizar para la generación.
            
        Returns:
            list: Lista de diccionarios con información para cada diapositiva.
        """
        self.log_message(f"Generando estructura para presentación sobre: {tema} con {num_diapositivas} diapositivas")
        
        estructura = []
        
        try:
            # Prompt para generar la estructura de la presentación
            prompt = (
                f"Crea una estructura para una presentación de PowerPoint sobre '{tema}' con {num_diapositivas} diapositivas. " +
                f"Para cada diapositiva, necesito: " +
                f"1. Un título corto y conciso (máximo 50 caracteres) " +
                f"2. Un prompt para generar el contenido de la diapositiva (con contexto específico) " +
                f"3. Un prompt para generar una imagen relacionada con esa diapositiva (muy descriptivo y visual). " +
                f"Muestra cada diapositiva en un formato JSON simple como: " +
                f"{{\"diapositiva\": 1, \"titulo\": \"Título\", \"contenido_prompt\": \"prompt para contenido\", \"imagen_prompt\": \"prompt para imagen\"}}"
            )
            
            respuesta_completa = ""
            
            # Elegir el modelo de IA adecuado según el parámetro
            if "claude-3.7-sonnet" in modelo:
                # Basado en IA_sonnet_3_7.py
                for event in replicate.stream(
                    "anthropic/claude-3.7-sonnet",
                    input={
                        "prompt": prompt,
                        "max_tokens": 8192,
                        "system_prompt": "Eres un asistente experto en crear presentaciones PowerPoint. Tu objetivo es crear estructuras claras y bien organizadas basadas en el tema proporcionado. Debes proporcionar exactamente el número de diapositivas solicitado, ni más ni menos.",
                        "max_image_resolution": 0.5
                    }
                ):
                    respuesta_completa += str(event)
                    
            elif "claude-3.5-sonnet" in modelo:
                # Basado en IA_sonnet_3_5.py
                for event in replicate.stream(
                    "anthropic/claude-3.5-sonnet",
                    input={
                        "prompt": prompt,
                        "max_tokens": 8192,
                        "system_prompt": "Eres un asistente experto en crear presentaciones PowerPoint. Tu objetivo es crear estructuras claras y bien organizadas basadas en el tema proporcionado. Debes proporcionar exactamente el número de diapositivas solicitado, ni más ni menos.",
                        "max_image_resolution": 0.5
                    }
                ):
                    respuesta_completa += str(event)
                    
            elif "deepseek-r1" in modelo:
                # Basado en IA_deepseek.py
                for event in replicate.stream(
                    "deepseek-ai/deepseek-r1",
                    input={
                        "prompt": prompt,
                        "top_p": 1,
                        "max_tokens": 20480,
                        "temperature": 0.1,
                        "system_prompt": "Eres un asistente experto en crear presentaciones PowerPoint. Tu objetivo es crear estructuras claras y bien organizadas basadas en el tema proporcionado. Debes proporcionar exactamente el número de diapositivas solicitado, ni más ni menos.",
                        "presence_penalty": 0,
                        "frequency_penalty": 0
                    }
                ):
                    respuesta_completa += str(event)
            
            elif "dolphin" in modelo:
                # Basado en IA_dolphin.py
                for event in replicate.stream(
                    "mikeei/dolphin-2.9-llama3-70b-gguf:7cd1882cb3ea90756d09decf4bc8a259353354703f8f385ce588b71f7946f0aa",
                    input={
                        "prompt": prompt,
                        "temperature": 0.6,
                        "system_prompt": "Eres un asistente experto en crear presentaciones PowerPoint. Tu objetivo es crear estructuras claras y bien organizadas basadas en el tema proporcionado. Debes proporcionar exactamente el número de diapositivas solicitado, ni más ni menos.",
                        "max_new_tokens": 8000,
                        "repeat_penalty": 1.1,
                        "prompt_template": "<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
                    }
                ):
                    respuesta_completa += str(event)
            
            elif "haiku" in modelo:
                # Basado en IA_haiku.py
                for event in replicate.stream(
                    "anthropic/claude-3.5-haiku",
                    input={
                        "prompt": prompt,
                        "max_tokens": 8192,
                        "system_prompt": "Eres un asistente experto en crear presentaciones PowerPoint. Tu objetivo es crear estructuras claras y bien organizadas basadas en el tema proporcionado. Debes proporcionar exactamente el número de diapositivas solicitado, ni más ni menos."
                    }
                ):
                    respuesta_completa += str(event)
            
            elif "grok" in modelo:
                # Basado en IA_grok_2.py
                if not os.environ.get('GROK_API_KEY'):
                    self.log_message("Error: GROK_API_KEY no está configurada en el entorno")
                    raise Exception("GROK_API_KEY no configurada")
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
                }
                
                data = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Eres un asistente experto en crear presentaciones PowerPoint. Tu objetivo es crear estructuras claras y bien organizadas basadas en el tema proporcionado. Debes proporcionar exactamente el número de diapositivas solicitado, ni más ni menos."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "model": "grok-2-1212",
                    "stream": False,
                    "temperature": 0.6
                }
                
                response = requests.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    respuesta_completa = response.json()['choices'][0]['message']['content']
                else:
                    self.log_message(f"Error al llamar a la API de Grok: {response.status_code}")
                    raise Exception(f"Error en la API de Grok: {response.text}")
                    
            else:  # Modelo por defecto (meta-llama o similar)
                # Basado en IA_llama.py
                for event in replicate.stream(
                    "meta/meta-llama-3.1-405b-instruct",
                    input={
                        "prompt": prompt,
                        "top_k": 50,
                        "top_p": 0.9,
                        "max_tokens": 8000,
                        "min_tokens": 0,
                        "temperature": 0.6,
                        "system_prompt": "Eres un asistente experto en crear presentaciones PowerPoint. Tu objetivo es crear estructuras claras y bien organizadas basadas en el tema proporcionado. Debes proporcionar exactamente el número de diapositivas solicitado, ni más ni menos.",
                        "presence_penalty": 0,
                        "frequency_penalty": 0
                    }
                ):
                    respuesta_completa += str(event)
            
            # Parsear la respuesta para extraer la estructura
            import json
            import re
            
            # Buscamos patrones JSON en la respuesta
            json_pattern = r'\{.*?\}'
            matches = re.findall(json_pattern, respuesta_completa, re.DOTALL)
            
            # Procesamos cada coincidencia encontrada
            for i, match in enumerate(matches):
                if i >= num_diapositivas:
                    break
                    
                try:
                    slide_data = json.loads(match)
                    estructura.append({
                        'titulo': slide_data.get('titulo', f"Diapositiva {i+1}"),
                        'contenido_prompt': slide_data.get('contenido_prompt', f"Información sobre {tema} para la diapositiva {i+1}"),
                        'imagen_prompt': slide_data.get('imagen_prompt', f"Imagen visual sobre {tema} para la diapositiva {i+1}")
                    })
                except json.JSONDecodeError:
                    # Si hay error en el parsing, creamos una estructura genérica
                    self.log_message(f"Error al parsear JSON, usando estructura genérica para diapositiva {i+1}")
                    estructura.append({
                        'titulo': f"Diapositiva {i+1} sobre {tema}",
                        'contenido_prompt': f"Información detallada sobre {tema} para la diapositiva {i+1}",
                        'imagen_prompt': f"Imagen visual sobre {tema} para la diapositiva {i+1}"
                    })
            
            # Si no tenemos suficientes diapositivas, completamos con genéricas
            while len(estructura) < num_diapositivas:
                indice = len(estructura) + 1
                estructura.append({
                    'titulo': f"Diapositiva {indice} sobre {tema}",
                    'contenido_prompt': f"Información detallada sobre {tema} para la diapositiva {indice}",
                    'imagen_prompt': f"Imagen visual sobre {tema} para la diapositiva {indice}"
                })
                
        except Exception as e:
            self.log_message(f"Error al generar estructura: {str(e)}")
            # Crear una estructura genérica en caso de error
            for i in range(num_diapositivas):
                estructura.append({
                    'titulo': f"Diapositiva {i+1} sobre {tema}",
                    'contenido_prompt': f"Información detallada sobre {tema} para la diapositiva {i+1}",
                    'imagen_prompt': f"Imagen visual sobre {tema} para la diapositiva {i+1}"
                })
        
        self.log_message(f"Estructura generada con {len(estructura)} diapositivas")
        return estructura

class AgenteTitulo:
    """
    Agente encargado de refinar los títulos para las diapositivas.
    """
    def __init__(self, signals=None):
        self.signals = signals
        
    def log_message(self, msg):
        print(msg)
        if self.signals:
            self.signals.update_log.emit(str(msg))
    
    def generar(self, titulo):
        """
        Refina un título para que sea conciso y apropiado para una diapositiva.
        
        Args:
            titulo (str): Título propuesto para la diapositiva.
            
        Returns:
            str: Título refinado (limitado a 50 caracteres).
        """
        # Simplemente aseguramos que el título no exceda los 50 caracteres
        if len(titulo) > 50:
            titulo = titulo[:47] + "..."
        
        return titulo

class AgenteContenido:
    """
    Agente encargado de generar el contenido textual para cada diapositiva.
    """
    def __init__(self, signals=None):
        self.signals = signals
        
    def log_message(self, msg):
        print(msg)
        if self.signals:
            self.signals.update_log.emit(str(msg))
    
    def generar(self, contenido_prompt, tema_general, modelo):
        """
        Genera contenido textual para una diapositiva.
        
        Args:
            contenido_prompt (str): Prompt específico para el contenido.
            tema_general (str): Tema general de la presentación para contexto.
            modelo (str): Modelo de IA a utilizar.
            
        Returns:
            str: Contenido textual para la diapositiva (limitado a 500 caracteres).
        """
        self.log_message(f"Generando contenido para: {contenido_prompt}")
        
        try:
            # Prompt para generar el contenido
            prompt = (
                f"Genera un texto conciso y claro para una diapositiva de PowerPoint sobre el siguiente tema: " +
                f"{contenido_prompt}. " +
                f"Este texto forma parte de una presentación general sobre '{tema_general}'. " +
                f"El texto debe ser informativo, directo y fácil de leer. " +
                f"Limita la respuesta a un máximo de 400 caracteres. " +
                f"NO incluyas el título de la diapositiva, sólo el contenido."
            )
            
            respuesta_completa = ""
            
            # Elegir el modelo de IA adecuado según el parámetro
            if "claude-3.7-sonnet" in modelo:
                # Basado en IA_sonnet_3_7.py
                for event in replicate.stream(
                    "anthropic/claude-3.7-sonnet",
                    input={
                        "prompt": prompt,
                        "max_tokens": 8192,
                        "system_prompt": "Eres un asistente experto en crear contenido conciso y efectivo para presentaciones. Tu tarea es generar texto claro y directo, limitado a 400 caracteres.",
                        "max_image_resolution": 0.5
                    }
                ):
                    respuesta_completa += str(event)
                    
            elif "claude-3.5-sonnet" in modelo:
                # Basado en IA_sonnet_3_5.py
                for event in replicate.stream(
                    "anthropic/claude-3.5-sonnet",
                    input={
                        "prompt": prompt,
                        "max_tokens": 8192,
                        "system_prompt": "Eres un asistente experto en crear contenido conciso y efectivo para presentaciones. Tu tarea es generar texto claro y directo, limitado a 400 caracteres.",
                        "max_image_resolution": 0.5
                    }
                ):
                    respuesta_completa += str(event)
                    
            elif "deepseek-r1" in modelo:
                # Basado en IA_deepseek.py
                for event in replicate.stream(
                    "deepseek-ai/deepseek-r1",
                    input={
                        "prompt": prompt,
                        "top_p": 1,
                        "max_tokens": 1024,
                        "temperature": 0.1,
                        "system_prompt": "Eres un asistente experto en crear contenido conciso y efectivo para presentaciones. Tu tarea es generar texto claro y directo, limitado a 400 caracteres.",
                        "presence_penalty": 0,
                        "frequency_penalty": 0
                    }
                ):
                    respuesta_completa += str(event)
            
            elif "dolphin" in modelo:
                # Basado en IA_dolphin.py
                for event in replicate.stream(
                    "mikeei/dolphin-2.9-llama3-70b-gguf:7cd1882cb3ea90756d09decf4bc8a259353354703f8f385ce588b71f7946f0aa",
                    input={
                        "prompt": prompt,
                        "temperature": 0.6,
                        "system_prompt": "Eres un asistente experto en crear contenido conciso y efectivo para presentaciones. Tu tarea es generar texto claro y directo, limitado a 400 caracteres.",
                        "max_new_tokens": 1024,
                        "repeat_penalty": 1.1,
                        "prompt_template": "<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant"
                    }
                ):
                    respuesta_completa += str(event)
            
            elif "haiku" in modelo:
                # Basado en IA_haiku.py
                for event in replicate.stream(
                    "anthropic/claude-3.5-haiku",
                    input={
                        "prompt": prompt,
                        "max_tokens": 8192,
                        "system_prompt": "Eres un asistente experto en crear contenido conciso y efectivo para presentaciones. Tu tarea es generar texto claro y directo, limitado a 400 caracteres."
                    }
                ):
                    respuesta_completa += str(event)
            
            elif "grok" in modelo:
                # Basado en IA_grok_2.py
                if not os.environ.get('GROK_API_KEY'):
                    self.log_message("Error: GROK_API_KEY no está configurada en el entorno")
                    raise Exception("GROK_API_KEY no configurada")
                
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
                }
                
                data = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "Eres un asistente experto en crear contenido conciso y efectivo para presentaciones. Tu tarea es generar texto claro y directo, limitado a 400 caracteres."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "model": "grok-2-1212",
                    "stream": False,
                    "temperature": 0.6
                }
                
                response = requests.post(
                    "https://api.x.ai/v1/chat/completions",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    respuesta_completa = response.json()['choices'][0]['message']['content']
                else:
                    self.log_message(f"Error al llamar a la API de Grok: {response.status_code}")
                    raise Exception(f"Error en la API de Grok: {response.text}")
                    
            else:  # Modelo por defecto (meta-llama o similar)
                # Basado en IA_llama.py
                for event in replicate.stream(
                    "meta/meta-llama-3.1-405b-instruct",
                    input={
                        "prompt": prompt,
                        "top_k": 50,
                        "top_p": 0.9,
                        "max_tokens": 1024,
                        "min_tokens": 0,
                        "temperature": 0.6,
                        "system_prompt": "Eres un asistente experto en crear contenido conciso y efectivo para presentaciones. Tu tarea es generar texto claro y directo, limitado a 400 caracteres.",
                        "presence_penalty": 0,
                        "frequency_penalty": 0
                    }
                ):
                    respuesta_completa += str(event)
            
            # Limpiar y limitar el contenido
            contenido = respuesta_completa.strip()
            if len(contenido) > 500:  # Damos un poco de margen extra sobre los 400 solicitados
                contenido = contenido[:497] + "..."
                
            return contenido
                
        except Exception as e:
            self.log_message(f"Error al generar contenido: {str(e)}")
            return f"Información sobre {contenido_prompt[:50]}..."

class AgenteImagen:
    """
    Agente encargado de generar imágenes para las diapositivas.
    """
    def __init__(self, signals=None):
        self.signals = signals
        
    def log_message(self, msg):
        print(msg)
        if self.signals:
            self.signals.update_log.emit(str(msg))
    
    def generar(self, imagen_prompt, modelo_imagen, imagen_personalizada=None):
        """
        Genera una imagen para una diapositiva.
        
        Args:
            imagen_prompt (str): Prompt para generar la imagen.
            modelo_imagen (str): Modelo de IA a utilizar para la imagen.
            imagen_personalizada (str, optional): Ruta a una imagen personalizada de referencia.
            
        Returns:
            PIL.Image: Imagen generada.
        """
        self.log_message(f"Generando imagen para: {imagen_prompt}")
        
        try:
            # Traducir al inglés para mejores resultados
            translator = GoogleTranslator(target='en')
            try:
                imagen_prompt_en = translator.translate(imagen_prompt)
            except Exception as e:
                self.log_message(f"Error en la traducción: {str(e)}")
                imagen_prompt_en = imagen_prompt
                
            # Configuración básica para la imagen (se sobrescribirá según el modelo)
            image_input = {
                "prompt": f"a photo in the context of a PowerPoint presentation about {imagen_prompt_en}, professional style with soft lighting, high resolution and exceptional clarity",
            }
            
            # Adaptar configuración según el modelo
            if 'sdxl-lightning-4step' in modelo_imagen:
                # Basado en IA_sdxl.py
                image_input.update({
                    "width": 1024,
                    "height": 1024,
                    "scheduler": "K_EULER",
                    "num_outputs": 1,
                    "guidance_scale": 0,
                    "negative_prompt": "worst quality, low quality",
                    "num_inference_steps": 4,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "bytedance/sdxl-lightning-4step:727e49a643e999d602a896c774a0658ffefea21465756a6ce24b7ea4165eba6a",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'flux-schnell' in modelo_imagen:
                # Basado en IA_fluxschnell.py
                image_input.update({
                    "go_fast": True,
                    "megapixels": "1",
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "webp",
                    "output_quality": 80,
                    "num_inference_steps": 4,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "black-forest-labs/flux-schnell",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'hyper-flux-8step' in modelo_imagen:
                # Basado en IA_flux8.py
                image_input.update({
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "webp",
                    "guidance_scale": 3.5,
                    "output_quality": 80,
                    "num_inference_steps": 8,
                    "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic",
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "bytedance/hyper-flux-8step:81946b1e09b256c543b35f37333a30d0d02ee2cd8c4f77cd915873a1ca622bad",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'hyper-flux-16step' in modelo_imagen:
                # Basado en IA_flux16.py
                image_input.update({
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "webp",
                    "guidance_scale": 3.5,
                    "output_quality": 80,
                    "num_inference_steps": 16,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "bytedance/hyper-flux-16step:382cf8959fb0f0d665b26e7e80b8d6dc3faaef1510f14ce017e8c732bb3d1eb7",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'photomaker' in modelo_imagen and imagen_personalizada:
                # Basado en IA_photomaker.py
                import base64
                with open(imagen_personalizada, "rb") as image_file:
                    Image1 = base64.b64encode(image_file.read()).decode('utf-8')
                
                image_input.update({
                    "prompt": f"A person img {imagen_prompt_en}, photo in the context of a PowerPoint presentation",
                    "num_steps": 50,
                    "style_name": "Photographic (Default)",
                    "input_image": f"data:image/jpeg;base64,{Image1}",
                    "num_outputs": 1,
                    "guidance_scale": 5,
                    "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
                    "style_strength_ratio": 20,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'fluxpulid' in modelo_imagen and imagen_personalizada:
                # Basado en IA_fluxpulid.py
                import base64
                with open(imagen_personalizada, "rb") as image_file:
                    Image1 = base64.b64encode(image_file.read()).decode('utf-8')
                
                image_input.update({
                    "width": 896,
                    "height": 1152,
                    "prompt": f"A person img {imagen_prompt_en}, photo in the context of a PowerPoint presentation",
                    "true_cfg": 1,
                    "id_weight": 1,
                    "num_steps": 20,
                    "start_step": 4,
                    "num_outputs": 1,
                    "output_format": "webp",
                    "guidance_scale": 4,
                    "output_quality": 80,
                    "main_face_image": f"data:image/jpeg;base64,{Image1}",
                    "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
                    "max_sequence_length": 128,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "zsxkib/flux-pulid:8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'dgmtnzflux' in modelo_imagen:
                # Basado en IA_dgmtnzflux.py
                image_input.update({
                    "model": "dev",
                    "prompt": f"DGMTNZ {imagen_prompt_en}, a photo in the context of a PowerPoint presentation",
                    "lora_scale": 1,
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "webp",
                    "guidance_scale": 3.5,
                    "output_quality": 90,
                    "prompt_strength": 0.8,
                    "extra_lora_scale": 1,
                    "num_inference_steps": 28,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "dgmtnz/dgmtnzflux:2df4f3bc8070ddda1854e25218cf5ac159cc0d51c9fcfdd08447712075807e8b",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'sana' in modelo_imagen:
                # Basado en IA_sana.py
                image_input.update({
                    "width": 1024,
                    "height": 1024,
                    "model_variant": "1600M-1024px",
                    "guidance_scale": 5,
                    "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
                    "pag_guidance_scale": 2,
                    "num_inference_steps": 18,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "nvidia/sana:c6b5d2b7459910fec94432e9e1203c3cdce92d6db20f714f1355747990b52fa6",
                    input=image_input
                )
                image_url = str(output)
                
            elif 'imagen-3' in modelo_imagen:
                # Basado en IA_imagen3.py
                image_input.update({
                    "aspect_ratio": "1:1",
                    "prompt": f"{imagen_prompt_en}, a photo in the context of a PowerPoint presentation, professional photographers style with soft lighting, high resolution and exceptional clarity"
                })
                output = replicate.run(
                    "google/imagen-3",
                    input=image_input
                )
                image_url = output
                
            elif 'imagen-3-fast' in modelo_imagen:
                # Basado en IA_imagen3fast.py
                image_input.update({
                    "aspect_ratio": "1:1",
                    "prompt": f"{imagen_prompt_en}, a photo in the context of a PowerPoint presentation, professional photographers style with soft lighting and exceptional clarity"
                })
                output = replicate.run(
                    "google/imagen-3-fast",
                    input=image_input
                )
                image_url = output
                
            elif 'model3_4' in modelo_imagen:
                # Basado en IA_model3_4.py
                image_input.update({
                    "width": 1024,
                    "height": 1024,
                    "scheduler": "K_EULER",
                    "num_outputs": 1,
                    "guidance_scale": 3.5,
                    "negative_prompt": "bad quality, worst quality, text, signature, watermark, extra limbs, schematic, diagram, graph, chart, table, text, logo, watermark, comparative, infographic, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, jpeg artifacts, signature, watermark, username, blurry",
                    "num_inference_steps": 28,
                    "nsfw_chekcer": False,
                    "output_format": "png",
                    "output_quality": 100
                })
                output = replicate.run(
                    "lightweight-ai/model3_4:3db8401934ab8847047c76cce766bc7390a54ae0a5342e42da8b27098b78f5ca",
                    input=image_input
                )
                image_url = output[0]
                
            elif 'grok' in modelo_imagen:
                # Basado en IA_grok_2_image.py
                if not os.environ.get('GROK_API_KEY'):
                    self.log_message("Error: GROK_API_KEY no está configurada en el entorno")
                    raise Exception("GROK_API_KEY no configurada")
                    
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {os.environ.get('GROK_API_KEY')}"
                }
                
                data = {
                    "model": "grok-2-image-1212",
                    "prompt": f"{imagen_prompt_en}, a photo in the context of a PowerPoint presentation",
                    "n": 1,
                    "response_format": "url"
                }
                
                response = requests.post(
                    "https://api.x.ai/v1/images/generations",
                    headers=headers,
                    json=data
                )
                
                if response.status_code == 200:
                    image_url = response.json()['data'][0]['url']
                else:
                    self.log_message(f"Error al generar imagen con Grok: {response.status_code}")
                    raise Exception(f"Error en la API de Grok: {response.text}")
                
            else:
                # Modelo por defecto - hyper-flux-16step
                self.log_message(f"Modelo {modelo_imagen} no reconocido, usando hyper-flux-16step")
                image_input.update({
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "webp",
                    "guidance_scale": 3.5,
                    "output_quality": 80,
                    "num_inference_steps": 16,
                    "disable_safety_checker": True
                })
                output = replicate.run(
                    "bytedance/hyper-flux-16step:382cf8959fb0f0d665b26e7e80b8d6dc3faaef1510f14ce017e8c732bb3d1eb7",
                    input=image_input
                )
                image_url = output[0]
            
            # Descargar la imagen
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))
            return img
                
        except Exception as e:
            self.log_message(f"Error al generar imagen: {str(e)}")
            # Crear una imagen de error básica
            error_img = Image.new('RGB', (800, 600), color=(240, 240, 240))
            return error_img

class PresentacionParalela:
    """
    Clase principal que coordina la generación paralela de la presentación.
    """
    def __init__(self, signals=None):
        self.signals = signals
        self.agente_organizador = AgenteOrganizador(signals)
        self.agente_titulo = AgenteTitulo(signals)
        self.agente_contenido = AgenteContenido(signals)
        self.agente_imagen = AgenteImagen(signals)
        
    def log_message(self, msg):
        print(msg)
        if self.signals:
            self.signals.update_log.emit(str(msg))
    
    def generar_presentacion(self, tema, num_diapositivas, modelo_texto, modelo_imagen, imagen_personalizada=None):
        """
        Genera una presentación completa utilizando procesamiento paralelo.
        
        Args:
            tema (str): Tema general de la presentación.
            num_diapositivas (int): Número de diapositivas a generar.
            modelo_texto (str): Modelo de IA para generar texto.
            modelo_imagen (str): Modelo de IA para generar imágenes.
            imagen_personalizada (str, optional): Ruta a una imagen personalizada.
            
        Returns:
            list: Lista de diccionarios con la información de cada diapositiva.
        """
        self.log_message(f"Iniciando generación de presentación sobre: {tema}")
        
        # Verificar disponibilidad de los modelos antes de iniciar
        self.log_message("Verificando disponibilidad de los modelos...")
        
        # Probar modelo de texto
        texto_disponible = test_model_availability(modelo_texto, "texto", self.signals)
        if not texto_disponible:
            self.log_message(f"⚠️ El modelo de texto {modelo_texto} no está disponible. Cambiando al modelo por defecto.")
            modelo_texto = "meta/meta-llama-3.1-405b-instruct"  # Modelo por defecto
        
        # Probar modelo de imagen
        imagen_disponible = test_model_availability(modelo_imagen, "imagen", self.signals)
        if not imagen_disponible:
            self.log_message(f"⚠️ El modelo de imagen {modelo_imagen} no está disponible. Cambiando al modelo por defecto.")
            modelo_imagen = "bytedance/hyper-flux-16step"  # Modelo por defecto actualizado (antes: stability-ai/sdxl)
            
        self.log_message("Verificación de modelos completada. Iniciando generación...")
        
        # 1. Generar estructura general
        estructura = self.agente_organizador.generar_estructura(tema, num_diapositivas, modelo_texto)
        
        # 2. Preparar estructura de resultados
        resultados = []
        for i in range(len(estructura)):
            resultados.append({
                'titulo': '',
                'contenido': '',
                'imagen': None,
                'indice': i
            })
        
        # 3. Procesar en paralelo utilizando ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=3*len(estructura)) as executor:
            # Trabajos para títulos
            futures_titulos = {
                executor.submit(self.agente_titulo.generar, estructura[i]['titulo']): i 
                for i in range(len(estructura))
            }
            
            # Trabajos para contenidos
            futures_contenidos = {
                executor.submit(self.agente_contenido.generar, estructura[i]['contenido_prompt'], tema, modelo_texto): i 
                for i in range(len(estructura))
            }
            
            # Trabajos para imágenes
            futures_imagenes = {
                executor.submit(self.agente_imagen.generar, estructura[i]['imagen_prompt'], modelo_imagen, imagen_personalizada): i 
                for i in range(len(estructura))
            }
            
            # Recopilar resultados de títulos
            for future in concurrent.futures.as_completed(futures_titulos):
                i = futures_titulos[future]
                try:
                    resultados[i]['titulo'] = future.result()
                    self.log_message(f"Título {i+1} completado: {resultados[i]['titulo'][:30]}...")
                except Exception as e:
                    self.log_message(f"Error en título {i+1}: {str(e)}")
                    resultados[i]['titulo'] = f"Diapositiva {i+1}"
            
            # Recopilar resultados de contenidos
            for future in concurrent.futures.as_completed(futures_contenidos):
                i = futures_contenidos[future]
                try:
                    resultados[i]['contenido'] = future.result()
                    self.log_message(f"Contenido {i+1} completado: {resultados[i]['contenido'][:30]}...")
                except Exception as e:
                    self.log_message(f"Error en contenido {i+1}: {str(e)}")
                    resultados[i]['contenido'] = f"Información sobre {tema} para la diapositiva {i+1}"
            
            # Recopilar resultados de imágenes
            for future in concurrent.futures.as_completed(futures_imagenes):
                i = futures_imagenes[future]
                try:
                    resultados[i]['imagen'] = future.result()
                    self.log_message(f"Imagen {i+1} completada")
                except Exception as e:
                    self.log_message(f"Error en imagen {i+1}: {str(e)}")
                    resultados[i]['imagen'] = Image.new('RGB', (800, 600), color=(240, 240, 240))
        
        self.log_message(f"Generación de presentación completada con {len(resultados)} diapositivas")
        return resultados 