import json
import os
import random
import logging
from pymongo import MongoClient
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import joblib
import time
from datetime import datetime

SOGLIA_DATA = datetime.strptime("11-07-2025", "%d-%m-%Y")

# CONFIG
MONGO_URI = "mongo_url"
DB_NAME = "Bandi"
BANDI_COLLECTION = "Lombardia"
REQUIRED_FIELDS = [
    "codice", "categoria", "titolo", "url", "stato",
    "tipo_utente", "data_chiusura", "allegati", "scheda_info", "regione"
]

# Carica modello e encoder solo una volta
pipeline_categoria = joblib.load("modello_tfidf_svm.joblib")
label_encoder_categoria = joblib.load("modello_label_encoder.joblib")

# Caricamento del modello, tokenizer e label encoder per tipo_utente
MODEL_PATH = "./modello_tipo_utente"
tokenizer_tipo_utente = AutoTokenizer.from_pretrained(MODEL_PATH)
model_tipo_utente = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
label_encoder_tipo_utente = joblib.load("label_encoder_tipo_utente.joblib")

"""
# MODELLO ML 
MODEL_PATH = "./modello_bandi"
tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH)
label_encoder = joblib.load("label_encoder.joblib")
"""
# LOGGING 
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bandi_process.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# MONGO
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
bandi_collection = db[BANDI_COLLECTION]

def genera_codice_bando(regione):
    prefix = regione[:2].upper() if regione else "XX"
    numero = random.randint(100000000000, 999999999999)
    return prefix + str(numero)

def normalizza_data(data_input):
    from datetime import datetime

    if not data_input or not isinstance(data_input, str):
        return None

    data_input = data_input.strip()

    mesi = {
        "Gen": "Jan", "Feb": "Feb", "Mar": "Mar", "Apr": "Apr",
        "Mag": "May", "Giu": "Jun", "Lug": "Jul", "Ago": "Aug",
        "Set": "Sep", "Ott": "Oct", "Nov": "Nov", "Dic": "Dec"
    }

    # Caso 1: formato numerico tipo "31/07/2025"
    try:
        data_obj = datetime.strptime(data_input, "%d/%m/%Y")
        return data_obj.strftime("%d-%m-%Y")
    except ValueError:
        pass

    # Caso 1b: formato numerico con orario tipo "31/07/2025 12:00"
    try:
        data_obj = datetime.strptime(data_input, "%d/%m/%Y %H:%M")
        return data_obj.strftime("%d-%m-%Y")
    except ValueError:
        pass

    # Caso 2: formato con mese italiano abbreviato "8 Set 2025"
    for ita, eng in mesi.items():
        if ita in data_input:
            data_input_eng = data_input.replace(ita, eng)
            try:
                data_obj = datetime.strptime(data_input_eng, "%d %b %Y")
                return data_obj.strftime("%d-%m-%Y")
            except ValueError:
                return None

    return None
