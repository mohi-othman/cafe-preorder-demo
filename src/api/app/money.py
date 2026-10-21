"""SAR text (what the admin types) <-> whole halalas (what the database stores). No floats."""

import re

MAX_HALALAS = 100_000_00  # 100,000 SAR; keeps prices far from the integer column limit

_ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩٫", "0123456789.")
_SAR = re.compile(r"(\d+)(?:\.(\d{1,2}))?")


def sar_to_halalas(text: str) -> int:
    """'18.50' -> 1850. Accepts Arabic-Indic digits. Raises ValueError for anything else."""
    m = _SAR.fullmatch(text.strip().translate(_ARABIC_DIGITS))
    if m is None:
        raise ValueError("Price must be a number in SAR with at most 2 decimals, e.g. 18.50")
    whole, fraction = m.groups()
    halalas = int(whole) * 100 + int((fraction or "0").ljust(2, "0"))
    if halalas > MAX_HALALAS:
        raise ValueError("Price is too high")
    return halalas


def halalas_to_sar(halalas: int) -> str:
    """1850 -> '18.50'."""
    return f"{halalas // 100}.{halalas % 100:02d}"
