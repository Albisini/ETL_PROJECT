from pymongo import MongoClient
import pandas as pd
from sqlalchemy import create_engine, text

pd.set_option('display.max_columns', None)

# Connessione a MongoDB
client = MongoClient('mongo_url')
db = client['Bandi']
collection = db['Lombardia']

print("Collezioni presenti nel DB 'Bandi':")
print(db.list_collection_names())

# Estrazione dati da MongoDB
dati = list(collection.find())
df = pd.DataFrame(dati)

# Rimozione spazi inutili da stringhe
for col in df.columns:
    if df[col].dtype == 'object':
        df[col] = df[col].astype(str).str.strip()
# Formattazione data_chiusura
if "data_chiusura" in df.columns:
    df["data_chiusura"] = pd.to_datetime(df["data_chiusura"], errors='coerce').dt.strftime('%d/%m/%Y')

df["paese"] = "Italia"
# Selezione colonne di interesse
df = df[[
    "codice",  "categoria","titolo", "stato", "tipo_utente", "data_chiusura", "regione", "paese"
]]
df = df.drop_duplicates()
print("Anteprima dati:")
print(df.head())

# Salvataggio CSV
df.to_csv("bandi.csv", index=False, encoding='utf-8')
print("CSV salvato come 'bandi_lombardia.csv'")

# Connessione al DB SQLite tramite SQLAlchemy
engine = create_engine('sqlite:///bandi_lombardia.db', echo=False)

# Salvataggio dati puliti in SQLite (tabella bandi)
df.to_sql("bandi", con=engine, if_exists='replace', index=False)
print("Dati puliti salvati nel database SQLite 'bandi_lombardia.db' nella tabella 'bandi'.")

with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(DISTINCT codice) FROM bandi;"))
    count_distinct_codici = result.scalar()

print(f"\nNumero totale di codici distinti: {count_distinct_codici}")
# Esecuzione query per categorie distinte
with engine.connect() as conn:
    result = conn.execute(text("SELECT DISTINCT categoria FROM bandi ORDER BY categoria;"))
    categorie_distinte = [row[0] for row in result]

print("\nCategorie distinte pulite:")
for categoria in categorie_distinte:
    print("-", categoria)

