import requests
import time
import os
import re
from flask import Flask, request, render_template, send_file, redirect, url_for, flash
from openai import OpenAI
import markdown

# Inicialización del cliente de OpenAI con la clave API y el proyecto (si aplica)
client = OpenAI(api_key="tu_api_key",
                project="tu_id_proyecto_(si_aplica)")

assistant_id = "tu_id_asistente" # ID del asistente para interactuar con OpenAI

app = Flask(__name__)
app.secret_key = 'tu_secret_key_para_flask' # Llave secreta para manejar sesiones y mensajes flash

@app.route('/')
def index():
    # Renderiza la página de inicio
    return render_template('index.html')

@app.route('/process_data', methods=['POST'])
def process_data():
    # Obtiene los datos ingresados en el formulario (organización e ID de la conversación)
    nombre_entidad = request.form.get('organization').strip().upper()
    conversation_id = request.form.get('conversation_id').strip()

    # Verifica que se hayan ingresado ambos datos, si no, muestra un mensaje de error
    if not nombre_entidad or not conversation_id:
        flash("Por favor ingrese tanto la organización como el ID de la conversación.", "error")
        return redirect(url_for('index'))

    # Define las URLs y el host de acuerdo a la organización seleccionada
    if nombre_entidad == "organización1":
        token_url = 'url_obtener_token_genesys'
        host = 'host_organización_genesys'
    elif nombre_entidad == "organización2":
        token_url = 'url_obtener_token_genesys'
        host = 'host_organización_genesys'
    else:
        flash("Organización no válida. Debe ser 'organización1' o 'organización2'.", "error")
        return redirect(url_for('index'))
    
    # Obtiene el token de acceso usando la URL configurada
    token = obtener_token_de_acceso(token_url)

    # Recupera las grabaciones asociadas a la conversación 
    if token:
        recordings = obtener_recording(token, conversation_id, host)
        if not recordings:
            flash("No se encontró la conversación proporcionada. Por favor revisa el ID de la Conversación o la Organización", "error")
            return redirect(url_for('index'))

        for recording in recordings:
            recording_id = recording.get('id')
            print(f"Recording ID: {recording_id}")
                
            # Llamar a la función para obtener detalles del recording y el nombre del usuario
            media_uri, user_name = obtener_detalles_recording(token, conversation_id, recording_id, host)
                
            if media_uri:
                print(f"Media URI: {media_uri}")
                # Descargar el archivo de audio y mostrar el nombre del usuario
                ruta_audio = descargar_audio(media_uri, conversation_id, user_name)
                    
                if ruta_audio:
                    # Llamar a la función para transcribir el audio descargado
                    transcription = transcribir_audio(ruta_audio)
                    if transcription:
                        # Enviar la transcripción y el nombre del agente al asistente
                        respuesta = enviar_al_asistente(transcription, user_name)
                        if respuesta:
                            # Convertir Markdown a HTML para la respuesta
                            respuesta_html = markdown.markdown(respuesta)
                            print(f"En este formato se recibe la respuesta del asistente limpio de referencias: {respuesta}")
                                
                            # Mostrar la respuesta en la página web y permitir descarga
                            return render_template('response.html', respuesta=respuesta_html, user_name=user_name, conversation_id=conversation_id)
                        else:
                            flash("Error al obtener respuesta del asistente.", "error")
                            return redirect(url_for('index'))
                    else:
                        flash("Error durante la transcripción del audio.", "error")
                        return redirect(url_for('index'))
                else:
                    flash("Error al descargar el archivo de audio.", "error")
                    return redirect(url_for('index'))
            else:
                flash("No se pudo obtener el Media URI para el recording.", "error")
                return redirect(url_for('index'))
    else:
        flash("No se pudo obtener el token.", "error")
        return redirect(url_for('index'))

# Nueva ruta para descargar el archivo de audio
@app.route('/download_audio/<conversation_id>')
def download_audio(conversation_id):
    # Ruta del archivo de audio
    carpeta_audios = 'audios'
    archivo_audio = os.path.join(carpeta_audios, f"{conversation_id}.WAV")

    # Verifica si el archivo existe antes de servirlo
    if os.path.exists(archivo_audio):
        return send_file(archivo_audio, as_attachment=True, download_name=f"{conversation_id}.WAV")
    else:
        flash("El archivo de audio no existe.", "error")
        return redirect(url_for('index'))

