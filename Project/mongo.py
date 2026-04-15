from pymongo import MongoClient
import json
import os

# Connessione al database MongoDB (modifica se usi MongoDB Atlas)
client = MongoClient("mongodb://localhost:27017")
db = client["voice2care"]
collection = db["cartelle_cliniche"]

def salva_cartella_clinica(json_data):
    """
    Inserisce una cartella clinica (dizionario Python) nel database MongoDB.
    """
    try:
        collection.insert_one(json_data)
        print("✅ Cartella clinica salvata nel database.")
    except Exception as e:
        print(f"❌ Errore durante il salvataggio nel database: {e}")

def cerca_utenti(query):
    """
    Cerca utenti nel database in base al nome, cognome o codice fiscale.
    Se la query è vuota, restituisce solo i primi 100 utenti ordinati alfabeticamente.
    """
    if not query:
        return list(
            collection.find({}, {"_id": 0, "id": 1, "nome": 1, "cognome": 1})
                     .sort([("cognome", 1), ("nome", 1)])
                     .limit(100)
        )

    regex = {"$regex": query, "$options": "i"}
    filtro = {
        "$or": [
            {"nome": regex},
            {"cognome": regex},
            {"id": regex}
        ]
    }
    return list(
        collection.find(filtro, {"_id": 0, "id": 1, "nome": 1, "cognome": 1})
    )

def trova_cartella(codice_fiscale):
    cartella = collection.find_one({"id": codice_fiscale})
    if cartella:
        # Fix legacy salvataggio errato di residenza come stringa
        if isinstance(cartella.get("residenza"), str):
            cartella["residenza"] = {
                "via": cartella["residenza"],
                "comune": "",
                "provincia": ""
            }
    return cartella

def elimina_cartella(codice_fiscale):
    """
    Elimina una cartella clinica dal database in base al codice fiscale.
    """
    result = collection.delete_one({"id": codice_fiscale})
    return result.deleted_count > 0

def recupera_tutte_cartelle():
    """
    Restituisce tutte le cartelle cliniche dal database, escludendo il campo '_id'.
    """
    try:
        return list(collection.find({}, {"_id": 0}))
    except Exception as e:
        print(f"❌ Errore durante il recupero delle cartelle: {e}")
        return []
    
def modifica_cartella(codice_fiscale, nuovi_dati):
    try:
        # Rimuovi eventuale chiave _id se presente
        if "_id" in nuovi_dati:
            del nuovi_dati["_id"]

        result = collection.update_one(
            {"id": codice_fiscale},
            {"$set": nuovi_dati}
        )
        return result.modified_count > 0
    except Exception as e:
        print(f"❌ Errore durante la modifica: {e}")
        return False

def get_database_connection():
    # Importa la tua funzione esistente da mongo.py
    return collection