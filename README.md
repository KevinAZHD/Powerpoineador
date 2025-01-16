# Powerpoineador

Powerpoineador es un programa de escritorio que genera automáticamente presentaciones de PowerPoint utilizando diferentes modelos de Inteligencia Artificial, tanto para la generación de texto como para las imágenes.

![Interfaz principal del programa](imágenes/captura.png)

## Descripción

El programa ofrece una interfaz gráfica intuitiva, donde el usuario puede generar presentaciones de PowerPoint de manera automática, utilizando la Inteligencia Artificial soportada por dos tipos de APIs:

- **Replicate API**: Para generar tanto texto como imágenes.
- **xAI API**: Para generación de texto (experimental).

## Características

- Interfaz gráfica de usuario intuitiva y fácil de entender.
- Múltiples modelos de IA para texto e imágenes.
- Soporte para imágenes personalizadas en modelos específicos.
- Guardado automático de configuraciones.
- Contador de palabras integrado.
- Opción de apertura automática de presentaciones.

## Modelos Disponibles

### Modelos de Texto:
- **meta-llama-3.1-405b-instruct**: Modelo con censura de contenido (recomendado).
- **dolphin-2.9-llama3-70b-gguf**: Modelo sin censura de contenido.
- **grok-2-1212**: Modelo experimental de xAI.

### Modelos de Imagen:
- **hyper-flux-8step**: Generación rápida y económica
- **photomaker**: Optimizado y mejorado para rostros (requiere imagen de referencia).
- **flux-pulid**: Optimizado para rostros (requiere también de imagen).
- **hyper-flux-16step**: Balance entre velocidad y calidad.
- **sdxl-lightning-4step**: Económico sin filtros.
- **flux-schnell**: Enfocado en velocidad.
- **flux-diego**: Estilo meme.

## Requisitos

- Windows 7 o superior.
- Microsoft PowerPoint (opcional si desactiva la apertura automática).
- Conexión a Internet.
- Clave API de Replicate y/o xAI (opcional).
- Python 3.9+ (solo para ejecución desde código fuente).

## Instalación

### Usando el ejecutable (.exe):
1. Descarga el último release desde la sección "Releases".
2. Ejecuta `Powerpoineador.exe`.

### Usando el código fuente (.py):
1. Instala Python 3.9 o superior.
2. Clona el repositorio:
```bash
git clone https://github.com/tu_nombre_de_usuario/Powerpoineador.git
```
3. Instala las dependencias:
```bash
pip install -r requirements.txt
```
4. Ejecuta el programa:
```bash
python Powerpoineador.py
```

## Obtención de APIs

### Replicate API:
1. Crea una cuenta en [Replicate](https://replicate.com).
2. Ve a tu perfil → API Tokens.
3. Genera un nuevo token.
4. Copia el token en el programa.

### xAI API (Grok):
1. Solicita acceso en [xAI](https://console.x.ai).
2. Una vez aprobado, genera tu clave API.
3. Copia la clave que comienza con "xai-" en el programa.

## Licencia

Este proyecto se ha creado de manera Open-Source bajo la licencia GPL (Licencia Pública General de GNU). Esto significa que puedes copiar, modificar y distribuir el código, siempre y cuando mantengas la misma licencia y hagas público cualquier cambio que realices.

## Soporte

Si tiene algún problema o duda con respecto a esta guía o al Powerpoineador, no dude en comunicarlo. Estamos aquí tanto yo como el co-creador del proyecto para ayudar y mejorar continuamente este recurso para la comunidad.

Por favor, tenga en cuenta que este proyecto se mantiene con la intención de ser un recurso útil y profesional. Cualquier contribución o sugerencia para mejorar es siempre bienvenida.

## Créditos

- Este proyecto ha sido desarrollado por [Kevin Adán Zamora](https://github.com/KevinAZHD) y [Diego Martínez Fernández](https://github.com/Dgmtnz).
- Interfaz gráfica desarrollada con PySide6 gracias a [Kevin Adán Zamora](https://github.com/KevinAZHD).
- Todos los enlaces proporcionados anteriormente.
- Gracias por leer y utilizar esta guía de Powerpoineador.
