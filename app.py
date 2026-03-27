import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import sqlite3
from datetime import datetime
import os

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="CoopDiag - Capitalis Global", layout="wide")

# Couleurs de la charte Capitalis Global
VERT_LOGO = "#2E7D32"  
BLEU_TEXTE = "#011627" 
ROUGE_CORAIL = "#FF7F50"

# --- GESTION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('coop_data.db')
    c = conn.cursor()
    # Mise à jour de la table pour inclure les nouveaux critères
    c.execute('''CREATE TABLE IF NOT EXISTS diagnostics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, 
                  nom_coop TEXT, 
                  score REAL, 
                  volume TEXT, 
                  vehicules TEXT, 
                  campagnes TEXT, 
                  certif TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- BARRE LATÉRALE AVEC LOGO (Version Robuste) ---
with st.sidebar:
    # On cherche un fichier qui commence par 'logo' peu importe l'extension
    logo_trouve = False
    for fichier in os.listdir('.'):
        # On cherche un fichier nommé 'logo' (sans casse) avec extension image
        if fichier.lower().startswith('logo') and fichier.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
            try:
                st.image(fichier, use_container_width=True)
                logo_trouve = True
                break # On arrête dès qu'on en trouve un
            except Exception:
                continue # Si erreur, on essaie le suivant

    if not logo_trouve:
        st.warning("💡 Pour afficher le logo, place un fichier image nommé 'logo' (png ou jpg) dans le dossier du projet.")

    st.header("📋 Évaluation")
    nom_coop = st.text_input("Nom de la coopérative", "Ma Coopérative")
    
    st.divider()

    # MODULE 1 : GOUVERNANCE (30%)
    with st.expander("⚖️ Gouvernance", expanded=True):
        q1 = st.checkbox("Statuts conformes à l'OHADA ?")
        q2 = st.checkbox("AG tenues régulièrement ?")
        q3 = st.checkbox("Registre des membres à jour ?")
        q4 = st.checkbox("Traçabilité des volumes établie ?")
        
        nb_campagnes = st.select_slider(
            "Nombre de campagnes réalisées :",
            options=["0", "1", "2+"]
        )
        
        camp_pt = 1 if nb_campagnes == "2+" else (0.5 if nb_campagnes == "1" else 0)
        gov_score = ((sum([q1, q2, q3, q4]) + camp_pt) / 5) * 100

    # MODULE 2 : FINANCE (30%)
    with st.expander("💰 Finance", expanded=False):
        f1 = st.checkbox("Excédent net dégagé ?")
        f2 = st.checkbox("Trésorerie saine ?")
        f3 = st.checkbox("Commissaire aux comptes ?")
        fin_score = (sum([f1, f2, f3]) / 3) * 100

    # MODULE 3 : OPÉRATIONS (20%)
    with st.expander("⚙️ Performance Op.", expanded=False):
        volume_cat = st.radio("Volume annuel :", ["Moins de 200 tonnes", "200 tonnes ou plus"])
        nb_vehicules = st.select_slider("Véhicules de collecte :", options=["0", "1", "2", "3", "4", "5+"])
        o1 = st.checkbox("Taux de perte < 5% ?")
        
        vol_pt = 1 if volume_cat == "200 tonnes ou plus" else 0
        veh_pt = 1 if nb_vehicules != "0" else 0
        ops_score = ((sum([o1]) + vol_pt + veh_pt) / 3) * 100

    # MODULE 4 : IMPACT & DURABILITÉ (20%)
    with st.expander("🌍 Impact & Durabilité", expanded=True):
        i1 = st.checkbox("Ristournes versées ?")
        i2 = st.checkbox("+30% Femmes/Jeunes au CA ?")
        certif_status = st.radio("Certification :", ["Non", "En cours", "Certifié"])
        
        cert_pt = 1 if certif_status == "Certifié" else (0.5 if certif_status == "En cours" else 0)
        imp_score = ((sum([i1, i2]) + cert_pt) / 3) * 100

    st.divider()
    if st.button("💾 Sauvegarder le Diagnostic"):
        score_final = (gov_score * 0.3) + (fin_score * 0.3) + (ops_score * 0.2) + (imp_score * 0.2)
        conn = sqlite3.connect('coop_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO diagnostics (date, nom_coop, score, volume, vehicules, campagnes, certif) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (datetime.now().strftime("%d/%m/%Y %H:%M"), nom_coop, round(score_final, 2), volume_cat, nb_vehicules, nb_campagnes, certif_status))
        conn.commit()
        conn.close()
        st.success("Données archivées.")

# --- AFFICHAGE DES RÉSULTATS ---
st.title("📊 CoopDiag par Capitalis Global")
score_global = (gov_score * 0.3) + (fin_score * 0.3) + (ops_score * 0.2) + (imp_score * 0.2)

col1, col2 = st.columns([1, 1])

with col1:
    color = VERT_LOGO if score_global >= 75 else (ROUGE_CORAIL if score_global < 50 else "#FFA500")
    st.markdown(f'<div style="background-color:{color}; padding:20px; border-radius:10px; text-align:center;"><h1 style="color:white; margin:0;">{score_global:.1f}%</h1></div>', unsafe_allow_html=True)
    
    df_radar = pd.DataFrame({'Module': ['Gouv.', 'Fin.', 'Ops', 'Imp.'], 'Score': [gov_score, fin_score, ops_score, imp_score]})
    fig = px.line_polar(df_radar, r='Score', theta='Module', line_close=True, range_r=[0,100])
    fig.update_traces(fill='toself', line_color=VERT_LOGO)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Analyse de Conformité")
    if nb_campagnes != "2+":
        st.error(f"🚫 **Éligibilité Crédit : REFUSÉE.** (Campagnes : {nb_campagnes})")
    else:
        st.success("✅ **Éligibilité Crédit : VALIDÉE.** (Expérience suffisante)")
        
    if certif_status == "Non":
        st.warning("⚠️ **Certification :** Préparation à la certification urgente !")
    
    st.divider()
    st.subheader("Historique récent")
    conn = sqlite3.connect('coop_data.db')
    try:
        df_h = pd.read_sql_query("SELECT nom_coop, score, campagnes, certif FROM diagnostics ORDER BY id DESC LIMIT 5", conn)
        st.table(df_h)
    except:
        st.write("Aucune donnée.")
    conn.close()

# --- GÉNÉRATION DU RAPPORT PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists('logo.png'):
            self.image('logo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.ln(20)

def generate_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"RAPPORT DE DIAGNOSTIC : {nom_coop}", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Score Global : {score_global:.1f}%", ln=True)
    pdf.cell(0, 10, f"Campagnes : {nb_campagnes} | Certification : {certif_status}", ln=True)
    if nb_campagnes != "2+":
        pdf.set_text_color(200, 0, 0)
        pdf.cell(0, 10, "STATUT : INELIGIBLE AU FINANCEMENT", ln=True)
    return pdf.output(dest='S').encode('latin-1')

st.sidebar.download_button("📥 Télécharger le Rapport PDF", data=generate_pdf(), file_name=f"Diag_{nom_coop}.pdf")