"""Conseils traçables, jamais appliqués automatiquement."""

import pandas as pd


def generate_recommendations(df, quality):
    advice = []
    for _, item in quality["missing"].iterrows():
        if not item["manquantes"]:
            continue
        col = item["colonne"]
        original = df[col]
        name = col.lower()
        if any(token in name for token in ("id", "code", "clé", "key")):
            action = "Vérifier la source et l'unicité ; ne pas inventer ou moyenner un identifiant."
        elif any(token in name for token in ("date", "time", "heure")):
            action = "Vérifier le format et la source ; ne pas remplacer arbitrairement la date."
        elif any(token in name for token in ("prix", "montant", "amount", "total", "revenue", "cost")):
            action = "Vérifier avec les pièces métier ; zéro et moyenne pourraient fausser les résultats financiers."
        elif pd.api.types.is_numeric_dtype(original):
            action = "Étudier la cause ; envisager médiane ou exclusion après vérification de l'impact."
        else:
            action = "Étudier la cause ; envisager une catégorie 'Inconnu' seulement si le métier le permet."
        advice.append({"anomalie": "Valeurs manquantes", "colonne": col,
                       "constat": f"{item['manquantes']} ({item['pourcentage']} %)", "recommandation": action})
    for _, item in quality["empty_strings"].iterrows():
        if item["chaines_vides"]:
            advice.append({"anomalie": "Chaînes vides", "colonne": item["colonne"],
                           "constat": str(item["chaines_vides"]),
                           "recommandation": "Confirmer si les espaces/chaînes vides désignent des valeurs manquantes."})
    for _, item in quality["suspect_types"].iterrows():
        if item["valeurs_suspectes"]:
            advice.append({"anomalie": "Types hétérogènes", "colonne": item["colonne"],
                           "constat": str(item["valeurs_suspectes"]),
                           "recommandation": "Examiner les exemples et le sens métier avant toute conversion."})
    for _, item in quality["outliers"].iterrows():
        if item["valeurs_atypiques"]:
            advice.append({"anomalie": "Valeurs atypiques (IQR)", "colonne": item["colonne"],
                           "constat": str(item["valeurs_atypiques"]),
                           "recommandation": "Contrôler les valeurs extrêmes ; elles peuvent être valides. Ne pas supprimer automatiquement."})
    for _, item in quality["constant_columns"].iterrows():
        if item["constante"] or item["quasi_constante"]:
            advice.append({"anomalie": "Colonne constante ou quasi constante", "colonne": item["colonne"],
                           "constat": "Constante" if item["constante"] else "Au moins 95 % identiques",
                           "recommandation": "Vérifier l'utilité analytique avant toute exclusion ; une constante peut être métier."})
    for _, item in quality["format_issues"].iterrows():
        if item["formats_suspects"]:
            advice.append({"anomalie": "Format incohérent", "colonne": item["colonne"],
                           "constat": f"{item['formats_suspects']} valeur(s) : {item['detail']}",
                           "recommandation": "Contrôler le format attendu et les valeurs sources avant toute conversion."})
    for _, item in quality["extra_spaces"].iterrows():
        if item["espaces_parasites"]:
            advice.append({"anomalie": "Espaces parasites", "colonne": item["colonne"],
                           "constat": str(item["espaces_parasites"]),
                           "recommandation": "Comparer les valeurs avant/après suppression des espaces en bordure."})
    for _, item in quality["case_inconsistencies"].iterrows():
        if item["variantes_casse"]:
            advice.append({"anomalie": "Variantes de casse", "colonne": item["colonne"],
                           "constat": str(item["variantes_casse"]),
                           "recommandation": "Vérifier si majuscules et minuscules doivent désigner la même catégorie."})
    for _, item in quality["numeric_signs"].iterrows():
        if item["valeurs_negatives"] or item["valeurs_zero"]:
            advice.append({"anomalie": "Valeurs numériques à vérifier", "colonne": item["colonne"],
                           "constat": f"{item['valeurs_negatives']} négative(s), {item['valeurs_zero']} nulle(s)",
                           "recommandation": "Contrôler les règles métier : montants négatifs et zéros peuvent être légitimes."})
    for _, item in quality["cardinality"].iterrows():
        if item["cardinalite_elevee"]:
            advice.append({"anomalie": "Cardinalité élevée", "colonne": item["colonne"],
                           "constat": f"{item['pourcentage_uniques']} % de valeurs distinctes",
                           "recommandation": "Déterminer s'il s'agit d'un identifiant ou d'une variable peu adaptée à un regroupement."})
    if quality["duplicate_full_count"]:
        advice.append({"anomalie": "Doublons complets", "colonne": "Toutes",
                       "constat": str(quality["duplicate_full_count"]),
                       "recommandation": "Comparer les clés métier et les transactions : répétition technique ≠ erreur métier."})
    if quality["duplicate_subset_count"]:
        advice.append({"anomalie": "Doublons sur colonnes choisies", "colonne": ", ".join(map(str, quality["duplicate_subset_columns"])),
                       "constat": str(quality["duplicate_subset_count"]),
                       "recommandation": "Vérifier si ces colonnes forment réellement une clé unique ; ne rien supprimer sans validation."})
    return pd.DataFrame(advice, columns=["anomalie", "colonne", "constat", "recommandation"])
