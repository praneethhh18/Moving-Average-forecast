"""Moving-average forecasting demo.

This script generates or loads a time series, computes a simple moving
average smoother, and produces short-term forecasts by extending the
moving average into the future. The output includes a tabular view of
recent history, the forecast horizon, and an ASCII sparkline so the
demo works in any terminal without external plotting libraries.
"""
from __future__ import annotations

import argparse
import calendar
import csv
import datetime as dt
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence


@dataclass
class SeriesPoint:
    """Represents a single observation in the time series."""

    date: dt.date
    value: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Moving-average forecasting demo that works with a demo dataset or a CSV."
    )
    parser.add_argument(
        "--window",
        type=int,
        default=3,
        help="Window size (number of observations) for the moving average.",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=6,
        help="How many periods ahead to forecast.",
    )
    parser.add_argument(
        "--data",
        type=Path,
        help="Optional path to a CSV with columns 'date' (YYYY-MM-DD) and 'value'.",
    )
    parser.add_argument(
        "--history",
        type=int,
        default=10,
        help="Number of historical rows to print in the summary table.",
    )
    return parser.parse_args()


def load_series_from_csv(path: Path) -> List[SeriesPoint]:
    if not path.exists():
        raise FileNotFoundError(f"Could not find data file: {path}")

    points: List[SeriesPoint] = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
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
        raise ValueError("No valid rows were found in the CSV file.")
    return points


def generate_demo_series(length: int = 36) -> List[SeriesPoint]:
    start = dt.date(2021, 1, 1)
    series: List[SeriesPoint] = []
    for i in range(length):
        date = add_months(start, i)
        seasonal = 12 * math.sin((2 * math.pi * i) / 12)
        trend = 0.9 * i
        cyclical = ((i % 5) - 2) * 1.8
        value = 120 + trend + seasonal + cyclical
        series.append(SeriesPoint(date=date, value=round(value, 2)))
    return series


def moving_average(values: Sequence[float], window: int) -> List[Optional[float]]:
    if window <= 0:
        raise ValueError("Window must be a positive integer.")
    results: List[Optional[float]] = []
    for idx in range(len(values)):
        start = max(0, idx - window + 1)
        window_slice = values[start : idx + 1]
        if len(window_slice) < window:
            results.append(None)
        else:
            results.append(sum(window_slice) / window)
    return results


def forecast(values: Sequence[float], window: int, horizon: int) -> List[float]:
    if horizon <= 0:
        return []
    history = list(values)
    forecasts: List[float] = []
    for _ in range(horizon):
        window_slice = history[-window:]
        forecasts.append(sum(window_slice) / len(window_slice))
        history.append(forecasts[-1])
    return forecasts


def add_months(date: dt.date, months: int) -> dt.date:
    year = date.year + (date.month - 1 + months) // 12
    month = (date.month - 1 + months) % 12 + 1
    day = min(date.day, calendar.monthrange(year, month)[1])
    return dt.date(year, month, day)


def select_history(points: Sequence[SeriesPoint], lookback: int) -> Sequence[SeriesPoint]:
    if lookback <= 0:
        return []
    return points[-lookback:]


def print_history_table(points: Sequence[SeriesPoint], smoothed: Sequence[Optional[float]]):
    print("\nRecent history")
    print("Date        Actual    MA")
    print("----------------------------")
    for point, ma in zip(points, smoothed[-len(points) :]):
        ma_display = f"{ma:8.2f}" if ma is not None else "    --  "
        print(f"{point.date.isoformat()}  {point.value:7.2f}  {ma_display}")


def print_forecast_table(dates: Sequence[dt.date], values: Sequence[float]):
    print("\nForecast horizon")
    print("Date        Prediction")
    print("----------------------")
    for date, value in zip(dates, values):
        print(f"{date.isoformat()}  {value:10.2f}")


SPARK_CHARS = " .:-=+*#%@"


def sparkline(values: Sequence[float]) -> str:
    if not values:
        return ""
    v_min = min(values)
    v_max = max(values)
    if v_min == v_max:
        return "=" * len(values)
    span = v_max - v_min
    scale = len(SPARK_CHARS) - 1
    chars = []
    for value in values:
        normalized = int(round(((value - v_min) / span) * scale))
        chars.append(SPARK_CHARS[normalized])
    return "".join(chars)


def print_ascii_chart(actuals: Sequence[float], forecasts: Sequence[float]):
    if not actuals:
        return
    combined = list(actuals) + list(forecasts)
    normalized = sparkline(combined)
    split_idx = len(actuals)
    history_line = normalized[:split_idx]
    future_line = normalized[split_idx:]
    print("\nASCII sparkline (| separates history/prediction)")
    print(f"{history_line}|{future_line}")


def main():
    args = parse_args()
    if args.data:
        series = load_series_from_csv(args.data)
    else:
        series = generate_demo_series()

    values = [point.value for point in series]
    smoothed = moving_average(values, args.window)
    forecasts = forecast(values, args.window, args.horizon)
    future_dates = [add_months(series[-1].date, i + 1) for i in range(args.horizon)]

    history_points = select_history(series, args.history)
    print("Moving-average forecasting demo")
    print(f"Window size: {args.window}")
    print(f"Forecast horizon: {args.horizon}")
    print_history_table(history_points, smoothed)
    print_forecast_table(future_dates, forecasts)
    print_ascii_chart(values, forecasts)


if __name__ == "__main__":
    main()