def controlla_e_correggi_bando(bando):
    modificato = False
    errori = []

    possibili_url = ["url", "link_dettaglio", "link", "url_bando", "web", "indirizzo", "website"]
    if "url" not in bando:
        trovato_url = False
        for alt in possibili_url:
            if alt in bando:
                bando["url"] = bando.pop(alt)
                modificato = True
                trovato_url = True
                break
        if not trovato_url:
            errori.append("Manca campo obbligatorio: url")

    for campo in REQUIRED_FIELDS:
        if campo == "url":
            continue
        if campo == "codice":
            if "codice" not in bando or not bando["codice"].strip():
                regione = bando.get("regione", "")
                bando["codice"] = genera_codice_bando(regione)
                modificato = True

        if campo == "allegati":
            if campo not in bando:
                bando["allegati"] = []
                modificato = True
        elif campo == "scheda_info":
            if campo not in bando:
                bando["scheda_info"] = {}
                modificato = True
        else:
            if campo not in bando:
                errori.append(f"Manca campo obbligatorio: {campo}")

    #if "data_chiusura" in bando and isinstance(bando["data_chiusura"], str) and bando["data_chiusura"].strip() == "":
        #bando["data_chiusura"] = None
        #modificato = True
    if "data_chiusura" not in bando:
        bando["data_chiusura"] = None
        modificato = True
    else:
        originale = bando["data_chiusura"]
        nuova_data = normalizza_data(originale)

        if nuova_data:
            data_dt = None
            try:
                data_dt = datetime.strptime(nuova_data, "%d-%m-%Y")
            except ValueError:
                try:
                    data_dt = datetime.strptime(nuova_data, "%Y-%m-%d")
                    nuova_data = data_dt.strftime("%d-%m-%Y")  # Converti nel formato corretto
                except ValueError:
                    pass  # gestito sotto

            if data_dt:
                if data_dt >= SOGLIA_DATA and nuova_data != originale:
                    bando["data_chiusura"] = nuova_data
                    modificato = True
                elif data_dt < SOGLIA_DATA:
                    bando.pop("data_chiusura", None)
                    modificato = True
            else:
                errori.append(f"Formato data non valido: {nuova_data}")

        elif isinstance(originale, str) and originale.strip() == "":
            bando["data_chiusura"] = None
            modificato = True

    # Validazione finale
    if "data_chiusura" not in bando:
        errori.append("Manca campo obbligatorio: data_chiusura")

    if "allegati" in bando:
        allegati_validi = []
        for allegato in bando["allegati"]:
            if not isinstance(allegato, dict):
                errori.append("Oggetto allegato non è un dizionario")
                break

            # Mappatura dei campi alternativi
            nome = allegato.get("name") or allegato.get("nome") or allegato.get("titolo")
            link = allegato.get("link") or allegato.get("url")

            # Se mancano i valori, li saltiamo o generiamo errore
            if isinstance(nome, str) and nome.strip() and isinstance(link, str) and link.strip():
                allegati_validi.append({"name": nome.strip(), "link": link.strip()})
            else:
                errori.append(f"Allegato non valido: {allegato}")
                break

        # Solo se tutti sono validi, sovrascrive
        if not errori:
            bando["allegati"] = allegati_validi
    if "scheda_info" in bando and not isinstance(bando["scheda_info"], dict):
        bando["scheda_info"] = {"descrizione": str(bando["scheda_info"])}
        modificato = True
    return modificato, errori, bando

def prepare_text_categoria(titolo, scheda_info):
    if isinstance(scheda_info, dict):
        parti = [str(v) for v in scheda_info.values() if isinstance(v, (str, int, float))]
        scheda_info_str = " ".join(parti)
    else:
        scheda_info_str = str(scheda_info or "")
    return f"{titolo} {scheda_info_str}"

def completa_categoria(bando):
    categoria = bando.get("categoria")
    if not categoria:
        titolo = bando.get("titolo")
        scheda_info = bando.get("scheda_info", {})
        if titolo:
            testo = prepare_text_categoria(titolo, scheda_info)
            pred = pipeline_categoria.predict([testo])[0]
            categoria_predetta = label_encoder_categoria.inverse_transform([pred])[0]
            bando["categoria"] = categoria_predetta
    return bando

def predici_tipo_utente(titolo, scheda_info):
    if not titolo:
        return None
    testo = f"{titolo} - {scheda_info}"
    inputs = tokenizer_tipo_utente(testo, return_tensors="pt", padding=True, truncation=True)
    with torch.no_grad():
        outputs = model_tipo_utente(**inputs)
        pred = torch.argmax(outputs.logits, dim=1).item()
    tipo_utente_predetto = label_encoder_tipo_utente.inverse_transform([pred])[0]
    return tipo_utente_predetto

