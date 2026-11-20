"""Contrôles génériques et prudents, sans interprétation métier automatique."""

import pandas as pd
import re
from datetime import datetime


def _format_issues(name, values):
    """Règles conservatrices : dates / emails et mélange de formats de dates."""
    label = str(name).lower()
    texts = [value.strip() for value in values if isinstance(value, str) and value.strip()]
    if not texts:
        return 0, ""
    if "email" in label or "e-mail" in label or "courriel" in label:
        pattern = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
        return sum(not bool(pattern.fullmatch(value)) for value in texts), "Format d'adresse électronique suspect"
    if any(token in label for token in ("date", "naissance", "échéance")):
        formats = (("ISO", "%Y-%m-%d", r"\d{4}-\d{2}-\d{2}"),
                   ("FR/US", "%d/%m/%Y", r"\d{2}/\d{2}/\d{4}"),
                   ("Tirets", "%d-%m-%Y", r"\d{2}-\d{2}-\d{4}"))
        recognized, invalid = set(), 0
        for value in texts:
            matching = next(((label, fmt) for label, fmt, regex in formats if re.fullmatch(regex, value)), None)
            if matching is None:
                invalid += 1
                continue
            recognized.add(matching[0])
            try:
                datetime.strptime(value, matching[1])
            except ValueError:
                invalid += 1
        return invalid + (len(texts) - invalid if len(recognized) > 1 else 0), (
            "Dates invalides ou formats mélangés (attention aux jours/mois ambigus)" if len(recognized) > 1
            else "Date invalide ou format non reconnu")
    return 0, ""


def check_duplicates(df: pd.DataFrame, subset=None):
    """Ne calcule que les doublons, sans relancer les autres contrôles de qualité."""
    if not df.columns.is_unique:
        raise ValueError("Les noms des colonnes doivent être uniques.")
    selected = list(subset) if subset else list(df.columns)
    if any(column not in df.columns for column in selected):
        raise ValueError("Une colonne sélectionnée n'existe pas.")
    full_mask = df.duplicated(keep=False)
    same_key = selected == list(df.columns)
    selected_mask = full_mask if same_key else df.duplicated(subset=selected, keep=False)
    extra_full = int(df.duplicated(keep="first").sum())
    extra_selected = extra_full if same_key else int(df.duplicated(subset=selected, keep="first").sum())
    return {
        "duplicate_full_count": extra_full,
        "duplicate_full_affected": int(full_mask.sum()),
        "duplicate_subset_count": extra_selected,
        "duplicate_subset_affected": int(selected_mask.sum()),
        "duplicate_subset_columns": selected,
        "duplicate_full_indices": df.index[full_mask].tolist(),
        "duplicate_subset_indices": df.index[selected_mask].tolist(),
        "duplicate_full_rows": df.loc[full_mask].copy(),
        "duplicate_subset_rows": df.loc[selected_mask].copy(),
    }


