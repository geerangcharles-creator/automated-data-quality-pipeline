"""Interface Streamlit du pipeline de qualité des données V1."""

import streamlit as st
import plotly.express as px
import streamlit.components.v1 as components
from html import escape
import hashlib
from time import perf_counter
from io import BytesIO

from src.file_loader import FileLoadError, list_excel_sheets, load_data
from src.data_profiler import profile_data
from src.quality_checker import check_quality, check_duplicates
from src.recommendations import generate_recommendations
from src.report_generator import html_report, summary_csv
from src.outlier_explorer import explore_outliers


def afficher_tableau(df):
    """Affiche des tableaux sans PyArrow."""
    if df.empty:
        st.info("Aucune ligne à afficher.")
    else:
        html = df.to_html(index=False, escape=True, border=0, classes="quality-table")
        st.markdown(f'<div class="quality-table-scroll">{html}</div>', unsafe_allow_html=True)


def afficher_graphique(fig):
    """Affiche Plotly sans sérialisation Arrow."""
    components.html(fig.to_html(full_html=False, include_plotlyjs=True), height=450)


def section_heading(number, label, description):
    st.markdown(
        f'<div class="section-heading"><span class="section-number">{number}</span>'
        f'<div><h2>{escape(label)}</h2><p>{escape(description)}</p></div></div>',
        unsafe_allow_html=True,
    )


