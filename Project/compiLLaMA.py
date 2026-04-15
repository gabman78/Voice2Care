
import json
import time
from groq import Groq
from fpdf import FPDF
from PIL import Image
import os

groq_client = Groq(api_key="")



# Funzione per pulire l’output LLaMA
def estrai_json_pulito(output):
    output = output.strip()
    if output.startswith("```"):
        lines = output.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        output = "\n".join(lines)
    return output


def costruisci_prompt_pdf(json_data):
    json_input = json.dumps(json_data, ensure_ascii=False, indent=2)
    json_input = json_input.replace("{", "{{").replace("}", "}}")
    return f"""
    Sei un esperto soccorritore e devi compilare un modulo PDF di cartella clinica pre-ospedaliera.

    Hai a disposizione un file JSON contenente i dati estratti, ma alcuni campi
    potrebbero dover essere dedotti in questa fase (es. numero civico o provincia di nascita).

    ✅ **Prima di tutto**, estrai o costruisci questi campi:
    - `residenza.civico`: se `residenza.via` contiene un numero (es. 'Via Roma 123'), separalo.
    - `provincia_nascita`: se `luogo_nascita` è un comune italiano noto, deduci la provincia, non la regione (es. 'NA' da 'Massa di Somma').
    - `equipaggio`: contiene autista, soccorritore e medico, voglio suddividerli in campi distinti. 
    - in `annotazioni` fai tui un riassunto dei campi `allergie`, `patologie`, `lesioni`.
    - prima dei valori `trattamenti effettuati` ed `esami diagnostici` vorrei che fosse riportato il nome della dicitura, come 'Trattamenti effettuati:' e 'Esami diagnostici:'.
    - espandi il campo `farmaci` come Farmaco1, Farmaco2, etc., se presenti piu farmaci, seguendo le posizioni indicate.
    - il campo `ora_intervento` è riportato due volte per due posizioni diverse
    - ricava se possibile il campo `sesso` come 'M' o 'F'
    - se il JSON contiene i valori `Glasgow Coma Scale Iniziale`con le tre componenti `oculare`, `verbale`, `motoria`, calcola la loro somma e scrivila come numero nella posizione: x=112.5, y=214


    ✅ **Poi**, procedi alla mappatura coordinata dei campi (testi e checkbox)...

    ---

    ✅ CAMPI TESTUALI:
    - Cognome + Nome: x=25, y=73
    - Data di nascita: x=15, y=78
    - Età: x=100, y=73
    - Luogo di nascita: x=45, y=78
    - Provincia di nascita: x=135, y=78
    - Via: x=10, y=89
    - Civico: x=130, y=89
    - Comune residenza: x=20, y=84
    - Provincia residenza: x=135, y=84 
    - Telefono: x=15, y=94
    - Data intervento: x=20, y=7
    - Luogo intervento: x=76, y=7
    - Condizione riferita: x=55, y=28
    - Autista: x=172, y=17
    - Soccorritore: x=172, y=23
    - Medico: x=175, y=44

    - Sintomi principali: x=55, y=33

    - Farmaco1: x=171, y=238 
    - Farmaco2: x=171, y=242
    - Farmaco3: x=171, y=246
    - Farmaco4: x=171, y=250 
    - Farmaco5: x=171, y=254
    - Farmaco6: x=171, y=258

    - Ora intervento1: x=35, y=127
    - Ora intervento2: x=20, y=12
    - SpO₂: x=31, y=191
    - FC bpm: x=30, y=197
    - PA mmHg: x=30, y=205
    - Glicemia: x=30, y=212
    - Temperatura: x=30, y=220

    - Annotazioni: x=5, y=273
    - Trattamenti effettuati: x=5, y=278.5
    - Esami diagnostici: x=5, y=283.5
    ---

    ☑️ CHECKBOX (posizioni da spuntare obbligatoriamente se presenti campi validi):

    Restituisci come: {{"x": float, "y": float}}

    ❗ Alcuni gruppi sono **mutuamente esclusivi**: scegli solo **una** voce per ciascuno dei seguenti gruppi:
    - `Sesso`: solo una tra M o F
    - `Codice uscita`: solo una tra Bianco, Verde, Giallo, Rosso , da non confondere con `Codice rientro`
    - `Codice rientro`: solo una tra Bianco, Verde, Giallo, Rosso, da non confondere con `Codice uscita`
    - `Coscienza Stato`: solo una tra Vigile, Risposta verbale, Risposta fisica, Incosciente
    - `Cute Colore`: solo una tra Normale, Pallida, Cianotica, Sudata
    - `Respiro Tipo`: solo una tra Normale, Tachipnoico, Bradipnoico, assente
    - `Reattivita pupille`: Se entrambi gli occhi SX e DX sono "Reattiva", spunta Reattiva. In ogni altro caso (anche uno solo "Non reattiva"), spunta solo Non reattiva.
    - `Pupilla DX`: dimensione pupilla (scegli solo una): Dilatata, Ristretta, Normale
    - `Pupilla SX`: dimensione pupilla (scegli solo una): Dilatata, Ristretta, Normale

    ❗ OBBLIGHI IMPORTANTI per la gestione delle CHECKBOX:

    - Tutti i gruppi mutuamente esclusivi devono avere una checkbox selezionata.
    - È obbligatorio dedurre il valore corretto anche in presenza di sinonimi o dati parziali.
    - Non saltare checkbox per ambiguità: seleziona quella più coerente.
    - In caso di condizioni multiple, scegli quella più significativa.
    - In assenza di dati espliciti, usa inferenza ragionata.
    - Nessun gruppo può essere lasciato vuoto: ogni omissione è un errore.
    - In `Provvedimenti` considera esclusivamente i campi del json `Provvedimenti-prima valutazione` e `Provvedimenti - ospedale` spuntando solo i provvedimenti chiaramente menzionati o con sinonimi.

    - Sesso:
        - M: x=139, y=73.5
        - F: x=146.5, y=73.5

    - Codice uscita: Bianco=27, Verde=37, Giallo=48, Rosso=58 (y=45)
    - Codice rientro: Bianco=105, Verde=115, Giallo=125, Rosso=136 (y=45)

    - Attivazioni:
        - Carabinieri: x=0.5, y=56
        - Polizia stradale: x=32, y=56
        - Polizia Municipale: x=63, y=56
        - Vigili del Fuoco: x=95, y=56
        - Guardia Medica: x=126, y=56
        - 118: x=0.5, y=60
        - Automedica: x=32, y=60
        - Elisoccorso: x=63, y=60

    - Pupilla DX:
        - Dilatata: x=190, y=141
        - Ristretta: x=190, y=133
        - Normale: x=190, y=137

    - Pupilla SX:
        - Dilatata: x=172, y=141
        - Ristretta: x=172, y=133
        - Normale: x=172, y=137

    - Reattività pupille:
        - Reattiva: x=192, y=127
        - Non reattiva: x=199, y=127

    - Firma rifiuto: x=180, y=115
    - Firma decesso: x=180, y=100

    - Coscienza Stato:
        - Vigile: x=26.5, y=132.5
        - Risposta verbale: x=26.5, y=134
        - Risposta fisica: x=26.5, y=138
        - Incosciente: x=26.5, y=146

    - Cute colore:
        - Normale: x=26.5, y=151
        - Pallida: x=26.5, y=155
        - Cianotica: x=26.5, y=156
        - Sudata: x=26.5, y=160

    - Respiro Tipo:
        - Normale: x=26.5, y=169
        - Tachipnoico: x=26.5, y=173
        - Bradipnoico: x=26.5, y=177
        - Assente: x=26.5, y=181

    - Provvedimenti:
        - Aspirazione: x=0.5, y=239
        - Cannula orofaringea: x=0.5, y=243
        - Saturazione (SpO₂) : x=0.5, y=247 
        - Ossigeno: x=0.5, y=251
        - Intubazione: x=0.5, y=255
        - Emostasi: x=42, y=239
        - Accesso venoso: x=42, y=243
        - Elettrocardiogramma (ECG): x=42, y=247
        - Pressione Sanguigna (NIBP): x=42, y=251
        - Monitoraggio Cardiaco Elettronico (MCE): x=42, y=255
        - Defibrillatore (DAE): x=42, y=259
        - Collare cervicale: x=84, y=239
        - KED: x=84, y=243
        - Barella cucchiaio: x=84, y=247
        - Tavola spinale: x=84, y=251
        - Steccobenda: x=84, y=255
        - Materassino depressione: x=84, y=259
        - Coperta isotermica: x=126, y=239
        - Medicazione: x=126, y=243
        - Ghiaccio: x=126, y=247
        - Osservazione: x=126, y=251

    -Glasgow Coma Scale Iniziale: 
        - oculare:
            4: x=133.5, y=140
            3: x=133.5, y=144
            2: x=133.5, y=148
            1: x=133.5, y=152
        - verbale:
            5: x=133.5, y=159
            4: x=133.5, y=163
            3: x=133.5, y=167
            2: x=133.5, y=171
            1: x=133.5, y=175
        - motoria:
            6: x=133.5, y=182
            5: x=133.5, y=186
            4: x=133.5, y=191
            3: x=133.5, y=195
            2: x=133.5, y=200
            1: x=133.5, y=204
            
    ---


    🎯 Obiettivo:
    Analizza il seguente JSON dati paziente e restituisci **ESCLUSIVAMENTE** un oggetto JSON valido con due chiavi:

    - `"testi"`: array di oggetti `{{ "x": int, "y": int, "valore": string }}`
    - `"checkbox"`: array di oggetti `{{ "x": float, "y": float }}`

    📥 Esempio atteso:
    {{
      "testi": [
        {{ "x": 20, "y": 7, "valore": "2025-06-06" }},
        {{ "x": 76, "y": 7, "valore": "Pronto Soccorso Ospedale del Mare" }}
      ],
      "checkbox": [
        {{ "x": 48, "y": 67 }},
        {{ "x": 100, "y": 75 }}
      ]
    }}

    ❌ NON includere codice Markdown (niente ```json).
    ❌ NON aggiungere spiegazioni, note, commenti o testo fuori dal JSON.

    📦 JSON input:
    {json_input}
    """