def normalizza_tipo_utente(tipo_raw):
    if not isinstance(tipo_raw, str):
        return "Generale"

    tipo = tipo_raw.strip().lower()
    if any(separatore in tipo_raw for separatore in ["\n", ",", " e ", ";"]):
        return "Generale"

    if tipo in ["ente", "entee", "enti", "enti e operatori", "enti pubblici"]:
        return "Enti"
    elif tipo in ["impresa", "impresee", "impreese"]:
        return "Imprese"
    elif tipo in ["generali", "generale", "genarele"]:
        return "Generale"
    else:
        return tipo_raw.strip().capitalize()
def completa_tipo_utente(bando):
    if not bando.get("tipo_utente"):
        titolo = bando.get("titolo", "")
        scheda_info = bando.get("scheda_info", {})
        if isinstance(scheda_info, dict):
            scheda_info_str = " ".join(f"{k}: {v}" for k, v in scheda_info.items())
        else:
            scheda_info_str = str(scheda_info)

        tipo_utente_trovato = predici_tipo_utente(titolo, scheda_info_str)
        if tipo_utente_trovato:
            tipo_normalizzato = normalizza_tipo_utente(tipo_utente_trovato)
            bando["tipo_utente"] = tipo_normalizzato
            logging.info(f"[ML] Tipo_utente predetto e normalizzato: '{tipo_normalizzato}' per bando: '{titolo}'")
        else:
            logging.warning(f"[ML] Nessun tipo_utente trovato per bando: '{titolo}'")
    else:
        bando["tipo_utente"] = normalizza_tipo_utente(bando["tipo_utente"])
    return bando



def salva_bando_in_mongo(bando):
    bando.pop("_id", None)
    bandi_collection.insert_one(bando)
    logging.info(f"Bando '{bando.get('codice', '?')}' inserito in MongoDB.")

def processa_file_json(percorso_file):
    logging.info(f"Inizio elaborazione file: {percorso_file}")
    with open(percorso_file, "r", encoding="utf-8") as f:
        dati = json.load(f)

    if isinstance(dati, dict):
        dati = [dati]

    modificati = False
    errori_totali = []
    dati_validi = []

    for i, bando in enumerate(dati):
        bando = completa_tipo_utente(bando)
        bando = completa_categoria(bando)
        modificato, errori, bando_corr = controlla_e_correggi_bando(bando)
        if modificato:
            dati[i] = bando_corr
            modificati = True
        if errori:
            titolo = bando.get("titolo", "<titolo non disponibile>")
            errori_totali.append({"indice": i, "errori": errori, "titolo": titolo})
            logging.error(f"Bando indice {i} (titolo: '{titolo}') ha errori: {errori}")
        else:
            dati_validi.append(bando_corr)

    if modificati:
        backup = percorso_file + ".bak"
        os.rename(percorso_file, backup)
        with open(percorso_file, "w", encoding="utf-8") as f:
            json.dump(dati, f, indent=4, ensure_ascii=False)
        logging.info(f"File corretto e salvato: {percorso_file} (backup in {backup})")

    if errori_totali:
        logging.warning(f"Errori trovati nel file {percorso_file}:")
        for err in errori_totali:
            logging.warning(f"  - Bando indice {err['indice']} (titolo: '{err['titolo']}'): {err['errori']}")
        logging.error("Caricamento interrotto: uno o più bandi non rispettano il modello.")
    else:
        for bando_valido in dati_validi:
            salva_bando_in_mongo(bando_valido)

def processa_cartella(cartella):
    if not os.path.exists(cartella):
        logging.error(f"La cartella '{cartella}' non esiste!")
        return
    for nome_file in os.listdir(cartella):
        if nome_file.endswith(".json"):
            percorso = os.path.join(cartella, nome_file)
            processa_file_json(percorso)
if __name__ == "__main__":
    path = "./bandi.json"  # oppure "./bandi_json" se è una cartella
    if os.path.isfile(path):
        processa_file_json(path)
    elif os.path.isdir(path):
        processa_cartella(path)
    else:
        logging.error(f"Percorso '{path}' non valido.")
