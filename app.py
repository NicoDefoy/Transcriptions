from flask import Flask, render_template, request, jsonify
import os
import whisper
from werkzeug.utils import secure_filename
from pydub import AudioSegment
from fpdf import FPDF

# Initialiser l'application Flask
app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Charger le modèle Whisper
model = whisper.load_model("base")

# Page d'accueil
@app.route('/')
def index():
    return render_template("index.html")

# Route pour gérer la transcription
@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error": "Aucun fichier fourni"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nom de fichier vide"}), 400
    
    # Sécuriser le nom de fichier et enregistrer
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    # Convertir le fichier en .wav si nécessaire
    if not file_path.endswith('.wav'):
        audio = AudioSegment.from_file(file_path)
        file_path_wav = os.path.splitext(file_path)[0] + ".wav"
        audio.export(file_path_wav, format="wav")
        os.remove(file_path)
        file_path = file_path_wav

    # Transcrire l'audio avec Whisper
    result = model.transcribe(file_path)
    transcription_text = result["text"]

    # Créer un PDF de la transcription
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, transcription_text)
    pdf_output_path = os.path.splitext(file_path)[0] + ".pdf"
    pdf.output(pdf_output_path)

    # Supprimer le fichier audio après la transcription
    os.remove(file_path)

    # Retourner la transcription et le lien de téléchargement du PDF
    return jsonify({
        "transcription": transcription_text,
        "pdf_path": pdf_output_path
    })

# Exécuter l'application
if __name__ == '__main__':
    app.run(debug=True)
