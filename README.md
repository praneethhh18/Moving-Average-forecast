# Moving-Average Forecasting Demo

A lightweight Python project that demonstrates how to build a simple moving-average forecaster. The CLI stays zero-dependency by design, while an optional Streamlit UI lets you explore the same model interactively.

## How it works

Given a time series $y_t$ and window size $w$, the demo computes the rolling mean
$$MA_t = \frac{1}{w} \sum_{i=0}^{w-1} y_{t-i}$$
and extends the final window forward to produce a naive forecast. This approach is intentionally simple, making it a great starting point before moving to more advanced models.

## Project layout

```text
data/
  monthly_demand.csv   # Example input (monthly observations)
src/
  moving_average_demo.py
streamlit_app.py        # Streamlit dashboard entry point
requirements.txt        # Optional dependencies for the dashboard
```

## Prerequisites

- Python 3.9+
- (Optional) A CSV file with columns `date` (YYYY-MM-DD) and `value`

## Usage

From the repository root:

```bash
python src/moving_average_demo.py --window 4 --horizon 6 --history 8
```

### Use the bundled CSV

```bash
python src/moving_average_demo.py --data data/monthly_demand.csv --window 3 --horizon 5
```

### Point at your own data

```bash
python src/moving_average_demo.py --data path/to/series.csv --window 6 --horizon 4
```

Arguments:

- `--window`: number of observations in the moving-average window (default `3`)
- `--horizon`: number of periods to project (default `6`)
- `--history`: number of trailing rows to show in the history table (default `10`)
- `--data`: optional CSV path; falls back to a synthetic monthly signal if omitted

## Sample output

```text
Moving-average forecasting demo
Window size: 4
Forecast horizon: 5

Recent history
Date        Actual    MA
----------------------------
2023-07-01   143.40    153.20
2023-08-01   140.10    149.15
2023-09-01   138.41    144.40
2023-10-01   139.50    140.35
2023-11-01   143.81    140.45
2023-12-01   141.90    140.91

Forecast horizon
Date        Prediction
----------------------
2024-01-01      140.91
2024-02-01      141.53
2024-03-01      142.04
2024-04-01      141.59
2024-05-01      141.52

ASCII sparkline (| separates history/prediction)
 :=++-:... :-+#***+=::-+**%@@@*+++**|+****
```

## Streamlit dashboard

Bring up an interactive UI with live charts, file uploads, and CSV downloads:

```bash
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

The sidebar lets you pick the data source (synthetic signal, bundled CSV, or your own upload with `date,value` columns), adjust the moving-average window, forecast horizon, and history length. The main panel renders rich tables, an Altair line chart splitting history vs. forecast, plus a download button for the combined series. To deploy on Streamlit Community Cloud, push this repo to GitHub, create a new app targeting `streamlit_app.py`, and set the working directory to the repo root.

## Next steps

- Swap in more advanced smoothing (exponential, Holt-Winters) while keeping the interface.
- Persist the forecasts to CSV/JSON if you need to consume them downstream.
- Extend the Streamlit UI with richer charts, confidence bands, or authentication if you plan to share it broadly.
