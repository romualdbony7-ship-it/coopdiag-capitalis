import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import sqlite3
from datetime import datetime
import os

# --- CONFIGURATION AVEC ICÔNE POUR ANDROID ---
# Assure-toi que "logo.png" est bien le nom exact sur ton GitHub
FICHIER_LOGO = "logo.png" 

st.set_page_config(
    page_title="CoopDiag Capitalis",
    page_icon=FICHIER_LOGO, 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# Couleurs Capitalis Global
VERT_LOGO = "#2E7D32"  
ROUGE_CORAIL = "#FF7F50"

# --- LOGIQUE BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('coop_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS diagnostics
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, nom_coop TEXT, 
                  score REAL, volume TEXT, vehicules TEXT, campagnes TEXT, certif TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- BARRE LATÉRALE (LOGO & ÉVALUATION) ---
with st.sidebar:
    # Recherche du logo (ta version robuste)
    logo_trouve = False
    for fichier in os.listdir('.'):
        if fichier.lower().startswith('logo') and fichier.lower().endswith(('.png', '.jpg', '.jpeg', '.ico')):
            st.image(fichier, use_container_width=True)
            logo_trouve = True
            break
    
    st.header("📋 Diagnostic")
    nom_coop = st.text_input("Nom de la coopérative", "Ma Coop")
    
    # Utilisation d'expanders pour ne pas surcharger l'écran mobile
    with st.expander("⚖️ Gouvernance", expanded=False):
        q1 = st.checkbox("OHADA conforme?")
        q2 = st.checkbox("AG régulières?")
        q3 = st.checkbox("Registre à jour?")
        nb_campagnes = st.select_slider("Campagnes :", options=["0", "1", "2+"])
        camp_pt = 1 if nb_campagnes == "2+" else (0.5 if nb_campagnes == "1" else 0)
        gov_score = ((sum([q1, q2, q3]) + camp_pt) / 4) * 100

    with st.expander("💰 Finance", expanded=False):
        f1 = st.checkbox("Excédent net?")
        f2 = st.checkbox("Trésorerie saine?")
        fin_score = (sum([f1, f2]) / 2) * 100

    with st.expander("🌍 Certif. & Impact", expanded=False):
        certif_status = st.radio("Certification :", ["Non", "En cours", "Certifié"])
        cert_pt = 1 if certif_status == "Certifié" else (0.5 if certif_status == "En cours" else 0)
        imp_score = cert_pt * 100

    if st.button("💾 Sauvegarder", use_container_width=True):
        score_final = (gov_score * 0.4) + (fin_score * 0.3) + (imp_score * 0.3)
        conn = sqlite3.connect('coop_data.db')
        c = conn.cursor()
        c.execute("INSERT INTO diagnostics (date, nom_coop, score, campagnes, certif) VALUES (?, ?, ?, ?, ?)",
                  (datetime.now().strftime("%d/%m/%Y"), nom_coop, round(score_final, 2), nb_campagnes, certif_status))
        conn.commit()
        conn.close()
        st.success("Enregistré !")

# --- AFFICHAGE PRINCIPAL (OPTIMISÉ MOBILE) ---
st.title("📊 CoopDiag")
st.caption("Capitalis Global - Expertise Coopérative")

score_global = (gov_score * 0.4) + (fin_score * 0.3) + (imp_score * 0.3)

# Affichage du score en gros (très lisible sur smartphone)
color = VERT_LOGO if score_global >= 75 else (ROUGE_CORAIL if score_global < 50 else "#FFA500")
st.markdown(f"""
    <div style="background-color:{color}; padding:15px; border-radius:15px; text-align:center;">
        <h2 style="color:white; margin:0;">Score : {score_global:.1f}%</h2>
    </div>
    """, unsafe_allow_html=True)

# Graphique Radar : On réduit la taille pour le mobile
df_radar = pd.DataFrame({'Module': ['Gouv.', 'Fin.', 'Imp.'], 'Score': [gov_score, fin_score, imp_score]})
fig = px.line_polar(df_radar, r='Score', theta='Module', line_close=True, range_r=[0,100], height=300)
fig.update_traces(fill='toself', line_color=VERT_LOGO)
fig.update_layout(margin=dict(l=20, r=20, t=20, b=20)) # Réduit les marges blanches
st.plotly_chart(fig, use_container_width=True)

# Alertes d'éligibilité
if nb_campagnes != "2+":
    st.error("🚫 **INÉLIGIBLE AU CRÉDIT**")
else:
    st.success("✅ **ÉLIGIBLE AU CRÉDIT**")

# Bouton de téléchargement large pour le pouce
def generate_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Rapport : {nom_coop}", ln=True)
    pdf.cell(0, 10, f"Score : {score_global:.1f}%", ln=True)
    return pdf.output(dest='S').encode('latin-1')

st.download_button("📥 Télécharger le PDF", data=generate_pdf(), file_name="Rapport.pdf", use_container_width=True)