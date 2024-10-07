from flask import Flask, request, send_file, jsonify, render_template
from pydub import AudioSegment
import whisper
from fpdf import FPDF
import os
import ssl

# Désactiver la vérification SSL temporairement
ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__)

# Fonction pour ajouter des points et des retours à la ligne pour la lisibilité
def format_transcription(text):
    sentences = text.split('.')
    formatted_text = ""
    for sentence in sentences:
        sentence = sentence.strip().capitalize()
        if sentence:
            formatted_text += sentence + ".\n\n"
    return formatted_text

# Fonction pour créer un PDF en UTF-8
def create_pdf(transcription, filename="transcription.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, transcription.encode('latin-1', 'replace').decode('latin-1'))
    pdf.output(filename)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    temp_filename = "temp_audio.wav"
    
    # Convertir en .wav si nécessaire
    if file.filename.endswith('.m4a'):
        audio = AudioSegment.from_file(file)
        audio.export(temp_filename, format="wav")
    else:
        file.save(temp_filename)
    
    try:
        # Transcription avec Whisper
        model = whisper.load_model("base")
        result = model.transcribe(temp_filename)
        transcription = result["text"]
        
        # Mise en forme de la transcription
        formatted_transcription = format_transcription(transcription)
        
        # Création du PDF
        pdf_filename = "transcription.pdf"
        create_pdf(formatted_transcription, pdf_filename)
        
        # Supprimer le fichier temporaire
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
        
        # Envoi du PDF
        return send_file(pdf_filename, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
