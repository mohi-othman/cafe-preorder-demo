import pytest

from app.money import halalas_to_sar, sar_to_halalas


@pytest.mark.parametrize("text, halalas", [
    ("18.50", 1850),
    ("18.5", 1850),
    ("18", 1800),
    ("0", 0),
    ("0.01", 1),
    ("0.29", 29),  # float(0.29) * 100 == 28.999999999999996
    ("1.15", 115),  # float(1.15) * 100 == 114.99999999999999
    (" 75.00 ", 7500),
    ("١٨٫٥٠", 1850),  # Arabic-Indic digits and decimal separator
    ("١٢", 1200),
])
def test_sar_text_becomes_whole_halalas(text, halalas):
    assert sar_to_halalas(text) == halalas


@pytest.mark.parametrize("text", ["", " ", "-1", "18.505", "18,50", "abc", "1e3", ".5", "18.", "100000.01", "nan"])
def test_bad_sar_text_is_rejected(text):
    with pytest.raises(ValueError):
        sar_to_halalas(text)


@pytest.mark.parametrize("halalas, text", [(1850, "18.50"), (1800, "18.00"), (1, "0.01"), (0, "0.00"), (7505, "75.05")])
def test_halalas_become_sar_text(halalas, text):
    assert halalas_to_sar(halalas) == text