def check_quality(df: pd.DataFrame, subset=None, include_duplicates=True):
    if not df.columns.is_unique:
        raise ValueError("Les noms des colonnes doivent être uniques pour le diagnostic.")
    if subset and any(col not in df.columns for col in subset):
        raise ValueError("Une colonne sélectionnée n'existe pas.")
    selected = list(subset) if subset else list(df.columns)
    null_rows, empty_rows, suspect_rows, outlier_rows = [], [], [], []
    constant_rows, format_rows, spaces_rows, numeric_rows, cardinality_rows, case_rows = [], [], [], [], [], []
    for name in df.columns:
        series = df[name]
        missing = series.isna()
        is_text = series.map(lambda x: isinstance(x, str))
        empty = series.map(lambda x: isinstance(x, str) and not x.strip())
        nonmissing = series[~missing & ~empty]
        unique_count = int(nonmissing.nunique(dropna=True))
        constant_rows.append({"colonne": str(name), "valeurs_distinctes": unique_count,
                              "constante": unique_count == 1 and len(nonmissing) > 0,
                              "quasi_constante": bool(len(nonmissing) >= 10 and unique_count > 1 and
                                                     nonmissing.value_counts(dropna=False).iloc[0] / len(nonmissing) >= .95)})
        formats_count, formats_detail = _format_issues(name, nonmissing)
        format_rows.append({"colonne": str(name), "formats_suspects": formats_count, "detail": formats_detail})
        spaces_count = int(series.map(lambda x: isinstance(x, str) and bool(x) and x != x.strip()).sum())
        spaces_rows.append({"colonne": str(name), "espaces_parasites": spaces_count})
        if bool(is_text.any()):
            text_values = [str(x).strip() for x in nonmissing if isinstance(x, str)]
            normalized = {x.casefold() for x in text_values}
            raw = set(text_values)
            case_rows.append({"colonne": str(name), "variantes_casse": max(0, len(raw) - len(normalized))})
        else:
            case_rows.append({"colonne": str(name), "variantes_casse": 0})
        cardinality_rows.append({"colonne": str(name), "valeurs_uniques": unique_count,
                                 "pourcentage_uniques": round(unique_count / len(nonmissing) * 100, 2) if len(nonmissing) else 0.0,
                                 "cardinalite_elevee": bool(len(nonmissing) >= 20 and unique_count / len(nonmissing) >= .90)})
        numeric_count = int(pd.to_numeric(nonmissing, errors="coerce").notna().sum())
        nonmissing_count = len(nonmissing)
        # Texte numérique mêlé à du texte non numérique : signal, pas correction.
        suspicious_count = (nonmissing_count - numeric_count if
                            0 < numeric_count < nonmissing_count and bool(is_text.any()) else 0)
        null_rows.append({"colonne": str(name), "manquantes": int(missing.sum()),
                          "pourcentage": round(float(missing.mean() * 100), 2) if len(df) else 0.0})
        empty_rows.append({"colonne": str(name), "chaines_vides": int(empty.sum()),
                           "pourcentage": round(float(empty.mean() * 100), 2) if len(df) else 0.0})
        suspect_rows.append({"colonne": str(name), "valeurs_suspectes": suspicious_count,
                             "detail": "Valeurs numériques et non numériques mélangées" if suspicious_count else ""})
        # IQR uniquement sur colonnes réellement numériques, avec assez de valeurs.
        numbers = series if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series) else None
        count, low, high = 0, None, None
        if numbers is not None:
            valid = pd.to_numeric(numbers, errors="coerce").dropna()
            if len(valid) >= 4 and valid.nunique() >= 2:
                q1, q3 = valid.quantile([.25, .75])
                iqr = q3 - q1
                if iqr > 0:
                    low, high = float(q1 - 1.5 * iqr), float(q3 + 1.5 * iqr)
                    count = int(((valid < low) | (valid > high)).sum())
            numeric_rows.append({"colonne": str(name), "valeurs_negatives": int((valid < 0).sum()),
                                 "valeurs_zero": int((valid == 0).sum())})
        else:
            numeric_rows.append({"colonne": str(name), "valeurs_negatives": 0, "valeurs_zero": 0})
        outlier_rows.append({"colonne": str(name), "valeurs_atypiques": count,
                             "borne_basse": low, "borne_haute": high})
    return {
        "missing": pd.DataFrame(null_rows), "empty_strings": pd.DataFrame(empty_rows),
        "suspect_types": pd.DataFrame(suspect_rows), "outliers": pd.DataFrame(outlier_rows),
        "constant_columns": pd.DataFrame(constant_rows), "format_issues": pd.DataFrame(format_rows),
        "extra_spaces": pd.DataFrame(spaces_rows), "numeric_signs": pd.DataFrame(numeric_rows),
        "cardinality": pd.DataFrame(cardinality_rows), "case_inconsistencies": pd.DataFrame(case_rows),
        **(check_duplicates(df, selected) if include_duplicates else {}),
    }
