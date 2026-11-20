import pandas as pd

from src.data_profiler import profile_data
from src.quality_checker import check_quality, check_duplicates
from src.recommendations import generate_recommendations
from src.report_generator import html_report, summary_csv


def sample():
    return pd.DataFrame({"id": [1, 1, 2, 3], "age": [20, 20, None, 40],
                         "ville": ["Paris", "Paris", "  ", "Lyon"]})


def test_counts_and_missing():
    df = sample()
    p = profile_data(df)
    q = check_quality(df, ["id"])
    assert (p["lignes"], p["colonnes"]) == (4, 3)
    assert q["missing"].set_index("colonne").loc["age", "manquantes"] == 1
    assert q["missing"].set_index("colonne").loc["age", "pourcentage"] == 25.0
    assert q["empty_strings"].set_index("colonne").loc["ville", "chaines_vides"] == 1


def test_duplicates_and_unmodified():
    df = sample()
    before = df.copy(deep=True)
    q = check_quality(df, ["id"])
    assert q["duplicate_full_count"] == 1
    assert q["duplicate_full_affected"] == 2
    assert q["duplicate_subset_count"] == 1
    pd.testing.assert_frame_equal(df, before)


def test_subset_differs_from_full():
    df = pd.DataFrame({"id": [1, 1], "montant": [10, 20]})
    q = check_quality(df, ["id"])
    assert q["duplicate_full_count"] == 0
    assert q["duplicate_subset_count"] == 1


def test_duplicates_only_keeps_exact_results():
    df = sample()
    full = check_quality(df, ["id"])
    isolated = check_duplicates(df, ["id"])
    assert isolated["duplicate_full_count"] == full["duplicate_full_count"]
    assert isolated["duplicate_subset_count"] == full["duplicate_subset_count"]
    assert isolated["duplicate_subset_indices"] == full["duplicate_subset_indices"]
    without_duplicates = check_quality(df, include_duplicates=False)
    assert "duplicate_full_count" not in without_duplicates


def test_empty_dataframe_and_reports():
    df = pd.DataFrame(columns=["id", "montant"])
    q = check_quality(df)
    assert q["duplicate_full_count"] == 0
    assert q["missing"]["pourcentage"].tolist() == [0, 0]
    advice = generate_recommendations(df, q)
    assert b"doublon_complet" in summary_csv(q)
    assert b"<html" in html_report(profile_data(df), q, advice)


def test_recommendations_never_edit_data():
    df = sample()
    before = df.copy(deep=True)
    q = check_quality(df)
    advice = generate_recommendations(df, q)
    assert len(advice) > 0
    pd.testing.assert_frame_equal(df, before)


def test_html_escapes_untrusted_filename():
    df = sample()
    q = check_quality(df)
    html = html_report(profile_data(df), q, generate_recommendations(df, q), '<script>alert(1)</script>')
    assert b"&lt;script&gt;" in html
    assert b"<script>" not in html
