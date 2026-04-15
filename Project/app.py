import streamlit as st
import av
import tempfile
import numpy as np
import queue
import time
import soundfile as sf
import librosa
import json             
import uuid            
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime  
import os      
from codice_fiscale import calcola_codice_fiscale
from codicefiscale import codicefiscale
from speech2txt import *
from LLM import *
from layout import *
from mongo import *
from analytics import *
from wordcloud import WordCloud
from query_personalizzate import *
from compiLLaMA import *
from heatmap import *
from query_vocali import *


st.set_page_config(page_title="Voice to Text", layout="centered")
aggiungi_sfondo("images/sfondo.png")


# Inizializza session_state
if "page" not in st.session_state:
    st.session_state.page = "home"
if "text_trascritto" not in st.session_state:
    st.session_state.text_trascritto = ""
if "frames_received" not in st.session_state:
    st.session_state.frames_received = 0

if "audio_registrato" not in st.session_state:
    st.session_state.audio_registrato = False


# Aggiungi stato per Analytics
if "analytics_data" not in st.session_state:
    st.session_state.analytics_data = None


def go_to(page_name):
    st.session_state.page = page_name

def reset_to_home():
    st.session_state.clear()  # Pulisce tutto lo stato
    st.session_state.page = "home"
    st.rerun()

query_params = st.query_params
if query_params.get("page") == "carica_audio":
        go_to("carica_audio")
elif query_params.get("page") == "registrazione":
        go_to("registrazione")
