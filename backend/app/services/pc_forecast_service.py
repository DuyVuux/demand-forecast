from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import time
from functools import lru_cache
from pathlib import Path

import math
from ..utils.logger import get_logger

log = get_logger("service.pc_forecast")

# Path to the directory containing individual JSON files for each model
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "model_result" / "DemandForecast_Product_Customer"

def _normalize_date(ds: Optional[str]) -> Optional[str]:
    if not ds:
        return None
    # Input format: "YYYY-MM-DD HH:MM:SS" -> keep date part only
    return str(ds)[:10]

def _normalize_record(rec: Dict) -> Dict:
    customer_code = rec.get("CustomerCode") or rec.get("customer_code")
    product_code = rec.get("ProductCode") or rec.get("product_code")
    model = rec.get("Model") or rec.get("model")
    metrics_src = rec.get("metrics", {})
    metrics = {
        "MAE": float(metrics_src.get("MAE", 0) or 0),
        "RMSE": float(metrics_src.get("RMSE", 0) or 0),
        "MAPE": float(metrics_src.get("MAPE", 0) or 0),
    }

    train_end_raw: Optional[str] = (
        rec.get("TrainEndDate") or rec.get("train_end_date") or rec.get("train_end")
    )
    train_end_date = _normalize_date(train_end_raw)

    history_list: List[Dict] = []
    history_src = rec.get("history") or rec.get("actuals")
    if isinstance(history_src, list):
        for h in history_src:
            date = _normalize_date(h.get("ds") or h.get("date"))
            val = h.get("actual") or h.get("y")
            if date and val is not None:
                try:
                    history_list.append({"date": date, "actual": float(val)})
                except (ValueError, TypeError):
                    history_list.append({"date": date, "actual": None})

    forecasts = rec.get("forecast") or rec.get("predictions", [])
    fc_list: List[Dict] = []
    for r in forecasts:
        date = _normalize_date(r.get("ds") or r.get("date"))
        if not date:
            continue
        
        # The logic below was incorrectly filtering out valid forecast data.
        # The source JSON already separates history and forecast, so we don't need this check.
        # if train_end_date and date <= train_end_date:
        #     ...
        #     continue

        try:
            # CRITICAL FIX: The keys in the JSON are 'forecast', 'lower_80', etc., not 'yhat'.
            fc_list.append(
                {
                    "date": date,
                    "yhat": float(r.get("yhat") or r.get("forecast", 0) or 0),
                    "yhat_lower_80": float(r.get("yhat_lower_80") or r.get("lower_80", 0) or 0),
                    "yhat_upper_80": float(r.get("yhat_upper_80") or r.get("upper_80", 0) or 0),
                }
            )
        except (ValueError, TypeError):
             fc_list.append(
                {
                    "date": date,
                    "forecast": None,
                    "lower_80": None,
                    "upper_80": None,
                }
            )

    transition_date = train_end_date
    if not transition_date and history_list:
        try:
            transition_date = max(h.get("date") or "" for h in history_list)
        except ValueError:
            transition_date = None
    


    demand_mean = None
    demand_std_dev = None
    if history_list:
        actuals = [h['actual'] for h in history_list if h.get('actual') is not None]
        if len(actuals) > 1:
            demand_mean = sum(actuals) / len(actuals)
            variance = sum([((x - demand_mean) ** 2) for x in actuals]) / (len(actuals) - 1)
            demand_std_dev = math.sqrt(variance)
        elif len(actuals) == 1:
            demand_mean = actuals[0]
            demand_std_dev = 0 # Cannot compute std dev from a single point

    return {
        "customer_code": customer_code,
        "product_code": product_code,
        "model": model,
        "metrics": metrics,
        "train_end_date": train_end_date,
        "transition_date": transition_date,
        "history": sorted(history_list, key=lambda x: x.get('date', '')) if history_list else [],
        "forecast": sorted(fc_list, key=lambda x: x.get('date', '')) if fc_list else [],
        "demand_mean": demand_mean,
        "demand_std_dev": demand_std_dev,
    }

@lru_cache(maxsize=10) # Cache up to 10 model files
def load_records_from_model_file(model_name: str) -> List[Dict]:
    """Load and normalize records from a specific model's JSON file."""
    t0 = time.perf_counter()
    
    # Sanitize model_name to create a filename, e.g., "Random Forest" -> "random_forest_results.json"
    # Map frontend model name to backend filename if they differ
    filename_base = model_name.lower().replace(' ', '_')
    if filename_base == 'arima':
        filename_base = 'sarima'  # Map 'ARIMA' model to 'sarima_results.json' file

    file_name = f"{filename_base}_results.json"
    source_file = DATA_DIR / file_name

    if not source_file.exists():
        log.warning(f"Source file not found for model '{model_name}': {source_file}")
        return []

    log.info(f"Loading PC forecast data for model '{model_name}' from {source_file}...")
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        log.error(f"Error reading or parsing {source_file}: {e}")
        return []

    if not isinstance(raw_data, list):
        log.error(f"Data in {source_file} is not a list.")
        return []

    normalized_records = [_normalize_record(rec) for rec in raw_data]
    dur = (time.perf_counter() - t0) * 1000
    log.info(f"Loaded and normalized {len(normalized_records)} records for model '{model_name}' in {dur:.2f}ms")

    return normalized_records

def find_pc_forecast_record(customer_code: str, product_code: str, model: str) -> Optional[Dict]:
    """Finds a forecast record from the specified model's file."""
    if not model:
        log.error("Model name is required to find a forecast record.")
        return None

    model_records = load_records_from_model_file(model)
    if not model_records:
        return None

    customer_upper = customer_code.strip().upper()
    product_upper = product_code.strip().upper()

    for record in model_records:
        if (
            (record.get("customer_code") or "").strip().upper() == customer_upper
            and (record.get("product_code") or "").strip().upper() == product_upper
        ):
            return record # Return the first match

    log.warning(f"No record found for C={customer_code}, P={product_code} in model '{model}'.")
    return None

def get_pc_models() -> List[str]:
    """Returns a list of available models by scanning for result files."""
    model_names = []
    for f in DATA_DIR.glob("*_result.json"):
        # "random_forest_result.json" -> "Random Forest"
        model_slug = f.name.replace("_result.json", "")
        model_name = model_slug.replace("_", " ").title()
        model_names.append(model_name)
    
    log.info(f"Discovered models from filenames: {model_names}")
    return sorted(model_names)