def obtener_token_de_acceso(token_url):
    # Realiza una solicitud para obtener el token de acceso
    response = requests.get(token_url)
    if response.status_code == 200:
        access_token = response.json().get('token')
        return access_token
    else:
        print(f"Error al obtener el token de acceso: {response.status_code}")
        return None

def obtener_recording(token, conversation_id, host):
    # Obtiene los metadatos de grabación de una conversación específica
    url = f"{host}/api/v2/conversations/{conversation_id}/recordingmetadata"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()  # Aquí se obtiene directamente la lista
    else:
        print(f"Error al obtener el recording id de la conversación {conversation_id}: {response.status_code}, {response.text}")
        return []

def obtener_detalles_recording(token, conversation_id, recording_id, host):
    # Intenta obtener los detalles de la grabación, incluyendo mediaUri y nombre de usuario
    url = f"{host}/api/v2/conversations/{conversation_id}/recordings/{recording_id}?formatId=WAV&download=true"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    intentos = 0
    max_intentos = 10  # Número máximo de intentos

    while intentos < max_intentos:
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            recording_details = response.json()
            media_uri = recording_details.get('mediaUris', {}).get('S', {}).get('mediaUri')
            user_name = recording_details.get('users', [{}])[0].get('name', 'Nombre no encontrado')

            if media_uri:
                return media_uri, user_name
            else:
                print("No se encontró mediaUri en la respuesta.")
                return None, None
        elif response.status_code == 202: # Si el archivo aún se está procesando
            intentos += 1
            time.sleep(20)
        else:
            print(f"Error al obtener los detalles del recording {recording_id}: {response.status_code}, {response.text}")
            return None, None

    return None, None

def descargar_audio(media_uri, conversation_id, user_name):
    # Verifica la carpeta de audios y descarga el archivo desde mediaUri
    carpeta_audios = 'audios'
    if not os.path.exists(carpeta_audios):
        os.makedirs(carpeta_audios)
    
    nombre_archivo = f"{carpeta_audios}/{conversation_id}.WAV"
    
    if os.path.exists(nombre_archivo):
        print(f"El archivo '{nombre_archivo}' ya existe. No se descargará nuevamente.")
        return nombre_archivo

    try:
        print(f"Intentando descargar el archivo desde: {media_uri}")
        response = requests.get(media_uri)
        if response.status_code == 200:
            with open(nombre_archivo, 'wb') as audio_file:
                audio_file.write(response.content)
            print(f"Archivo de audio descargado y guardado como: {nombre_archivo}")
            return nombre_archivo
        else:
            print(f"Error al descargar el archivo de audio. Código de estado: {response.status_code}")
            print(f"Contenido de la respuesta: {response.text}")
            return None
    except Exception as e:
        print(f"Ocurrió un error al descargar el archivo: {str(e)}")
        return None

def transcribir_audio(ruta_audio):
    # Transcribe el audio usando OpenAI y devuelve el texto
    try:
        with open(ruta_audio, 'rb') as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file, 
                response_format="text"
            )
            return transcription
    except Exception as e:
        print(f"Error durante la transcripción: {str(e)}")
        return None

def enviar_al_asistente(transcription, user_name):
    # Envía la transcripción al asistente de OpenAI y recupera la respuesta
    thread = client.beta.threads.create()
    thread_id = thread.id
    message_content = f"Transcripción: {transcription}. Asesor Educativo: {user_name}"
    print(f"Esto es lo que le estoy enviando al asistente: {message_content}")

    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=message_content
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    run = client.beta.threads.runs.retrieve(
        thread_id=thread_id,
        run_id=run.id
    )

    if run.status == 'completed':
        messages = client.beta.threads.messages.list(thread_id=thread_id)
        if messages.data and messages.data[0].content and messages.data[0].content[0].text:
            return limpiar_referencias(messages.data[0].content[0].text.value)
    return None

def limpiar_referencias(texto):
    # Elimina referencias en el texto usando expresiones regulares
    patron_referencias = r'【[^】]*\.pdf】|【[^\】]*†[^\】]*】'
    return re.sub(patron_referencias, '', texto)

if __name__ == '__main__':
    # Inicia la aplicación Flask en modo debug
    app.run(debug=True)
