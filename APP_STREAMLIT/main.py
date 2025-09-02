import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import hashlib
import os
from dotenv import load_dotenv

# ========== CARICA VARIABILI D'AMBIENTE ==========
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI") + "Bandi?retryWrites=true&w=majority"
PROJECT_ID = os.getenv("PROJECT_ID")
REGION = os.getenv("REGION_DS")  
MODEL_NAME = os.getenv("MODEL_NAME")

# ========== GEMINI ==========
from google import genai
from google.genai import types

client = genai.Client(
    vertexai=True,
    project=PROJECT_ID,
    location=REGION
)

model = MODEL_NAME

def generate_response(messages):
    response_text = ""
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=messages,
        config=types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=1024,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
            tools=[types.Tool(google_search=types.GoogleSearch())],
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        ),
    ):
        if chunk.candidates and chunk.candidates[0].content and chunk.candidates[0].content.parts:
            response_text += chunk.candidates[0].content.parts[0].text
    return response_text

# ========== CONFIG PAGINA ==========
st.set_page_config(page_title="Bandi Lombardia", layout="wide")

# ========== CONNESSIONE MONGO ==========
client_mongo = MongoClient(MONGO_URI)
db = client_mongo["Bandi"]
bandi_collection = db["Lombardia"]
utenti_collection = db["Utenti"]

# ========== FUNZIONI UTILI ==========
def get_data():
    dati = list(bandi_collection.find())
    df = pd.DataFrame(dati)
    if '_id' in df.columns:
        df['_id'] = df['_id'].astype(str)
    return df

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_credentials(login, password):
    user = utenti_collection.find_one({"email": login}) or utenti_collection.find_one({"username": login})
    if user and user["password"] == hash_password(password):
        return user
    return None

def register_user(username, email, password, profilo):
    if utenti_collection.find_one({"email": email}):
        return False
    user_data = {
        "username": username,
        "email": email,
        "password": hash_password(password),
        "profilo": profilo
    }
    utenti_collection.insert_one(user_data)
    return True

# ========== LOGIN ==========
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.profilo = ""
    st.session_state.bando_selezionato = None
    st.session_state.messages = []

def login_style():
    st.markdown("""
        <style>
        .block-container {
            max-width: 500px;
            margin: auto;
            padding-top: 50px;
        }
        </style>
    """, unsafe_allow_html=True)