# -----------------------------
# HOME
# -----------------------------
if st.session_state.page == "home":
    
    
    

    titolo_home()
    pulsanti_home_stilizzati()



    st.markdown("<hr>", unsafe_allow_html=True)

    st.markdown("""
    <div style='text-align: center; font-size: 1.5em; font-weight: 600; color:#264972;'>
        🤔 Oppure:
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("📂 Cerca pazienti nel database"):
            go_to("ricerca")
            st.rerun()

        if st.button("🔍 Query Personalizzate"):
            go_to("query_personalizzate")
            st.rerun()

    with col2:
        if st.button("📊 Visualizza Analytics"):
            go_to("analytics")
            st.rerun()
        
        if st.button("🗣️ Query Vocali"):
            go_to("query_vocali")
            st.rerun()
   

# -----------------------------
# CARICA AUDIO
# -----------------------------
elif st.session_state.page == "carica_audio":
    inietta_stile_pulsanti_generale()
    if st.button("⬅️ Torna alla Home"):
        go_to("home")


    st.header("📤 Carica un file audio")
    uploaded_file = st.file_uploader("Carica un file (.mp3, .wav, .m4a)", type=["mp3", "wav", "m4a"])

    if uploaded_file is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_path = tmp_file.name

        st.audio(tmp_path, format="audio/wav")

        y, sr = librosa.load(tmp_path, sr=None)
        duration = librosa.get_duration(y=y, sr=sr)

        st.markdown("### ✂️ Seleziona l'intervallo da trascrivere:")
        start_sec, end_sec = st.slider("Intervallo (in secondi)", 0.0, duration, (0.0, duration), step=0.5)

        start_sample = int(start_sec * sr)
        end_sample = int(end_sec * sr)
        y_trimmed = y[start_sample:end_sample]

        trimmed_path = tmp_path.replace(".wav", "_trimmed.wav")
        sf.write(trimmed_path, y_trimmed, sr)

        st.audio(trimmed_path, format="audio/wav")

        if st.button("Trascrivi intervallo selezionato"):
            with st.spinner("Trascrizione in corso..."):
                st.session_state.text_trascritto = transcribe_audio(trimmed_path)
                st.success("✅ Trascrizione completata!")
                go_to("risultati")
                st.rerun()
                

# -----------------------------
# REGISTRA AUDIO
# -----------------------------
elif st.session_state.page == "registrazione":
    if st.button("⬅️ Torna alla Home"):
        go_to("home")


    st.header("🎤 Registra dal microfono")
    inietta_stile_pulsanti_generale()

    
    audio_bytes = st.audio_input("🎙️ Premi per iniziare a registrare")

    if  st.session_state.get("reset_audio_input"):
        audio_bytes = None
        st.session_state["reset_audio_input"] = False  # Reset il flag dopo un giro

        
    if audio_bytes is not None:
        st.session_state.audio_registrato = True

    if not st.session_state.audio_registrato:
        with st.expander("🧭 Guida alla compilazione vocale (clicca per aprire)", expanded=False):
            st.markdown("### 🗣️ Cosa dire durante la registrazione audio")
            st.markdown("Segui questo schema per assicurarti che vengano registrate tutte le informazioni utili:")

            st.markdown("""
            <div style="border-left: 4px solid #4CAF50; padding-left: 16px; margin-bottom: 1rem;">
            <h4>👤 Dati Anagrafici</h4>
            <ul>
            <li>Nome e cognome del paziente</li>
            <li>Data e luogo di nascita</li>
            <li>Età approssimativa</li>
            <li>Luogo di residenza</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="border-left: 4px solid #2196F3; padding-left: 16px; margin-bottom: 1rem;">
            <h4>📅 Dettagli del soccorso</h4>
            <ul>
            <li>Data e ora del ricovero</li>
            <li>Luogo in cui è avvenuto l’intervento di soccorso</li>
            <li>Condizione riferita dal paziente</li>
            <li>Codice di uscita e di rientro</li>
            <li>Equipaggio intervenuto (nome e ruolo)</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="border-left: 4px solid #FF9800; padding-left: 16px; margin-bottom: 1rem;">
            <h4>🩺 Sintomi e diagnosi</h4>
            <ul>
            <li>Sintomi principali riportati</li>
            <li>Diagnosi sospetta e diagnosi finale</li>
            <li>Eventuali esami diagnostici effettuati</li>
            <li>Farmaci somministrati e trattamenti eseguiti</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="border-left: 4px solid #9C27B0; padding-left: 16px; margin-bottom: 1rem;">
            <h4>📊 Parametri vitali</h4>
            <ul>
            <li>Pressione arteriosa</li>
            <li>Frequenza cardiaca e respiratoria</li>
            <li>Saturazione, glicemia, temperatura</li>
            <li>Stato di coscienza, orientamento</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="border-left: 4px solid #795548; padding-left: 16px; margin-bottom: 1rem;">
            <h4>🔎 Lesioni e provvedimenti</h4>
            <ul>
            <li>Lesioni visibili (escoriazioni, ecchimosi...)</li>
            <li>Pupille reagenti</li>
            <li>Provvedimenti adottati (collare, trasporto, immobilizzazione...)</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div style="border-left: 4px solid #607D8B; padding-left: 16px;">
            <h4>📝 Annotazioni aggiuntive</h4>
            <ul>
            <li>Orario presunto dell’evento</li>
            <li>Stato collaborativo, autonomia del paziente</li>
            <li>Eventuali rifiuti o decessi</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)

    # 🎙️ Se l’audio è stato registrato, mostra il lettore
    if st.session_state.audio_registrato and audio_bytes is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes.getvalue())
            temp_audio_path = f.name

        st.audio(temp_audio_path, format="audio/wav")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("📝 Trascrivi audio registrato"):
                with st.spinner("Trascrizione in corso..."):
                    st.session_state.text_trascritto = transcribe_audio(temp_audio_path)
                    st.success("✅ Trascrizione completata!")
                    go_to("risultati")
                    st.rerun()

        with col2:
            if st.button("🔁 Effettua una nuova registrazione"):
                st.session_state.text_trascritto = ""
                st.session_state.audio_registrato = False
                st.session_state["reset_audio_input"] = True  # <-- Aggiungi un flag
                go_to("registrazione")
                st.rerun()





