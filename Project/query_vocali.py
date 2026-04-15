
import json
import time
import os
from speech2txt import *
from mongo import get_database_connection
from LLM import chiedi_a_llama
import re

def esegui_query_vocale(testo_utente, esempio_json):
    """
    Interpreta il testo naturale con LLaMA4 e interroga MongoDB.
    Ritorna i risultati della query.
    """

    esempio_testuale = json.dumps(esempio_json, indent=2)

    prompt = f"""
Hai ricevuto una domanda in linguaggio naturale da un operatore sanitario.
Il tuo compito è trasformarla in una query MongoDB in formato JSON,
che verrà eseguita sul database di cartelle cliniche.

📌 Esempio di cartella clinica reale (per capire i valori corretti e i nomi dei campi):

{esempio_testuale}

⚠️ Regole importanti:
- Usa i valori come nello schema: "sesso" deve essere "M" o "F", non "uomo"/"donna".
- Non usare operatori avanzati come $text o $where.
- La tua risposta deve essere solo il JSON valido della query, senza commenti o spiegazioni.
- Quando cerchi patologie o sintomi testuali, usa $regex con pattern che trovano tutte le varianti. Ad esempio:
  "covid.*" per trovare "covid", "covid19", "covid-19", ecc.
- Usa sempre "$options": "i" per ignorare maiuscole/minuscole.

Domanda dell'utente:
\"\"\"{testo_utente}\"\"\"
"""

    output = chiedi_a_llama(prompt)

    try:
        start = output.find("{")
        end = output.rfind("}") + 1
        json_clean = output[start:end]

        # 🩹 Correggi chiavi come $regex → "$regex"
        json_clean = re.sub(r'([{,]\s*)(\$[a-zA-Z0-9_]+)\s*:', r'\1"\2":', json_clean)

        query_dict = json.loads(json_clean)
    except Exception as e:
        raise ValueError(f"Errore nel parsing del JSON da LLaMA4: {str(e)}\nOutput:\n{output}")

    print(f"Query generata: {json.dumps(query_dict, indent=2)}")

    collection = get_database_connection()
    risultati = list(collection.find(query_dict, {"_id": 0}))
    return risultati
