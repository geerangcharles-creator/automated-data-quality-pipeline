"""Rapports générés uniquement à partir de diagnostics, sans données sources brutes."""

from html import escape
from io import StringIO

import pandas as pd


def summary_csv(quality):
    rows = []
    for key, name, metric in (("missing", "valeur_manquante", "manquantes"),
                              ("empty_strings", "chaine_vide", "chaines_vides"),
                              ("suspect_types", "type_suspect", "valeurs_suspectes"),
                              ("outliers", "valeur_atypique", "valeurs_atypiques"),
                              ("format_issues", "format_suspect", "formats_suspects"),
                              ("extra_spaces", "espace_parasite", "espaces_parasites"),
                              ("case_inconsistencies", "variante_casse", "variantes_casse"),
                              ("numeric_signs", "valeur_negative", "valeurs_negatives"),
                              ("numeric_signs", "valeur_zero", "valeurs_zero")):
        for _, item in quality[key].iterrows():
            rows.append({"anomalie": name, "colonne": item["colonne"], "nombre": int(item[metric])})
    for key, name, column in (("constant_columns", "colonne_constante", "constante"),
                              ("constant_columns", "quasi_constante", "quasi_constante"),
                              ("cardinality", "cardinalite_elevee", "cardinalite_elevee")):
        for _, item in quality[key].iterrows():
            rows.append({"anomalie": name, "colonne": item["colonne"], "nombre": int(item[column])})
    rows.extend([{"anomalie": "doublon_complet", "colonne": "Toutes", "nombre": quality["duplicate_full_count"]},
                 {"anomalie": "doublon_selection", "colonne": ", ".join(map(str, quality["duplicate_subset_columns"])),
                  "nombre": quality["duplicate_subset_count"]}])
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")


def html_report(profile, quality, recommendations, filename="fichier"):
    def table(df):
        return df.to_html(index=False, escape=True, border=0, classes="data") if not df.empty else "<p>Aucun résultat.</p>"

    sections = [("Profil des colonnes", profile["colonnes_details"]),
                ("Valeurs manquantes", quality["missing"]),
                ("Chaînes vides", quality["empty_strings"]),
                ("Types suspects", quality["suspect_types"]),
                ("Valeurs numériques atypiques (IQR)", quality["outliers"]),
                ("Colonnes constantes / quasi constantes", quality["constant_columns"]),
                ("Formats suspects", quality["format_issues"]),
                ("Espaces parasites", quality["extra_spaces"]),
                ("Variantes de casse", quality["case_inconsistencies"]),
                ("Nombres négatifs / zéros", quality["numeric_signs"]),
                ("Cardinalité des colonnes", quality["cardinality"]),
                ("Recommandations", recommendations)]
    body = "".join(f"<section><h2>{escape(title)}</h2>{table(df)}</section>" for title, df in sections)
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rapport de qualité des données</title><style>body{{font-family:Arial,sans-serif;max-width:1050px;margin:36px auto;padding:0 18px;color:#213047;background:#f8fafc}}h1{{color:#123d65}}section{{background:white;padding:20px;margin:18px 0;border-radius:12px;overflow-x:auto;box-shadow:0 1px 5px #dce4ef}}table{{border-collapse:collapse;width:100%}}td,th{{padding:9px 12px;border-bottom:1px solid #e6ecf2;text-align:left}}th{{background:#edf3fa}}.note{{padding:14px;background:#fff3d5;border-left:4px solid #e6a23c}}</style></head><body>
<h1>Diagnostic de qualité des données</h1><p><strong>Fichier :</strong> {escape(filename)}</p>
<p><strong>Dimensions :</strong> {profile['lignes']} lignes × {profile['colonnes']} colonnes</p>
<p><strong>Doublons complets supplémentaires :</strong> {quality['duplicate_full_count']} | <strong>sur colonnes sélectionnées :</strong> {quality['duplicate_subset_count']}</p>
<p><strong>Colonnes sélectionnées :</strong> {escape(', '.join(map(str, quality['duplicate_subset_columns'])))}</p>
<p class="note">Diagnostic indicatif. Aucune donnée d'origine n'a été modifiée. Valider chaque correction avec un responsable métier.</p>{body}</body></html>'''.encode("utf-8")
