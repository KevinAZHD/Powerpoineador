# Powerpoineador

Powerpoineador es un programa de escritorio que genera automáticamente presentaciones de PowerPoint utilizando diferentes modelos de Inteligencia Artificial, tanto para la generación de texto como para las imágenes.

![Interfaz principal del programa](imágenes/programa.png)

## Descripción

El programa ofrece una interfaz gráfica intuitiva, donde el usuario puede generar presentaciones de PowerPoint de manera automática, utilizando la Inteligencia Artificial soportada por dos tipos de APIs:

- **Replicate API** - Para generar tanto texto como imágenes.
- **xAI API** - Para generación de texto (experimental).

## Características

- Interfaz gráfica de usuario intuitiva y fácil de entender.
- Múltiples modelos de IA para texto e imágenes.
- Soporte para imágenes personalizadas en modelos específicos.
- Guardado automático de configuraciones.
- Contador de palabras integrado.
- Opción de apertura automática de presentaciones.

## Modelos Disponibles

### Modelos de Texto:

- **deepseek-r1** - Modelo chino optimizado para razonamiento y estructuración lógica.
- **claude-3.7-sonnet** - Nuevo modelo de Anthropic, más inteligente y con mejor capacidad de razonamiento.
- **claude-3.5-sonnet** - Modelo equilibrado de Anthropic con buena capacidad de comprensión.
- **claude-3.5-haiku** - Versión económica de Claude, excelente relación calidad-precio.
- **meta-llama-3.1-405b-instruct** - Modelo de Meta con controles de contenido.
- **dolphin-2.9-llama3-70b-gguf** - Modelo sin censura para contenido más flexible.
- **grok-2-1212** - Modelo experimental de xAI.

### Modelos de Imagen:

- **flux-schnell** - Modelo rápido con buena calidad.
- **imagen-3** - Modelo de Google con la mejor calidad de imagen.
- **imagen-3-fast** - Modelo de Google rápido y económico.
- **sana** - Modelo de NVIDIA equilibrado entre calidad y velocidad.
- **photomaker** - Modelo especializado en caras (requiere imagen de referencia).
- **fluxpulid** - Modelo también especializado en caras equilibrado entre calidad y velocidad (requiere imagen de referencia).
- **hyper-flux-8step** - Modelo muy rápido y económico.
- **hyper-flux-16step** - Modelo rápido y económico con mejor calidad.
- **sdxl-lightning-4step** - Modelo rápido y económico sin censura.
- **model3_4** - Modelo muy económico y sin censura.
- **dgmtnzflux** - Modelo estilo meme.

## Requisitos

- Sistema operativo Windows con soporte, o cualquier distribución de Linux (experimental).
- Microsoft PowerPoint, o LibreOffice Impress (opcionales si desactiva la apertura automática).
- Conexión a Internet.
- Clave API de Replicate y/o xAI (opcional).
- Python a la última versión si es posible (solo para ejecución desde código fuente).

## Instalación

### Método 1: Ejecutable

1. Descarga la última actualización desde [Releases](https://github.com/KevinAZHD/Powerpoineador/releases/)
2. Ejecuta `Powerpoineador.exe`

### Método 2: Código Fuente

1. Instala la última versión de Python si es posible.
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

#### Método 1: Desde el programa

1. Al abrir el programa, selecciona la opción "Obtener clave API de Replicate" en el apartado de "Replicate".
2. Serás redirigido al sitio web de Replicate para obtener su API (necesitas tener cuenta registrada, véase en el método 2).
3. Copia y pega la API en el programa.

#### Método 2: Manual

1. Crea una cuenta en [Replicate](https://replicate.com)
2. Ve a tu perfil → API Tokens.
3. Genera un nuevo token.
4. Copia y pega el token en el programa.

### xAI API:

#### Método 1: Desde el programa

1. Al abrir el programa, selecciona la opción "Obtener clave API de xAI" en el apartado de "xAI".
2. Serás redirigido al sitio web de xAI para obtener su API (necesitas tener cuenta registrada, véase en el método 2).
3. Copia y pega la API en el programa.

#### Método 2: Manual

1. Solicita acceso en [xAI](https://console.x.ai)
2. Una vez aprobado, genera tu clave API.
3. Copia y pega la clave que comienza con "xai-" en el programa.

## Licencia

Este proyecto se ha creado de manera Open-Source bajo la licencia GPL (Licencia Pública General de GNU). Esto significa que puedes copiar, modificar y distribuir el código, siempre y cuando mantengas la misma licencia y hagas público cualquier cambio que realices.

## Soporte

Si tiene algún problema o duda con respecto a esta guía o al Powerpoineador, no dude en comunicarlo. Estamos aquí tanto yo como los demás integrantes del proyecto para ayudar y mejorar continuamente este recurso para la comunidad.

Por favor, tenga en cuenta que este proyecto se mantiene con la intención de ser un recurso útil y profesional. Cualquier contribución o sugerencia para mejorar es siempre bienvenida.

## Créditos

- Este proyecto ha sido desarrollado por [Kevin Adán Zamora](https://github.com/KevinAZHD), [Diego Martínez Fernández](https://github.com/Dgmtnz), y [Leandro Pérez Martínez](https://github.com/Skade2050)
- Interfaz gráfica desarrollada con PySide6 gracias a [Kevin Adán Zamora](https://github.com/KevinAZHD)
- Todos los enlaces proporcionados anteriormente.
- Gracias por leer y utilizar esta guía de Powerpoineador.
