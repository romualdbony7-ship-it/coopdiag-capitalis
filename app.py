import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from datetime import datetime
import os
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(
    page_title="CoopDiag Pro - Capitalis Global",
    page_icon="📊",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- STYLE CSS PERSONNALISÉ POUR LES ALERTES ---
st.markdown("""
    <style>
    .reportview-container .main .block-container{ max-width: 900px; }
    .stAlert { margin-top: 10px; margin-bottom: 10px; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- VARIABLES GLOBALES & COULEURS ---
VERT_CAPITALIS = "#2E7D32"
ROUGE_ALERTE = "#D32F2F"
ORANGE_WARNING = "#F57C00"
FICHIER_LOGO = "logo.png"

# --- FONCTION UTILES ---
def charger_logo():
    if os.path.exists(FICHIER_LOGO):
        return FICHIER_LOGO
    return None

def calculer_score_module(points_obtenus, points_maximum):
    if points_maximum == 0: return 0
    return (points_obtenus / points_maximum) * 100

# =========================================================
# 1. IDENTIFICATION DE LA COOPÉRATIVE (SIDEBAR OPTIMISÉE MOBILE)
# =========================================================
with st.sidebar:
    logo_path = charger_logo()
    if logo_path:
        st.image(logo_path, use_container_width=True)
    st.header("📝 Nouvelle Audit")
    
    with st.expander("👤 Contacts & Siège", expanded=True):
        nom_coop = st.text_input("Nom de la coopérative", "Ma Coop")
        pca_nom = st.text_input("Nom du PCA")
        pca_contact = st.text_input("Contact PCA")
        email_coop = st.text_input("Email Coopérative")
        siege = st.text_input("Siège social")
        annee_crea = st.number_input("Année de création", min_value=1960, max_value=2026, value=2020)
        nb_membres = st.number_input("Nombre de membres", min_value=1)

    with st.expander("🌾 Filière & Campagnes", expanded=False):
        filieres_dispo = ["Cacao", "Hévéa", "Anacarde", "Palmiers à huile", "Maïs", "Vivrier", "Aquaculture"]
        filieres = st.multiselect("Filières concernées", filieres_dispo, default=["Cacao"])
        
        # Logique Maturité Filière Sensible
        filieres_sensibles = ["Cacao", "Hévéa", "Anacarde"]
        is_filiere_sensible = any(f in filieres_sensibles for f in filieres)
        maturite_status = "N/A"
        nb_campagnes = 0
        
        if is_filiere_sensible:
            nb_campagnes = st.number_input("Nombre de campagnes réalisées", min_value=0, step=1)
            if nb_campagnes < 2:
                st.error("🚨 Alerte : Coopérative immature")
                maturite_status = "Immature"
            else:
                st.success("✅ Coopérative mature")
                maturite_status = "Mature"

    with st.expander("🤝 Clients & Prix", expanded=False):
        clients = st.text_area("Nom des clients (un par ligne)")
        prix_campagne = st.number_input("Prix matière 1ère campagne (FCFA/kg)", min_value=0)

# =========================================================
# 2. CORP DE L'APPLICATION - FORMULAIRE D'AUDIT
# =========================================================
st.title("📊 CoopDiag Pro")
st.caption(f"Expertise : Capitalis Global | Date : {datetime.now().strftime('%d/%m/%Y')}")
st.markdown(f"**Audit en cours :** {nom_coop} ({maturite_status})")

st.divider()
tab1, tab2, tab3, tab4, tab5 = st.tabs(["⚖️ Gouv.", "🌿 Durabilité", "🚜 Ops", "💰 Finance", "🔍 Traçabilité"])

# --- MODULE 1 : GOUVERNANCE ---
with tab1:
    st.header("Module 1 : Gouvernance")
    col1, col2 = st.columns(2)
    with col1:
        g1 = st.checkbox("Docs légaux dispo? (RCCM, DEF, Pouvoirs)")
        g2 = st.checkbox("DG qualifié présent?")
    with col2:
        nb_employes = st.number_input("Nombre d'employés total", min_value=0, step=1)
        nb_cnps = st.number_input("Employés déclarés CNPS", min_value=0, step=1)
    
    # Alertes Gouvernance
    pts_gouv = sum([g1, g2])
    max_gouv = 4 # g1, g2, employés >=3, CNPS >=1
    
    if nb_employes < 3:
        st.warning("⚠️ Alerte : Effectif insuffisant (pas bon)")
    else: pts_gouv += 1
        
    if nb_cnps < 1:
        st.warning("⚠️ Alerte : Sécurité sociale faible (pas très bon)")
    else: pts_gouv += 1
        
    score_gouv = calculer_score_module(pts_gouv, max_gouv)

# --- MODULE 2 : DURABILITÉ ---
with tab2:
    st.header("Module 2 : Durabilité")
    certif = st.radio("Coopérative certifiée ?", ["Non", "En cours", "Oui"], horizontal=True)
    
    pts_dura = 0
    max_dura = 3 # Certif (Oui/En cours), Type, Vol Vendu

    if certif == "Non":
        st.error("🚨 Alerte : Coop pas éligible à un crédit")
    elif certif == "En cours":
        pts_dura += 0.5
        st.warning("⚠️ Éligibilité sous réserve de finalisation")
    else:
        pts_dura += 1
        
    type_cert = st.selectbox("Type de Certificat", ["Aucun", "RA (Rainforest)", "FT (Fairtrade)", "Projet interne"])
    if type_cert != "Aucun": pts_dura += 1
        
    vol_vendu = st.radio("Volume certifié déjà vendu ?", ["Non", "Oui"], horizontal=True)
    if vol_vendu == "Oui": pts_dura += 1
    
    score_dura = calculer_score_module(pts_dura, max_dura)

# --- MODULE 3 : PERFORMANCE OP ---
with tab3:
    st.header("Module 3 : Performance Opérationnelle")
    col1, col2 = st.columns(2)
    with col1:
        vol_n2 = st.number_input("Volume réalisé N-2 (tonnes)", min_value=0.0)
    with col2:
        vol_n1 = st.number_input("Volume réalisé N-1 (tonnes)", min_value=0.0)
    
    moy_vol = (vol_n1 + vol_n2) / 2 if (vol_n1 + vol_n2) > 0 else 0
    pts_ops = 0
    max_ops = 4 # Volume > 200, Sections, Flotte, Nb Véhicules conforme
    
    # Alerte Volume
    if 0 < moy_vol < 200:
        st.error("🚨 Alerte : Volume commercial très faible pour un crédit")
    elif moy_vol >= 200:
        pts_ops += 1
        
    nb_sections = st.number_input("Nombre de sections", min_value=0, step=1)
    if nb_sections > 0: pts_ops += 1
        
    flotte = st.radio("Flotte de véhicules ?", ["Non", "Oui"], horizontal=True)
    nb_vehicules = st.number_input("Nombre de véhicules", min_value=0, step=1)
    
    # Alertes Logistique
    if flotte == "Non":
        st.warning("⚠️ Alerte : Besoin de Véhicule")
    else:
        pts_ops += 1
        
    if vol_n1 > 500 and nb_vehicules < 2:
        st.warning("⚠️ Alerte : Besoin de Véhicule (Capacité insuffisante pour > 500t)")
    elif flotte == "Oui" and nb_vehicules >= 2:
        pts_ops += 1
        
    score_ops = calculer_score_module(pts_ops, max_ops)

# --- MODULE 4 : FINANCE ---
with tab4:
    st.header("Module 4 : Finance")
    fonds_roulement = st.number_input("Fonds de roulement (FCFA)", min_value=0)
    charges_op = st.number_input("Charges Op (f/kg sur 40t)", min_value=0.0)
    marge_nette = st.number_input("Marge nette après charges (f/kg sur 40t)", min_value=0.0)
    
    pts_fin = 0
    max_fin = 4 # Fonds Roulement, Charges, Marge (Ratio > 3%), Crédit

    if fonds_roulement > 0: pts_fin += 1
    if charges_op > 0: pts_fin += 1
    if marge_nette > 0: pts_fin += 1
    
    # Calcul Alerte Bénéfice (Excédant < 3% du CA)
    chiffre_affaire = (moy_vol * 1000) * prix_campagne
    ratio_benefice = 0
    if chiffre_affaire > 0:
        # Estimation de l'excédant basé sur la marge nette f/kg
        excedant_estime = marge_nette * (moy_vol * 1000)
        ratio_benefice = (excedant_estime / chiffre_affaire) * 100
        
        if ratio_benefice < 3:
            st.error(f"🚨 Alerte : Bénéfice faible ({ratio_benefice:.1f}% du CA, seuil 3%)")
        else:
            pts_fin += 1
    
    st.divider()
    credit_en_cours = st.radio("Crédit en cours ?", ["Non", "Oui"], horizontal=True)
    valeur_credit = 0
    if credit_en_cours == "Oui":
        valeur_credit = st.number_input("Valeur du crédit (FCFA)", min_value=0)
        
    score_fin = calculer_score_module(pts_fin, max_fin)

# --- MODULE TRAÇABILITÉ ---
with tab5:
    st.header("Module : Traçabilité")
    t1 = st.checkbox("Traçabilité des volumes Vendus?")
    t2 = st.checkbox("Bordereaux et reçu de vente dispo?")
    
    pts_traca = 0
    max_traca = 2
    
    if not t1 or not t2:
        st.error("🚨 Alerte : Besoin de traçabilité interne")
    
    if t1: pts_traca += 1
    if t2: pts_traca += 1
        
    score_traca = calculer_score_module(pts_traca, max_traca)

# =========================================================
# 3. SYNTHÈSE, SCORE FINAL ET GRAPHIQUE
# =========================================================
st.divider()
st.header("📋 Synthèse du Diagnostic Final")

# Calcul Score Global Pondéré (Coefficients Capitalis)
# Gouv 25%, Dura 20%, Ops 20%, Fin 20%, Traca 15%
score_final = (score_gouv * 0.25) + (score_dura * 0.20) + (score_ops * 0.20) + (score_fin * 0.20) + (score_traca * 0.15)

# Affichage du Score Métrique
col_sc1, col_sc2 = st.columns([1, 2])
with col_sc1:
    st.metric("Score de Maturité Global", f"{score_final:.1f}%")
with col_sc2:
    if score_final >= 75:
        st.success("🌟 Profil Excellent : Éligibilité Forte")
    elif score_final >= 50:
        st.warning("⚠️ Profil Moyen : Éligibilité sous condition de restructuration")
    else:
        st.error("🚨 Profil Critique : Risque élevé, non éligible")

# --- GRAPHIQUE DE PERFORMANCE ---
st.subheader("📈 Graphique de Performance par Module")
df_performance = pd.DataFrame({
    'Module': ['Gouvernance', 'Durabilité', 'Opérations', 'Finance', 'Traçabilité'],
    'Score (%)': [score_gouv, score_dura, score_ops, score_fin, score_traca]
})

fig = px.bar(
    df_performance, 
    x='Module', 
    y='Score (%)', 
    text='Score (%)',
    range_y=[0, 110],
    color='Score (%)',
    color_continuous_scale=[ROUGE_ALERTE, ORANGE_WARNING, VERT_CAPITALIS]
)
fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', marker_line_color='black', marker_line_width=1)
fig.update_layout(showlegend=False, coloraxis_showscale=False, height=350, margin=dict(l=20, r=20, t=30, b=20))
st.plotly_chart(fig, use_container_width=True)

# --- DÉTAILS DE LA SYNTHÈSE (Points Forts, Faibles, Besoins) ---
col_syn1, col_syn2 = st.columns(2)

with col_syn1:
    st.markdown("#### ✅ Points Positifs & Forces")
    # Logique d'affichage dynamique des points forts
    if g1 and g2 and nb_employes >= 3: st.write("- Gouvernance et staff structurés")
    if nb_campagnes >= 2: st.write("- Expérience confirmée (Coop mature)")
    if certif == "Oui": st.write("- Certification active (Accès marché)")
    if moy_vol >= 500: st.write("- Fort volume commercial exploité")
    if flotte == "Oui" and nb_vehicules >= 2: st.write("- Capacité logistique propre")
    if ratio_benefice >= 3: st.write(f"- Bonne rentabilité ({ratio_benefice:.1f}%)")
    if t1 and t2: st.write("- Chaîne de traçabilité maîtrisée")

with col_syn2:
    st.markdown("#### 🚩 Points Faibles, Alertes & Besoins")
    # Compilation des alertes définies dans les modules
    if is_filiere_sensible and nb_campagnes < 2: st.markdown(f"<span style='color:{ROUGE_ALERTE}'>• Alerte : Coopérative immature</span>", unsafe_allow_html=True)
    if nb_cnps < 1: st.markdown(f"<span style='color:{ORANGE_WARNING}'>• Point faible : Personnel non déclaré CNPS</span>", unsafe_allow_html=True)
    if certif == "Non": st.markdown(f"<span style='color:{ROUGE_ALERTE}'>• Alerte : Non éligible crédit (Pas de certif)</span>", unsafe_allow_html=True)
    if 0 < moy_vol < 200: st.markdown(f"<span style='color:{ROUGE_ALERTE}'>• Alerte : Volume trop faible pour crédit</span>", unsafe_allow_html=True)
    if flotte == "Non": st.markdown(f"<span style='color:{ORANGE_WARNING}'>• Besoin : Acquisition de Véhicule</span>", unsafe_allow_html=True)
    if vol_n1 > 500 and nb_vehicules < 2: st.markdown(f"<span style='color:{ORANGE_WARNING}'>• Besoin : Renforcement flotte (>500t)</span>", unsafe_allow_html=True)
    if chiffre_affaire > 0 and ratio_benefice < 3: st.markdown(f"<span style='color:{ORANGE_WARNING}'>• Point faible : Bénéfice faible ({ratio_benefice:.1f}%)</span>", unsafe_allow_html=True)
    if not t1 or not t2: st.markdown(f"<span style='color:{ROUGE_ALERTE}'>• Alerte : Besoin de traçabilité interne</span>", unsafe_allow_html=True)

# =========================================================
# 4. SAUVEGARDE ET GÉNÉRATION DU RAPPORT PDF
# =========================================================
st.divider()
col_btn1, col_btn2 = st.columns(2)

with col_btn1:
    if st.button("💾 Sauvegarder le Diagnostic", use_container_width=True):
        st.success(f"Diagnostic de {nom_coop} enregistré localement (Simulation).")
        st.balloons()
        # Note : Pour une vraie sauvegarde, connecte ici une Google Sheet ou DB.

# --- LOGIQUE GÉNÉRATION PDF AVEC FPDF ---
class PDF(FPDF):
    def header(self):
        # Logo Capitalis Global
        logo = charger_logo()
        if logo:
            self.image(logo, 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.cell(80)
        self.cell(30, 10, 'Rapport de Diagnostic Coopératif', 0, 0, 'C')
        self.ln(20)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}} | Capitalis Global - CoopDiag Pro', 0, 0, 'C')

# --- FONCTION DE NETTOYAGE (À placer avant la génération) ---
def clean(text):
    if text is None:
        return ""
    # Remplace les caractères qui font planter le PDF
    replacements = {
        '\u2022': '-',  # La puce noire devient un tiret
        '’': "'",       # L'apostrophe courbe devient droite
        '€': 'EUR',     # Le symbole Euro
        '\u201c': '"',  # Guillemets
        '\u201d': '"'
    }
    for old, new in replacements.items():
        text = str(text).replace(old, new)
    # Encode en latin-1 et remplace les inconnus par '?' pour éviter le crash
    return text.encode('latin-1', 'replace').decode('latin-1')

# --- LOGIQUE GÉNÉRATION PDF SÉCURISÉE ---
import plotly.io as pio
from datetime import datetime

import plotly.io as pio

def generer_rapport_pdf():
    try:
        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        
        def clean(text):
            if text is None: return ""
            replacements = {'\u2022': '-', '’': "'", '€': 'EUR'}
            for old, new in replacements.items():
                text = str(text).replace(old, new)
            return text.encode('latin-1', 'replace').decode('latin-1')

        # DATE EN HAUT À DROITE
        pdf.set_font('Arial', 'I', 9)
        date_now = datetime.now().strftime("%d/%m/%Y à %H:%M")
        pdf.cell(0, 5, clean(f"Document généré le : {date_now}"), 0, 1, 'R')
        pdf.ln(5)

        # IDENTIFICATION
        pdf.set_fill_color(240, 242, 246)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, clean(f"RAPPORT D'AUDIT : {nom_coop}"), 0, 1, 'L', True)
        pdf.ln(5)

        # SCORE GLOBAL
        pdf.set_font('Arial', 'B', 14)
        if score_final >= 75: pdf.set_text_color(46, 125, 50)
        elif score_final >= 50: pdf.set_text_color(245, 124, 0)
        else: pdf.set_text_color(211, 47, 47)
        pdf.cell(0, 10, clean(f"SCORE DE MATURITÉ : {score_final:.1f}%"), 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)

        # --- INSERTION DU GRAPHIQUE (SÉCURISÉE) ---
        try:
            # On génère l'image du graphique 'fig'
            img_bytes = pio.to_image(fig, format="png", width=700, height=400)
            with open("temp_chart.png", "wb") as f:
                f.write(img_bytes)
            pdf.image("temp_chart.png", x=15, w=180)
            pdf.ln(10) 
        except Exception as e:
            # Si kaleido n'est pas là, on affiche juste les scores en texte
            pdf.ln(10)
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, clean("(Graphique visuel non disponible - voir scores détaillés ci-dessous)"), 0, 1, 'C')

        # DÉTAILS DES SCORES
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, clean("Détails des performances :"), 0, 1)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 6, clean(f"- Gouvernance : {score_gouv:.1f}%"), 0, 1)
        pdf.cell(0, 6, clean(f"- Durabilité : {score_dura:.1f}%"), 0, 1)
        pdf.cell(0, 6, clean(f"- Opérations : {score_ops:.1f}%"), 0, 1)
        pdf.cell(0, 6, clean(f"- Finance : {score_fin:.1f}%"), 0, 1)
        pdf.cell(0, 6, clean(f"- Traçabilité : {score_traca:.1f}%"), 0, 1)

        return pdf.output(dest='S').encode('latin-1', 'replace')
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return None

# --- AFFICHAGE DU BOUTON ---
st.divider()
res_pdf = generer_rapport_pdf()
if res_pdf:
    st.download_button(
        label="📥 Télécharger le Rapport PDF Complet",
        data=res_pdf,
        file_name=f"Audit_{nom_coop}.pdf",
        mime="application/pdf",
        use_container_width=True
    )