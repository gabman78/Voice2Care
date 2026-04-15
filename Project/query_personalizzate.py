import streamlit as st
import pandas as pd
from datetime import datetime, date
import json
from typing import Dict, List, Any, Optional
import re
import matplotlib.pyplot as plt

#import mappa pazienti
import folium
from streamlit_folium import st_folium
import requests
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
from collections import defaultdict


class QueryPersonalizzate:
    @staticmethod
    def safe_sum_fields(*fields):
        try:
            return sum(int(f) for f in fields if f is not None)
        except (ValueError, TypeError):
            return 0

    def __init__(self, db_connection):
        """
        Inizializza la classe con la connessione al database
        """
        self.db = db_connection
        
    def mostra_interfaccia_query(self):
        """
        Mostra l'interfaccia principale per le query personalizzate
        """
        st.title("🔍 Query Personalizzate")
        st.markdown("---")
        
        # Scelta del tipo di query
        tipo_query = st.selectbox(
            "Seleziona il tipo di query:",
            [
                "Query con Menu Guidato",
                "Query SQL Personalizzata",
                "Query Predefinite",
                "🗺️ Mappa Geografica"
            ]
        )

        
        if tipo_query == "Query con Menu Guidato":
            self._query_menu_guidato()
        elif tipo_query == "Query SQL Personalizzata":
            self._query_sql_personalizzata()
        elif tipo_query == "Query Predefinite":
            self._query_predefinite()
        elif tipo_query == "🗺️ Mappa Geografica":
            self._mostra_mappa_geografica()
            

    
    def _query_menu_guidato(self):
        """
        Interfaccia per query guidate con menu a tendina
        """
        st.subheader("🎯 Query con Menu Guidato")
        
        # Inizializza i filtri
        filtri = {}
        if 'guidata_risultati' not in st.session_state:
            st.session_state.guidata_risultati = None
        if 'guidata_mostra_risultati' not in st.session_state:
            st.session_state.guidata_mostra_risultati = False

        # Sezione Dati Anagrafici
        with st.expander("👤 Filtri Anagrafici", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                # Nome
                nome_input = st.text_input("Nome (contiene)")
                if nome_input:
                    filtri['nome'] = nome_input
                
                # Sesso
                sesso = st.selectbox("Sesso", ["Tutti", "M", "F"])
                if sesso != "Tutti":
                    filtri['sesso'] = sesso
                
                # Età
                eta_min = st.number_input("Età minima", min_value=0, max_value=120, value=0)
                eta_max = st.number_input("Età massima", min_value=0, max_value=120, value=120)
                if eta_min > 0 or eta_max < 120:
                    filtri['eta_range'] = (eta_min, eta_max)
            
            with col2:
                # Cognome
                cognome_input = st.text_input("Cognome (contiene)")
                if cognome_input:
                    filtri['cognome'] = cognome_input
                
                # Luogo di nascita
                luogo_nascita = st.text_input("Luogo di nascita (contiene)")
                if luogo_nascita:
                    filtri['luogo_nascita'] = luogo_nascita
                
                # Comune di residenza
                comune_residenza = st.text_input("Comune di residenza (contiene)")
                if comune_residenza:
                    filtri['comune_residenza'] = comune_residenza
        
        # Sezione Intervento
        with st.expander("🚑 Filtri Intervento"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Data ricovero
                data_da = st.date_input("Data ricovero da", value=None)
                data_a = st.date_input("Data ricovero a", value=None)
                if data_da or data_a:
                    filtri['data_ricovero'] = (data_da, data_a)
                
                # Codice uscita (aggiornato)
                codice_uscita = st.selectbox("Codice uscita", ["Tutti", "BIANCO", "VERDE", "GIALLO", "ROSSO", "NERO"])
                if codice_uscita != "Tutti":
                    filtri['codice_uscita'] = codice_uscita
                
                # Condizione riferita
                condizione_riferita = st.text_input("Condizione riferita (contiene)")
                if condizione_riferita:
                    filtri['condizione_riferita'] = condizione_riferita
            
            with col2:
                # Luogo intervento
                luogo_intervento = st.text_input("Luogo intervento (contiene)")
                if luogo_intervento:
                    filtri['luogo_intervento'] = luogo_intervento
                
                # Codice rientro (aggiornato)
                codice_rientro = st.selectbox("Codice rientro", ["Tutti", "BIANCO", "VERDE", "GIALLO", "ROSSO", "NERO"])
                if codice_rientro != "Tutti":
                    filtri['codice_rientro'] = codice_rientro
                
                # Attivazioni
                attivazioni_options = ["Automedica", "Elisoccorso", "Forze dell'ordine", "Vigili del fuoco"]
                attivazioni_sel = st.multiselect("Attivazioni", attivazioni_options)
                if attivazioni_sel:
                    filtri['attivazioni'] = attivazioni_sel
        
        # Sezione Condizione Clinica
        with st.expander("🏥 Filtri Condizione Clinica"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Diagnosi sospetta
                diagnosi_sospetta = st.text_input("Diagnosi sospetta (contiene)")
                if diagnosi_sospetta:
                    filtri['diagnosi_sospetta'] = diagnosi_sospetta
                
                # Sintomi principali
                sintomi = st.text_input("Sintomi principali (contiene)")
                if sintomi:
                    filtri['sintomi_principali'] = sintomi
                
                # Stato di coscienza
                stato_coscienza = st.selectbox("Stato di coscienza", ["Tutti", "vigile", "soporoso", "stuporoso", "comatoso"])
                if stato_coscienza != "Tutti":
                    filtri['stato_coscienza'] = stato_coscienza
            
            with col2:
                # Diagnosi finale
                diagnosi_finale = st.text_input("Diagnosi finale (contiene)")
                if diagnosi_finale:
                    filtri['diagnosi_finale'] = diagnosi_finale
                
                # Lesioni riscontrate
                lesioni = st.text_input("Lesioni riscontrate (contiene)")
                if lesioni:
                    filtri['lesioni_riscontrate'] = lesioni
                
                # Tipo respiro
                tipo_respiro = st.selectbox("Tipo respiro", ["Tutti", "Spontaneo", "Assistito", "Controllato"])
                if tipo_respiro != "Tutti":
                    filtri['tipo_respiro'] = tipo_respiro
        
        # Sezione Parametri Vitali (aggiornata)
        with st.expander("📊 Filtri Parametri Vitali"):
            col1, col2 = st.columns(2)
            
            with col1:
                # Saturazione (aggiornato da SpO2)
                sat_min = st.number_input("Saturazione minima (%)", min_value=0, max_value=100, value=0)
                sat_max = st.number_input("Saturazione massima (%)", min_value=0, max_value=100, value=100)
                if sat_min > 0 or sat_max < 100:
                    filtri['saturazione_range'] = (sat_min, sat_max)
                
                # Frequenza cardiaca (aggiornato)
                fc_min = st.number_input("Frequenza cardiaca minima (bpm)", min_value=0, max_value=300, value=0)
                fc_max = st.number_input("Frequenza cardiaca massima (bpm)", min_value=0, max_value=300, value=300)
                if fc_min > 0 or fc_max < 300:
                    filtri['fc_range'] = (fc_min, fc_max)
                
                # Frequenza respiratoria
                fr_min = st.number_input("Frequenza respiratoria minima (atti/min)", min_value=0, max_value=60, value=0)
                fr_max = st.number_input("Frequenza respiratoria massima (atti/min)", min_value=0, max_value=60, value=60)
                if fr_min > 0 or fr_max < 60:
                    filtri['fr_range'] = (fr_min, fr_max)
            
            with col2:
                # Temperatura
                temp_min = st.number_input("Temperatura minima (°C)", min_value=30.0, max_value=45.0, value=30.0)
                temp_max = st.number_input("Temperatura massima (°C)", min_value=30.0, max_value=45.0, value=45.0)
                if temp_min > 30.0 or temp_max < 45.0:
                    filtri['temperatura_range'] = (temp_min, temp_max)
                
                # Glicemia
                glic_min = st.number_input("Glicemia minima (mg/dL)", min_value=0, max_value=500, value=0)
                glic_max = st.number_input("Glicemia massima (mg/dL)", min_value=0, max_value=500, value=500)
                if glic_min > 0 or glic_max < 500:
                    filtri['glicemia_range'] = (glic_min, glic_max)
        
        # Sezione Glasgow Coma Scale
        with st.expander("🧠 Filtri Glasgow Coma Scale"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**GCS Iniziale**")
                gcs_init_min = st.number_input("GCS Iniziale minimo", min_value=3, max_value=15, value=3)
                gcs_init_max = st.number_input("GCS Iniziale massimo", min_value=3, max_value=15, value=15)
                if gcs_init_min > 3 or gcs_init_max < 15:
                    filtri['gcs_iniziale_range'] = (gcs_init_min, gcs_init_max)
            
            with col2:
                st.write("**GCS Arrivo PS**")
                gcs_ps_min = st.number_input("GCS PS minimo", min_value=3, max_value=15, value=3)
                gcs_ps_max = st.number_input("GCS PS massimo", min_value=3, max_value=15, value=15)
                if gcs_ps_min > 3 or gcs_ps_max < 15:
                    filtri['gcs_ps_range'] = (gcs_ps_min, gcs_ps_max)
        
        # Pulsante per eseguire la query
        if st.button("🔍 Esegui Query", type="primary"):
            if filtri:
                st.session_state.guidata_risultati = self._esegui_query_guidata(filtri)
                st.session_state.guidata_mostra_risultati = True
            else:
                st.warning("Seleziona almeno un filtro per eseguire la query")

        if st.session_state.guidata_mostra_risultati and st.session_state.guidata_risultati is not None:
            self._mostra_risultati(st.session_state.guidata_risultati)

    
    def _query_sql_personalizzata(self):
        """
        Interfaccia per query SQL personalizzate
        """
        st.subheader("💻 Query SQL Personalizzata")
        
        # Aiuto per la struttura del database
        with st.expander("📋 Struttura Database e Esempi"):
            st.markdown("""
            **Struttura principale del documento:**
            
            **Dati Anagrafici:**
            - `nome`, `cognome`, `sesso`, `data_nascita`, `luogo_nascita`, `eta`, `id`, `telefono`
            - `residenza.via`, `residenza.comune`, `residenza.provincia`
            
            **Intervento:**
            - `data_di_ricovero`, `ora_di_ricovero`, `luogo_intervento`, `condizione_riferita`
            - `codice_uscita` (BIANCO, VERDE, GIALLO, ROSSO, NERO)
            - `codice_rientro` (BIANCO, VERDE, GIALLO, ROSSO, NERO)
            - `attivazioni` (array), `equipaggio` (array)
            
            **Condizione Clinica:**
            - `sintomi_principali` (array), `diagnosi_sospetta`, `diagnosi_finale`
            - `farmaci_indicati` (array), `trattamenti_effettuati` (array), `esami_diagnostici` (array)
            - `lesioni_riscontrate` (array)
            
            **Parametri Vitali:**
            - `parametri_vitali.pressione`, `parametri_vitali.frequenza_cardiaca`
            - `parametri_vitali.saturazione`, `parametri_vitali.glicemia`, `parametri_vitali.temperatura`
            
            **Respirazione:**
            - `respiro.tipo`, `respiro.frequenza`, `respiro.rumori`
            
            **Neurologia:**
            - `coscienza.stato`, `coscienza.orientamento`
            - `glasgow_coma_scale.iniziale.{oculare,verbale,motoria}`
            - `glasgow_coma_scale.arrivo_ps.{oculare,verbale,motoria}`
            - `pupille_reagenti.Dx`, `pupille_reagenti.Sx`
            
            **Altri:**
            - `cute.colore`, `cute.temperatura`, `cute.sudorazione`
            - `provvedimenti.prima_valutazione` (array), `provvedimenti.ospedale` (array)
            - `annotazioni`, `firma_paziente_rifiuto`, `firma_medico_decesso`
            
            **Esempi di query:**
            ```json
            // Pazienti con età > 65 anni
            {"eta": {"$gt": 65}}
            
            // Pazienti con saturazione < 90%
            {"parametri_vitali.saturazione": {"$regex": "^[0-8][0-9]%"}}
            
            // Pazienti con codice rosso
            {"codice_uscita": "ROSSO"}
            
            // Pazienti con diagnosi che contiene "trauma"
            {"diagnosi_finale": {"$regex": "trauma", "$options": "i"}}
            
            // Pazienti con attivazione elisoccorso
            {"attivazioni": {"$in": ["Elisoccorso"]}}
            
            // Pazienti con GCS iniziale < 8
            {"$expr": {"$lt": [{"$add": ["$glasgow_coma_scale.iniziale.oculare", "$glasgow_coma_scale.iniziale.verbale", "$glasgow_coma_scale.iniziale.motoria"]}, 8]}}
            ```
            """)
        
        # Area di testo per la query
        query_text = st.text_area(
            "Inserisci la tua query MongoDB (formato JSON):",
            height=200,
            placeholder='{"eta": {"$gt": 65}, "sesso": "M"}',
            help="Inserisci una query MongoDB valida in formato JSON"
        )
        
        if 'query_risultati' not in st.session_state:
            st.session_state.query_risultati = None
        if 'query_mostra_risultati' not in st.session_state:
            st.session_state.query_mostra_risultati = False
        # Colonne per i pulsanti
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("🔍 Esegui Query"):
                if query_text.strip():
                    try:
                        query_dict = json.loads(query_text)
                        st.session_state.query_risultati = self._esegui_query_personalizzata(query_dict)
                        st.session_state.query_mostra_risultati = True
                    except json.JSONDecodeError as e:
                        st.error(f"Errore nel formato JSON: {str(e)}")
                    except Exception as e:
                        st.error(f"Errore nell'esecuzione della query: {str(e)}")
                else:
                    st.warning("Inserisci una query per continuare")

        
        with col3:
            if st.button("📊 Conta Risultati"):
                if query_text.strip():
                    try:
                        query_dict = json.loads(query_text)
                        count = self._conta_risultati(query_dict)
                        st.success(f"La query restituisce {count} risultati")
                    except json.JSONDecodeError as e:
                        st.error(f"Errore nel formato JSON: {str(e)}")
                    except Exception as e:
                        st.error(f"Errore nel conteggio: {str(e)}")

        if st.session_state.query_mostra_risultati and st.session_state.query_risultati is not None:
            self._mostra_risultati(st.session_state.query_risultati)

    def _query_predefinite(self):
        """
        Query predefinite utili per analisi comuni
        """
        st.subheader("📈 Query Predefinite")
        
        query_predefinite = {
            "Pazienti critici (Saturazione < 90%)": {
                "parametri_vitali.saturazione": {"$regex": "^[0-8][0-9]%"}
            },
            "Pazienti anziani (> 75 anni)": {"eta": {"$gt": 75}},
            "Interventi notturni (20:00-06:00)": {
                "$or": [
                    {"ora_di_ricovero": {"$gte": "20:00"}},
                    {"ora_di_ricovero": {"$lte": "06:00"}}
                ]
            },
            "Pazienti con codice rosso": {"codice_uscita": "ROSSO"},
            "Pazienti con lesioni traumatiche": {
                "lesioni_riscontrate": {"$ne": [], "$exists": True}
            },
            "Pazienti ipertesi (PA > 140 sistolica)": {
                "parametri_vitali.pressione": {"$regex": "^1[4-9][0-9]|^[2-9][0-9][0-9]"}
            },
            "Pazienti con decimi (>= 37°C)": {
                "parametri_vitali.temperatura": {
                            "$regex": "^(37\\.|3[8-9]\\.|4[0-5]\\.)"
                }
            },
            "Interventi con elisoccorso": {"attivazioni": {"$in": ["Elisoccorso"]}},
            "Pazienti da Napoli": {"residenza.comune": {"$regex": "Napoli", "$options": "i"}},
            "Pazienti con trauma cranico": {
                "$or": [
                    {"diagnosi_finale": {"$regex": "cranico|testa|encefalo", "$options": "i"}},
                    {"lesioni_riscontrate": {"$regex": "cranico|testa|encefalo", "$options": "i"}}
                ]
            },
            "Pazienti con GCS < 8 (iniziale)": {
                "$expr": {
                    "$lt": [
                        {"$add": [
                            "$glasgow_coma_scale.iniziale.oculare",
                            "$glasgow_coma_scale.iniziale.verbale", 
                            "$glasgow_coma_scale.iniziale.motoria"
                        ]}, 8
                    ]
                }
            },
            "Pazienti non coscienti": {
                "coscienza.stato": {"$ne": "vigile"}
            },
            "Pazienti con dolore toracico": {
                "sintomi_principali": {"$regex": "toracico|petto|torace", "$options": "i"}
            },
            "Pazienti con difficoltà respiratoria": {
                "sintomi_principali": {"$regex": "respirat|dispnea|fiato", "$options": "i"}
            },
            "Interventi con automedica": {"attivazioni": {"$in": ["Automedica"]}}
        }
        if 'predef_risultati' not in st.session_state:
            st.session_state.predef_risultati = None
        if 'predef_mostra_risultati' not in st.session_state:
            st.session_state.predef_mostra_risultati = False

        query_selezionata = st.selectbox(
            "Seleziona una query predefinita:",
            list(query_predefinite.keys())
        )
        
        # Mostra la query selezionata
        st.json(query_predefinite[query_selezionata])
        
        col1, spacer, col2 = st.columns([1, 8, 1])

        with col1:
            if st.button("🔍 Esegui Query Predefinita"):
                st.session_state.predef_risultati = self._esegui_query_personalizzata(query_predefinite[query_selezionata])
                st.session_state.predef_mostra_risultati = True

        with col2:
            if st.button("📊 Conta Risultati"):
                count = self._conta_risultati(query_predefinite[query_selezionata])
                st.success(f"La query restituisce {count} risultati")
                
        if st.session_state.predef_mostra_risultati and st.session_state.predef_risultati is not None:
            self._mostra_risultati(st.session_state.predef_risultati)

    def _esegui_query_guidata(self, filtri: Dict) -> List[Dict]:
        """
        Converte i filtri dell'interfaccia guidata in query MongoDB
        """
        query = {}
        
        # Filtri anagrafici
        if 'nome' in filtri:
            query['nome'] = {"$regex": filtri['nome'], "$options": "i"}
        
        if 'cognome' in filtri:
            query['cognome'] = {"$regex": filtri['cognome'], "$options": "i"}
        
        if 'sesso' in filtri:
            query['sesso'] = filtri['sesso']
        
        if 'eta_range' in filtri:
            eta_min, eta_max = filtri['eta_range']
            query['eta'] = {"$gte": eta_min, "$lte": eta_max}
        
        if 'luogo_nascita' in filtri:
            query['luogo_nascita'] = {"$regex": filtri['luogo_nascita'], "$options": "i"}
        
        if 'comune_residenza' in filtri:
            query['residenza.comune'] = {"$regex": filtri['comune_residenza'], "$options": "i"}
        
        # Filtri intervento
        if 'data_ricovero' in filtri:
            data_da, data_a = filtri['data_ricovero']
            date_query = {}
            if data_da:
                date_query["$gte"] = data_da.strftime("%Y-%m-%d")
            if data_a:
                date_query["$lte"] = data_a.strftime("%Y-%m-%d")
            if date_query:
                query['data_di_ricovero'] = date_query
        
        if 'codice_uscita' in filtri:
            query['codice_uscita'] = filtri['codice_uscita']
        
        if 'codice_rientro' in filtri:
            query['codice_rientro'] = filtri['codice_rientro']
        
        if 'luogo_intervento' in filtri:
            query['luogo_intervento'] = {"$regex": filtri['luogo_intervento'], "$options": "i"}
        
        if 'condizione_riferita' in filtri:
            query['condizione_riferita'] = {"$regex": filtri['condizione_riferita'], "$options": "i"}
        
        if 'attivazioni' in filtri:
            query['attivazioni'] = {"$in": filtri['attivazioni']}
        
        # Filtri condizione clinica
        if 'diagnosi_sospetta' in filtri:
            query['diagnosi_sospetta'] = {"$regex": filtri['diagnosi_sospetta'], "$options": "i"}
        
        if 'diagnosi_finale' in filtri:
            query['diagnosi_finale'] = {"$regex": filtri['diagnosi_finale'], "$options": "i"}
        
        if 'sintomi_principali' in filtri:
            query['sintomi_principali'] = {"$regex": filtri['sintomi_principali'], "$options": "i"}
        
        if 'lesioni_riscontrate' in filtri:
            query['lesioni_riscontrate'] = {"$regex": filtri['lesioni_riscontrate'], "$options": "i"}
        
        if 'stato_coscienza' in filtri:
            query['coscienza.stato'] = filtri['stato_coscienza']
        
        if 'tipo_respiro' in filtri:
            query['respiro.tipo'] = filtri['tipo_respiro']
        
        # Filtri parametri vitali (aggiornati)
        if 'saturazione_range' in filtri:
            sat_min, sat_max = filtri['saturazione_range']
            # Usa regex per estrarre il valore numerico dalla stringa (es. "100%")
            if sat_min > 0:
                query['parametri_vitali.saturazione'] = {"$regex": f"^[{sat_min//10}-9][0-9]%"}
        
        if 'fc_range' in filtri:
            fc_min, fc_max = filtri['fc_range']
            # Usa regex per estrarre il valore dalla stringa (es. "94 bpm")
            if fc_min > 0 or fc_max < 300:
                query['parametri_vitali.frequenza_cardiaca'] = {"$regex": f"[0-9]+ bpm"}
        
        if 'fr_range' in filtri:
            fr_min, fr_max = filtri['fr_range']
            if fr_min > 0 or fr_max < 60:
                query['respiro.frequenza'] = {"$regex": f"[0-9]+ atti/min"}
        
        if 'temperatura_range' in filtri:
            temp_min, temp_max = filtri['temperatura_range']
            if temp_min > 30.0 or temp_max < 45.0:
                query['parametri_vitali.temperatura'] = {"$regex": f"[0-9]+\\.[0-9]+ °C"}
        
        if 'glicemia_range' in filtri:
            glic_min, glic_max = filtri['glicemia_range']
            if glic_min > 0 or glic_max < 500:
                query['parametri_vitali.glicemia'] = {"$regex": f"[0-9]+ mg/dL"}
        
        # Filtri Glasgow Coma Scale
        if 'gcs_iniziale_range' in filtri:
            gcs_min, gcs_max = filtri['gcs_iniziale_range']
            query['$expr'] = {
                "$and": [
                    {"$gte": [{"$add": [
                        "$glasgow_coma_scale.iniziale.oculare",
                        "$glasgow_coma_scale.iniziale.verbale",
                        "$glasgow_coma_scale.iniziale.motoria"
                    ]}, gcs_min]},
                    {"$lte": [{"$add": [
                        "$glasgow_coma_scale.iniziale.oculare",
                        "$glasgow_coma_scale.iniziale.verbale",
                        "$glasgow_coma_scale.iniziale.motoria"
                    ]}, gcs_max]}
                ]
            }
        
        if 'gcs_ps_range' in filtri:
            gcs_min, gcs_max = filtri['gcs_ps_range']
            if '$expr' in query:
                # Se già esiste un filtro $expr, combinalo
                existing_expr = query['$expr']
                query['$expr'] = {
                    "$and": [
                        existing_expr,
                        {"$gte": [{"$add": [
                            "$glasgow_coma_scale.arrivo_ps.oculare",
                            "$glasgow_coma_scale.arrivo_ps.verbale",
                            "$glasgow_coma_scale.arrivo_ps.motoria"
                        ]}, gcs_min]},
                        {"$lte": [{"$add": [
                            "$glasgow_coma_scale.arrivo_ps.oculare",
                            "$glasgow_coma_scale.arrivo_ps.verbale",
                            "$glasgow_coma_scale.arrivo_ps.motoria"
                        ]}, gcs_max]}
                    ]
                }
            else:
                query['$expr'] = {
                    "$and": [
                        {"$gte": [{"$add": [
                            "$glasgow_coma_scale.arrivo_ps.oculare",
                            "$glasgow_coma_scale.arrivo_ps.verbale",
                            "$glasgow_coma_scale.arrivo_ps.motoria"
                        ]}, gcs_min]},
                        {"$lte": [{"$add": [
                            "$glasgow_coma_scale.arrivo_ps.oculare",
                            "$glasgow_coma_scale.arrivo_ps.verbale",
                            "$glasgow_coma_scale.arrivo_ps.motoria"
                        ]}, gcs_max]}
                    ]
                }
        
        return self._esegui_query_personalizzata(query)
    
    def _esegui_query_personalizzata(self, query: Dict) -> List[Dict]:
        """
        Esegue una query personalizzata sul database
        """
        try:
            # Assumendo che self.db sia la collection MongoDB
            risultati = list(self.db.find(query))  # Limita a 1000 risultati
            return risultati
        except Exception as e:
            st.error(f"Errore nell'esecuzione della query: {str(e)}")
            return []
    
    def _conta_risultati(self, query: Dict) -> int:
        """
        Conta i risultati di una query senza restituire i documenti
        """
        try:
            return self.db.count_documents(query)
        except Exception as e:
            st.error(f"Errore nel conteggio: {str(e)}")
            return 0
    
    def _mostra_risultati(self, risultati: List[Dict]):
        """
        Mostra i risultati della query in formato tabellare e dettagliato
        """
        if not risultati:
            st.warning("Nessun risultato trovato per la query specificata")
            return
        
        st.success(f"Trovati {len(risultati)} risultati")
        
        # Tab per diverse visualizzazioni
        tab1, tab2, tab3 = st.tabs(["📊 Tabella Riassuntiva", "📋 Dettagli Completi", "📈 Statistiche"])
        
        with tab1:
            # Crea una tabella riassuntiva
            df_summary = self._crea_tabella_riassuntiva(risultati)
            st.dataframe(df_summary, use_container_width=True)
            
            # Opzione per download
            csv = df_summary.to_csv(index=False)
            st.download_button(
                label="📥 Scarica CSV",
                data=csv,
                file_name=f"query_risultati_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with tab2:
            # Mostra dettagli completi
            for i, doc in enumerate(risultati[:10]):  # Mostra solo i primi 10 per performance
                with st.expander(f"Paziente {i+1}: {doc.get('nome', 'N/A')} {doc.get('cognome', 'N/A')}"):
                    self._mostra_dettagli_paziente(doc)
            
            if len(risultati) > 10:
                st.info(f"Mostrati i primi 10 risultati su {len(risultati)} totali")
        
        with tab3:
            # Statistiche sui risultati
            self._mostra_statistiche(risultati)
    
    def _mostra_dettagli_paziente(self, doc: Dict):
        """
        Mostra i dettagli completi di un singolo paziente in formato organizzato
        """
        # Dati Anagrafici
        st.subheader("👤 Dati Anagrafici")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Nome:** {doc.get('nome', 'N/A')}")
            st.write(f"**Cognome:** {doc.get('cognome', 'N/A')}")
            st.write(f"**Sesso:** {doc.get('sesso', 'N/A')}")
            st.write(f"**Età:** {doc.get('eta', 'N/A')}")
            st.write(f"**ID:** {doc.get('id', 'N/A')}")
        
        with col2:
            st.write(f"**Data Nascita:** {doc.get('data_nascita', 'N/A')}")
            st.write(f"**Luogo Nascita:** {doc.get('luogo_nascita', 'N/A')}")
            st.write(f"**Telefono:** {doc.get('telefono', 'N/A')}")
            
            # Residenza
            residenza = doc.get('residenza', {})
            if residenza:
                st.write(f"**Via:** {residenza.get('via', 'N/A')}")
                st.write(f"**Comune:** {residenza.get('comune', 'N/A')}")
                st.write(f"**Provincia:** {residenza.get('provincia', 'N/A')}")
        
        # Dati Intervento
        st.subheader("🚑 Dati Intervento")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Data Ricovero:** {doc.get('data_di_ricovero', 'N/A')}")
            st.write(f"**Ora Ricovero:** {doc.get('ora_di_ricovero', 'N/A')}")
            st.write(f"**Luogo Intervento:** {doc.get('luogo_intervento', 'N/A')}")
            st.write(f"**Condizione Riferita:** {doc.get('condizione_riferita', 'N/A')}")
        
        with col2:
            st.write(f"**Codice Uscita:** {doc.get('codice_uscita', 'N/A')}")
            st.write(f"**Codice Rientro:** {doc.get('codice_rientro', 'N/A')}")
            
            # Attivazioni
            attivazioni = doc.get('attivazioni', [])
            if attivazioni:
                st.write(f"**Attivazioni:** {', '.join(attivazioni) if isinstance(attivazioni, list) else attivazioni}")
            
            # Equipaggio
            equipaggio = doc.get('equipaggio', [])
            if equipaggio:
                st.write(f"**Equipaggio:** {', '.join(equipaggio) if isinstance(equipaggio, list) else equipaggio}")
        
        # Condizione Clinica
        st.subheader("🏥 Condizione Clinica")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Diagnosi Sospetta:** {doc.get('diagnosi_sospetta', 'N/A')}")
            st.write(f"**Diagnosi Finale:** {doc.get('diagnosi_finale', 'N/A')}")
            
            # Sintomi principali
            sintomi = doc.get('sintomi_principali', [])
            if sintomi:
                sintomi_str = ', '.join(sintomi) if isinstance(sintomi, list) else sintomi
                st.write(f"**Sintomi Principali:** {sintomi_str}")
        
        with col2:
            # Lesioni riscontrate
            lesioni = doc.get('lesioni_riscontrate', [])
            if lesioni:
                lesioni_str = ', '.join(lesioni) if isinstance(lesioni, list) else lesioni
                st.write(f"**Lesioni Riscontrate:** {lesioni_str}")
            
            # Farmaci indicati
            farmaci = doc.get('farmaci_indicati', [])
            if farmaci:
                farmaci_str = ', '.join(farmaci) if isinstance(farmaci, list) else farmaci
                st.write(f"**Farmaci Indicati:** {farmaci_str}")
            
            # Trattamenti effettuati
            trattamenti = doc.get('trattamenti_effettuati', [])
            if trattamenti:
                trattamenti_str = ', '.join(trattamenti) if isinstance(trattamenti, list) else trattamenti
                st.write(f"**Trattamenti Effettuati:** {trattamenti_str}")
        
        # Parametri Vitali
        st.subheader("📊 Parametri Vitali")
        parametri = doc.get('parametri_vitali', {})
        if parametri:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Pressione:** {parametri.get('pressione', 'N/A')}")
                st.write(f"**Frequenza Cardiaca:** {parametri.get('frequenza_cardiaca', 'N/A')}")
            
            with col2:
                st.write(f"**Saturazione:** {parametri.get('saturazione', 'N/A')}")
                st.write(f"**Temperatura:** {parametri.get('temperatura', 'N/A')}")
            
            with col3:
                st.write(f"**Glicemia:** {parametri.get('glicemia', 'N/A')}")
        
        # Respirazione
        st.subheader("🫁 Respirazione")
        respiro = doc.get('respiro', {})
        if respiro:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Tipo:** {respiro.get('tipo', 'N/A')}")
                st.write(f"**Frequenza:** {respiro.get('frequenza', 'N/A')}")
            
            with col2:
                st.write(f"**Rumori:** {respiro.get('rumori', 'N/A')}")
        
        # Coscienza e Neurologia
        st.subheader("🧠 Stato Neurologico")
        col1, col2 = st.columns(2)
        
        with col1:
            # Coscienza
            coscienza = doc.get('coscienza', {})
            if coscienza:
                st.write(f"**Stato Coscienza:** {coscienza.get('stato', 'N/A')}")
                st.write(f"**Orientamento:** {coscienza.get('orientamento', 'N/A')}")
            
            # Pupille
            pupille = doc.get('pupille_reagenti', {})
            if pupille:
                st.write(f"**Pupille Dx:** {pupille.get('Dx', 'N/A')}")
                st.write(f"**Pupille Sx:** {pupille.get('Sx', 'N/A')}")
        
        with col2:
            # Glasgow Coma Scale
            gcs = doc.get('glasgow_coma_scale', {})
            if gcs:
                gcs_iniziale = gcs.get('iniziale', {})
                gcs_ps = gcs.get('arrivo_ps', {})
                
                if gcs_iniziale:
                    totale_init = (gcs_iniziale.get('oculare', 0) + 
                                  gcs_iniziale.get('verbale', 0) + 
                                  gcs_iniziale.get('motoria', 0))
                    st.write(f"**GCS Iniziale:** {totale_init} (O:{gcs_iniziale.get('oculare', 0)}, V:{gcs_iniziale.get('verbale', 0)}, M:{gcs_iniziale.get('motoria', 0)})")
                
                if gcs_ps:
                    totale_ps = (gcs_ps.get('oculare', 0) + 
                                gcs_ps.get('verbale', 0) + 
                                gcs_ps.get('motoria', 0))
                    st.write(f"**GCS Arrivo PS:** {totale_ps} (O:{gcs_ps.get('oculare', 0)}, V:{gcs_ps.get('verbale', 0)}, M:{gcs_ps.get('motoria', 0)})")
        
        # Cute
        st.subheader("🎨 Aspetto Cutaneo")
        cute = doc.get('cute', {})
        if cute:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"**Colore:** {cute.get('colore', 'N/A')}")
            
            with col2:
                st.write(f"**Temperatura:** {cute.get('temperatura', 'N/A')}")
            
            with col3:
                st.write(f"**Sudorazione:** {cute.get('sudorazione', 'N/A')}")
        
        # Provvedimenti
        st.subheader("⚕️ Provvedimenti")
        provvedimenti = doc.get('provvedimenti', {})
        if provvedimenti:
            col1, col2 = st.columns(2)
            
            with col1:
                prima_val = provvedimenti.get('prima_valutazione', [])
                if prima_val:
                    prima_val_str = ', '.join(prima_val) if isinstance(prima_val, list) else prima_val
                    st.write(f"**Prima Valutazione:** {prima_val_str}")
            
            with col2:
                ospedale = provvedimenti.get('ospedale', [])
                if ospedale:
                    ospedale_str = ', '.join(ospedale) if isinstance(ospedale, list) else ospedale
                    st.write(f"**Ospedale:** {ospedale_str}")
        
        # Esami diagnostici
        esami = doc.get('esami_diagnostici', [])
        if esami:
            st.subheader("🔬 Esami Diagnostici")
            esami_str = ', '.join(esami) if isinstance(esami, list) else esami
            st.write(esami_str)
        
        # Annotazioni
        annotazioni = doc.get('annotazioni', '')
        if annotazioni:
            st.subheader("📝 Annotazioni")
            st.write(annotazioni)
        
        # Firme
        col1, col2 = st.columns(2)
        
        with col1:
            firma_rifiuto = doc.get('firma_paziente_rifiuto', '')
            if firma_rifiuto:
                st.write(f"**Firma Paziente Rifiuto:** {firma_rifiuto}")
        
        with col2:
            firma_decesso = doc.get('firma_medico_decesso', '')
            if firma_decesso:
                st.write(f"**Firma Medico Decesso:** {firma_decesso}")
    
    def _crea_tabella_riassuntiva(self, risultati: List[Dict]) -> pd.DataFrame:
        """
        Crea una tabella riassuntiva dai risultati con tutti i campi principali
        """
        dati_tabella = []
        
        for doc in risultati:
            # Estrai GCS totali
            gcs_iniziale = doc.get('glasgow_coma_scale', {}).get('iniziale', {})
            gcs_totale_init = self.safe_sum_fields(
                gcs_iniziale.get('oculare'),
                gcs_iniziale.get('verbale'),
                gcs_iniziale.get('motoria')
            )
            
            gcs_ps = doc.get('glasgow_coma_scale', {}).get('arrivo_ps', {})
            gcs_totale_ps = self.safe_sum_fields(
                gcs_ps.get('oculare'),
                gcs_ps.get('verbale'),
                gcs_ps.get('motoria')
            )

            
            # Estrai parametri vitali
            parametri = doc.get('parametri_vitali', {})
            respiro = doc.get('respiro', {})
            coscienza = doc.get('coscienza', {})
            residenza = doc.get('residenza', {})
            
            # Converti array in stringhe
            sintomi = doc.get('sintomi_principali', [])
            sintomi_str = ', '.join(sintomi) if isinstance(sintomi, list) and sintomi else 'N/A'
            
            lesioni = doc.get('lesioni_riscontrate', [])
            lesioni_str = ', '.join(lesioni) if isinstance(lesioni, list) and lesioni else 'N/A'
            
            attivazioni = doc.get('attivazioni', [])
            attivazioni_str = ', '.join(attivazioni) if isinstance(attivazioni, list) and attivazioni else 'N/A'
            
            riga = {
                # Dati anagrafici
                'ID': doc.get('id', 'N/A'),
                'Nome': doc.get('nome', 'N/A'),
                'Cognome': doc.get('cognome', 'N/A'),
                'Età': doc.get('eta', 'N/A'),
                'Sesso': doc.get('sesso', 'N/A'),
                'Data Nascita': doc.get('data_nascita', 'N/A'),
                'Luogo Nascita': doc.get('luogo_nascita', 'N/A'),
                'Comune Residenza': residenza.get('comune', 'N/A'),
                'Provincia': residenza.get('provincia', 'N/A'),
                
                # Dati intervento
                'Data Ricovero': doc.get('data_di_ricovero', 'N/A'),
                'Ora Ricovero': doc.get('ora_di_ricovero', 'N/A'),
                'Luogo Intervento': doc.get('luogo_intervento', 'N/A'),
                'Codice Uscita': doc.get('codice_uscita', 'N/A'),
                'Codice Rientro': doc.get('codice_rientro', 'N/A'),
                'Attivazioni': attivazioni_str,
                
                # Condizione clinica
                'Condizione Riferita': doc.get('condizione_riferita', 'N/A'),
                'Sintomi Principali': sintomi_str,
                'Diagnosi Sospetta': doc.get('diagnosi_sospetta', 'N/A'),
                'Diagnosi Finale': doc.get('diagnosi_finale', 'N/A'),
                'Lesioni Riscontrate': lesioni_str,
                
                # Parametri vitali
                'Pressione': parametri.get('pressione', 'N/A'),
                'Frequenza Cardiaca': parametri.get('frequenza_cardiaca', 'N/A'),
                'Saturazione': parametri.get('saturazione', 'N/A'),
                'Temperatura': parametri.get('temperatura', 'N/A'),
                'Glicemia': parametri.get('glicemia', 'N/A'),
                
                # Respirazione
                'Tipo Respiro': respiro.get('tipo', 'N/A') if isinstance(respiro, dict) else respiro or 'N/A',

                'Frequenza Respiratoria': respiro.get('frequenza', 'N/A') if isinstance(respiro, dict) else 'N/A',

                
                # Neurologia
                'Stato Coscienza': coscienza.get('stato', 'N/A') if isinstance(coscienza, dict) else coscienza or 'N/A',
                'GCS Iniziale': gcs_totale_init if gcs_totale_init > 0 else 'N/A',
                'GCS Arrivo PS': gcs_totale_ps if gcs_totale_ps > 0 else 'N/A',
            }
            dati_tabella.append(riga)
        
        return pd.DataFrame(dati_tabella)
    
    def _mostra_statistiche(self, risultati: List[Dict]):
        """
        Mostra statistiche dettagliate sui risultati
        """
        if not risultati:
            return
        
        # Statistiche generali
        st.subheader("📊 Statistiche Generali")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Totale Pazienti", len(risultati))
        
        with col2:
            età_valida = [doc.get('eta', 0) for doc in risultati if doc.get('eta') and isinstance(doc.get('eta'), (int, float))]
            if età_valida:
                età_media = sum(età_valida) / len(età_valida)
                st.metric("Età Media", f"{età_media:.1f} anni")
            else:
                st.metric("Età Media", "N/A")
        
        with col3:
            maschi = sum(1 for doc in risultati if doc.get('sesso') == 'M')
            perc_maschi = (maschi/len(risultati)*100) if len(risultati) > 0 else 0
            st.metric("Maschi", f"{maschi} ({perc_maschi:.1f}%)")
        
        with col4:
            femmine = sum(1 for doc in risultati if doc.get('sesso') == 'F')
            perc_femmine = (femmine/len(risultati)*100) if len(risultati) > 0 else 0
            st.metric("Femmine", f"{femmine} ({perc_femmine:.1f}%)")
        
        # Distribuzione per codice uscita
        st.subheader("🚨 Distribuzione Codici Uscita")
        codici_uscita = {}
        for doc in risultati:
            codice = doc.get('codice_uscita', 'N/A')
            codici_uscita[codice] = codici_uscita.get(codice, 0) + 1
        
        if codici_uscita:
            df_codici = pd.DataFrame(list(codici_uscita.items()), columns=['Codice', 'Frequenza'])
            st.bar_chart(df_codici.set_index('Codice'))
        
        # Distribuzione età
        st.subheader("👥 Distribuzione per Età")
        if età_valida:
            fig, ax = plt.subplots()
            ax.hist(età_valida, bins=10, edgecolor='black')
            ax.set_title("Distribuzione Età")
            ax.set_xlabel("Età")
            ax.set_ylabel("Frequenza")
            st.pyplot(fig)

        
        # Top 10 comuni
        st.subheader("🏘️ Top 10 Comuni di Residenza")
        comuni = {}
        for doc in risultati:
            comune = doc.get('residenza', {}).get('comune', 'N/A')
            if comune != 'N/A':
                comuni[comune] = comuni.get(comune, 0) + 1
        
        if comuni:
            top_comuni = sorted(comuni.items(), key=lambda x: x[1], reverse=True)[:10]
            df_comuni = pd.DataFrame(top_comuni, columns=['Comune', 'Frequenza'])
            st.bar_chart(df_comuni.set_index('Comune'))
        
        # Top diagnosi
        st.subheader("🏥 Top 10 Diagnosi Finali")
        diagnosi = {}
        for doc in risultati:
            diag = doc.get('diagnosi_finale', 'N/A')
            if diag != 'N/A' and diag.strip():
                diagnosi[diag] = diagnosi.get(diag, 0) + 1
        
        if diagnosi:
            top_diagnosi = sorted(diagnosi.items(), key=lambda x: x[1], reverse=True)[:10]
            df_diagnosi = pd.DataFrame(top_diagnosi, columns=['Diagnosi', 'Frequenza'])
            st.bar_chart(df_diagnosi.set_index('Diagnosi'))
        
        # Statistiche GCS
        st.subheader("🧠 Statistiche Glasgow Coma Scale")
        gcs_iniziali = []
        gcs_ps = []
        
        for doc in risultati:
            gcs_init = doc.get('glasgow_coma_scale', {}).get('iniziale', {})
            totale_init = self.safe_sum_fields(
                gcs_init.get('oculare'),
                gcs_init.get('verbale'),
                gcs_init.get('motoria')
            )
            if totale_init > 0:
                gcs_iniziali.append(totale_init)

            gcs_arrivo = doc.get('glasgow_coma_scale', {}).get('arrivo_ps', {})
            totale_ps = self.safe_sum_fields(
                gcs_arrivo.get('oculare'),
                gcs_arrivo.get('verbale'),
                gcs_arrivo.get('motoria')
            )
            if totale_ps > 0:
                gcs_ps.append(totale_ps)

        
        if gcs_iniziali or gcs_ps:
            col1, col2 = st.columns(2)
            
            with col1:
                if gcs_iniziali:
                    st.write("**GCS Iniziale:**")
                    st.write(f"Media: {sum(gcs_iniziali)/len(gcs_iniziali):.1f}")
                    st.write(f"Min: {min(gcs_iniziali)}, Max: {max(gcs_iniziali)}")
                    
                    # Distribuzione GCS iniziale
                    df_gcs_init = pd.DataFrame({'GCS_Iniziale': gcs_iniziali})
                    st.bar_chart(df_gcs_init['GCS_Iniziale'].value_counts().sort_index())
            
            with col2:
                if gcs_ps:
                    st.write("**GCS Arrivo PS:**")
                    st.write(f"Media: {sum(gcs_ps)/len(gcs_ps):.1f}")
                    st.write(f"Min: {min(gcs_ps)}, Max: {max(gcs_ps)}")
                    
                    # Distribuzione GCS PS
                    df_gcs_ps = pd.DataFrame({'GCS_PS': gcs_ps})
                    st.bar_chart(df_gcs_ps['GCS_PS'].value_counts().sort_index())
    

    def _geocodifica_indirizzo(self, comune, provincia, via=None):
            """
            Geocodifica un indirizzo italiano usando Nominatim
            """
            geolocator = Nominatim(user_agent="paziente_tracker")
            
            # Prova diversi formati di indirizzo
            indirizzi_da_provare = []
            
            if via:
                indirizzi_da_provare.append(f"{via}, {comune}, {provincia}, Italia")
            
            indirizzi_da_provare.extend([
                f"{comune}, {provincia}, Italia",
                f"{comune}, Italia",
                f"{comune}"
            ])
            
            for indirizzo in indirizzi_da_provare:
                try:
                    location = geolocator.geocode(indirizzo, timeout=10)
                    if location:
                        return location.latitude, location.longitude
                    time.sleep(1)  # Rispetta i rate limits
                except GeocoderTimedOut:
                    continue
                except Exception as e:
                    continue
            
            return None, None

    def _raggruppa_per_comune(self, risultati):
            """
            Raggruppa i pazienti per comune e conta le occorrenze
            """
            comuni_count = defaultdict(list)
            
            for doc in risultati:
                residenza = doc.get('residenza', {})
                comune = residenza.get('comune', '').strip()
                provincia = residenza.get('provincia', '').strip()
                via = residenza.get('via', '').strip()
                
                if comune:
                    key = f"{comune}_{provincia}" if provincia else comune
                    comuni_count[key].append({
                        'comune': comune,
                        'provincia': provincia,
                        'via': via,
                        'paziente': f"{doc.get('nome', 'N/A')} {doc.get('cognome', 'N/A')}",
                        'eta': doc.get('eta', 'N/A'),
                        'sesso': doc.get('sesso', 'N/A'),
                        'data_ricovero': doc.get('data_di_ricovero', 'N/A'),
                        'codice_uscita': doc.get('codice_uscita', 'N/A')
                    })
            
            return dict(comuni_count)

    def _crea_mappa_pazienti(self, risultati):
            """
            Crea una mappa interattiva con la distribuzione geografica dei pazienti
            """
            if not risultati:
                st.warning("Nessun dato disponibile per la mappa")
                return
            
            st.subheader("🗺️ Mappa Geografica Pazienti")
            
            # Opzioni di visualizzazione
            col1, col2 = st.columns(2)
            
            with col1:
                modalita_zoom = st.selectbox(
                    "Modalità visualizzazione:",
                    ["Raggruppamento per Comune", "Indirizzi Specifici"]
                )
            
            with col2:
                mostra_dettagli = st.checkbox("Mostra dettagli pazienti nei popup", value=True)
            
            # Raggruppa per comune
            comuni_data = self._raggruppa_per_comune(risultati)
            
            if not comuni_data:
                st.warning("Nessun dato geografico valido trovato")
                return
            
            # Inizializza la mappa centrata sull'Italia
            mappa = folium.Map(
                location=[41.8719, 12.5674],  # Centro Italia (Roma)
                zoom_start=6,
                tiles='OpenStreetMap'
            )
            
            # Barra di progresso per la geocodifica
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            geocoded_data = []
            total_comuni = len(comuni_data)
            
            # Cache per le coordinate già geocodificate
            if 'geocode_cache' not in st.session_state:
                st.session_state.geocode_cache = {}
            
            for idx, (key, pazienti_list) in enumerate(comuni_data.items()):
                progress_bar.progress((idx + 1) / total_comuni)
                status_text.text(f"Geocodificando {key}... ({idx + 1}/{total_comuni})")
                
                comune = pazienti_list[0]['comune']
                provincia = pazienti_list[0]['provincia']
                
                # Controlla la cache
                cache_key = f"{comune}_{provincia}"
                if cache_key in st.session_state.geocode_cache:
                    lat, lon = st.session_state.geocode_cache[cache_key]
                else:
                    lat, lon = self._geocodifica_indirizzo(comune, provincia)
                    if lat and lon:
                        st.session_state.geocode_cache[cache_key] = (lat, lon)
                
                if lat and lon:
                    geocoded_data.append({
                        'comune': comune,
                        'provincia': provincia,
                        'lat': lat,
                        'lon': lon,
                        'count': len(pazienti_list),
                        'pazienti': pazienti_list
                    })
            
            progress_bar.empty()
            status_text.empty()
            
            if not geocoded_data:
                st.error("Impossibile geocodificare nessun indirizzo")
                return
            
            # Aggiungi marker alla mappa
            for data in geocoded_data:
                count = data['count']
                comune = data['comune']
                provincia = data['provincia']
                pazienti = data['pazienti']
                
                # Crea il popup con informazioni
                popup_html = f"""
                <div style="width: 250px;">
                    <h4>{comune} ({provincia})</h4>
                    <p><strong>Numero pazienti:</strong> {count}</p>
                """
                
                if mostra_dettagli and count <= 10:  # Mostra dettagli solo per gruppi piccoli
                    popup_html += "<hr><strong>Dettagli pazienti:</strong><br>"
                    for paziente in pazienti[:5]:  # Mostra max 5 pazienti
                        popup_html += f"""
                        • {paziente['paziente']} ({paziente['eta']} anni, {paziente['sesso']})<br>
                        &nbsp;&nbsp;Data: {paziente['data_ricovero']}, Codice: {paziente['codice_uscita']}<br>
                        """
                    if count > 5:
                        popup_html += f"<em>... e altri {count - 5} pazienti</em><br>"
                
                popup_html += "</div>"
                
                # Determina il colore e la dimensione del marker in base al numero di pazienti
                if count == 1:
                    color = 'lightblue'
                    radius = 8
                elif count <= 5:
                    color = 'blue'
                    radius = 12
                elif count <= 10:
                    color = 'orange'
                    radius = 16
                elif count <= 20:
                    color = 'red'
                    radius = 20
                else:
                    color = 'darkred'
                    radius = 25
                
                # Aggiungi marker cluster-style
                folium.CircleMarker(
                    location=[data['lat'], data['lon']],
                    radius=radius,
                    popup=folium.Popup(popup_html, max_width=350),
                    color='white',
                    weight=2,
                    fillColor=color,
                    fillOpacity=0.7,
                    tooltip=f"{comune} ({provincia}): {count} pazienti"
                ).add_to(mappa)
                
                # Aggiungi etichetta con il numero per gruppi > 1
                if count > 1:
                    folium.DivIcon(
                        html=f'<div style="font-size: 12px; font-weight: bold; color: white; text-align: center; margin-top: -6px;">{count}</div>',
                        icon_size=(20, 20),
                        icon_anchor=(10, 10),
                    ).add_to(mappa)
            
        
            # Mostra la mappa

            st.markdown("""
                <style>
                .folium-map {
                    height: 500px !important;
                    border: 2px solid #ccc;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    margin-bottom: 1rem;
                }
                </style>
                """, unsafe_allow_html=True)

            # Chiamata diretta
            map_data = st_folium(mappa, width=700, height=500)

            


            # Legenda sotto la mappa
            st.markdown("""
                <div style="padding: 10px; border: 1px solid #ccc; border-radius: 10px; background-color: #fff;">
                    <strong>📋 Legenda</strong><br>
                    <span style="color:lightblue;">●</span> 1 paziente<br>
                    <span style="color:blue;">●</span> 2–5 pazienti<br>
                    <span style="color:orange;">●</span> 6–10 pazienti<br>
                    <span style="color:red;">●</span> 11–20 pazienti<br>
                    <span style="color:darkred;">●</span> 20+ pazienti
                </div>
                """, unsafe_allow_html=True)


            
            # Statistiche geografiche
            st.subheader("📊 Statistiche Geografiche")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Comuni Rappresentati", len(geocoded_data))
            
            with col2:
                province = set(data['provincia'] for data in geocoded_data if data['provincia'])
                st.metric("Province Rappresentate", len(province))
            
            with col3:
                max_pazienti = max(data['count'] for data in geocoded_data)
                comune_max = next(data['comune'] for data in geocoded_data if data['count'] == max_pazienti)
                st.metric("Max Pazienti per Comune", f"{max_pazienti} ({comune_max})")
            
            with col4:
                geocoded_count = sum(data['count'] for data in geocoded_data)
                perc_geocoded = (geocoded_count / len(risultati)) * 100
                st.metric("% Geocodificati", f"{perc_geocoded:.1f}%")
            
            # Top 10 comuni
            st.subheader("🏆 Top 10 Comuni per Numero Pazienti")
            top_comuni = sorted(geocoded_data, key=lambda x: x['count'], reverse=True)[:10]
            
            df_top = pd.DataFrame([{
                'Comune': f"{data['comune']} ({data['provincia']})",
                'Numero Pazienti': data['count'],
                'Percentuale': f"{(data['count']/len(risultati)*100):.1f}%"
            } for data in top_comuni])
            
            st.dataframe(df_top, use_container_width=True)

    def _mostra_risultati(self, risultati: List[Dict]):
            """
            Mostra i risultati della query in formato tabellare e dettagliato (VERSIONE AGGIORNATA)
            """
            if not risultati:
                st.warning("Nessun risultato trovato per la query specificata")
                return
            
            st.success(f"Trovati {len(risultati)} risultati")
            
            # Tab per diverse visualizzazioni (AGGIORNATO con la mappa)
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Tabella Riassuntiva", "📋 Dettagli Completi", "📈 Statistiche", "🗺️ Mappa Geografica"])
            
            with tab1:
                # Crea una tabella riassuntiva
                df_summary = self._crea_tabella_riassuntiva(risultati)
                st.dataframe(df_summary, use_container_width=True)
                
                # Opzione per download
                csv = df_summary.to_csv(index=False)
                st.download_button(
                    label="📥 Scarica CSV",
                    data=csv,
                    file_name=f"query_risultati_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with tab2:
                # Mostra dettagli completi
                for i, doc in enumerate(risultati[:10]):  # Mostra solo i primi 10 per performance
                    with st.expander(f"Paziente {i+1}: {doc.get('nome', 'N/A')} {doc.get('cognome', 'N/A')}"):
                        self._mostra_dettagli_paziente(doc)
                
                if len(risultati) > 10:
                    st.info(f"Mostrati i primi 10 risultati su {len(risultati)} totali")
            
            with tab3:
                # Statistiche sui risultati
                self._mostra_statistiche(risultati)
            
            with tab4:
                # NUOVA TAB: Mappa geografica
                self._crea_mappa_pazienti(risultati)
    
    
    def _mostra_mappa_geografica(self):
        """
        Wrapper per visualizzare la mappa geografica con dati predefiniti
        """

        # Esegui una query per ottenere i dati (es. tutti i pazienti o pazienti recenti)
        query = {}  # o una query predefinita più selettiva
        risultati = self._esegui_query_personalizzata(query)

        if risultati:
            self._crea_mappa_pazienti(risultati)
        else:
            st.warning("Nessun dato disponibile per la visualizzazione sulla mappa.")

# Funzione principale da chiamare in app.py
def mostra_query_personalizzate(db_connection):
    """
    Funzione principale da importare e chiamare in app.py
    """
    query_handler = QueryPersonalizzate(db_connection)
    query_handler.mostra_interfaccia_query()





