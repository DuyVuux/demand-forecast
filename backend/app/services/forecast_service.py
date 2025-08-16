from __future__ import annotations
from io import BytesIO, StringIO
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from fastapi import UploadFile
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sqlalchemy.orm import Session
from statsmodels.tsa.arima.model import ARIMA

from ..db import save_product_customer_sales_df, save_product_sales_df
from ..utils.logger import get_logger

log = get_logger("service.forecast")


def _read_csv_upload(upload: UploadFile) -> pd.DataFrame:
    upload.file.seek(0)
    content = upload.file.read()
    try:
        s = content.decode("utf-8")
    except Exception:  # noqa: BLE001
        s = content
    if isinstance(s, bytes):
        df = pd.read_csv(BytesIO(content))
    else:
        df = pd.read_csv(StringIO(s))
    return df


def _ensure_columns(df: pd.DataFrame, cols: List[str]) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"Thiếu cột trong CSV: {missing}. Yêu cầu các cột: {cols}"
        )


def _resample_series(df: pd.DataFrame, group_cols: List[str]) -> List[Tuple[Tuple, pd.Series]]:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], utc=True, errors="coerce").dt.tz_convert(None)
    df = df.dropna(subset=["date"])
    df = df.sort_values("date")
    results: List[Tuple[Tuple, pd.Series]] = []
    for key, g in df.groupby(group_cols):
        s = (
            g.set_index("date")["quantity_sold"].astype(float).resample("D").sum().sort_index()
        )
        results.append((key if isinstance(key, tuple) else (key,), s))
    return results


def _forecast_series_arima(y: pd.Series, horizon: int) -> List[float]:
    preds = [float(y.iloc[-1]) if len(y) else 0.0] * horizon
    if len(y) < 5:
        return preds
    try:
        model = ARIMA(
            y,
            order=(1, 1, 1),
            enforce_stationarity=False,
            enforce_invertibility=False,
        )
        fit = model.fit()
        fc = fit.forecast(steps=horizon)
        return [float(max(0.0, v)) for v in fc.tolist()]
    except Exception as e:  # noqa: BLE001
        log.warning(f"ARIMA fail, fallback naive: {e}")
        return preds


def _forecast_series_regression(y: pd.Series, horizon: int, model_type: str) -> List[float]:
    df = pd.DataFrame({"y": y})
    for lag in [1, 7]:
        df[f"lag_{lag}"] = df["y"].shift(lag)
    df = df.dropna()
    if len(df) < 5:
        return [float(y.iloc[-1]) if len(y) else 0.0] * horizon
    X = df[[c for c in df.columns if c.startswith("lag_")]].values
    target = df["y"].values
    model = RandomForestRegressor(n_estimators=200, random_state=42) if model_type == "rf" else LinearRegression()
    model.fit(X, target)

    last_values = y.iloc[-7:].tolist()
    while len(last_values) < 7:
        last_values = [last_values[0]] + last_values
    preds: List[float] = []
    for _ in range(horizon):
        x_next = np.array([[last_values[-1], last_values[-7]]])
        yhat = float(model.predict(x_next)[0])
        yhat = max(0.0, yhat)
        preds.append(yhat)
        last_values.append(yhat)
        if len(last_values) > 7:
            last_values = last_values[-7:]
    return preds


def _forecast_series(y: pd.Series, horizon: int, model_type: str) -> List[float]:
    m = (model_type or "arima").lower()
    if m == "arima":
        return _forecast_series_arima(y, horizon)
    if m in ("linreg", "linear", "linear_regression"):
        return _forecast_series_regression(y, horizon, "linreg")
    if m in ("rf", "random_forest"):
        return _forecast_series_regression(y, horizon, "rf")
    return [float(y.iloc[-1]) if len(y) else 0.0] * horizon


async def forecast_by_product(
    file: UploadFile, horizon: int, model_type: str, db: Session
) -> Dict:
    df = _read_csv_upload(file)
    _ensure_columns(df, ["product_id", "date", "quantity_sold"])
    try:
        save_product_sales_df(db, df[["product_id", "date", "quantity_sold"]])
    except Exception as e:  # noqa: BLE001
        log.warning(f"Persist product_sales failed: {e}")

    series_list = _resample_series(df, ["product_id"])
    items: List[Dict] = []
    for (product_id,), s in series_list:
        preds = _forecast_series(s, horizon, model_type)
        start = (
            s.index.max() + pd.Timedelta(days=1)
            if len(s)
            else pd.Timestamp.today().normalize()
        )
        dates = pd.date_range(start, periods=horizon, freq="D")
        for d, yhat in zip(dates, preds):
            items.append(
                {
                    "product_id": str(product_id),
                    "date": d.strftime("%Y-%m-%d"),
                    "forecast": float(yhat),
                }
            )
    log.info(f"Product forecast done: groups={len(series_list)}, items={len(items)}")
    return {"forecast": items, "meta": {"horizon": horizon, "model": model_type}}


async def forecast_by_product_customer(
    file: UploadFile, horizon: int, model_type: str, db: Session
) -> Dict:
    df = _read_csv_upload(file)
    _ensure_columns(df, ["product_id", "customer_id", "date", "quantity_sold"])
    try:
        save_product_customer_sales_df(
            db, df[["product_id", "customer_id", "date", "quantity_sold"]]
        )
    except Exception as e:  # noqa: BLE001
        log.warning(f"Persist product_customer_sales failed: {e}")

    series_list = _resample_series(df, ["product_id", "customer_id"])
    items: List[Dict] = []
    for (product_id, customer_id), s in series_list:
        preds = _forecast_series(s, horizon, model_type)
        start = (
            s.index.max() + pd.Timedelta(days=1)
            if len(s)
            else pd.Timestamp.today().normalize()
        )
        dates = pd.date_range(start, periods=horizon, freq="D")
        for d, yhat in zip(dates, preds):
            items.append(
                {
                    "product_id": str(product_id),
                    "customer_id": str(customer_id),
                    "date": d.strftime("%Y-%m-%d"),
                    "forecast": float(yhat),
                }
            )
    log.info(
        f"Product-Customer forecast done: groups={len(series_list)}, items={len(items)}"
    )
    return {"forecast": items, "meta": {"horizon": horizon, "model": model_type}}