# -----------------------------
# RISULTATI & CARTELLA CLINICA
# -----------------------------
elif st.session_state.page == "risultati":
    if st.session_state.page == "home":
        st.stop()

    inietta_stile_pulsanti_generale()

    if st.button("⬅️ Torna alla Home"):
        go_to("home")


    if st.button("🗑️ Elimina trascrizione"):
        st.session_state.text_trascritto = ""
        st.success("✅ Trascrizione eliminata correttamente. Verrai reindirizzato alla Home...")
        time.sleep(2)
        go_to("home")
        st.rerun()


    with st.expander("📝 Clicca per Visualizzare/Modificare la Trascrizione", expanded=False):
        st.session_state.text_trascritto = st.text_area(
            "Trascrizione", value=st.session_state.text_trascritto, height=300
        )


    st.markdown("---")
    st.header("📋 Cartella Clinica Automatica")

    if st.button("🧠\nCompila\nCartella\nClinica", key="llama_submit"):
        testo = st.session_state.text_trascritto
        if testo.strip():
            prompt = costruisci_prompt(testo)

            try:
                with st.spinner("Compilazione in corso.."):
                    output = chiedi_a_llama(prompt)
                    clean_output = estrai_json_pulito(output)

                    try:
                        json_data = json.loads(clean_output)
                
                    except json.JSONDecodeError:
                        st.error("❌ L'audio inserito non contiene abbastanza informazioni utili per compilare la cartella clinica.")
                        st.markdown("🔁 Verrai reindirizzato alla pagina iniziale per una nuova registrazione...")
                        st.code(clean_output)

                        # 👇 Questo delay funziona solo se il rerun avviene dopo
                        time.sleep(3)
                        st.session_state.page = "registrazione"
                        st.rerun()
            
                   

                    # Calcola codice fiscale
                    nome = json_data.get("nome", "")
                    cognome = json_data.get("cognome", "")
                    sesso = json_data.get("sesso", "")
                    data_nascita = json_data.get("data_nascita", "")
                    luogo_nascita = json_data.get("luogo_nascita", "")

                    unique_id = calcola_codice_fiscale(nome, cognome, sesso, data_nascita, luogo_nascita)
                    if unique_id.startswith("ID"):
                        st.warning(f"⚠️ Codice fiscale non calcolabile. Assegnato ID univoco: {unique_id}")

                    timestamp = datetime.now().isoformat()
                    json_data["id"] = unique_id
                    json_data["timestamp"] = timestamp

                    output_dir = "cartelle_cliniche"
                    os.makedirs(output_dir, exist_ok=True)
                    filepath = os.path.join(output_dir, f"{unique_id}.json")

                    with open(filepath, "w", encoding="utf-8") as f:
                        json.dump(json_data, f, ensure_ascii=False, indent=4)

                    salva_cartella_clinica(json_data)

                    st.success("✅ Cartella clinica salvata.")
                    st.markdown(f"📁 File: `{filepath}`")
                    cartella_salvata = trova_cartella(unique_id)
                    cartella_salvata = converti_objectid(cartella_salvata)
                    st.session_state.json_data = cartella_salvata
                    st.session_state["cartella_compilata"] = True
                    st.rerun()



                    st.markdown("---")


                    with st.expander("📦 Visualizza JSON salvato", expanded=False):
                        json_string = json.dumps(cartella_salvata, indent=4, ensure_ascii=False)
                        edited_json = st.text_area("Modifica JSON", value=json_string, height=400, key="json_editor")

                        if st.button("💾 Salva modifiche al JSON", key="save_json_button"):
                            try:
                                json_modificato = json.loads(edited_json)
                                with open(filepath, "w", encoding="utf-8") as f:
                                    json.dump(json_modificato, f, ensure_ascii=False, indent=4)
                                salva_cartella_clinica(json_modificato)
                                st.success("✅ Modifiche salvate correttamente.")
                                st.session_state.json_data = json_modificato
                                st.rerun()
                            except json.JSONDecodeError:
                                st.error("❌ Il JSON modificato non è valido.")

                    # Pulsante per creare e scaricare il PDF
                    if "json_data" not in st.session_state:
                        st.session_state.json_data = json_data
                    else:
                        st.session_state.json_data.update(json_data)

                
                                        
          
            except Exception as e:
                st.error("❌ Errore durante la compilazione della cartella clinica.")
                st.markdown("### Prompt inviato:")
                st.code(prompt, language="text")
                st.markdown("### Output ricevuto:")
                st.code(output, language="text")
                st.markdown(f"### Dettagli errore: `{str(e)}`")
                st.stop()

    
        else:
            st.warning("⚠️ Nessun testo trascritto disponibile.")
    
    if st.session_state.get("cartella_compilata") and "json_data" in st.session_state:
        mostra_json_stilizzato(st.session_state["json_data"])
        st.markdown("---")
        st.subheader("📄 Scarica la cartella clinica in PDF")

        col_pdf, col_delete = st.columns(2)

        with col_pdf:
            if st.button("📄 Genera PDF"):
                try:
                    dati_puliti = converti_objectid(st.session_state.json_data)
                    prompt_pdf = costruisci_prompt_pdf(dati_puliti)
                    output_pdf = chiedi_a_llama(prompt_pdf)
                    istruzioni = json.loads(estrai_json_pulito(output_pdf))

                    output_dir = "static/pdf_cartelle"
                    os.makedirs(output_dir, exist_ok=True)
                    filename = f"{st.session_state.json_data['id']}.pdf"
                    output_path = esporta_cartella_pdf_da_istruzioni(istruzioni, st.session_state.json_data, filename)
                    st.success("✅ PDF generato correttamente!")
                    with open(output_path, "rb") as f:
                        pdf_bytes = f.read()
                        st.download_button(
                            label="📥 Download",
                            data=pdf_bytes,
                            file_name=filename,
                            mime="application/pdf",
                            key=f"download_{filename}"
                        )
                except Exception as e:
                    st.warning("⚠️ Errore durante la generazione del PDF, riprova.")

        with col_delete:
            if st.button("❌ Elimina cartella clinica", key="elimina_post_registrazione"):
                id_paziente = st.session_state["json_data"].get("id", "")
                if id_paziente:
                    successo = elimina_cartella(id_paziente)
                    if successo:
                        st.success("✅ Cartella clinica eliminata. Verrai reindirizzato alla Home...")
                        st.session_state.text_trascritto = ""
                        st.session_state.json_data = None
                        st.session_state.cartella_compilata = False
                        time.sleep(2)
                        go_to("home")
                        st.rerun()
                    else:
                        st.error("❌ Errore durante l'eliminazione.")


