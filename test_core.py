"""Run: python test_core.py — asserts, no framework."""
import pandas as pd

from core import fmt, pick_columns, summarise

df = pd.DataFrame({
    "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
    "amount": [100, 150, 90, 260],
    "region": ["north", "south", "north", "south"],
    "note": ["a1", "b2", "c3", "d4"],          # unique strings, not a category
})

dates, numeric, categories = pick_columns(df)
assert dates == ["date"], dates
assert numeric == ["amount"], numeric
assert categories == ["region"], categories     # 'note' is all-unique, correctly excluded

k = summarise(df["amount"])
assert k["count"] == 4 and k["total"] == 600.0
assert k["min"] == 90.0 and k["max"] == 260.0
assert round(k["change_pct"], 1) == 160.0       # 100 -> 260

assert summarise(pd.Series([], dtype=float)) == {}
assert summarise(pd.Series([None, None])) == {}
assert summarise(pd.Series([0, 5]))["change_pct"] is None    # no divide-by-zero

# a text column that pandas would happily coerce must not become a date
assert pick_columns(pd.DataFrame({"x": ["red", "blue", "red"]}))[0] == []

assert fmt(None) == "—"
assert fmt(1234.5) == "1,234.5"
assert fmt(2_500_000) == "2,500,000"

print("all checks passed")
