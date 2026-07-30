# CSV Dashboard

Upload a spreadsheet, get a dashboard. Pick the date column, the number that
matters, and how to group it — charts and a summary table follow.

Aimed at arts organisations: the recurring job of turning a programme
spreadsheet into the attendance-and-budget breakdown a funder asks for.

## Run

```bash
/opt/anaconda3/bin/streamlit run ~/csv-dashboard/app.py
```

Uses the anaconda python, which already has streamlit, pandas and altair — no
venv, no installs, no disk cost.

## Check

```bash
/opt/anaconda3/bin/python3 ~/csv-dashboard/test_core.py
```

Asserts on the column-detection and KPI logic. No framework.

## Files

| File | What |
|---|---|
| `app.py` | The streamlit UI |
| `core.py` | Pure logic — column detection, KPIs, number formatting |
| `test_core.py` | Self-check |
| `sample_arts_programme.csv` | Fake festival programme, 179 rows, for the demo button |

## What it does

- Detects which columns are dates, numbers and categories — no configuration.
- Time chart bucketed by day/week/month (month by default — that's what funders
  ask for), grouped by any category.
- Bar chart and a **summary table of every numeric column per group**, which is
  the thing people currently assemble by hand. Downloadable as CSV.

## Next, when a real client turns up

- Swap the sample for one from *their* world before you show them.
- Excel input: `pd.read_excel` is one line, needs `openpyxl`.
- PDF export is the most likely first ask — not built.
- Multiple value columns in the charts — the summary table already does all of
  them, the charts still take one at a time.
