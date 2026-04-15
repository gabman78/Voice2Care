import json
from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["voice2care"]
collection = db["cartelle_cliniche"]

# Recupera tutti i documenti
dati = list(collection.find({}, {"_id": 0}))  # rimuove campo _id

# Salva in un file JSON
with open("DBCompleto.json", "w", encoding="utf-8") as f:
    json.dump(dati, f, ensure_ascii=False, indent=4)

print("✅ Esportazione completata!")
