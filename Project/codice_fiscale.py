import os
from codicefiscale import codicefiscale
import unicodedata

def calcola_codice_fiscale(nome, cognome, sesso, data_nascita, luogo_nascita):
    # Per i cognomi con apostrofi o accenti
    def pulisci_stringa(s): 
        return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().replace("'", "").strip()
    try:
        nome = pulisci_stringa(nome)
        cognome = pulisci_stringa(cognome)
        sesso = sesso.strip().upper()
        data_nascita = data_nascita.strip()
        luogo_nascita = pulisci_stringa(luogo_nascita)
        cf = codicefiscale.encode(
            lastname=cognome,
            firstname=nome,
            gender=sesso,
            birthdate=data_nascita,
            birthplace=luogo_nascita
        )
        if cf:
            return cf.upper()
        else:
            print(f"[DEBUG] Codice fiscale non generato con dati: "
                  f"{nome=}, {cognome=}, {sesso=}, {data_nascita=}, {luogo_nascita=}")
    except Exception as e:
        print("Errore calcolo CF:", e)
        print(f"[EXCEPTION DATA] {nome=}, {cognome=}, {sesso=}, {data_nascita=}, {luogo_nascita=}")

    # Fallback incrementale
    counter_path = "cartelle_cliniche/id_counter.txt"
    os.makedirs(os.path.dirname(counter_path), exist_ok=True)
    if os.path.exists(counter_path):
        with open(counter_path, "r") as f:
            current = int(f.read().strip())
    else:
        current = 0
    current += 1

    with open(counter_path, "w") as f:
        f.write(str(current))
    return f"ID{current:04d}"