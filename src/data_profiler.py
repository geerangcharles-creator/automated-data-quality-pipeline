"""Profil descriptif des données."""

import pandas as pd


def profile_data(df: pd.DataFrame):
    columns = []
    for pos, name in enumerate(df.columns):
        series = df.iloc[:, pos]
        columns.append({"colonne": str(name), "type": str(series.dtype),
                        "valeurs_uniques": int(series.nunique(dropna=True)),
                        "lignes": len(series)})
    return {"lignes": int(len(df)), "colonnes": int(df.shape[1]),
            "colonnes_details": pd.DataFrame(columns),
            "apercu": df.head(10).copy(),
            "statistiques": (df.describe(include="all").transpose().astype(object).where(
                lambda table: table.notna(), "") if len(df) else pd.DataFrame())}
