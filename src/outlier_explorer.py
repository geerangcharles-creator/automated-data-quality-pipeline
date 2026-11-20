"""Investigation ciblée des valeurs IQR avec conservation du contexte des lignes."""

import pandas as pd


def explore_outliers(df: pd.DataFrame, column: str, lower: float, upper: float, direction="Tous"):
    """Renvoie une copie des lignes atypiques, sans modifier le dataset original.

    Les limites viennent du même diagnostic IQR que le tableau de contrôle.
    """
    if column not in df.columns:
        raise ValueError("Colonne absente du jeu de données.")
    if not pd.api.types.is_numeric_dtype(df[column]) or pd.api.types.is_bool_dtype(df[column]):
        raise ValueError("L'exploration IQR nécessite une colonne numérique.")
    if pd.isna(lower) or pd.isna(upper):
        return df.iloc[0:0].copy()
    values = pd.to_numeric(df[column], errors="coerce")
    below, above = values < lower, values > upper
    if direction == "Inférieures":
        mask = below
    elif direction == "Supérieures":
        mask = above
    elif direction == "Tous":
        mask = below | above
    else:
        raise ValueError("Direction inconnue.")
    return df.loc[mask].copy()
