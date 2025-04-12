import os
from flask import Flask, render_template, request, redirect, send_from_directory, flash
from datetime import datetime
from gtts import gTTS

import vertexai
from vertexai.preview.generative_models import GenerativeModel, Part

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
BOOK_FOLDER = 'books'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(BOOK_FOLDER, exist_ok=True)

ALLOWED_AUDIO = {'wav'}
ALLOWED_BOOKS = {'pdf'}
BOOK_PATH = os.path.join(BOOK_FOLDER, 'book.pdf')

def allowed_file(filename, allowed_set):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_set

def text_to_speech(text, output_path):
    tts = gTTS(text)
    tts.save(output_path)

def transcribe_audio_with_gemini(file_path):
    vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"), location="us-central1")
    model = GenerativeModel("gemini-1.5-pro")
    with open(file_path, "rb") as f:
        audio_part = Part.from_data(data=f.read(), mime_type="audio/wav")

    prompt = "Transcribe the user's speech."
    response = model.generate_content([prompt, audio_part])
    return response.text.strip()

def ask_question_with_pdf(question):
    vertexai.init(project=os.getenv("GOOGLE_CLOUD_PROJECT"), location="us-central1")
    model = GenerativeModel("gemini-1.5-pro")

    if not os.path.exists(BOOK_PATH):
        return "No book uploaded. Please select a PDF."

    with open(BOOK_PATH, "rb") as f:
        pdf_part = Part.from_data(data=f.read(), mime_type="application/pdf")

    prompt = f"""You're a helpful assistant. Use the book to answer the user's question. Keep the response short and concise.

Question: {question}
Answer:"""

    response = model.generate_content([prompt, pdf_part])
    return response.text.strip()

@app.route('/')
def index():
    files = [f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f, ALLOWED_AUDIO)]
    return render_template('index.html', files=sorted(files, reverse=False))

@app.route('/upload', methods=['POST'])
def upload():
    audio = request.files.get('audio_data')
    book = request.files.get('book')

    if not audio:
        return "Audio is missing", 400

    filename = datetime.now().strftime("%Y%m%d-%I%M%S%p") + '.wav'
    audio_path = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(audio_path)

    if book and allowed_file(book.filename, ALLOWED_BOOKS):
        book.save(BOOK_PATH)

    question = transcribe_audio_with_gemini(audio_path)
    answer = ask_question_with_pdf(question)

    with open(audio_path + '.txt', 'w') as f:
        f.write(f"Q: {question}\nA: {answer}")

    tts_path = audio_path.replace('.wav', '_response.mp3')
    text_to_speech(answer, tts_path)

    return redirect('/')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/script.js')
def serve_script():
    return send_from_directory('', 'script.js')

if __name__ == '__main__':
    # app.run(debug=True)
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
