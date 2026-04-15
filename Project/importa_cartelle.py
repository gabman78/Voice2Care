from pymongo import MongoClient
import json
import os

# Connessione al database MongoDB locale
client = MongoClient("mongodb://mongo:27017")
db = client["voice2care"]
collection = db["cartelle_cliniche"]

def importa_cartelle_da_file(percorso_file):
    """
    Importa una lista di cartelle cliniche da file JSON nel database MongoDB.
    Se una cartella con lo stesso ID esiste già, viene sovrascritta.
    """
    if not os.path.exists(percorso_file):
        print(f"❌ File non trovato: {percorso_file}")
        return

    try:
        with open(percorso_file, "r", encoding="utf-8") as f:
            cartelle = json.load(f)

        conteggio_aggiornati = 0
        for cartella in cartelle:
            result = collection.replace_one(
                {"id": cartella["id"]}, cartella, upsert=True
            )
            if result.matched_count:
                conteggio_aggiornati += 1

        print(f"✅ {len(cartelle)} cartelle elaborate.")
        print(f"↪️ {conteggio_aggiornati} cartelle aggiornate, {len(cartelle) - conteggio_aggiornati} nuove inserite.")
    except Exception as e:
        print(f"❌ Errore durante l'importazione: {e}")

def importa_singola_cartella(cartella):
    """
    Importa una singola cartella clinica nel database MongoDB.
    Se esiste già una cartella con lo stesso ID, non viene aggiunta.
    """
    try:
        if not isinstance(cartella, dict):
            raise ValueError("Il parametro 'cartella' deve essere un dizionario Python.")

        cartella_id = cartella.get("id")
        if not cartella_id:
            raise ValueError("La cartella clinica deve contenere un campo 'id'.")

      
        collection.insert_one(cartella)
        print(f"✅ Cartella con ID '{cartella_id}' importata con successo.")
    except Exception as e:
        print(f"❌ Errore durante l'importazione della cartella: {e}")


if __name__ == "__main__":
    importa_cartelle_da_file("json_samples/cartelle_cliniche_v7.json")
    
    
#    with open("cartelle_cliniche/CNNMTT01P20M289H.json", "r", encoding="utf-8") as f:
#        cartella = json.load(f)

#    importa_singola_cartella(cartella)