if not st.session_state.logged_in:
    login_style()
    st.title("Bandi per Te")
    scelta = st.radio("Hai già un account?", ["Login", "Registrazione"])

    if scelta == "Registrazione":
        username = st.text_input("Nome utente")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        profilo = st.selectbox("Seleziona il tuo profilo", ["Imprese", "Enti", "Cittadini"])
    else:
        login_input = st.text_input("Nome utente o Email")
        password = st.text_input("Password", type="password")

    if st.button("Accedi" if scelta == "Login" else "Registrati"):
        if scelta == "Registrazione":
            if not username or not email or not password:
                st.error("Inserisci nome utente, email e password.")
            else:
                success = register_user(username, email, password, profilo)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.profilo = profilo
                    st.session_state.messages = []
                    st.success("Registrazione completata!")
                    st.rerun()
                else:
                    st.error("Email già registrata.")
        else:
            if not login_input or not password:
                st.error("Inserisci nome utente o email e password.")
            else:
                user = check_credentials(login_input, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.profilo = user["profilo"]
                    st.session_state.messages = []
                    st.success(f"Benvenuto, {user['username']}!")
                    st.rerun()
                else:
                    st.error("Credenziali non valide.")

# ========== AREA LOGGATA ==========
else:
    st.sidebar.success(f"👤 {st.session_state.username} ({st.session_state.profilo})")
    if st.sidebar.button("Esci"):
        st.session_state.logged_in = False
        st.session_state.bando_selezionato = None
        st.session_state.messages = []
        st.rerun()

    # ====== DATI BANDI ======
    df = get_data()
    profilo = st.session_state.profilo

    if st.session_state.bando_selezionato:
        if st.button("⬅️ Torna all'elenco", key="torna"):
            st.session_state.bando_selezionato = None
            st.rerun()

        bando = df[df['_id'] == st.session_state.bando_selezionato].squeeze()
        st.header(f"📌 {bando.get('titolo', 'Titolo non disponibile')}")

        if 'scheda_info' in bando and isinstance(bando['scheda_info'], dict):
            st.subheader("ℹ️ Informazioni sul Bando")
            for chiave, valore in bando['scheda_info'].items():
                st.write(f"**{chiave.capitalize()}**: {valore}")

        if 'allegati' in bando and isinstance(bando['allegati'], list):
            st.subheader("📎 Allegati")
            for allegato in bando['allegati']:
                nome = allegato.get('name', 'Documento')
                link = allegato.get('link', '#')
                st.markdown(f"- 📄 [{nome}]({link})", unsafe_allow_html=True)

    else:
        col1, col2 = st.columns([2, 3])
        with col1:
            st.subheader("🔍 Filtra bandi")
            keyword = st.text_input("Cerca nel titolo")
            categoria_options = ["Tutte"] + sorted(df['categoria'].dropna().unique()) if 'categoria' in df.columns else ["Tutte"]
            categoria_scelta = st.selectbox("📂 Categoria", categoria_options)
            regione_options = ["Tutte"] + sorted(df['regione'].dropna().unique()) if 'regione' in df.columns else ["Tutte"]
            regione_scelta = st.selectbox("🌍 Regione", regione_options)
            scadenza_max = st.date_input("📅 Mostra bandi con scadenza fino a", value=None)

        with col2:
            st.title(f"📄 Elenco Bandi – Profilo: *{profilo}*")
            df_filtrato = df.copy()
            if keyword:
                df_filtrato = df_filtrato[df_filtrato['titolo'].str.contains(keyword, case=False, na=False)]
            if categoria_scelta != "Tutte":
                df_filtrato = df_filtrato[df_filtrato['categoria'] == categoria_scelta]
            if regione_scelta != "Tutte":
                df_filtrato = df_filtrato[df_filtrato['regione'] == regione_scelta]
            if scadenza_max and 'data_chiusura' in df_filtrato.columns:
                df_filtrato['data_chiusura'] = pd.to_datetime(
                    df_filtrato['data_chiusura'], format="%d-%m-%Y", errors='coerce')
                scadenza_max_dt = pd.to_datetime(scadenza_max)
                df_filtrato = df_filtrato[df_filtrato['data_chiusura'] <= scadenza_max_dt]
            if 'tipo_utente' in df_filtrato.columns:
                df_filtrato = df_filtrato[df_filtrato['tipo_utente'].apply(lambda x: ("generale" in str(x).lower() or (profilo.lower() in str(x).lower() if pd.notna(x) else False)))]

            st.write(f"### {len(df_filtrato)} bandi trovati per il profilo **{profilo}**")

            for _, row in df_filtrato.iterrows():
                titolo = row.get('titolo', 'Senza titolo')
                id_str = row['_id']
                if st.button(f"🔗 {titolo}", key=id_str):
                    st.session_state.bando_selezionato = id_str
                    st.rerun()

    # ====== CHATBOT SOTTO TUTTO ======
    st.markdown("---")
    st.subheader("💬 Assistente Virtuale")

    if "messages" not in st.session_state or not st.session_state.messages:
        st.session_state.messages = [
            types.Content(role="model", parts=[types.Part(text="Ciao! Come posso aiutarti ?")])
        ]

    for msg in st.session_state.messages:
        role = "user" if msg.role == "user" else "assistant"
        text = msg.parts[0].text if msg.parts and hasattr(msg.parts[0], 'text') else "[Contenuto non testuale]"
        st.chat_message(role).write(text)

    if prompt := st.chat_input("Fai una domanda sui bandi..."):
        st.chat_message("user").write(prompt)
        user_msg = types.Content(role="user", parts=[types.Part(text=prompt)])
        st.session_state.messages.append(user_msg)

        with st.chat_message("assistant"):
            with st.spinner("Sto pensando..."):
                response = generate_response(st.session_state.messages)
                st.write(response)

        model_msg = types.Content(role="model", parts=[types.Part(text=response)])
        st.session_state.messages.append(model_msg)