#------------------------------
# VISUALIZZA CARTELLE CLINICHE
#------------------------------
elif st.session_state.page == "ricerca":
    if st.button("⬅️ Torna alla Home"):
        go_to("home")

    st.header("🔍 Ricerca Cartelle Cliniche")

    query = st.text_input("🔎 Cerca per nome, cognome o codice fiscale")
    utenti = cerca_utenti(query) 
    
    if utenti:
            utenti_ordinati = sorted(
                utenti,
                key=lambda x: (
                    x.get("cognome", "").lower(),
                    x.get("nome", "").lower()
            )
            )   
            for i, utente in enumerate(utenti_ordinati):
                col1, colonna_opzioni = st.columns([7, 3])      
           

                with col1:
                    label = f"{utente['cognome'].upper()} {utente['nome'].capitalize()} ({utente['id']})"
                    edit_mode_key = f"edit_mode_{utente['id']}"

                    with st.expander(label, expanded=st.session_state.get(edit_mode_key, False)):
                            cartella = trova_cartella(utente["id"])
                            if cartella:
                                sesso = utente.get("sesso", "").lower()
                                col_dati, col_img = st.columns([7, 3])  # 7 per i dati, 3 per l'immagine

                                with col_dati:
                                    edit_mode_key = f"edit_mode_{utente['id']}"
                                    if st.session_state.get(edit_mode_key):
                                        edited_data = {}
                                        st.markdown("### ✏️ Modifica campi")
                                        for key, value in cartella.items():
                                            if key in ["id", "timestamp"]:
                                                st.text_input(label=key, value=value, disabled=True, key=f"{utente['id']}_{key}_readonly")

                                            elif isinstance(value, list):
                                                raw_input = st.text_area(key, ", ".join(value))
                                                edited_data[key] = [normalizza_markdown_grassetto(s.strip()) for s in raw_input.split(",")]

                                            elif key == "residenza" and isinstance(value, dict):
                                                st.markdown("##### 🏠 Residenza")
                                                via = st.text_input("Via", value.get("via", ""))
                                                comune = st.text_input("Comune", value.get("comune", ""))
                                                provincia = st.text_input("Provincia", value.get("provincia", ""))
                                                edited_data["residenza"] = {
                                                    "via": normalizza_markdown_grassetto(via),
                                                    "comune": normalizza_markdown_grassetto(comune),
                                                    "provincia": normalizza_markdown_grassetto(provincia)
                                                }

                                            elif isinstance(value, dict):
                                                st.markdown(f"##### ✏️ {key}")
                                                raw_json = st.text_area(f"{key} (inserire JSON valido)", json.dumps(value, indent=2, ensure_ascii=False))
                                                try:
                                                    parsed = json.loads(raw_json)
                                                    if isinstance(parsed, dict):
                                                        edited_data[key] = parsed
                                                    else:
                                                        st.error(f"⚠️ Il campo '{key}' deve essere un dizionario JSON.")
                                                except json.JSONDecodeError:
                                                    st.error(f"❌ Il campo '{key}' contiene un JSON non valido.")

                                            else:
                                                edited_data[key] = normalizza_markdown_grassetto(
                                                    st.text_input(label=key, value=str(value), key=f"{utente['id']}_{key}_edit")
                                                )


                                    else:
                                        mostra_json_stilizzato(cartella)

                                if st.session_state.get(edit_mode_key):
                                    col_save, col_inutile, col_cancel = st.columns([3, 4, 3])
                                    with col_save:
                                        if st.button("💾 Salva", key=f"save_{utente['id']}"):
                                            successo = modifica_cartella(utente["id"], edited_data)
                                            if successo:
                                                st.success("✅ Modifica salvata.")
                                                st.session_state[edit_mode_key] = False
                                                st.rerun()
                                            else:
                                                st.error("❌ Errore durante il salvataggio.")

                                    with col_cancel:
                                        if st.button("❌ Annulla", key=f"cancel_{utente['id']}"):
                                            st.session_state[edit_mode_key] = False
                                            st.rerun()

                                with col_img:
                    
                                    sesso = cartella.get("sesso", "").upper()  # oppure .lower() se vuoi usarlo in minuscolo

                                    if sesso == "M":
                                            st.image("immagini_profili/uomo.png", width=100)
                                    elif sesso == "F":
                                            st.image("immagini_profili/donna.png", width=100)
                                    else:
                                            st.image("immagini_profili/uomo.png", width=100)  # fallback
                            else:
                                st.warning("Cartella non trovata nel database.")
                           

                with colonna_opzioni:
                    col2, col3, col4 = st.columns([3, 3, 4])  

                    with col2:
                        delete_clicked = st.button(
                            "❌", 
                            key=f"delete_{utente['id']}_{i}", 
                            help="Elimina questa cartella clinica"
                        )

                    with col3:
                        edit_key = f"edit_{utente['id']}_{i}"
                        if st.button("✏️", key=f"edit_{utente['id']}_{i}", help="Modifica la cartella clinica"):
                            st.session_state[f"edit_mode_{utente['id']}"] = True
                            st.rerun()

                    with col4:
                        errore_pdf = None
                        pdf_key = f"pdf_{utente['id']}_{i}"
                        if st.button("⬇️", key=pdf_key, help="Scarica cartella clinica in PDF"):
                            try:
                                cartella = trova_cartella(utente["id"])
                                if not cartella:
                                    st.warning("Cartella non trovata.")
                                    st.stop()

                                # Costruzione e chiamata LLaMA
                                cartella_pulita = converti_objectid(cartella)
                                prompt_pdf = costruisci_prompt_pdf(json.dumps(cartella_pulita, ensure_ascii=False))                              
                                output_pdf = chiedi_a_llama(prompt_pdf)
                                istruzioni = json.loads(estrai_json_pulito(output_pdf))

                                # Genera il PDF nella cartella 'static'
                                output_dir = "static/pdf_cartelle"
                                os.makedirs(output_dir, exist_ok=True)
                                filename = f"{utente['id']}.pdf"
                                output_path = esporta_cartella_pdf_da_istruzioni(istruzioni, cartella_pulita, filename)

                                st.session_state[f"pdf_path_{utente['id']}"] = output_path
                                st.session_state[f"pdf_filename_{utente['id']}"] = filename       


                            except Exception as e:
                                errore_pdf = str(e)

                    if errore_pdf:
                        st.error(f"❌ Tentativo fallito. Riprova tra qualche secondo.🙏🏼")
                    pdf_path = st.session_state.get(f"pdf_path_{utente['id']}")
                    pdf_filename = st.session_state.get(f"pdf_filename_{utente['id']}")

                    if pdf_path and os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                            st.download_button(
                                label="📥 Scarica cartella PDF",
                                data=pdf_bytes,
                                file_name=pdf_filename,
                                mime="application/pdf",
                                key=f"download_{utente['id']}"
                            )
                    elif pdf_path:
                        st.warning("⚠️ PDF non trovato. Riprova tra qualche secondo.")
                    
                    if delete_clicked:
                        successo = elimina_cartella(utente["id"])
                        if successo:
                            st.success(f"✅ Cartella di {(utente.get('nome') or '--')} {(utente.get('cognome') or '--')} eliminata correttamente!")
                            st.rerun()
                        else:
                            st.error("❌ Errore durante l'eliminazione.")

                                        

    elif query:
                    st.info("Nessun risultato trovato.")
            



