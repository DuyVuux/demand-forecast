from __future__ import annotations
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import time

from ..utils.logger import get_logger

log = get_logger("service.rf_pc_results")

# Directory containing RandomForest Product-Customer result JSON files
DATA_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "model_result"
    / "DemandForecast_Product_Customer"
    / "RandomForest"
)

_cache: Dict = {"mtime": None, "records": []}


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


def _normalize_date(ds: str | None) -> str:
    if not ds:
        return ""
    # Input format: "YYYY-MM-DD HH:MM:SS" → keep date part only
    return str(ds)[:10]


def _load_files() -> List[Dict]:
    records: List[Dict] = []
    if not DATA_DIR.exists():
        log.warning(f"Result directory not found: {DATA_DIR}")
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
            # --- Basic fields ---
            customer_code = rec.get("CustomerCode") or rec.get("customer_code")
            product_code = rec.get("ProductCode") or rec.get("product_code")
            model = rec.get("Model") or rec.get("model") or "RandomForest"
            metrics = {
                "MAE": float(rec.get("MAE", 0) or 0),
                "RMSE": float(rec.get("RMSE", 0) or 0),
                "MAPE": float(rec.get("MAPE", 0) or 0),
            }

            # --- Train end date (various possible keys) ---
            train_end_raw: Optional[str] = (
                rec.get("TrainEndDate")
                or rec.get("train_end_date")
                or rec.get("train_end")
                or rec.get("LastTrainDate")
                or rec.get("last_train_date")
                or rec.get("train_last_date")
                or rec.get("last_train_ds")
            )
            train_end_date = _normalize_date(train_end_raw)

            # --- History (actual) ---
            history_list: List[Dict] = []
            history_src = (
                rec.get("history")
                or rec.get("actuals")
                or rec.get("historical")
                or rec.get("actual")
            )
            if isinstance(history_src, list):
                for h in history_src:
                    date = _normalize_date(h.get("ds") or h.get("date"))
                    val = h.get("actual")
                    if val is None:
                        val = h.get("y") or h.get("y_true") or h.get("value")
                    if date:
                        try:
                            history_list.append({"date": date, "actual": float(val) if val is not None else None})
                        except Exception:  # noqa: BLE001
                            history_list.append({"date": date, "actual": None})

            # --- Forecast ---
            forecasts = rec.get("forecast") or rec.get("forecasts") or rec.get("predictions") or []
            fc_list: List[Dict] = []
            for r in forecasts or []:
                date = _normalize_date(r.get("ds") or r.get("date"))
                # skip entries that fall into training range if train_end_date is known
                if train_end_date and date and date <= train_end_date:
                    # If combined timeline holds actuals inside forecast rows
                    actual_val = r.get("actual") or r.get("y") or r.get("y_true")
                    if actual_val is not None:
                        try:
                            history_list.append({"date": date, "actual": float(actual_val)})
                        except Exception:  # noqa: BLE001
                            history_list.append({"date": date, "actual": None})
                    continue

                try:
                    fc_list.append(
                        {
                            "date": date,
                            "yhat": float(r.get("yhat", 0) or 0),
                            "yhat_lower_80": float(r.get("yhat_lower_80", 0) or 0),
                            "yhat_upper_80": float(r.get("yhat_upper_80", 0) or 0),
                        }
                    )
                except Exception:  # noqa: BLE001
                    fc_list.append(
                        {
                            "date": date,
                            "yhat": None,
                            "yhat_lower_80": None,
                            "yhat_upper_80": None,
                        }
                    )

            # Transition date: prefer explicit train_end_date, else last history date
            transition_date = train_end_date
            if not transition_date and history_list:
                try:
                    transition_date = max(h.get("date") or "" for h in history_list) or None
                except Exception:  # noqa: BLE001
                    transition_date = None
            # If still missing, infer as the day before the first forecast date
            if not transition_date and fc_list:
                try:
                    fc_dates = [x.get("date") for x in fc_list if x.get("date")]
                    if fc_dates:
                        first_fc = min(fc_dates)
                        d = datetime.strptime(first_fc, "%Y-%m-%d") - timedelta(days=1)
                        transition_date = d.strftime("%Y-%m-%d")
                except Exception:  # noqa: BLE001
                    pass

            item = {
                "customer_code": customer_code,
                "product_code": product_code,
                "model": model,
                "metrics": metrics,
                "train_end_date": train_end_date,
                "transition_date": transition_date,
                "history": history_list,
                "forecast": fc_list,
            }
            records.append(item)
    return records


def load_rf_pc_records(force_reload: bool = False) -> List[Dict]:
    start = time.perf_counter()
    mtime = _dir_mtime(DATA_DIR)
    if not force_reload and _cache.get("mtime") == mtime and _cache.get("records"):
        return _cache["records"]

    records = _load_files()
    _cache["mtime"] = mtime
    _cache["records"] = records
    dur = (time.perf_counter() - start) * 1000
    log.info(
        f"Loaded RF Product-Customer results: files={len(list(DATA_DIR.glob('*.json')))} "
        f"records={len(records)} ({dur:.1f} ms)"
    )
    return records
