import pandas as pd

from src.quality_checker import check_quality
from src.recommendations import generate_recommendations
from src.report_generator import summary_csv, html_report
from src.data_profiler import profile_data


def test_constant_and_near_constant_columns():
    df = pd.DataFrame({"fixe": ["A"] * 20, "presque": ["A"] * 19 + ["B"]})
    result = check_quality(df)
    flags = result["constant_columns"].set_index("colonne")
    assert bool(flags.loc["fixe", "constante"])
    assert bool(flags.loc["presque", "quasi_constante"])


def test_invalid_dates_and_mixed_formats():
    df = pd.DataFrame({"date_achat": ["2026-01-03", "03/01/2026", "2026-02-30"],
                       "email": ["a@example.org", "wrong-email", None]})
    flags = check_quality(df)["format_issues"].set_index("colonne")
    assert flags.loc["date_achat", "formats_suspects"] >= 2
    assert flags.loc["email", "formats_suspects"] == 1


def test_whitespace_case_numbers_and_exports():
    df = pd.DataFrame({"ville": [" Kinshasa ", "kinshasa", "KINSHASA"],
                       "montant": [-10, 0, 100]})
    original = df.copy(deep=True)
    result = check_quality(df)
    assert result["extra_spaces"].set_index("colonne").loc["ville", "espaces_parasites"] == 1
    assert result["case_inconsistencies"].set_index("colonne").loc["ville", "variantes_casse"] == 2
    assert result["numeric_signs"].set_index("colonne").loc["montant", "valeurs_negatives"] == 1
    assert result["numeric_signs"].set_index("colonne").loc["montant", "valeurs_zero"] == 1
    advice = generate_recommendations(df, result)
    assert "Espaces parasites" in advice["anomalie"].tolist()
    assert b"colonne_constante" in summary_csv(result)
    assert b"Formats suspects" in html_report(profile_data(df), result, advice)
    pd.testing.assert_frame_equal(df, original)
