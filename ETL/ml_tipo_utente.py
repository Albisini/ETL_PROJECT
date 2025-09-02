from pymongo import MongoClient
import pandas as pd
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from sklearn.preprocessing import LabelEncoder
import torch
import joblib

# Connessione a MongoDB
client = MongoClient("mongo_url")
db = client["Bandi"]
collection = db["Lombardia"]

# Estrae dati: titolo + scheda_info + tipo_utente
bandi = []
for doc in collection.find({"tipo_utente": {"$exists": True}}):  # solo bandi etichettati
    titolo = doc.get("titolo", "")
    raw_info = doc.get("scheda_info", {})
    if isinstance(raw_info, dict):
        scheda_info = " ".join(f"{k}: {v}" for k, v in raw_info.items())
    else:
        scheda_info = str(raw_info)
    testo = f"{titolo} - {scheda_info}".strip()
    tipo_utente = doc["tipo_utente"]
    bandi.append({"text": testo, "label": tipo_utente})  # CAMBIO: label è tipo_utente

df = pd.DataFrame(bandi)

#Encoding delle etichette
le = LabelEncoder()
df["label"] = le.fit_transform(df["label"])

# Creazione dataset HuggingFace
dataset = Dataset.from_pandas(df)

# tokenizzazione
model_name = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)

def tokenize(example):
    return tokenizer(example["text"], padding="max_length", truncation=True)

dataset = dataset.map(tokenize)

#Split train/test
dataset = dataset.train_test_split(test_size=0.2)
train_ds = dataset["train"]
test_ds = dataset["test"]

# Caricamento modello per classificazione
model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=len(le.classes_))

# Addestramento
training_args = TrainingArguments(
    output_dir="./modello_tipo_utente",
    evaluation_strategy="epoch",
    per_device_train_batch_size=8,
    per_device_eval_batch_size=8,
    num_train_epochs=4,
    logging_dir="./logs",
    logging_steps=10,
    save_strategy="epoch"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=test_ds
)

trainer.train()

#Salva modello, tokenizer e label encoder
trainer.save_model("modello_tipo_utente")
tokenizer.save_pretrained("modello_tipo_utente")
joblib.dump(le, "label_encoder_tipo_utente.joblib")

print("Modello per tipo_utente, tokenizer e label encoder salvati con successo!")
