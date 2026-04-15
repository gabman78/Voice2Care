import streamlit as st
import json
import time
import streamlit as st
from groq import Groq
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches

groq_client = Groq(api_key="")

def estrai_json_pulito(output):
    output = output.strip()
    if output.startswith("```"):
        lines = output.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        output = "\n".join(lines)
    return output

def costruisci_prompt_heatmap(json_data):
    sintomi = json_data.get("sintomi_principali", [])
    lesioni = json_data.get("lesioni_riscontrate", [])
    annotazioni = json_data.get("annotazioni", "")

    testo = "\n".join(sintomi + lesioni + [annotazioni])

    prompt = f"""
Sei un assistente medico esperto in comprensione clinica del linguaggio naturale.

Hai il compito di analizzare i seguenti testi (sintomi, lesioni, annotazioni) per estrarre **manifestazioni localizzate** su specifiche parti del corpo.

📦 Output atteso:
Un oggetto JSON dove:
- Le **chiavi** sono zone anatomiche (in italiano) scelte **solo tra**:
  "testa", "collo", "torace", "addome", "schiena",
  "braccio sinistro", "gomito sinistro", "mano sinistra",
  "braccio destro", "gomito destro", "mano destra",
  "bacino",
  "gamba sinistra", "ginocchio sinistro", "piede sinistro",
  "gamba destra", "ginocchio destro", "piede destro"
- I **valori** sono liste di sintomi o lesioni localizzate in quella zona.

🔁 Gestione delle varianti:
- Riconosci **sinonimi** e abbreviazioni (es: "ginocchio dx" = "ginocchio destro", "arto inferiore sinistro" ≈ "gamba sinistra").
- Interpreta anche le **formulazioni indirette** ("dolore al lato sinistro del ginocchio", "ematoma al braccio dx").
- Considera singolari, plurali e aggettivi ("gomiti gonfi", "alle ginocchia", "alla mano sinistra").
- Non generalizzare: se trovi “ginocchio” o “gomito”, **non usare** “gamba” o “braccio”, ma la parte esatta.
- Se una zona non è elencata tra le chiavi permesse, **ignora**.

📄 Testo clinico da analizzare:
\"\"\"{testo}\"\"\"

✅ Rispondi con **solo** un oggetto JSON valido. Nessuna spiegazione, niente testo extra.
"""
    return prompt


def chiedi_a_llama_heatmap(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = groq_client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Tentativo {attempt + 1} fallito: {e}")
            time.sleep(3)
    return "Errore persistente."

def mappa_zone_con_llama(json_data):
    prompt = costruisci_prompt_heatmap(json_data)
    output = chiedi_a_llama_heatmap(prompt)
    try:
        pulito = estrai_json_pulito(output)
        return json.loads(pulito)
    except Exception as e:
        st.error("❌ Errore nel parsing del JSON generato da LLaMA.")
        st.code(output)
        return {}

#per il pdf
def salva_heatmap(json_data, image_path="images/corpo.png", output_path="moduli/heatmap.png"):
    zone_mappate = mappa_zone_con_llama(json_data)

    body_zones = {
        "testa": (512, 160), "collo": (512, 280), "torace": (512, 360),
        "addome": (512, 560), "schiena": (512, 600), "gomito sinistro": (760, 560),
        "gomito destro": (260, 560), "braccio sinistro": (730, 480), "braccio destro": (310, 480),
        "mano sinistra": (820, 800), "mano destra": (200, 800), "bacino": (512, 740),
        "ginocchio destro": (400, 1080), "ginocchio sinistro": (624, 1080),
        "gamba sinistra": (400, 1250), "gamba destra": (624, 1250),
        "piede sinistro": (400, 1430), "piede destro": (624, 1430)
    }

    img = Image.open(image_path)
    fig, ax = plt.subplots(figsize=(6, 9))
    ax.imshow(img)

    ax.set_title("Heatmap Lesioni/Traumi", fontsize=18, weight='bold', color='black', pad=20)
    
    for zona, sintomi in zone_mappate.items():
        if zona in body_zones:
            x, y = body_zones[zona]
            ax.add_patch(patches.Circle((x, y), radius=60, color='red', alpha=0.4))
            ax.text(x, y - 70, zona, fontsize=8, color='red', ha='center')

    ax.axis('off')
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
    return output_path


def visualizza_heatmap(json_data, image_path="images/corpo.png"):
    # 1. Ottieni mappatura da LLaMA
    zone_mappate = mappa_zone_con_llama(json_data)

    # 2. Coordinate anatomiche
    body_zones = {
        "testa": (512, 160),
        "collo": (512, 280),
        "torace": (512, 360),
        "addome": (512, 560),
        "schiena": (512, 600),
        "gomito sinistro": (760, 560),
        "gomito destro": (260, 560),
        "braccio sinistro": (730, 480),
        "braccio destro": (310, 480),
        "mano sinistra": (820, 800),
        "mano destra": (200, 800),
        "bacino": (512, 740),
        "ginocchio destro": (400, 1080),
        "ginocchio sinistro": (624, 1080),
        "gamba sinistra": (400, 1250),
        "gamba destra": (624, 1250),
        "piede sinistro": (400, 1430),
        "piede destro": (624, 1430)
    }

    try:
        img = Image.open(image_path)
    except Exception as e:
        st.error(f"Errore nel caricamento dell'immagine: {e}")
        return

    fig, ax = plt.subplots(figsize=(6, 9))
    ax.imshow(img)

    for zona, sintomi in zone_mappate.items():
        if zona in body_zones:
            x, y = body_zones[zona]
            ax.add_patch(patches.Circle((x, y), radius=60, color='red', alpha=0.4))
            ax.text(x, y - 70, zona, fontsize=8, color='red', ha='center')
        else:
            st.warning(f"⚠️ Zona '{zona}' non mappata nel body_zones.")

    ax.axis('off')
    ax.set_title("Heatmap zone interessate", fontsize=16, fontweight='bold')
    st.pyplot(fig)