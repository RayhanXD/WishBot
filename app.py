from flask import Flask, render_template, request
from flask_socketio import SocketIO
from dotenv import load_dotenv
import requests
from openai import OpenAI
from groq import Groq
import os

load_dotenv()  # Add this line if it's not already present
client = Groq(
    api_key=os.getenv('GROQ_API_KEY'),
)
api_key_open = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/Users/rayhanmohammad/cursor-ai-project/UPLOAD_FOLDER'
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

chat_history = [
    {"role": "system", "content": "You are a helpful assistant."}
]

@app.route('/')
def home():
    return render_template('index3.html') #reads HTML file from templates folder

@app.route('/upload/<id>', methods=['POST'])
def upload(id):
    audio_file = request.files['file']
    audio_file.save('audio.webm')
    connectionID = id

    # Now you can use the saved audio file for further processing
    with open('audio.webm', 'rb') as f:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key_open}"},
            files={"file": f},
            data={"model": "whisper-1"}
        )
    transcript = response.json()

    user_message = {
        "role": "user",
        "content": transcript["text"]
    }

    chat_history.append(user_message)

    chat_response = client.chat.completions.create(
        messages=chat_history,
        model="mixtral-8x7b-32768",
        max_tokens=300,
        stream=True,
    )
    
    socketio.emit('user_text', {'data': transcript['text']})

    for chunk in chat_response:
        if chunk.choices[0].delta.content is not None:
            print(chunk.choices[0].delta.content, end="")
            socketio.emit('chatbot_text', {'data': chunk.choices[0].delta.content})
            assistant_message = {
                "role": "assistant",
                "content": chunk.choices[0].delta.content
            }
            chat_history.append(assistant_message)

    return '', 200

if __name__ == '__main__':
    socketio.run(app, port=8000)