import json
from pymongo import MongoClient
from bson import ObjectId
import datetime
from collections import Counter

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC  # uso SVM lineare

def convert_mongo_types(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    if isinstance(obj, datetime.datetime):
        return obj.isoformat()
    return obj

# Connessione MongoDB
client = MongoClient("mongodb+srv://galbisini:ZnVz5IA9fm3Iic4n@cluster0.nmxvyvu.mongodb.net/Bandi?retryWrites=true&w=majority")
db = client["Bandi"]
collection = db["Lombardia"]

cursor = collection.find({
    "titolo": {"$ne": None},
    "scheda_info": {"$ne": None},
    "categoria": {"$ne": None}
}, {"titolo": 1, "scheda_info": 1, "categoria": 1})

data = []
for doc in cursor:
    clean_doc = {k: convert_mongo_types(v) for k, v in doc.items()}
    data.append(clean_doc)

print(f"Bandi usati per addestramento: {len(data)}")

def prepare_text(entry):
    titolo = entry.get("titolo", "")
    si = entry.get("scheda_info", {})

    if isinstance(si, dict):
        # Prendi tutti i valori stringa/numerici di scheda_info e concatena
        parti = [str(v) for v in si.values() if isinstance(v, (str, int, float))]
        scheda_testo = " ".join(parti)
    else:
        scheda_testo = str(si) if si else ""

    testo = f"{titolo} {scheda_testo}"
    return testo

# Prepara testi e labels
texts = [prepare_text(d) for d in data]
labels = [d.get("categoria", "unknown") for d in data]

# Filtra le classi con almeno 2 esempi
counts = Counter(labels)
filtered_data = []
for d in data:
    cat = d.get("categoria", "unknown")
    if counts[cat] > 1:
        filtered_data.append(d)

texts = [prepare_text(d) for d in filtered_data]
labels = [d.get("categoria", "unknown") for d in filtered_data]

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(labels)

X_train, X_test, y_train, y_test = train_test_split(texts, y, test_size=0.2, random_state=42, stratify=y)

# Pipeline TF-IDF + SVM lineare

pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
    ("clf", LinearSVC(max_iter=1000))
])

pipeline.fit(X_train, y_train)
acc = pipeline.score(X_test, y_test)
print(f"Accuracy: {acc:.2f}")
### oleeee finalmente

# Salva i modelli
import joblib
joblib.dump(pipeline, "modello_tfidf_svm.joblib")
joblib.dump(label_encoder, "modello_label_encoder.joblib")

# Funzione per predire categoria nuovi bandi
def predici_categoria(bandi_json):
    testi = []
    for b in bandi_json:
        testi.append(prepare_text(b))
    y_pred = pipeline.predict(testi)
    return label_encoder.inverse_transform(y_pred)

# Esempio d’uso
bando_nuovo = [{
    "titolo": "ORGANISMO INTERMEDIO - PR FESR 2021-2027. Intervento 1.3.3.3 ...",
    "scheda_info": {
        "Area organizzativa": "DIPARTIMENTO SVILUPPO ECONOMICO",
        "Struttura": "Settore Beni e attività culturali",
        "Procedura": "Bando per la concessione di contributi"
    }
}]

categorie_predette = predici_categoria(bando_nuovo)
print("Categoria predetta:", categorie_predette[0])
