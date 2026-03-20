import json
import pandas as pd
import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import date

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="Bildschirmzeit Tracker", page_icon="📱", layout="centered")

# --- DATENBANK-VERBINDUNG ---
@st.cache_resource
def get_google_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = json.loads(st.secrets["google_json"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("Bildschirmzeit_Tracker")

# --- DATEN LADEN & SPEICHERN ---
@st.cache_data(ttl=60) 
def lade_klassen_daten():
    try:
        sheet = get_google_sheet()
        worksheet = sheet.worksheet("Klassen")
        return {str(row["Klassenname"]): str(row["PIN"]) for row in worksheet.get_all_records()}
    except Exception as e:
        st.error(f"Hier ist der Fehler: {e}") # <-- Das zeigt uns jetzt den Fehler in roter Schrift an!
        return {}

@st.cache_data(ttl=60)
def lade_schueler(klasse):
    try:
        sheet = get_google_sheet()
        worksheet = sheet.worksheet("Personen")
        records = worksheet.get_all_records()
        return [str(row["Name"]) for row in records if str(row["Klasse"]) == klasse]
    except:
        return []

def speichere_schueler(name, klasse):
    sheet = get_google_sheet()
    worksheet = sheet.worksheet("Personen")
    worksheet.append_row([name, klasse])
    st.cache_data.clear()

def speichere_zeit(datum, name, klasse, minuten):
    sheet = get_google_sheet()
    worksheet = sheet.worksheet("Tracking")
    worksheet.append_row([str(datum), name, klasse, minuten])
    st.cache_data.clear()

@st.cache_data(ttl=60)
def lade_tracking_df(klasse):
    try:
        sheet = get_google_sheet()
        worksheet = sheet.worksheet("Tracking")
        records = worksheet.get_all_records()
        if not records:
            return pd.DataFrame()
        
        df = pd.DataFrame(records)
        df["Klasse"] = df["Klasse"].astype(str)
        df = df[df["Klasse"] == klasse]
        
        if not df.empty:
            df["Minuten"] = pd.to_numeric(df["Minuten"], errors='coerce').fillna(0)
            df["Datum"] = pd.to_datetime(df["Datum"], errors='coerce').dt.date
        return df
    except:
        return pd.DataFrame()

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

# --- HAUPT-APP ---
def main_app():
    klasse = st.session_state["klasse"]
    st.title(f"Dashboard - Klasse {klasse}")
    
    tab1, tab2, tab3 = st.tabs(["⏱️ Zeit eintragen", "📊 Auswertung & Graphen", "⚙️ Verwaltung"])
    
    with tab1:
        st.subheader("Bildschirmzeit eintragen")
        schueler_liste = lade_schueler(klasse)
        
        if not schueler_liste:
            st.warning("Es sind noch keine Namen hinterlegt. Gehe in den Reiter '⚙️ Verwaltung', um Schüler:innen hinzuzufügen.")
        else:
            with st.form("eingabe_form"):
                auswahl_datum = st.date_input("Datum", date.today())
                auswahl_name = st.selectbox("Wer bist du?", schueler_liste)
                eingabe_minuten = st.number_input("Bildschirmzeit (in Minuten)", min_value=0, step=1)
                
                if st.form_submit_button("Speichern"):
                    speichere_zeit(auswahl_datum, auswahl_name, klasse, eingabe_minuten)
                    st.success(f"Gespeichert: {eingabe_minuten} Minuten für {auswahl_name} am {auswahl_datum}.")
        
    with tab2:
        st.subheader("Auswertung der Klasse")
        df = lade_tracking_df(klasse)
        
        if df.empty:
            st.info("Es wurden noch keine Zeiten für diese Klasse eingetragen.")
        else:
            gesamt_minuten = df["Minuten"].sum()
            gesamt_stunden = round(gesamt_minuten / 60, 1)
            st.metric("Gesamte Bildschirmzeit der Klasse", f"{gesamt_stunden} Stunden")
            
            st.markdown("#### Verlauf der gesamten Klasse")
            df_klasse_tag = df.groupby("Datum")["Minuten"].sum().reset_index()
            df_klasse_tag.set_index("Datum", inplace=True)
            st.line_chart(df_klasse_tag)
            
            st.markdown("#### Verlauf pro Person")
            schueler_auswahl = st.selectbox("Person auswählen", df["Name"].unique())
            df_person = df[df["Name"] == schueler_auswahl]
            df_person_tag = df_person.groupby("Datum")["Minuten"].sum().reset_index()
            df_person_tag.set_index("Datum", inplace=True)
            st.bar_chart(df_person_tag)
            
            st.markdown("#### Gesamtübersicht")
            df_ranking = df.groupby("Name")["Minuten"].sum().reset_index()
            df_ranking["Stunden"] = round(df_ranking["Minuten"] / 60, 1)
            df_ranking = df_ranking.sort_values(by="Minuten")
            st.dataframe(df_ranking[["Name", "Stunden", "Minuten"]], hide_index=True)

    with tab3:
        st.subheader("Lehrkräfte-Bereich: Schüler:innen hinzufügen")
        st.write("Hier können neue Namen direkt in die Datenbank eingetragen werden.")
        
        with st.form("neuer_schueler_form", clear_on_submit=True):
            neuer_name = st.text_input("Name der Person")
            if st.form_submit_button("Hinzufügen"):
                if neuer_name.strip() == "":
                    st.error("Bitte einen Namen eingeben.")
                else:
                    speichere_schueler(neuer_name.strip(), klasse)
                    st.success(f"{neuer_name} wurde zur Klasse {klasse} hinzugefügt!")
                    
    st.divider()
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
