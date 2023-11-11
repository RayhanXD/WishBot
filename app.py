from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import requests
from openai import OpenAI
import os

client = OpenAI()

load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = '/Users/rayhanmohammad/cursor-ai-project/UPLOAD_FOLDER'

@app.route('/')
def home():
    return render_template('index2.html') #reads HTML file from templates folder

@app.route('/upload', methods=['POST'])
def upload():
    audio_file = request.files['file']
    audio_file.save('audio.webm')

    # Now you can use the saved audio file for further processing
    with open('audio.webm', 'rb') as f:
        response = requests.post(
            "https://api.openai.com/v1/audio/transcriptions",
            headers={"Authorization": f"Bearer {api_key}"},
            files={"file": f},
            data={"model": "whisper-1"}
        )
    transcript = response.json()
    print(transcript["text"])

    # Send the transcribed text to the ChatCompletion API
    chat_response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": transcript["text"]
            }
        ],
        max_tokens=300,
    )

    # Return the assistant's reply
    return chat_response.choices[0].message.content

if __name__ == '__main__':
    app.run(port=8000)