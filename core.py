"""Pure helpers — no streamlit, so they can be tested with plain python."""
from __future__ import annotations

import pandas as pd

MAX_CATEGORIES = 50  # more distinct values than this and it isn't a category


def pick_columns(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    """Split columns into (date-like, numeric, categorical).

    A column can land in more than one bucket — the caller picks.
    """
    dates, numeric, categories = [], [], []
    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            numeric.append(col)
            continue
        if pd.api.types.is_datetime64_any_dtype(s):
            dates.append(col)
            continue
        # object/string: parseable as a date, or low-cardinality enough to group by?
        parsed = pd.to_datetime(s, errors="coerce", format="mixed")
        if parsed.notna().mean() > 0.8:
            dates.append(col)
        elif 0 < s.nunique(dropna=True) <= min(MAX_CATEGORIES, max(1, len(s) // 2)):
            categories.append(col)
    return dates, numeric, categories


def summarise(s: pd.Series) -> dict:
    """KPIs for one numeric column. Empty/all-NaN input gives an empty dict."""
    s = pd.to_numeric(s, errors="coerce").dropna()
    if s.empty:
        return {}
    first, last = s.iloc[0], s.iloc[-1]
    return {
        "count": int(s.size),
        "total": float(s.sum()),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "min": float(s.min()),
        "max": float(s.max()),
        "change_pct": float((last - first) / abs(first) * 100) if first else None,
    }


def fmt(v: float | None, nd: int = 2) -> str:
    if v is None:
        return "—"
    if abs(v) >= 1e6:
        return f"{v:,.0f}"
    return f"{v:,.{nd}f}".rstrip("0").rstrip(".") if nd else f"{v:,.0f}"
