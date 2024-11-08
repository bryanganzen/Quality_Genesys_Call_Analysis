# Quality_Genesys_Call_Analysis
Esta aplicación permite obtener y procesar grabaciones de conversaciones de Genesys Cloud.

## Descripción del Proyecto

Esta aplicación en Python, construida con Flask, permite obtener y procesar grabaciones de conversaciones de Genesys Cloud. La aplicación facilita la obtención del token de acceso, la recuperación de grabaciones de conversaciones específicas, la descarga de archivos de audio, la transcripción de las grabaciones y el envío de la transcripción a un asistente de OpenAI, proporcionando la respuesta en formato HTML para visualizarla en la interfaz web.

## Funcionalidades

1. **Obtención de Token de Acceso**:
   - Obtiene un token de acceso mediante una solicitud a la URL configurada para autenticar la API de Genesys Cloud.

2. **Listado de Grabaciones**:
   - Recupera las grabaciones (metadatos de grabación) asociadas a una conversación en Genesys Cloud.

3. **Detalles y Descarga de Grabación**:
   - Obtiene el `mediaUri` y el nombre del usuario asociado a una grabación específica y descarga el archivo de audio en formato `.WAV`.

4. **Transcripción del Audio**:
   - Utiliza OpenAI para transcribir el archivo de audio descargado, utilizando el modelo `whisper-1`.

5. **Interacción con OpenAI Assistant**:
   - Envía la transcripción y el nombre del agente al asistente de OpenAI, quien devuelve una respuesta que se procesa y limpia antes de ser visualizada en HTML.

6. **Interfaz Web y Descarga de Audio**:
   - Proporciona una interfaz web donde el usuario puede ingresar la organización y el ID de la conversación, ver la respuesta generada, y descargar el archivo de audio.

## Configuración y Uso

### Prerrequisitos

- **Python 3.x**
- Librerías requeridas: `requests`, `flask`, `openai`, `markdown`
- Instala las librerías necesarias ejecutando:

```bash
pip install requests flask openai markdown
```

## Configuración de Variables

1. **API Key de OpenAI:**
- Agrega tu API key de OpenAI en la inicialización del cliente de OpenAI.
2. **Assistant ID:**
- Define el ID del asistente en la variable assistant_id.
3. **URLs y Hosts de Genesys:**
-Configura las URLs para obtener el token y los hosts de acuerdo a la organización (organización1 o organización2).

## Ejecución

1. **Ejecuta el código:**

```bash
python quality.py
```

2. Abre el navegador y ve a **http://localhost:5000** para acceder a la interfaz web.

3. Ingresa los datos de la organización e ID de la conversación para procesar la grabación y recibir la respuesta del asistente.

## Endpoints

1. `/`:
    - Página principal donde se puede ingresar la organización y el ID de conversación.
3. `/process_data`:
    - Endpoint que procesa los datos ingresados, obteniendo la grabación, transcribiéndola y enviándola al asistente.
4. `/download_audio/<conversation_id>`:
    - Endpoint para descargar el archivo de audio en formato .WAV de la conversación especificada.

## Estructura del Código

- **obtener_token_de_acceso:** Obtiene el token de acceso de la URL configurada.
- **obtener_recording:** Recupera los metadatos de grabación de una conversación específica.
- **obtener_detalles_recording:** Obtiene el `mediaUri` y el nombre del usuario de una grabación.
- **descargar_audio:** Descarga el archivo de audio usando el `mediaUri`.
- **transcribir_audio:** Transcribe el archivo de audio descargado.
- **enviar_al_asistente:** Envía la transcripción al asistente de OpenAI y recupera la respuesta.
- **limpiar_referencias:** Elimina referencias innecesarias del texto de la respuesta usando expresiones regulares.

## Archivos de Salida

- **Audio:** Los archivos de audio descargados se almacenan en la carpeta audios y están en formato `.WAV`.
  - **NOTA: Se puede modificar el formato por `.MP3`**
- **Respuesta HTML:** La respuesta en formato Markdown se convierte a `HTML` y se presenta en la página web.
