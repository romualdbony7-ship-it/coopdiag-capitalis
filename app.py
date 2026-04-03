import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import gspread
from datetime import datetime

# --- CONFIGURATION ET STYLE ---
st.set_page_config(page_title="Capitalis - Diagnostic Expert", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- FONCTIONS TECHNIQUES ---
def sauvegarder_dans_sheets(donnees):
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open("Diagnostics_Coop").sheet1
        sh.append_row(donnees)
        return True
    except Exception as e:
        if "200" not in str(e):
            st.error(f"Erreur Sheets : {e}")
            return False
        return True

# --- INTERFACE UTILISATEUR ---
st.title("🛡️ Capitalis : Diagnostic Coopératif 360°")

# Initialisation des alertes et scores
alertes = []
points_faibles = []
points_forts = []
besoins = []

# --- ONGLET 1 : IDENTIFICATION ---
with st.expander("🏢 Identification de la Coopérative", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        nom_coop = st.text_input("Nom de la Coopérative")
        pca_nom = st.text_input("Nom du PCA")
        pca_contact = st.text_input("Contact PCA")
        email_coop = st.text_input("Email de la Coopérative")
    with col2:
        siege = st.text_input("Siège Social")
        annee_crea = st.number_input("Année de création", min_value=1960, max_value=2026, value=2020)
        nb_membres = st.number_input("Nombre de membres", min_value=0)
        filiere = st.multiselect("Filières", ["Cacao", "Hévéa", "Anacarde", "Palmier à huile", "Maïs", "Vivrier", "Aquaculture", "Manioc", "Riz", "Transformation"])

    # Logique Maturité
    if any(f in ["Cacao", "Hévéa", "Anacarde"] for f in filiere):
        campagnes = st.number_input("Nombre de campagnes réalisées", min_value=0)
        if campagnes < 2:
            alertes.append("⚠️ Coop immature (Moins de 2 campagnes)")
        else:
            points_forts.append("✅ Coop mature")

    clients = st.text_area("Nom des clients principaux")
    prix_mat = st.number_input("Prix matière 1ère campagne (moyenne)", min_value=0)

# --- MODULES DE DIAGNOSTIC ---
tabs = st.tabs(["⚖️ Gouv", "🌿 Dura", "🚜 Ops", "💰 Finance", "🔍 Traça", "📊 SYNTHÈSE"])

with tabs[0]: # Gouvernance
    st.subheader("Gouvernance & RH")
    docs = st.checkbox("Présence docs légaux (RCCM, DEF, Pouvoirs)?")
    dg = st.checkbox("Présence d'un DG qualifié?")
    nb_emp = st.number_input("Nombre d'employés", min_value=0)
    nb_cnps = st.number_input("Employés déclarés CNPS", min_value=0)
    
    if not docs: alertes.append("❌ Absence de documents légaux")
    if nb_emp < 3: points_faibles.append("Effectif trop réduit (< 3 pers)")
    if nb_cnps < 1: points_faibles.append("Risque social : Aucun employé déclaré CNPS")

with tabs[1]: # Durabilité
    st.subheader("Certifications")
    certifie = st.radio("Coopérative certifiée ?", ["Oui", "Non", "En cours"])
    if certifie == "Non":
        alertes.append("🚫 Pas éligible au crédit (Non certifiée)")
    
    types_cert = st.multiselect("Type de Certificat", ["RA", "FT", "PURATOS", "Cocoa-life", "MONDELEZ", "Autre"])
    validite = st.date_input("Date de validité du certificat")
    if validite <= datetime.now().date():
        alertes.append("⏰ Certificat inactif ou expiré")

with tabs[2]: # Opérations
    st.subheader("Performance Opérationnelle")
    vol_n1 = st.number_input("Volume N-1 (Tonnes)", min_value=0.0)
    vol_n2 = st.number_input("Volume N-2 (Tonnes)", min_value=0.0)
    vol_moyen = (vol_n1 + vol_n2) / 2
    
    if vol_moyen < 200:
        alertes.append("📉 Volume trop faible pour un crédit (< 200t)")
    
    flotte = st.radio("Flotte de véhicules ?", ["Oui", "Non"])
    nb_vehicules = st.number_input("Nombre de véhicules", min_value=0)
    if flotte == "Non": besoins.append("Besoin urgent de véhicules")
    if vol_moyen > 500 and nb_vehicules < 2: alertes.append("🚗 Sous-équipement logistique")

with tabs[3]: # Finance
    st.subheader("Bilan et Ratios")
    col_a, col_p = st.columns(2)
    with col_a:
        st.write("**ACTIF**")
        immobs = st.number_input("Matériel/Local", min_value=0)
        stock = st.number_input("Valeur Stock", min_value=0)
        banque = st.number_input("Caisse/Banque", min_value=0)
        total_actif = immobs + stock + banque
        st.metric("Total Actif", f"{total_actif:,} F")
    
    with col_p:
        st.write("**PASSIF**")
        dettes = st.number_input("Total Dettes financières", min_value=0)
        besoin_credit = st.number_input("Montant Besoin de crédit souhaité", min_value=0)
        # Calcul automatique fonds propres pour équilibrer
        fonds_propres = total_actif - dettes
        st.metric("Fonds Propres (Auto)", f"{fonds_propres:,} F")

    # Ratio d'endettement
    ratio = ((dettes + besoin_credit) / (total_actif + besoin_credit)) * 100 if total_actif > 0 else 0
    if ratio >= 70:
        alertes.append(f"🚩 Surendettement (Ratio: {ratio:.1f}%)")
    else:
        points_forts.append(f"💰 Bon ratio d'endettement ({ratio:.1f}%)")

    # Alerte bénéfice
    ca_estime = vol_moyen * 1000 * prix_mat
    marge_nette = st.number_input("Marge nette totale", min_value=0)
    if ca_estime > 0 and (marge_nette / ca_estime) < 0.03:
        alertes.append("💸 Rentabilité faible (< 3% du CA)")

with tabs[4]: # Traçabilité
    st.subheader("Traçabilité interne")
    traca_v = st.checkbox("Traçabilité des volumes vendu?")
    traca_d = st.checkbox("Bordereaux/Reçus disponibles?")
    if not traca_v or not traca_d:
        alertes.append("🔍 Besoin de traçabilité interne")

# --- ONGLET SYNTHÈSE ET SCORE ---
with tabs[5]:
    st.header("📊 Tableau de Bord de Synthèse")
    
    # Calcul Score (Simplifié pour l'exemple)
    score = 100 - (len(alertes) * 10)
    score = max(0, min(score, 100))
    
    st.metric("Score Global de Maturité", f"{score}%")
    
    c1, c2 = st.columns(2)
    with c1:
        st.error("🚨 Alertes & Points Faibles")
        for a in alertes + points_faibles: st.write(a)
    with c2:
        st.success("🌟 Points Forts")
        for p in points_forts: st.write(p)
        st.info("🛠️ Besoins")
        for b in besoins: st.write(b)

    # Graphique de performance
    fig = px.bar(x=["Gouvernance", "Durabilité", "Opérations", "Finance", "Traçabilité"], 
                 y=[80 if docs else 30, 90 if certifie=="Oui" else 20, 70 if vol_moyen>200 else 40, 100-ratio, 85 if traca_v else 10],
                 title="Performance par Module (%)", range_y=[0, 100])
    st.plotly_chart(fig, use_container_width=True)

    # --- SAUVEGARDE ET PDF ---
    if st.button("💾 Sauvegarder le Diagnostic"):
        data = [str(datetime.now()), nom_coop, score, str(alertes), str(besoins)]
        if sauvegarder_dans_sheets(data):
            st.success("Données synchronisées avec Google Sheets !")

    st.download_button("📥 Télécharger le Rapport PDF", data="Contenu PDF", file_name=f"Rapport_{nom_coop}.pdf")