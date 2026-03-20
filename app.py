import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Bildschirmzeit Tracker", page_icon="📱", layout="centered")

# --- DATENBANK-VERBINDUNG ---
# (Die Zugangsdaten holen wir uns sicher aus den Streamlit Secrets, die wir gleich anlegen)
def get_google_sheet():
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    client = gspread.authorize(creds)
    # Trage hier den genauen Namen deiner Google Tabelle ein:
    return client.open("Bildschirmzeit_Tracker")

# --- LOGIN-SYSTEM ---
def login():
    st.title("📱 Bildschirmzeit Tracker")
    st.write("Bitte wähle deine Klasse und gib den PIN ein.")
    
    # In einer finalen Version laden wir die Klassen direkt aus Google Sheets.
    # Für den ersten Test tragen wir sie hier kurz ein:
    klasse = st.selectbox("Klasse auswählen", ["1A", "3B", "5C"])
    pin_eingabe = st.text_input("Klassen-PIN", type="password")
    
    if st.button("Einloggen"):
        # Test-PINs (werden später mit der Google Tabelle abgeglichen)
        test_pins = {"1A": "1234", "3B": "4812", "5C": "0000"}
        
        if pin_eingabe == test_pins.get(klasse):
            st.session_state["logged_in"] = True
            st.session_state["klasse"] = klasse
            st.rerun()
        else:
            st.error("Falscher PIN! Bitte versuche es noch einmal.")

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
