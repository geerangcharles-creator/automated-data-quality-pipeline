import pandas as pd
import pytest

from src.outlier_explorer import explore_outliers


def test_explorer_preserves_context_and_source():
    df = pd.DataFrame({"Quantity": [-100, 1, 2, 60], "InvoiceNo": ["A", "B", "C", "D"]})
    before = df.copy(deep=True)
    result = explore_outliers(df, "Quantity", -10, 20)
    assert result["InvoiceNo"].tolist() == ["A", "D"]
    assert result.index.tolist() == [0, 3]
    pd.testing.assert_frame_equal(df, before)


def test_explorer_direction():
    df = pd.DataFrame({"Quantity": [-100, 1, 60]})
    assert explore_outliers(df, "Quantity", -10, 20, "Inférieures").index.tolist() == [0]
    assert explore_outliers(df, "Quantity", -10, 20, "Supérieures").index.tolist() == [2]


def test_explorer_ignores_missing_and_invalid_limits():
    df = pd.DataFrame({"Quantity": [None, 2.0, 300.0]})
    assert len(explore_outliers(df, "Quantity", -10, 20)) == 1
    assert explore_outliers(df, "Quantity", float("nan"), 20).empty


def test_explorer_rejects_text_columns():
    with pytest.raises(ValueError):
        explore_outliers(pd.DataFrame({"code": ["A", "B"]}), "code", 0, 1)
