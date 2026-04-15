
import streamlit as st
from speech2txt import *
import numpy as np
from groq import Groq
import time     
from datetime import datetime  
     

groq_client = Groq(api_key="")


def chiedi_a_llama(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Tentativo {attempt + 1} fallito: {e}")
            time.sleep(3)
    return "Errore persistente."



def costruisci_prompt(testo_audio):
    with open("json_samples/cartella_clinica_vuota.json", "r", encoding="utf-8") as f:
        json_vuoto = f.read()

    with open("json_samples/json_esempio.json", "r", encoding="utf-8") as f:
        esempio_compilato = f.read()

    prompt = f"""
Sei un esperto di medicina d'urgenza. Hai due input:
1. Una trascrizione audio convertita in testo.
2. Un oggetto JSON che rappresenta una cartella clinica **vuota**.

🎯 Il tuo compito:
- Compila il più possibile i campi del JSON **solo con le informazioni presenti nella trascrizione**.
- Non inventare nulla. Se un campo non è menzionato, lascialo vuoto come nel JSON di partenza.
- Mantieni **intatta la struttura del JSON**: non aggiungere nuove chiavi, non rimuoverle.
- Compila i valori usando lo stile coerente (formati corretti, dizionari, liste, numeri reali).
- NON cambiare o rinominare le chiavi. Le chiavi devono rimanere ESATTAMENTE quelle presenti nel JSON da migliorare (es. 'respiro', 'cute', 'coscienza' devono essere dizionari).
- Ricavare campi non presenti nel JSON ma deducibili dalla trascrizione, come `sesso` derivandolo dal nome, età (calcolandola dalla data), etc.

📌 Formati attesi:
- Date: `YYYY-MM-DD`
- Orari: `HH:MM` (24h)
- Numeri reali dove previsto (es. temperatura, glicemia)
- Nessun campo va rimosso
- Nessun testo libero o markdown: **rispondi solo con JSON puro**

📦 Esempio di JSON compilato correttamente:
{esempio_compilato}

---

📄 Trascrizione:
\"\"\"{testo_audio.strip()}\"\"\"

📦 JSON da completare:
{json_vuoto}
RISPETTA rigorosamente questa struttura.
Rispondi con **solo il JSON compilato**.
"""
    return prompt


# Funzione di pulizia dell'output
def estrai_json_pulito(output):
    output = output.strip()

    # Rimuove blocchi markdown tipo ```json ... ```
    if output.startswith("```"):
        lines = output.splitlines()

        # Rimuove prima e ultima riga se iniziano con ```
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]

        output = "\n".join(lines)

    return output




