import whisper
import os
import streamlit as st
import soundfile as sf
import librosa

# Carica il modello solo una volta
model = whisper.load_model("medium")

def transcribe_audio(file_path: str) -> str:
    """
    Trascrive un file audio in testo usando Whisper.
    Controlla che l'audio sia valido prima della trascrizione.
    """
    if not os.path.exists(file_path):
        return "❌ File audio non trovato."

    try:
        # Carica l'audio per controllare la durata
        y, sr = librosa.load(file_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)

        if duration < 1.0:
            return "❌ Audio troppo breve per essere trascritto, si prega di riprovare."

        # Procedi con la trascrizione
        result = model.transcribe(file_path)
        return result["text"]

    except Exception as e:
        return f"❌ Errore durante la trascrizione: {str(e)}"