# -----------------------------
# ANALYTICS
# -----------------------------
elif st.session_state.page == "analytics":
    inietta_stile_pulsanti_generale()

    if st.button("⬅️ Torna alla Home"):
        go_to("home")

    mostra_distribuzioni()
    st.markdown("---")
    mostra_query_personalizzata()
    st.markdown("---")

    st.markdown("### 📈 Scegli un’analisi da visualizzare")

    b1, b2 = st.columns(2)
    b3, b4 = st.columns(2)
    b5, b6 = st.columns(2)
    b7, b8 = st.columns(2)

    df = st.session_state.analytics_data

    if b1.button("🚹🚺Distribuzione per sesso"):
        grafico_sesso()
    if b2.button("🏥Cause di ricovero più comuni"):
        grafico_top_motivi()
    if b3.button("👨🏼‍⚕️Diagnosi più frequenti"):
        grafico_top_diagnosi()
    if b4.button("🚑Metodi di arrivo"):
        grafico_metodo_arrivo()
    if b5.button("📅Ricoveri per mese"):
        grafico_ricoveri_per_mese()
    if b6.button("🕙Fasce orarie ricoveri"):
        grafico_fasce_orarie()
    if b7.button("👴🏼Età media per diagnosi"):
        grafico_eta_media_per_diagnosi()
    if b8.button("☁️Word-cloud sintomi"):
        grafico_wordcloud_sintomi()

    st.markdown("---")
    if st.button("🏠 Torna alla Home"):
        go_to("home")

