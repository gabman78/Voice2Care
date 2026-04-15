import streamlit as st
import matplotlib.pyplot as plt
import base64
import io
from wordcloud import WordCloud
from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017")
db = client["voice2care"]
collection = db["cartelle_cliniche"]

def mostra_distribuzioni():
    st.header("📊 Analisi Statistiche Dinamiche")

    esempio_doc = collection.find_one()
    campi_disponibili = ["età"] + [k for k in esempio_doc.keys() if k not in ["_id", "data_nascita"]]
    campo_scelto = st.selectbox("📌 Seleziona un campo da analizzare", campi_disponibili)
    if campo_scelto == "età":
        # Calcolo età lato client (non disponibile direttamente su Mongo)
        cursor = collection.find({"data_nascita": {"$exists": True}})
        dati = list(cursor)
        età = []
        for d in dati:
            try:
                nascita = datetime.strptime(d["data_nascita"], "%Y-%m-%d")
                anni = (datetime.today() - nascita).days // 365
                età.append(anni)
            except:
                continue

        if not età:
            st.warning("⚠️ Nessuna data di nascita valida.")
            return

        fig, ax = plt.subplots()
        ax.hist(età, bins=20, edgecolor='black')
        ax.set_xlabel("Età")
        ax.set_ylabel("Numero di pazienti")
        st.pyplot(fig)

    else:
        pipeline = []

        # Verifica se il campo scelto è una lista in almeno un documento
        esempio_array = collection.find_one({campo_scelto: {"$type": "array"}})
        if esempio_array:
            pipeline.append({"$unwind": f"${campo_scelto}"})

        # Aggiungi le fasi valide
        pipeline.extend([
            {"$group": {"_id": f"${campo_scelto}", "conteggio": {"$sum": 1}}},
            {"$sort": {"conteggio": -1}}
        ])
        risultati = list(collection.aggregate(pipeline))

        if not risultati:
            st.warning("⚠️ Nessun dato disponibile.")
            return

        labels = [r["_id"] for r in risultati if r["_id"]]
        counts = [r["conteggio"] for r in risultati if r["_id"]]

        fig, ax = plt.subplots(figsize=(min(25, len(labels) * 0.5), 6))
        ax.bar(labels, counts, edgecolor='black')
        ax.set_xlabel(campo_scelto.capitalize())
        ax.set_ylabel("Numero di pazienti")
        plt.xticks(rotation=90)

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", bbox_inches="tight")
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.read()).decode()

        st.markdown(
            f"""
            <div style='overflow-x: auto; width: 100%; border: 1px solid #ccc; padding: 10px;'>
                <img src='data:image/png;base64,{img_base64}'/>
            </div>
            """,
            unsafe_allow_html=True
        )

def mostra_query_personalizzata():
    st.subheader("🔎 Query personalizzata")
    campo = st.selectbox("Campo", collection.find_one().keys())
    valore = st.text_input("Valore da cercare")

    if valore:
        filtro = {campo: {"$regex": valore, "$options": "i"}}
        risultati = list(collection.find(filtro, {"_id": 0}))
        st.write(f"🔍 Trovati: {len(risultati)}")
        st.dataframe(risultati)

def grafico_sesso():
    st.subheader("🔹 Distribuzione per sesso")
    pipeline = [
        {"$group": {"_id": "$sesso", "conteggio": {"$sum": 1}}},
        {"$sort": {"conteggio": -1}}
    ]
    risultati = list(collection.aggregate(pipeline))

    labels = [r["_id"] for r in risultati]
    sizes = [r["conteggio"] for r in risultati]

    fig, ax = plt.subplots()
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis('equal')
    st.pyplot(fig)

def grafico_top_motivi(top_n=10):
    st.subheader(f"🔹 Top {top_n} motivi di ricovero")
    pipeline = [
        {"$unwind": "$motivo_del_ricovero"},
        {"$group": {"_id": "$motivo_del_ricovero", "conteggio": {"$sum": 1}}},
        {"$sort": {"conteggio": -1}},
        {"$limit": top_n}
    ]
    risultati = list(collection.aggregate(pipeline))

    motivi = [r["_id"] for r in risultati]
    conteggi = [r["conteggio"] for r in risultati]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(motivi, conteggi, edgecolor='black')
    ax.invert_yaxis()
    st.pyplot(fig)

