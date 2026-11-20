"""Chargement prudent de CSV et classeurs Excel."""

from io import BytesIO
from pathlib import Path

import pandas as pd


class FileLoadError(ValueError):
    """Erreur compréhensible par l'utilisateur."""


def _read_bytes(file):
    if isinstance(file, (str, Path)):
        path = Path(file)
        name = path.name
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise FileLoadError(f"Impossible d'ouvrir le fichier : {exc}") from exc
    else:
        name = getattr(file, "name", "fichier.csv")
        if hasattr(file, "getvalue"):
            data = file.getvalue()
        else:
            file.seek(0)
            data = file.read()
    if not data:
        raise FileLoadError("Le fichier est vide (0 octet).")
    return str(name), data


def list_excel_sheets(file):
    name, data = _read_bytes(file)
    if Path(name).suffix.lower() != ".xlsx":
        raise FileLoadError("La liste des feuilles est réservée aux fichiers .xlsx.")
    try:
        return pd.ExcelFile(BytesIO(data), engine="openpyxl").sheet_names
    except Exception as exc:
        raise FileLoadError(f"Classeur Excel illisible : {exc}") from exc


def load_data(file, sheet_name=None, separator="auto", encoding="auto"):
    """Charge une copie en mémoire ; ne modifie jamais le fichier original."""
    name, data = _read_bytes(file)
    suffix = Path(name).suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        raise FileLoadError("Format non pris en charge : utiliser .csv ou .xlsx.")
    try:
        if suffix == ".xlsx":
            df = pd.read_excel(BytesIO(data), sheet_name=sheet_name if sheet_name is not None else 0,
                               engine="openpyxl")
        else:
            encodings = [encoding] if encoding != "auto" else ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
            last_exc = None
            for enc in encodings:
                try:
                    sep = None if separator == "auto" else separator
                    df = pd.read_csv(BytesIO(data), sep=sep, engine="python" if sep is None else "c",
                                     encoding=enc, on_bad_lines="error")
                    break
                except (UnicodeError, UnicodeDecodeError) as exc:
                    last_exc = exc
            else:
                raise FileLoadError(f"Encodage CSV non reconnu : {last_exc}")
    except FileLoadError:
        raise
    except pd.errors.EmptyDataError as exc:
        raise FileLoadError("Le fichier ne contient pas de colonnes exploitables.") from exc
    except Exception as exc:
        raise FileLoadError(f"Lecture impossible : {exc}") from exc
    if not isinstance(df, pd.DataFrame) or df.shape[1] == 0:
        raise FileLoadError("Aucune table exploitable n'a été trouvée.")
    return df.copy(deep=True)