def metric_card(label, value, note, accent="blue"):
    st.markdown(
        f'<div class="metric-card {accent}"><div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(str(value))}</div>'
        f'<div class="metric-note">{escape(note)}</div></div>',
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Data Quality Pipeline", page_icon="🔎", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html, body, [data-testid="stAppViewContainer"] {font-family:'DM Sans',Arial,sans-serif;}
[data-testid="stAppViewContainer"] {background:#f5f7fb;color:#17283f;}
[data-testid="stHeader"] {background:transparent;}
.block-container {max-width:1240px;padding-top:2.2rem;padding-bottom:4rem;}
.hero {padding:34px 40px;background:linear-gradient(117deg,#102b49 0%,#173d63 70%,#165777 100%);border-radius:20px;color:#fff;margin:0 0 28px;box-shadow:0 15px 30px rgba(23,49,76,.12);}
.hero .eyebrow {font-size:12px;font-weight:800;letter-spacing:2.1px;color:#8fe2dd;text-transform:uppercase;margin-bottom:12px;}
.hero h1 {font-size:37px;line-height:1.16;letter-spacing:-1.25px;color:#fff;margin:0 0 12px;font-weight:800;}
.hero p {max-width:670px;color:#d9e7f4;font-size:15px;line-height:1.65;margin:0;}
.hero-badges {margin-top:20px;display:flex;gap:9px;flex-wrap:wrap;}
.hero-badges span {display:inline-block;border:1px solid rgba(190,224,239,.27);background:rgba(255,255,255,.08);border-radius:20px;padding:6px 12px;font-size:12px;color:#e8f5fa;}
.section-heading {display:flex;gap:15px;align-items:center;margin:29px 0 17px;}
.section-number {display:inline-flex;align-items:center;justify-content:center;background:#e1f3f3;color:#087d81;border-radius:11px;min-width:40px;height:40px;font-weight:800;font-size:14px;}
.section-heading h2 {color:#173250;font-size:22px;font-weight:800;line-height:1.2;margin:0;}
.section-heading p {color:#718198;font-size:13px;margin:5px 0 0;}
.metric-card {background:white;border:1px solid #e4ebf3;border-radius:16px;padding:22px 22px 18px;min-height:149px;box-shadow:0 4px 16px rgba(26,51,81,.04);border-top:4px solid #3476aa;}
.metric-card.teal {border-top-color:#13a5a4;}.metric-card.amber {border-top-color:#e8a742;}.metric-card.purple {border-top-color:#8069c5;}
.metric-label {color:#667991;font-size:12px;font-weight:700;letter-spacing:.3px;}
.metric-value {font-size:34px;font-weight:800;color:#153451;line-height:1.3;margin-top:8px;}
.metric-note {color:#8493a7;font-size:12px;margin-top:4px;}
.quality-table-scroll {overflow-x:auto;border:1px solid #e3eaf2;border-radius:13px;background:#fff;margin:12px 0 24px;box-shadow:0 2px 8px rgba(10,37,64,.035);}
.quality-table {width:100%;border-collapse:collapse;color:#2c4159;font-size:13px;}
.quality-table th {background:#eaf1f8;color:#234761;font-size:12px;font-weight:800;text-align:left;padding:13px 15px;white-space:nowrap;border-bottom:1px solid #dce5ee;}
.quality-table td {padding:11px 15px;border-bottom:1px solid #edf1f6;white-space:nowrap;}
.quality-table tbody tr:last-child td {border-bottom:0;}
.quality-table tbody tr:nth-child(even) {background:#f9fbfd;}
.quality-table tbody tr:hover {background:#eef8f8;}
[data-testid="stFileUploader"] {background:#fff;border:1px solid #e4eaf1;border-radius:14px;padding:12px 18px;}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:7px;background:#eef2f7;padding:6px;border-radius:12px;}
[data-testid="stTabs"] button[role="tab"] {border-radius:9px;color:#526b82;padding:10px 16px;font-weight:700;}
[data-testid="stTabs"] button[aria-selected="true"] {background:#fff;color:#0b7b81;box-shadow:0 2px 8px rgba(23,42,64,.08);}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {background:transparent;}
[data-testid="stDownloadButton"] button {background:#16677b;color:white;border:0;border-radius:10px;font-weight:700;min-height:43px;}
@media(max-width:700px){.hero{padding:25px 22px}.hero h1{font-size:29px}.block-container{padding-top:1.2rem}}
</style>
<div class="hero">
  <div class="eyebrow">Data analyst workspace · Version 1.1</div>
  <h1>Data Quality Pipeline</h1>
  <p>Explorez vos fichiers, identifiez les anomalies et produisez un diagnostic clair, sans modifier les données d'origine.</p>
  <div class="hero-badges"><span>CSV & Excel</span><span>Contrôles explicables</span><span>Rapports exportables</span></div>
</div>
""", unsafe_allow_html=True)

section_heading("01", "Importer un jeu de données", "Commencez par sélectionner un fichier à analyser.")
file = st.file_uploader("Importer un fichier CSV ou Excel (.xlsx)", type=["csv", "xlsx"])
if file is None:
    st.write("Pour commencer, importez un fichier ou utilisez le jeu de données d'exemple fourni dans `data/sample_data.csv`.")
    st.stop()

suffix = file.name.lower().rsplit(".", 1)[-1]
file_bytes = file.getvalue()
file_signature = hashlib.sha256(file_bytes).hexdigest()
file_cache_key = (file.name, file_signature)
if st.session_state.get("file_cache_key") != file_cache_key:
    st.session_state["file_cache_key"] = file_cache_key
    st.session_state["sheet_names"] = None
    st.session_state["loaded_data"] = None
    st.session_state["load_key"] = None
    st.session_state["analysis_cache"] = {}
    st.session_state["duplicates_cache"] = {}

sheet, sep, encoding = None, "auto", "auto"
if suffix == "xlsx":
    try:
        if st.session_state["sheet_names"] is None:
            with st.spinner("Lecture de la liste des feuilles Excel..."):
                st.session_state["sheet_names"] = list_excel_sheets(file)
        sheets = st.session_state["sheet_names"]
        sheet = st.selectbox("Feuille Excel", sheets)
    except FileLoadError as exc:
        st.error(str(exc))
        st.stop()
else:
    left, right = st.columns(2)
    sep = left.selectbox("Séparateur CSV", ["auto", ",", ";", "\t", "|"])
    encoding = right.selectbox("Encodage", ["auto", "utf-8-sig", "utf-8", "cp1252", "latin-1"])

try:
    load_key = (file_cache_key, sheet, sep, encoding)
    if st.session_state["load_key"] != load_key:
        started = perf_counter()
        with st.spinner("Chargement du fichier en mémoire (une seule fois)..."):
            source = BytesIO(file_bytes)
            source.name = file.name
            st.session_state["loaded_data"] = load_data(source, sheet_name=sheet, separator=sep, encoding=encoding)
        st.session_state["load_key"] = load_key
        st.session_state["load_duration"] = perf_counter() - started
        st.session_state["analysis_cache"] = {}
        st.session_state["duplicates_cache"] = {}
    df = st.session_state["loaded_data"]
    if not df.columns.is_unique:
        st.error("Le fichier comporte des noms de colonnes identiques. Renommez-les dans une copie pour pouvoir les contrôler.")
        st.stop()
except (FileLoadError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

section_heading("02", "Configurer l'analyse", "Choisissez votre périmètre et les clés de détection des doublons.")
mode = st.radio("Mode", ["Analyse globale", "Analyse ciblée"], horizontal=True)
all_columns = list(df.columns)
if mode == "Analyse globale":
    analysis_columns = all_columns
    st.caption("Toutes les colonnes sont analysées.")
else:
    analysis_columns = st.multiselect("Colonnes à analyser", all_columns, default=all_columns)
    if not analysis_columns:
        st.warning("Sélectionnez au moins une colonne à analyser.")
        st.stop()

duplicate_columns = st.multiselect(
    "Colonnes utilisées pour rechercher les doublons ciblés",
    all_columns, default=all_columns,
    help="Cette clé est indépendante de la sélection de colonnes analysées. Les doublons portent sur le fichier entier.",
)
if not duplicate_columns:
    st.warning("Sélectionnez au moins une colonne pour la recherche des doublons ciblés.")
    st.stop()

selected_df = df.loc[:, analysis_columns]
analysis_key = tuple(analysis_columns)
if analysis_key not in st.session_state["analysis_cache"]:
    with st.spinner("Profilage et contrôles de qualité en cours..."):
        started = perf_counter()
        profile_result = profile_data(selected_df)
        quality_result = check_quality(selected_df, include_duplicates=False)
        st.session_state["analysis_cache"] = {
            analysis_key: (profile_result, quality_result, perf_counter() - started)
        }
profile, quality_cached, analysis_duration = st.session_state["analysis_cache"][analysis_key]
quality = dict(quality_cached)

duplicate_key = tuple(duplicate_columns)
if duplicate_key not in st.session_state["duplicates_cache"]:
    with st.spinner("Recherche des doublons sur le fichier complet..."):
        started = perf_counter()
        duplicate_result = check_duplicates(df, duplicate_columns)
        st.session_state["duplicates_cache"] = {
            duplicate_key: (duplicate_result, perf_counter() - started)
        }
full_quality, duplicate_duration = st.session_state["duplicates_cache"][duplicate_key]
for key in (
    "duplicate_full_count", "duplicate_full_affected", "duplicate_full_indices",
    "duplicate_full_rows", "duplicate_subset_count", "duplicate_subset_affected",
    "duplicate_subset_indices", "duplicate_subset_rows", "duplicate_subset_columns",
):
    quality[key] = full_quality[key]
advice = generate_recommendations(selected_df, quality)
st.caption(f"⏱ Chargement initial : {st.session_state['load_duration']:.1f} s · "
           f"Diagnostic : {analysis_duration:.1f} s · Doublons : {duplicate_duration:.1f} s. "
           "Les résultats déjà calculés sont réutilisés lorsque vous modifiez l'affichage.")

section_heading("03", "Vue générale", "Les principaux indicateurs du diagnostic.")
c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("LIGNES DU FICHIER", f"{len(df):,}", "Volume total", "blue")
with c2:
    metric_card("COLONNES ANALYSÉES", len(analysis_columns), f"sur {len(all_columns)} colonnes", "teal")
with c3:
    metric_card("VALEURS MANQUANTES", int(quality["missing"]["manquantes"].sum()), "Dans la sélection", "amber")
with c4:
    metric_card("DOUBLONS COMPLETS", quality["duplicate_full_count"], "Sur le fichier complet", "purple")
st.caption(f"Dimensions originales : {len(df)} lignes × {len(df.columns)} colonnes. "
           f"Sélection : {', '.join(map(str, analysis_columns))}")

section_heading("04", "Explorer les résultats", "Parcourez le profil, les contrôles et les recommandations.")
tab1, tab2, tab_explore, tab_advanced, tab3, tab4 = st.tabs(
    ["📋 Profil", "🔎 Contrôles", "🔬 Investigation", "🧪 Qualité avancée", "💡 Recommandations", "📥 Exporter"]
)
with tab1:
    st.markdown("#### Aperçu (10 premières lignes)")
    afficher_tableau(profile["apercu"])
    st.markdown("#### Structure")
    afficher_tableau(profile["colonnes_details"])
    st.markdown("#### Statistiques descriptives")
    afficher_tableau(profile["statistiques"].reset_index())

with tab2:
    st.markdown("#### Valeurs manquantes")
    afficher_tableau(quality["missing"])
    if len(quality["missing"]):
        fig = px.bar(quality["missing"], x="colonne", y="pourcentage", text="pourcentage",
                     color_discrete_sequence=["#149c9a"],
                     labels={"pourcentage": "Valeurs manquantes (%)", "colonne": "Colonne"})
        fig.update_layout(yaxis_range=[0, 100], template="plotly_white", margin=dict(l=26, r=22, t=24, b=32),
                          font=dict(family="Arial", color="#2a445b"), plot_bgcolor="#fff", paper_bgcolor="#fff")
        afficher_graphique(fig)
    st.markdown("#### Chaînes vides (espaces compris)")
    afficher_tableau(quality["empty_strings"])
    st.markdown("#### Doublons — fichier complet")
    st.caption("Ces décomptes sont indépendants du filtre de colonnes à analyser.")
    st.write(f"Doublons complets supplémentaires : **{quality['duplicate_full_count']}** ; lignes impliquées : **{quality['duplicate_full_affected']}**")
    st.write(f"Doublons supplémentaires sur la sélection : **{quality['duplicate_subset_count']}** ; lignes impliquées : **{quality['duplicate_subset_affected']}**")
    st.caption("Une occurrence par groupe est conservée dans le comptage 'supplémentaires'. Les tableaux affichent toutes les lignes du groupe.")
    visible_columns = list(dict.fromkeys([*analysis_columns, *duplicate_columns]))
    afficher_tableau(quality["duplicate_subset_rows"].loc[:, visible_columns].head(100))
    st.markdown("#### Types suspects")
    afficher_tableau(quality["suspect_types"])
    st.markdown("#### Valeurs numériques atypiques (méthode IQR)")
    afficher_tableau(quality["outliers"])
    st.caption("Ces alertes statistiques ne prouvent pas qu'une valeur est erronée.")

with tab_explore:
    st.markdown("#### Explorer les lignes atypiques")
    st.caption("Les seuils proviennent de la méthode IQR. Les autres colonnes sont conservées pour comprendre chaque transaction.")
    outliers_summary = quality["outliers"]
    available = outliers_summary.loc[outliers_summary["valeurs_atypiques"] > 0, "colonne"].tolist()
    if not available:
        st.info("Aucune valeur atypique détectée par IQR dans les colonnes analysées.")
    else:
        selected_column = st.selectbox("Colonne numérique à examiner", available)
        row = outliers_summary.loc[outliers_summary["colonne"] == selected_column].iloc[0]
        low, high = row["borne_basse"], row["borne_haute"]
        direction = st.radio("Valeurs à afficher", ["Tous", "Inférieures", "Supérieures"], horizontal=True)
        matches = explore_outliers(df, selected_column, low, high, direction)
        k1, k2, k3 = st.columns(3)
        k1.metric("Lignes suspectes", len(matches))
        k2.metric("Borne basse", f"{low:,.2f}")
        k3.metric("Borne haute", f"{high:,.2f}")
        if any(word in selected_column.lower() for word in ("id", "code")):
            st.warning("Cette colonne semble être un identifiant : l'IQR n'est généralement pas pertinent pour ce type de variable.")
        if not matches.empty:
            st.markdown("#### Examiner les transactions dans leur contexte")
            context_columns = st.multiselect("Colonnes de contexte à afficher", list(df.columns),
                                             default=list(df.columns[:min(8, len(df.columns))]))
            preview_count = st.select_slider("Nombre de lignes affichées", options=[10, 25, 50, 100], value=25)
            ascending = st.radio("Trier les valeurs", ["Plus grandes d'abord", "Plus petites d'abord"], horizontal=True)
            sorted_matches = matches.sort_values(selected_column, ascending=(ascending == "Plus petites d'abord"))
            visible = list(dict.fromkeys([selected_column, *context_columns]))
            preview = sorted_matches.loc[:, visible].head(preview_count).copy()
            preview.insert(0, "ligne_source", preview.index + 2)
            afficher_tableau(preview)
            st.caption(f"Aperçu limité à {min(preview_count, len(matches)):,} ligne(s) sur {len(matches):,} ; les calculs utilisent toutes les lignes du fichier.")
            st.warning("L'export ci-dessous peut contenir des identifiants et données sensibles. Vérifiez qui y aura accès.")
            csv = sorted_matches.copy()
            csv.insert(0, "ligne_source", csv.index + 2)
            st.download_button("📥 Télécharger les lignes atypiques filtrées (CSV)",
                               data=csv.to_csv(index=False).encode("utf-8-sig"),
                               file_name=f"anomalies_iqr_{selected_column}.csv", mime="text/csv")
            st.caption("Les données originales ne sont jamais modifiées ; ce fichier contient toutes les colonnes des lignes filtrées.")

with tab_advanced:
    st.markdown("#### Colonnes constantes et quasi constantes")
    st.caption("Constante : une seule valeur non manquante distincte. Quasi constante : au moins 95 % de valeurs identiques (10 lignes renseignées minimum).")
    afficher_tableau(quality["constant_columns"])
    st.markdown("#### Formats incohérents")
    st.caption("Vérifie les colonnes de dates et d'emails identifiées par leur nom. Les formats de dates mélangés sont signalés ; les dates ambiguës nécessitent une vérification humaine.")
    afficher_tableau(quality["format_issues"])
    st.markdown("#### Espaces parasites et variantes de casse")
    afficher_tableau(quality["extra_spaces"])
    afficher_tableau(quality["case_inconsistencies"])
    st.markdown("#### Valeurs négatives et zéros")
    st.caption("Ces valeurs ne sont pas nécessairement des erreurs, particulièrement pour les ventes, annulations ou ajustements.")
    afficher_tableau(quality["numeric_signs"])
    st.markdown("#### Cardinalité")
    st.caption("Une cardinalité élevée correspond ici à au moins 90 % de valeurs distinctes parmi 20 valeurs renseignées ou plus.")
    afficher_tableau(quality["cardinality"])

with tab3:
    if advice.empty:
        st.success("Aucune recommandation déclenchée par les règles de la V1.")
    else:
        afficher_tableau(advice)
    st.warning("Aucune correction n'est réalisée automatiquement. Vérifiez chaque cas avec les règles métier.")

with tab4:
    st.markdown("#### Télécharger le rapport")
    st.caption("Les statistiques et alertes par colonne concernent la sélection. Les doublons concernent le fichier complet.")
    st.download_button("Rapport HTML", data=html_report(profile, quality, advice, file.name),
                       file_name="rapport_qualite.html", mime="text/html")
    st.download_button("Récapitulatif des anomalies CSV", data=summary_csv(quality),
                       file_name="recapitulatif_anomalies.csv", mime="text/csv")
    st.caption("Les exports contiennent les statistiques et recommandations, pas les lignes brutes du fichier.")