def grafico_top_diagnosi(top_n=10):
    st.subheader(f"🔹 Top {top_n} diagnosi sospette")
    pipeline = [
        {"$group": {"_id": "$diagnosi_sospetta", "conteggio": {"$sum": 1}}},
        {"$sort": {"conteggio": -1}},
        {"$limit": top_n}
    ]
    risultati = list(collection.aggregate(pipeline))

    diagnosi = [r["_id"] for r in risultati]
    conteggi = [r["conteggio"] for r in risultati]

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(diagnosi, conteggi, edgecolor='black')
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

def grafico_metodo_arrivo():
    st.subheader("🔹 Metodi di arrivo")
    pipeline = [
        {"$unwind": "$metodo_di_arrivo"},
        {"$group": {"_id": "$metodo_di_arrivo", "conteggio": {"$sum": 1}}}
    ]
    risultati = list(collection.aggregate(pipeline))
    labels = [r["_id"] for r in risultati]
    counts = [r["conteggio"] for r in risultati]

    fig, ax = plt.subplots()
    ax.bar(labels, counts, edgecolor='black')
    st.pyplot(fig)

def grafico_ricoveri_per_mese():
    st.subheader("🔹 Ricoveri per mese")
    pipeline = [
        {"$project": {"mese": {"$substr": ["$data_di_ricovero", 0, 7]}}},
        {"$group": {"_id": "$mese", "conteggio": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    risultati = list(collection.aggregate(pipeline))
    mesi = [r["_id"] for r in risultati]
    counts = [r["conteggio"] for r in risultati]

    fig, ax = plt.subplots()
    ax.plot(mesi, counts, marker='o')
    plt.xticks(rotation=45)
    st.pyplot(fig)

def grafico_fasce_orarie():
    st.subheader("🔹 Distribuzione per ora del giorno")
    cursor = collection.find({"ora_di_ricovero": {"$exists": True}})
    ore = []
    for doc in cursor:
        try:
            ora = int(doc["ora_di_ricovero"].split(":")[0])
            ore.append(ora)
        except:
            continue

    fig, ax = plt.subplots()
    ax.hist(ore, bins=24, edgecolor='black')
    ax.set_xlabel("Ora")
    ax.set_ylabel("Numero di ricoveri")
    st.pyplot(fig)

def grafico_eta_media_per_diagnosi(top_n=8):
    st.subheader("🔹 Età media per diagnosi sospetta")
    cursor = collection.find({"data_nascita": {"$exists": True}, "diagnosi_sospetta": {"$exists": True}})
    età_diagnosi = {}

    for doc in cursor:
        try:
            nascita = datetime.strptime(doc["data_nascita"], "%Y-%m-%d")
            eta = (datetime.today() - nascita).days // 365
            diagnosi = doc["diagnosi_sospetta"]
            if diagnosi in età_diagnosi:
                età_diagnosi[diagnosi].append(eta)
            else:
                età_diagnosi[diagnosi] = [eta]
        except:
            continue

    medie = {k: sum(v)/len(v) for k, v in età_diagnosi.items() if v}
    top = sorted(medie.items(), key=lambda x: x[1], reverse=True)[:top_n]
    diagnosi, medie_eta = zip(*top)

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.barh(diagnosi, medie_eta, edgecolor='black')
    ax.invert_yaxis()
    ax.set_xlabel("Età media")
    st.pyplot(fig)

def grafico_wordcloud_sintomi():
    st.subheader("🔹 Word-cloud dei sintomi principali")
    cursor = collection.find({"sintomi_principali": {"$exists": True}})
    testo = []
    for doc in cursor:
        sintomi = doc.get("sintomi_principali", [])
        if isinstance(sintomi, list):
            testo.extend(sintomi)
        else:
            testo.append(sintomi)

    if not testo:
        st.info("Nessun sintomo disponibile.")
        return

    wc = WordCloud(width=800, height=400, background_color="white").generate(" ".join(testo))
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig)
