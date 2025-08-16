from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import json
import time

from ..utils.logger import get_logger

log = get_logger("service.sku_forecast")

# Directory containing SKU-level forecast JSON files
DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "model_result"
    / "DemandForecast_Skus"
)

_cache: Dict = {"mtime": None, "_sku_models": [], "records": [], "lookup_map": {}}


def _dir_mtime(path: Path) -> float:
    if not path.exists():
        return 0.0
    latest = 0.0
    for p in path.glob("*.json"):
        try:
            latest = max(latest, p.stat().st_mtime)
        except Exception:  # noqa: BLE001
            pass
    return latest


def _normalize_date(ds: Optional[str]) -> str:
    if not ds:
        return ""
    return str(ds)[:10]


def _as_float(v) -> Optional[float]:
    try:
        return float(v)
    except Exception:  # noqa: BLE001
        return None


def _load_files() -> List[Dict]:
    records: List[Dict] = []
    if not DATA_DIR.exists():
        log.warning(f"SKU result directory not found: {DATA_DIR}")
        return records

    for fp in DATA_DIR.glob("*.json"):
        try:
            with fp.open("r", encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as e:  # noqa: BLE001
            log.exception(f"Failed to read {fp}: {e}")
            continue

        rows = payload if isinstance(payload, list) else [payload]
        for rec in rows:
            product_code = rec.get("product_code") or rec.get("ProductCode")
            # Cast to string to keep consistency in frontend filters
            if product_code is not None:
                product_code = str(product_code)

            model = rec.get("model") or rec.get("Model")

            # metrics can be nested or flattened
            metrics_obj = rec.get("metrics") or {}
            mae = metrics_obj.get("MAE", rec.get("MAE"))
            rmse = metrics_obj.get("RMSE", rec.get("RMSE"))
            mape = metrics_obj.get("MAPE", rec.get("MAPE"))
            metrics = {
                "MAE": _as_float(mae),
                "RMSE": _as_float(rmse),
                "MAPE": _as_float(mape),
            }

            train_end_date = _normalize_date(
                rec.get("train_end_date")
                or rec.get("TrainEndDate")
                or rec.get("LastTrainDate")
            )

            # History: list of {date, actual}
            history_list: List[Dict] = []
            history_src = rec.get("history") or rec.get("actuals") or rec.get("historical")
            if isinstance(history_src, list):
                for h in history_src:
                    d = _normalize_date(h.get("date") or h.get("ds"))
                    a = h.get("actual") if "actual" in h else h.get("y")
                    history_list.append({"date": d, "actual": _as_float(a)})
            # sort history
            history_list = sorted([h for h in history_list if h.get("date")], key=lambda x: x["date"])  # type: ignore

            # Forecast: list of {date, forecast, lower_80, upper_80}
            forecast_list: List[Dict] = []
            fc_src = rec.get("forecast") or rec.get("forecasts") or []
            if isinstance(fc_src, list):
                for r in fc_src:
                    d = _normalize_date(r.get("date") or r.get("Week") or r.get("ds"))
                    if train_end_date and d and d <= train_end_date:
                        # ignore any points that sit in train range
                        continue
                    y = r.get("forecast") if "forecast" in r else (r.get("yhat"))
                    lo = r.get("lower_80") if "lower_80" in r else (r.get("yhat_lower_80") or r.get("lower80"))
                    up = r.get("upper_80") if "upper_80" in r else (r.get("yhat_upper_80") or r.get("upper80"))
                    forecast_list.append(
                        {
                            "date": d,
                            "forecast": _as_float(y),
                            "lower_80": _as_float(lo),
                            "upper_80": _as_float(up),
                        }
                    )
            # sort forecast
            forecast_list = sorted([r for r in forecast_list if r.get("date")], key=lambda x: x["date"])  # type: ignore

            item = {
                "product_code": product_code,
                "model": model,
                "metrics": metrics,
                "train_end_date": train_end_date,
                "history": history_list,
                "forecast": forecast_list,
            }
            records.append(item)

    # Build a lookup map for faster access
    # { product_code: { model_name: record } }
    lookup_map = {}
    for item in records:
        pc = item.get("product_code")
        mdl = item.get("model")
        if not pc or not mdl:
            continue

        # Normalize model name for robust matching
        mdl_key = str(mdl).strip().lower()

        if pc not in lookup_map:
            lookup_map[pc] = {}
        lookup_map[pc][mdl_key] = item

    return records, lookup_map


def load_sku_records(force_reload: bool = False) -> List[Dict]:
    start = time.perf_counter()
    mtime = _dir_mtime(DATA_DIR)
    if not force_reload and _cache.get("mtime") == mtime and _cache.get("lookup_map"):
        return _cache["records"]

    records, lookup_map = _load_files()
    all_models = set()
    for record in records:
        model_name = record.get("model")
        if model_name:
            # Normalize common typo
            if model_name.strip().lower() == 'lighgbm':
                all_models.add('LightGBM')
            else:
                all_models.add(model_name.strip())
    _cache["_sku_models"] = sorted(list(all_models))

    _cache["mtime"] = mtime
    _cache["records"] = records
    _cache["lookup_map"] = lookup_map
    dur = (time.perf_counter() - start) * 1000
    log.info(
        f"Loaded SKU results: files={len(list(DATA_DIR.glob('*.json')))} records={len(records)} ({dur:.1f} ms)"
    )
    return records


def find_sku_forecast_record(product_code: str, model: str) -> Optional[Dict]:
    """Finds a specific SKU forecast record from the cache."""
    # Ensure cache is populated and up-to-date
    load_sku_records()

    lookup_map = _cache.get("lookup_map", {})

    # Normalize inputs for matching
    p_code_key = str(product_code).strip()
    model_key = model.strip().lower()

    # Handle common typo: LighGBM vs LightGBM
    record = lookup_map.get(p_code_key, {}).get(model_key)
    if record:
        return record
    
    # If user asks for 'lightgbm' but data has 'lighgbm', try finding it
    if model_key == "lightgbm":
        return lookup_map.get(p_code_key, {}).get("lighgbm")

    return None


def get_sku_models() -> list[str]:
    """Returns a list of available SKU forecast models."""
    # Ensure cache is populated and up-to-date
    load_sku_records()
    return _cache.get("_sku_models", [])
