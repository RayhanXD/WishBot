from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, join_room, leave_room
from dotenv import load_dotenv
import requests
import os

load_dotenv()

from openai import OpenAI
from groq import Groq

client = Groq(
    api_key=os.getenv('GROQ_API_KEY'),
)
api_key_open = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = '/Users/rayhanmohammad/cursor-ai-project/UPLOAD_FOLDER'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Global variable to store chat history
chat_history = [
    {"role": "system", "content": "You are a helpful assistant."}
]

@app.route('/')
def home():
    return render_template('index3.html')

@app.route('/upload/<id>', methods=['POST'])
def upload(id):
    connection_id = id
    
    audio_file = request.files['file']
    audio_file.save('audio.webm')

    with open('audio.webm', 'rb') as f:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key_open}"},
            files={"file": f},
            data={"model": "whisper-1"}
        )
    transcript = response.json()
    app.logger.info("Transcription Response: %s", transcript)  # Add this line for logging

    user_message = {
        "role": "user",
        "content": transcript["text"]
    }
    
    chat_history.append(user_message)
    
    chat_response = client.chat.completions.create(
        messages=chat_history,
        model="Llama3-70b-8192",
        max_tokens=300,
        stream=True,
    )
    
    socketio.emit('user_text', {'data': transcript['text']}, to=connection_id)

    for chunk in chat_response:
        app.logger.info("Chat Response Chunk: %s", chunk)  # Add this line for logging
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            socketio.emit('chatbot_text', {'data': chunk.choices[0].delta.content}, to=connection_id)
            assistant_message = {
                "role": "assistant",
                "content": chunk.choices[0].delta.content
            }
            chat_history.append(assistant_message)

    return '', 200

@socketio.on('connect')
def handle_connect():
    connection_id = request.sid  # Get the session ID
    join_room(connection_id)  # Join a unique room based on the session ID
    print(f"Client {connection_id} connected and joined room.")

@socketio.on('disconnect')
def handle_disconnect():
    connection_id = request.sid  # Get the session ID
    leave_room(connection_id)  # Leave the unique room based on the session ID
    print(f"Client {connection_id} disconnected and left room.")

if __name__ == '__main__':
    socketio.run(app, port=8000)
