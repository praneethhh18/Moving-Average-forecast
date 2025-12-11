"""Streamlit UI for the moving-average forecasting demo."""
from __future__ import annotations

import csv
import datetime as dt
import io
from pathlib import Path
from typing import List, Optional, Sequence

import altair as alt
import pandas as pd
import streamlit as st

from src.moving_average_demo import (
    SeriesPoint,
    add_months,
    forecast,
    generate_demo_series,
    load_series_from_csv,
    moving_average,
)

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE_CSV = DATA_DIR / "monthly_demand.csv"


def parse_uploaded_csv(buffer: object) -> List[SeriesPoint]:
    """Convert uploaded bytes into the SeriesPoint structure."""

    if hasattr(buffer, "getvalue"):
        raw_bytes = buffer.getvalue()
    elif isinstance(buffer, (bytes, bytearray)):
        raw_bytes = buffer
    else:
        raise ValueError("Unsupported upload payload; expected bytes-like object.")

    text = raw_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    points: List[SeriesPoint] = []
    for row in reader:
        if not row.get("date") or not row.get("value"):
            continue
        points.append(
            SeriesPoint(
                date=dt.date.fromisoformat(row["date"].strip()),
                value=float(row["value"].strip()),
            )
        )

    points.sort(key=lambda p: p.date)
    if not points:
        raise ValueError("No valid rows detected in the uploaded CSV.")
    return points


def make_history_frame(points: Sequence[SeriesPoint], smoothed: Sequence[Optional[float]]) -> pd.DataFrame:
    lookback = len(points)
    history_ma = smoothed[-lookback:]
    return pd.DataFrame(
        {
            "Date": [p.date for p in points],
            "Actual": [p.value for p in points],
            "Moving Average": history_ma,
        }
    )


def make_forecast_frame(dates: Sequence[dt.date], predictions: Sequence[float]) -> pd.DataFrame:
    return pd.DataFrame({"Date": dates, "Prediction": predictions})


def make_chart(history_dates: Sequence[dt.date], future_dates: Sequence[dt.date],
               history_values: Sequence[float], forecasts: Sequence[float]) -> alt.Chart:
    chart_df = pd.DataFrame(
        {
            "date": list(history_dates) + list(future_dates),
            "value": list(history_values) + list(forecasts),
            "series": ["History"] * len(history_values) + ["Forecast"] * len(forecasts),
        }
    )
    return (
        alt.Chart(chart_df)
        .mark_line(point=True)
        .encode(x="date:T", y="value:Q", color="series:N")
        .properties(height=340)
    )


def main() -> None:
    st.set_page_config(page_title="Moving-Average Forecasts", layout="wide")
    st.title("Moving-Average Forecasting Demo")
    st.caption("Tune the smoothing window, forecast horizon, and data source to explore the naive moving-average forecaster.")

    with st.sidebar:
        st.header("Controls")
        window = st.slider("Window size", min_value=2, max_value=12, value=3)
        horizon = st.slider("Forecast horizon", min_value=1, max_value=24, value=6)
        history_rows = st.slider("History rows", min_value=6, max_value=36, value=12)
        source = st.selectbox(
            "Data source",
            ["Synthetic signal", "Bundled CSV sample", "Upload your CSV"],
        )
        uploaded_file = None
        if source == "Upload your CSV":
            uploaded_file = st.file_uploader("CSV with columns date,value", type="csv")

    if source == "Synthetic signal":
        series = generate_demo_series(length=48)
    elif source == "Bundled CSV sample":
        if not SAMPLE_CSV.exists():
            st.error("Sample CSV is missing from the data/ directory.")
            st.stop()
        series = load_series_from_csv(SAMPLE_CSV)
    else:
        if uploaded_file is None:
            st.info("Upload a CSV file to continue.")
            st.stop()
        try:
            series = parse_uploaded_csv(uploaded_file)
        except ValueError as exc:
            st.error(str(exc))
            st.stop()

    values = [point.value for point in series]
    smoothed = moving_average(values, window)
    forecasts = forecast(values, window, horizon)
    future_dates = [add_months(series[-1].date, i + 1) for i in range(horizon)]
    history_points = series[-history_rows:]

    col1, col2 = st.columns(2)
    col1.metric("Last actual", f"{series[-1].value:.2f}", delta=None)
    col2.metric("Next forecast", f"{forecasts[0]:.2f}" if forecasts else "n/a")

    st.subheader("Recent history")
    st.dataframe(make_history_frame(history_points, smoothed), hide_index=True, use_container_width=True)

    st.subheader("Forecast horizon")
    forecast_frame = make_forecast_frame(future_dates, forecasts)
    st.dataframe(forecast_frame, hide_index=True, use_container_width=True)

    st.subheader("Chart")
    chart = make_chart([p.date for p in series], future_dates, values, forecasts)
    st.altair_chart(chart, use_container_width=True)

    combined = pd.concat(
        [
            pd.DataFrame({"date": [p.date for p in series], "value": values, "series": "history"}),
            pd.DataFrame({"date": future_dates, "value": forecasts, "series": "forecast"}),
        ],
        ignore_index=True,
    )
    csv_payload = combined.to_csv(index=False).encode("utf-8")
    st.download_button("Download combined series", data=csv_payload, file_name="moving_average_forecast.csv", mime="text/csv")


if __name__ == "__main__":
    main()