# -----------------------------
# QUERY PERSONALIZZATE
# -----------------------------
elif st.session_state.page == "query_personalizzate":
    inietta_stile_pulsanti_generale()

    if st.button("⬅️ Torna alla Home"):
        go_to("home")
        st.rerun()

    db_connection = get_database_connection()  
    mostra_query_personalizzate(db_connection)

  



# -----------------------------
# QUERY VOCALI
# -----------------------------
elif st.session_state.page == "query_vocali":
    if st.button("⬅️ Torna alla Home"):
        go_to("home")


    st.header("🎤 Cosa stai cercando?")

    


    audio_bytes = st.audio_input("🎙️ Premi per iniziare a registrare")      


    if audio_bytes is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            f.write(audio_bytes.getvalue())
            temp_audio_path_query = f.name

        st.audio(temp_audio_path_query, format="audio/wav")

        with st.spinner("🎧 Ricerca in corso..."):
            testo_query = transcribe_audio(temp_audio_path_query)
            st.success("✅ Ricerca Completata!")

            with open("json_samples/cartella_generata_grezza.json", "r", encoding="utf-8") as f:
                json_esempio = json.load(f)
                esempio = json.dumps(json_esempio, indent=2)

            try:
                risultati = esegui_query_vocale(testo_query, esempio)


                st.markdown("### 📄 Risultati ottenuti:")
                if isinstance(risultati, list) and risultati:
                    # Mostra in tabella scaricabile
                    df_summary = QueryPersonalizzate(None)._crea_tabella_riassuntiva(risultati)
                    st.dataframe(df_summary, use_container_width=True)

                    csv = df_summary.to_csv(index=False)
                    st.download_button(
                        label="📥 Scarica CSV",
                        data=csv,
                        file_name=f"risultati_vocali_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )

                    st.markdown("---")
                    st.markdown("### 🩺 Visualizza le Cartelle Cliniche complete dei pazienti trovati:")

                    # Se vuoi anche i risultati completi in JSON
                    for i, r in enumerate(risultati):
                        id_paziente = r.get("id", f"utente_{i}")
                        label = f"👤📋 Cartella di {r.get('nome', '')} {r.get('cognome', '')} ({id_paziente})"

                        with st.expander(label, expanded=False):
                            mostra_json_stilizzato(r)



                elif isinstance(risultati, dict):
                    st.json(risultati)
                else:
                    st.info("ℹ️ Nessun risultato trovato o formato non riconosciuto.")
            except Exception as e:
                st.error(f"❌ Errore durante l'elaborazione della query: {str(e)}")
