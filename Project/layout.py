import base64
import streamlit as st
import json
import html
import re
from bson import ObjectId
from heatmap import *
import uuid

def aggiungi_sfondo(image_path: str):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def converti_objectid(obj):
    if isinstance(obj, dict):
        return {k: converti_objectid(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [converti_objectid(item) for item in obj]
    elif isinstance(obj, ObjectId):
        return str(obj)
    else:
        return obj


def normalizza_markdown_grassetto(testo):
    # Trasforma "** Morfina **" in "**Morfina**"
    return re.sub(r"\*\*\s*(.*?)\s*\*\*", r"**\1**", testo)

def pulsanti_home_stilizzati():
    st.markdown(
        """
        <style>
        .stButton>button {
            border: none;
            width: 250px;
            height: 180px;
            border-radius: 20px;
            font-size: 40px !important;
            font-weight: 1200 !important;
            color: #2484A1;
            background-color: #ffffff10;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            cursor: pointer;
            margin: 20px auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            line-height: 1.4;
            text-align: center;
        }

        .stButton>button:hover {
            transform: scale(1.05);
            background-color: #ffffff20;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📤\nCarica\nAudio"):
            st.session_state.page = "carica_audio"
            st.rerun()

    with col2:
        if st.button("🎤\nRegistra\nAudio"):
            st.session_state.page = "registrazione"
            st.rerun()




def titolo_home():
    # Centrare immagine usando le colonne
    col1, col2, col3 = st.columns([2, 4, 1])
    with col2:
        st.image("images/logo.png", width=300)

    # Titolo e sottotitolo centrati
    st.markdown(
        """
        <style>
        .titolo-voice {
            text-align: center;
            font-size: 3em;
            font-weight: bold;
            color: #264972;
            margin-bottom: 0.3em;
        }

        .sottotitolo-voice {
            text-align: center;
            font-size: 2em;
            color: #264972;
            margin-top: 0.2em;
        }
        </style>

        <div class="sottotitolo-voice">👨🏼‍⚕️ Compila una cartella clinica con la tua voce</div>
        """,
        unsafe_allow_html=True
    )



def inietta_stile_pulsanti_generale():
    st.markdown(
        """
        <style>
        .stButton>button {
            border: none;
            width: 250px;
            height: 100px;
            border-radius: 20px;
            font-size: 25px !important;
            font-weight: 700;
            color: #2484A1;
            background-color: #ffffff10;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            cursor: pointer;
            margin: 20px auto;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            line-height: 1.4;
            text-align: center;
        }

        .stButton>button:hover {
            transform: scale(1.05);
            background-color: #ffffff20;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def mostra_json_stilizzato(data):
    st.markdown(f"""
    <div style="
        background-color: #cce6ff;
        padding: 12px;
        border-radius: 10px;
        font-size: 22px;
        font-weight: bold;
        text-align: center;
        color: #003366;
        margin-bottom: 15px;
    ">
        {data.get('cognome', '').upper()} {data.get('nome', '').capitalize()} ({data.get('id', 'N/D')})
    </div>
    """, unsafe_allow_html=True)

    def render_list(titolo, lista, icona="•"):
        st.markdown(f"#### {titolo}")
        if lista and isinstance(lista, list):
            for item in lista:
                if isinstance(item, dict):
                    for k, v in item.items():
                        st.markdown(f"{icona} **{k.capitalize()}:** {v}")
                else:
                    st.markdown(f"{icona} **{item}**")
        elif isinstance(lista, dict):
            for k, v in lista.items():
                st.markdown(f"{icona} **{k.capitalize()}:** {v}")
        else:
            st.markdown("—")

    def render_dict(titolo, diz):
        st.markdown(f"#### {titolo}")
        if isinstance(diz, dict):
            if diz:
                for k, v in diz.items():
                    st.markdown(f"- **{k.capitalize()}:** {v}")
            else:
                st.markdown("—")
        elif isinstance(diz, str):
            try:
                parsed = json.loads(diz)
                if isinstance(parsed, dict):
                    for k, v in parsed.items():
                        st.markdown(f"- **{k.capitalize()}:** {v}")
                else:
                    st.markdown("—")  # se non è un dizionario, ignoralo
            except Exception:
                st.markdown("—")  # fallback se parsing fallisce
        else:
            st.markdown("—")


    st.markdown("#### 👤 Dati anagrafici")
    st.markdown(f"- **Nome:** {data.get('nome', '—')}")
    st.markdown(f"- **Cognome:** {data.get('cognome', '—')}")
    st.markdown(f"- **Sesso:** {data.get('sesso', '—')}")
    st.markdown(f"- **Data di nascita:** {data.get('data_nascita', '—')}")
    st.markdown(f"- **Luogo di nascita:** {data.get('luogo_nascita', '—')}")
    st.markdown(f"- **Età:** {data.get('eta', '—')}")
    st.markdown(f"- **Codice Fiscale:** {data.get('id', '—')}")
    st.markdown(f"- **Telefono:** {data.get('telefono', '—')}")

    res = data.get("residenza", {})
    if isinstance(res, dict):
        st.markdown(f"- **Residenza:** {res.get('via', '')}, {res.get('comune', '')} ({res.get('provincia', '')})")
    elif isinstance(res, str):
        st.markdown(f"- **Residenza:** {res}")
    else:
        st.markdown("- **Residenza:** —")

    st.markdown("---")

    st.markdown("#### 🏥 Dati intervento")
    st.markdown(f"- **Data ricovero:** {data.get('data_di_ricovero') or data.get('intervento', {}).get('data_di_ricovero', '—')}")
    st.markdown(f"- **Ora ricovero:** {data.get('ora_di_ricovero') or data.get('intervento', {}).get('ora_di_ricovero', '—')}")
    st.markdown(f"- **Luogo intervento:** {data.get('luogo_intervento') or data.get('intervento', {}).get('luogo_intervento', '—')}")
    st.markdown(f"- **Condizione riferita:** {data.get('condizione_riferita') or data.get('intervento', {}).get('condizione_riferita', '—')}")
    st.markdown(f"- **Codice uscita:** {data.get('codice_uscita') or data.get('intervento', {}).get('codice_uscita', '—')}")
    st.markdown(f"- **Codice rientro:** {data.get('codice_rientro') or data.get('intervento', {}).get('codice_rientro', '—')}")

    render_list("👥 Attivazioni", data.get("attivazioni") or data.get("intervento", {}).get("attivazioni", []))
    render_list("🚑 Equipaggio", data.get("equipaggio") or data.get("intervento", {}).get("equipaggio", []))

    st.markdown("---")
    render_list("🩺 Sintomi principali", data.get("sintomi_principali") or data.get("condizione_clinica", {}).get("sintomi_principali", []))

    st.markdown("---")
    st.markdown("#### 🧪 Diagnosi sospetta")
    st.markdown(f"**{data.get('diagnosi_sospetta') or data.get('condizione_clinica', {}).get('diagnosi_sospetta', '—')}**")

    st.markdown("#### 🧬 Diagnosi finale")
    st.markdown(f"**{data.get('diagnosi_finale') or data.get('condizione_clinica', {}).get('diagnosi_finale', '—')}**")
    st.markdown("---")
    st.markdown("#### 🧍🏼Body Heatmap")
    
    # --- Generazione heatmap ---
    heatmap_key = f"heatmap_btn_{data['id']}"
    if st.button("🔥 Genera Heatmap", key=heatmap_key):
        st.session_state[f"mostra_heatmap_{data['id']}"] = True

    if st.session_state.get(f"mostra_heatmap_{data['id']}"):
        visualizza_heatmap(data, image_path="images/corpo.png")


       
    st.markdown("---")
    render_list("💊 Farmaci indicati",
        data.get("farmaci_indicati") or
        data.get("condizione_clinica", {}).get("farmaci_indicati") or
        data.get("trattamenti", {}).get("farmaci_indicati", []))

    render_list("🧰 Trattamenti effettuati",
        data.get("trattamenti_effettuati") or
        data.get("condizione_clinica", {}).get("trattamenti_effettuati") or
        data.get("trattamenti", {}).get("trattamenti_effettuati", []))

    render_list("🧫 Esami diagnostici",
        data.get("esami_diagnostici") or
        data.get("condizione_clinica", {}).get("esami_diagnostici") or
        data.get("trattamenti", {}).get("esami_diagnostici", []))

    st.markdown("---")
    render_dict("🧠 Parametri vitali", data.get("parametri_vitali", {}))
    render_dict("🫁 Respiro", data.get("respiro", {}))
    render_dict("🧍 Coscienza", data.get("coscienza", {}))
    render_dict("🧊 Cute", data.get("cute", {}))

    if "glasgow_coma_scale" in data and isinstance(data["glasgow_coma_scale"], dict):
        st.markdown("#### 🧠 Glasgow Coma Scale")
        for t, valori in data["glasgow_coma_scale"].items():
            if isinstance(valori, dict):
                st.markdown(f"- **{t.upper()}:** " + ", ".join(f"{k}:{v}" for k, v in valori.items()))
            else:
                st.markdown(f"- **{t.upper()}:** {valori}")
    else:
        st.markdown("#### 🧠 Glasgow Coma Scale\n—")

    if "pupille_reagenti" in data:
        st.markdown("#### 👁️‍🗨️ Pupille reagenti")
        pupille = data["pupille_reagenti"]
        if isinstance(pupille, dict):
            st.markdown(f"- **Dx:** {pupille.get('Dx', '—')}")
            st.markdown(f"- **Sx:** {pupille.get('Sx', '—')}")
        elif isinstance(pupille, str):
            st.markdown(f"- {pupille}")
        else:
            st.markdown("—")

    render_list("💥 Lesioni riscontrate", data.get("lesioni_riscontrate", []))

    st.markdown("---")
    provvedimenti = data.get("provvedimenti", {})
    if isinstance(provvedimenti, dict):
        for sezione, lista in provvedimenti.items():
            render_list(f"🛠️ Provvedimenti - {sezione}", lista)
    elif isinstance(provvedimenti, str):
        st.markdown("#### 🛠️ Provvedimenti")
        st.markdown(f"- {provvedimenti}")
    else:
        st.markdown("#### 🛠️ Provvedimenti\n—")

    st.markdown("#### 📌 Annotazioni")
    st.markdown(data.get("annotazioni") or data.get("altro", {}).get("annotazioni", "—"))

    st.markdown("#### 📝 Consensi e firme")
    st.markdown(f"- **Rifiuto trattamento:** {'✅' if data.get('firma_paziente_rifiuto') or data.get('altro', {}).get('firma_paziente_rifiuto') else '-'}")
    st.markdown(f"- **Constatazione decesso:** {'✅' if data.get('firma_medico_decesso') or data.get('altro', {}).get('firma_medico_decesso') else '-'}")

