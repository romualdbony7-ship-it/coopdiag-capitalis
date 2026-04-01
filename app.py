import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from fpdf import FPDF
import gspread
from datetime import datetime
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Capitalis - Diagnostic Expert", layout="wide")

# FONCTION 1 : SAUVEGARDER
def sauvegarder_dans_sheets(donnees):
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open("Diagnostics_Coop").sheet1
        sh.append_row(donnees)
        return True
    except Exception as e:
        if "200" not in str(e): # On ignore le faux message d'erreur 200
            st.error(f"Erreur de sauvegarde : {e}")
            return False
        return True

# FONCTION 2 : LIRE (HISTORIQUE)
def lire_historique_sheets():
    try:
        creds = st.secrets["gcp_service_account"]
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open("Diagnostics_Coop").sheet1
        
        # On tente la lecture classique
        return pd.DataFrame(sh.get_all_records())
        
    except Exception as e:
        # Si on reçoit le fameux message <Response [200]>
        if "200" in str(e) or "Response" in str(e):
            try:
                # On utilise une méthode alternative plus brute
                data = sh.get_all_values()
                if len(data) > 1:
                    return pd.DataFrame(data[1:], columns=data[0])
                return pd.DataFrame()
            except:
                return None
        
        st.error(f"Erreur de lecture : {e}")
        return None
# --- LOGIQUE PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists("logo.png"):
            self.image("logo.png", 10, 8, 30)
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'RAPPORT DE DIAGNOSTIC COOPERATIF', 0, 1, 'C')
        self.ln(10)

def clean(text):
    return str(text).encode('latin-1', 'replace').decode('latin-1')

# --- SAISIE DES INFORMATIONS GÉNÉRALES ---
st.title("📋 Diagnostic Coopératif Complet")

with st.expander("🏢 Identification & Localisation", expanded=True):
    col1, col2 = st.columns([1, 1])
    with col1:
        nom_coop = st.text_input("Nom de la Coopérative")
        pca_nom = st.text_input("Nom du PCA")
        pca_contact = st.text_input("Contact PCA")
        email_coop = st.text_input("Email de la coopérative")
    with col2:
        annee_crea = st.number_input("Année de création", 1960, 2026, 2020)
        siege = st.text_input("Siège Social")
        nb_membres = st.number_input("Nombre de membres", 0)
        filieres = st.multiselect("Filières", ["Cacao", "Hévéa", "Anacarde", "Palmiers à huile", "Maïs", "vivrier", "Aquaculture"])

# LOGIQUE DE MATURITÉ
alerte_maturite = ""
if any(f in filieres for f in ["Cacao", "Hévéa", "Anacarde"]):
    nb_campagnes = st.number_input("Nombre de campagnes réalisées", 0)
    alerte_maturite = "Coop immature" if nb_campagnes < 2 else "Coop mature"
    if alerte_maturite == "Coop immature": st.warning(alerte_maturite)
    else: st.success(alerte_maturite)

clients = st.text_area("Nom des clients")
prix_mat = st.number_input("Prix matière 1ère campagne (FCFA/kg)", 0)

# --- MODULES DE DIAGNOSTIC ---
st.divider()
tab1, tab2, tab3, tab4, tab5, tab_syn, tab_hist = st.tabs([
    "⚖️ Gouv", "🌿 Dura", "🚜 Ops", "💰 Fin", "🔍 Traca", "🏁 SYNTHÈSE", "📜 HISTORIQUE"
])

with tab1:
    g1 = st.checkbox("Présence docs légaux? (RCCM, DEF, Pouvoirs)")
    g2 = st.checkbox("Présence d'un DG qualifié?")
    n_emp = st.number_input("Nombre d'employés", 0)
    n_cnps = st.number_input("Employés déclarés CNPS", 0)
    score_gouv = ((g1 + g2 + (n_emp >= 3) + (n_cnps >= 1)) / 4) * 100

with tab2:
    certif = st.radio("Coopérative certifiée ?", ["Non", "Oui", "En cours"])
    t_cert = st.selectbox("Type de Certificat", ["Aucun", "RA", "FT", "Projet interne"])
    v_vendu = st.radio("Volume certifié déjà vendu ?", ["Non", "Oui"])
    score_dura = (((certif != "Non") + (t_cert != "Aucun") + (v_vendu == "Oui")) / 3) * 100

with tab3:
    vn2 = st.number_input("Volumes réalisés en N-2 (Tonnes)", 0.0)
    vn1 = st.number_input("Volumes réalisés en N-1 (Tonnes)", 0.0)
    moy_vol = (vn1 + vn2) / 2
    n_sect = st.number_input("Nombre de sections", 0)
    flotte = st.radio("Flotte de véhicules ?", ["Non", "Oui"])
    n_veh = st.number_input("Nombre de véhicules", 0)
    
    alerte_v = (moy_vol < 200)
    alerte_f = (flotte == "Non")
    alerte_n_veh = (moy_vol > 500 and n_veh < 2)
    score_ops = (((not alerte_v) + (not alerte_f) + (not alerte_n_veh)) / 3) * 100

with tab4:
    fdr = st.number_input("Fonds de roulement (FCFA)", 0)
    ch_op = st.number_input("Charges Op en f/kg sur 40t", 0.0)
    marge = st.number_input("Marge nette après charges en f/kg sur 40t", 0.0)
    credit = st.radio("Crédit en cours ?", ["Non", "Oui"])
    val_credit = st.number_input("Valeur du crédit", 0) if credit == "Oui" else 0
    
    ca_estime = moy_vol * 1000 * prix_mat
    benef_total = moy_vol * 1000 * marge
    seuil_benef = ca_estime * 0.03
    alerte_benef = (benef_total < seuil_benef) if ca_estime > 0 else False
    score_fin = (((fdr > 0) + (marge > 0) + (not alerte_benef)) / 3) * 100

