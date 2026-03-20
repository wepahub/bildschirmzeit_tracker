import json
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Bildschirmzeit Tracker", page_icon="📱", layout="centered")

# --- DATENBANK-VERBINDUNG ---
@st.cache_resource
def get_google_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # NEU: Das Programm liest den JSON-Text jetzt direkt aus dem Tresor
    creds_dict = json.loads(st.secrets["google_json"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("Bildschirmzeit_Tracker")

# --- KLASSEN & PINS LADEN ---
@st.cache_data(ttl=60) 
def lade_klassen_daten():
    try:
        sheet = get_google_sheet()
        worksheet = sheet.worksheet("Klassen")
        records = worksheet.get_all_records()
        return {str(row["Klassenname"]): str(row["PIN"]) for row in records}
    except Exception as e:
        st.error(f"Fehler beim Laden der Klassen: {e}")
        return {}

# --- LOGIN-BEREICH ---
def login():
    st.title("📱 Bildschirmzeit Tracker")
    st.write("Bitte wähle die Klasse und gib den PIN ein.")
    
    klassen_daten = lade_klassen_daten()
    
    if not klassen_daten:
        st.info("Verbindung zur Datenbank wird aufgebaut...")
        return

    klasse = st.selectbox("Klasse auswählen", list(klassen_daten.keys()))
    pin_eingabe = st.text_input("Klassen-PIN", type="password")
    
    if st.button("Einloggen"):
        if pin_eingabe == klassen_daten.get(klasse):
            st.session_state["logged_in"] = True
            st.session_state["klasse"] = klasse
            st.rerun()
        else:
            st.error("Falscher PIN! Bitte versuche es noch einmal.")

# --- HAUPT-APP (Nach dem Login) ---
def main_app():
    klasse = st.session_state["klasse"]
    st.title(f"Dashboard - Klasse {klasse}")
    
    tab1, tab2 = st.tabs(["⏱️ Zeit eintragen", "🏆 Ranking ansehen"])
    
    with tab1:
        st.subheader("Bildschirmzeit eintragen")
        st.info("Das Formular für die Schüler:innen bauen wir im nächsten Schritt ein!")
        
    with tab2:
        st.subheader("Aktuelles Ranking")
        st.info("Hier erscheint bald die Auswertung für die Klasse.")
        
    if st.button("Abmelden"):
        st.session_state["logged_in"] = False
        st.session_state["klasse"] = ""
        st.rerun()

# --- STEUERUNG ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    main_app()
# --- HAUPT-APP (Nach dem Login) ---
def main_app():
    klasse = st.session_state["klasse"]
    st.title(f"Dashboard - Klasse {klasse}")
    
    # Navigation über Tabs
    tab1, tab2 = st.tabs(["⏱️ Zeit eintragen", "🏆 Ranking ansehen"])
    
    with tab1:
        st.subheader("Deine Bildschirmzeit von heute")
        # Hier kommt im nächsten Schritt das Eingabeformular mit Kalender hin
        st.info("Das Eingabeformular wird im nächsten Schritt programmiert.")
        
    with tab2:
        st.subheader("Aktuelles Ranking")
        # Hier kommt später die Auswertung hin
        st.info("Hier erscheint bald die Auswertung für alle Schüler:innen der Klasse.")
        
    if st.button("Abmelden"):
        st.session_state["logged_in"] = False
        st.session_state["klasse"] = ""
        st.rerun()

# --- STEUERUNG ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login()
else:
    main_app()
