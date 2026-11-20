from io import BytesIO

import pandas as pd
import pytest

from src.file_loader import FileLoadError, list_excel_sheets, load_data


def uploaded(name, content):
    buf = BytesIO(content)
    buf.name = name
    return buf


def test_csv_empty_file():
    with pytest.raises(FileLoadError, match="vide"):
        load_data(uploaded("vide.csv", b""))


def test_csv_missing_data():
    df = load_data(uploaded("donnees.csv", b"id,montant\n1,\n2,10\n"))
    assert df["montant"].isna().sum() == 1


def test_invalid_extension():
    with pytest.raises(FileLoadError, match="Format"):
        load_data(uploaded("notes.txt", b"id\n1"))


def test_xlsx_sheet_choice():
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame({"a": [1]}).to_excel(writer, sheet_name="Une", index=False)
        pd.DataFrame({"b": [2]}).to_excel(writer, sheet_name="Deux", index=False)
    file = uploaded("classeur.xlsx", buf.getvalue())
    assert list_excel_sheets(file) == ["Une", "Deux"]
    assert load_data(file, sheet_name="Deux").columns.tolist() == ["b"]
