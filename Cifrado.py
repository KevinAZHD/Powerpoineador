import os, base64, platform
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class GestorCifrado:
    
    # Generar clave de cifrado
    @staticmethod
    def get_encryption_key():
        # Usar información del sistema para generar una semilla consistente
        system_info = f"{platform.node()}-{platform.machine()}-{os.getuid() if hasattr(os, 'getuid') else os.getlogin()}"
        salt = b'powerpoineador_salt'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(system_info.encode()))
        return key

    # Función para cifrar API
    @classmethod
    def encrypt_text(cls, text):
        if not text:
            return ""
        fernet = Fernet(cls.get_encryption_key())
        return fernet.encrypt(text.encode()).decode()

    # Función para descifrar API
    @classmethod
    def decrypt_text(cls, encrypted_text):
        if not encrypted_text:
            return None
        try:
            fernet = Fernet(cls.get_encryption_key())
            return fernet.decrypt(encrypted_text.encode()).decode()
        except Exception:
            # Si hay error al descifrar, puede ser que esté sin cifrar o que sea inválido
            return encrypted_text

    # Función para migrar claves antiguas
    @classmethod
    def migrar_claves_antiguas(cls, config_file):
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    import json
                    config = json.load(f)
                
                # Verificar si hay claves sin cifrar
                api_key = config.get('api_key')
                grok_api_key = config.get('grok_api_key')
                
                ha_cambiado = False
                
                # Verificar si una cadena es una clave cifrada de Fernet
                def parece_cifrado(texto):
                    # Las claves cifradas por Fernet comienzan con 'gAAAAA'
                    if not texto or not isinstance(texto, str):
                        return True  # Considerar nulos o no-strings como "ya cifrados"
                    return texto.startswith('gAAAAA')
                
                # Cifrar la clave API de Replicate si no parece estar cifrada
                if api_key and isinstance(api_key, str) and not parece_cifrado(api_key):
                    config['api_key'] = cls.encrypt_text(api_key)
                    ha_cambiado = True
                    
                # Cifrar la clave API de Grok si no parece estar cifrada
                if grok_api_key and isinstance(grok_api_key, str) and not parece_cifrado(grok_api_key):
                    config['grok_api_key'] = cls.encrypt_text(grok_api_key)
                    ha_cambiado = True
                
                if ha_cambiado:
                    with open(config_file, 'w', encoding='utf-8') as f:
                        json.dump(config, f, ensure_ascii=False, indent=4)
                
                return ha_cambiado
                
        except Exception as e:
            print(f"Error al migrar claves antiguas: {str(e)}")
            return False