# Funzione per compilare effettivamente il PDF
def esporta_cartella_pdf_da_istruzioni(istruzioni, json_data, filename="cartella.pdf"):
    output_dir = "static/pdf_cartelle"
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    pdf = FPDF(format='A4')
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    img_path = "images/cartella_clinica_vuota.png"
    img = Image.open(img_path)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img.save("moduli/tmp_modulo_resized.jpg")
       
    pdf.image("moduli/tmp_modulo_resized.jpg",x=0, y=0, w=210, h=297)

    from heatmap import salva_heatmap
    heatmap_path = salva_heatmap(json_data, image_path="images/corpo.png", output_path="moduli/heatmap.png")
    if os.path.exists(heatmap_path):
        pdf.image(heatmap_path, x=157, y=145, w=53, h=82)
    pdf.set_font("Arial", size=8)

    def scrivi(x, y, testo):
        pdf.set_xy(x, y)
        pdf.cell(0, 5, str(testo), ln=0)

    def spunta_checkbox(x, y):
        pdf.set_xy(x, y)
        pdf.set_font("Arial", size=10)
        pdf.cell(5, 5, "X")

    for campo in istruzioni.get("testi", []):
        scrivi(campo["x"], campo["y"], campo["valore"])

    for check in istruzioni.get("checkbox", []):
        spunta_checkbox(check["x"], check["y"])

    pdf.output(output_path)
    print(f"✅ PDF creato: {output_path}")
    return output_path