with tab5:
    trac_v = st.radio("Traçabilité des volumes vendus ?", ["Non", "Oui"])
    bord = st.radio("Bordereaux et reçus dispo ?", ["Non", "Oui"])
    score_traca = (((trac_v == "Oui") + (bord == "Oui")) / 2) * 100

# --- SYNTHÈSE & ALERTES ---
score_final = (score_gouv + score_dura + score_ops + score_fin + score_traca) / 5

with tab_syn:
    st.header("📊 Tableau de Bord de Performance")
    
    alertes_liste = []
    if alerte_maturite == "Coop immature": alertes_liste.append("⚠️ Coopérative immature (< 2 campagnes)")
    if n_emp < 3: alertes_liste.append("❌ Effectif insuffisant (< 3 personnes)")
    if n_cnps < 1: alertes_liste.append("❌ Absence de déclaration CNPS")
    if certif == "Non": alertes_liste.append("⚠️ Non éligible au crédit (Certification manquante)")
    if alerte_v: alertes_liste.append("⚠️ Volume commercial trop faible (< 200t)")
    if alerte_f: alertes_liste.append("🚨 Besoin de Véhicule (Pas de flotte)")
    if alerte_n_veh: alertes_liste.append("🚨 Besoin de Véhicule (Sous-équipé pour > 500t)")
    if alerte_benef: alertes_liste.append("⚠️ Bénéfice faible (< 3% du CA)")
    if trac_v == "Non" or bord == "Non": alertes_liste.append("🚨 Besoin de traçabilité interne")

    col_res1, col_res2 = st.columns([1, 1])
    with col_res1:
        st.metric("Score Global de Conformité", f"{score_final:.1f}%")
        # Graphique
        df_graph = pd.DataFrame({
            "Module": ["Gouv", "Dura", "Ops", "Fin", "Traca"],
            "Score": [score_gouv, score_dura, score_ops, score_fin, score_traca]
        })
        fig = px.bar(df_graph, x="Module", y="Score", color="Score", range_y=[0,100], 
                     color_continuous_scale="RdYlGn", title="Performance par Pilier")
        st.plotly_chart(fig, use_container_width=True)

    with col_res2:
        st.subheader("⚠️ Alertes & Besoins")
        if alertes_liste:
            for a in alertes_liste: st.error(a)
        else:
            st.success("Aucune alerte majeure détectée.")
        
        st.subheader("✅ Points Forts")
        if score_final > 70: st.success("Excellente performance globale")
        if g1 and g2: st.success("Gouvernance structurée et DG qualifié")
        if fdr > 0: st.success("Fonds de roulement positif")

# --- ACTIONS FINALES ---
st.divider()
c_btn1, c_btn2 = st.columns(2)

with c_btn1:
    if st.button("💾 Sauvegarder dans Google Sheets", use_container_width=True):
        data = [
            datetime.now().strftime("%d/%m/%Y"), nom_coop, pca_nom, ", ".join(filieres),
            f"{score_final:.1f}%", f"{score_gouv:.1f}%", f"{score_dura:.1f}%",
            f"{score_ops:.1f}%", f"{score_fin:.1f}%", f"{score_traca:.1f}%",
            " | ".join(alertes_liste)
        ]
        if sauvegarder_dans_sheets(data):
            st.success("Données synchronisées avec succès !")
            st.balloons()

with c_btn2:
    def export_pdf():
        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, clean(f"Coopérative : {nom_coop}"), 0, 1)
        pdf.set_font("Arial", "", 10)
        pdf.cell(0, 7, clean(f"PCA : {pca_nom} | Contact : {pca_contact}"), 0, 1)
        pdf.cell(0, 7, clean(f"Score de Performance : {score_final:.1f}%"), 0, 1)
        pdf.ln(5)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "SYNTHESE DES BESOINS ET ALERTES :", 0, 1)
        pdf.set_font("Arial", "", 10)
        for a in alertes_liste:
            pdf.cell(0, 7, f"- {clean(a)}", 0, 1)
        return pdf.output(dest='S').encode('latin-1', 'replace')

    st.download_button("📥 Télécharger le Rapport PDF", export_pdf(), 
                       f"Diagnostic_{nom_coop}.pdf", "application/pdf", use_container_width=True)
# ... (Vos codes pour tab1, tab2, tab3, tab4, tab5 et tab_syn) ...

# TOUT EN BAS DU FICHIER :
with tab_hist:
    st.header("📜 Historique des diagnostics")
    if st.button("🔄 Actualiser la liste", use_container_width=True):
        with st.spinner("Récupération des données..."):
            try:
                creds = st.secrets["gcp_service_account"]
                gc = gspread.service_account_from_dict(creds)
                sh = gc.open("Diagnostics_Coop").sheet1
                
                # On récupère toutes les lignes de la feuille
                toutes_les_lignes = sh.get_all_values()
                
                if len(toutes_les_lignes) > 1:
                    # La ligne 0 contient les titres, le reste contient les données
                    df_historique = pd.DataFrame(toutes_les_lignes[1:], columns=toutes_les_lignes[0])
                    
                    # On affiche les 10 derniers enregistrements
                    st.success(f"{len(toutes_les_lignes)-1} diagnostics trouvés.")
                    st.dataframe(
                        df_historique.iloc[::-1].head(10), 
                        use_container_width=True, 
                        hide_index=True
                    )
                else:
                    st.info("La base de données est vide. Les titres doivent être en ligne 1.")
            except Exception as e:
                st.error(f"Erreur de lecture : {e}")