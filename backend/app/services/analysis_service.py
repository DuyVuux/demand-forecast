from __future__ import annotations

import hashlib
import io
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi.responses import JSONResponse

import joblib
import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype

from ..config.settings import (
    EXCLUDED_COLUMNS as DEFAULT_EXCLUDED_COLUMNS,
    IDENTIFIER_PATTERNS as DEFAULT_IDENTIFIER_PATTERNS,
    INCLUDED_COLUMNS as DEFAULT_INCLUDED_COLUMNS,
    UNIQUE_RATIO_THRESHOLD as DEFAULT_UNIQUE_RATIO_THRESHOLD,
)

# --- Paths & Constants ---
BASE_DIR = Path(__file__).resolve().parents[2]  # -> backend/
ANALYSIS_DIR = BASE_DIR / "data" / "analysis"
CACHE_DIR = ANALYSIS_DIR / "cache"
UPLOADS_DIR = ANALYSIS_DIR / "uploads"
CONFIG_PATH = ANALYSIS_DIR / "config.json"
PIPELINE_VERSION = "1.1.0"

# --- In-memory state ---
JOBS: Dict[str, Job] = {}

# --- Data Models ---
@dataclass
class Job:
    job_id: str
    status: str  # queued, running, finished, failed
    file_hash: str
    file_path: str
    filename: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "status": self.status,
            "filename": self.filename,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

# --- Initial Setup ---
for d in (ANALYSIS_DIR, CACHE_DIR, UPLOADS_DIR):
    d.mkdir(parents=True, exist_ok=True)

def _ensure_analysis_logger() -> logging.Logger:
    logger = logging.getLogger("analysis")
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        logs_dir = BASE_DIR / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(logs_dir / "analysis.log", encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(fh)
    return logger

logger = _ensure_analysis_logger()

# --- Core Service Functions: Hashing, I/O, Caching ---
def _md5_bytes(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

def _load_df_from_bytes(file_bytes: bytes, filename: str) -> pd.DataFrame:
    ext = Path(filename).suffix.lower()
    file_stream = io.BytesIO(file_bytes)
    df = None

    try:
        if ext == '.csv':
            for encoding in ['utf-8', 'latin1', 'cp1252']:
                try:
                    file_stream.seek(0)
                    df = pd.read_csv(file_stream, encoding=encoding)
                    logger.info(f"Successfully read CSV '{filename}' with encoding '{encoding}'")
                    break
                except (UnicodeDecodeError, pd.errors.ParserError):
                    logger.warning(f"Failed to read CSV '{filename}' with encoding '{encoding}'")
                    continue
            if df is None:
                raise ValueError(f"Could not decode CSV file '{filename}' with attempted encodings.")

        elif ext in ['.xlsx', '.xls']:
            try:
                file_stream.seek(0)
                df = pd.read_excel(file_stream, engine='openpyxl' if ext == '.xlsx' else 'xlrd')
            except Exception as e:
                logger.warning(f"Reading Excel file '{filename}' failed, trying fallback engine. Error: {e}")
                file_stream.seek(0)
                fallback_engine = 'xlrd' if ext == '.xlsx' else 'openpyxl'
                df = pd.read_excel(file_stream, engine=fallback_engine)
        else:
            logger.info(f"Unknown extension '{ext}', attempting to read as CSV then Excel.")
            try:
                for encoding in ['utf-8', 'latin1', 'cp1252']:
                    try:
                        file_stream.seek(0)
                        df = pd.read_csv(file_stream, encoding=encoding)
                        logger.info(f"Read unknown file type '{filename}' as CSV with encoding '{encoding}'")
                        break
                    except (UnicodeDecodeError, pd.errors.ParserError):
                        continue
                if df is None: raise ValueError("CSV attempt failed.")
            except Exception:
                logger.warning(f"Could not read '{filename}' as CSV, trying as Excel.")
                file_stream.seek(0)
                df = pd.read_excel(file_stream)

        if df is None:
            raise ValueError(f"Could not read file '{filename}' with any available method.")

        df.columns = [str(c).strip() for c in df.columns]
        df.replace([np.inf, -np.inf], np.nan, inplace=True)

        # Attempt to convert object columns that look like dates
        for col in df.select_dtypes(include=['object']).columns:
            # Heuristic: if 'date' or 'time' is in the column name, it's a good candidate.
            if 'date' in col.lower() or 'time' in col.lower():
                try:
                    df[col] = pd.to_datetime(df[col], infer_datetime_format=True, dayfirst=True, errors='raise')
                    logger.info(f"Auto-converted column '{col}' to datetime.")
                    break # Stop after the first successful conversion to avoid converting other ID-like columns
                except (ValueError, TypeError):
                    logger.warning(f"Column '{col}' looks like a date but failed to convert.")
                    continue
        return df

    except Exception as e:
        logger.exception(f"Failed to load dataframe from file '{filename}'")
        raise ValueError(f"Could not parse file '{filename}'. Ensure it's a valid CSV or Excel file.") from e

def cache_path_for(file_hash: str) -> Path:
    return CACHE_DIR / f"{file_hash}.joblib"

def save_cache(file_hash: str, data: Dict[str, Any]):
    joblib.dump(data, cache_path_for(file_hash), compress=3)
    logger.info(f"Saved analysis cache for hash {file_hash}")

def load_cache(file_hash: str) -> Optional[Dict[str, Any]]:
    path = cache_path_for(file_hash)
    return joblib.load(path) if path.exists() else None

def save_upload(file_hash: str, filename: str, file_bytes: bytes) -> Path:
    ext = Path(filename).suffix or ".bin"
    path = UPLOADS_DIR / f"{file_hash}{ext}"
    path.write_bytes(file_bytes)
    return path

# --- Job Management --- 
def prepare_job(file_bytes: bytes, filename: str) -> Tuple[str, str, Path]:
    file_hash = _md5_bytes(file_bytes)
    job_id = file_hash
    path = save_upload(file_hash, filename, file_bytes)
    return job_id, file_hash, path

def register_job(job_id: str, file_hash: str, file_path: Path, filename: str) -> Job:
    job = Job(
        job_id=job_id,
        status="queued",
        file_hash=file_hash,
        file_path=str(file_path),
        filename=filename,
    )
    JOBS[job_id] = job
    logger.info(f"Registered job_id={job_id}, total_jobs={len(JOBS)}")
    return job

def get_job(job_id: str) -> Optional[Job]:
    return JOBS.get(job_id)

def job_status(job_id: str) -> Dict[str, Any]:
    job = get_job(job_id)
    if not job:
        return {"job_id": job_id, "status": "not_found"}
    if job.status not in ["failed", "finished"] and load_cache(job.file_hash):
        job.status = "finished"
        job.updated_at = datetime.now(timezone.utc)
    return job.to_dict()

def run_job(job_id: str):
    job = get_job(job_id)
    if not job:
        logger.error(f"run_job called with unknown job_id={job_id}")
        return

    job.status = "running"
    job.updated_at = datetime.now(timezone.utc)
    logger.info(f"Starting job {job_id} for '{job.filename}'")

    try:
        if (cached_results := load_cache(job.file_hash)):
            logger.info(f"Cache hit for job {job_id}. Loaded pre-computed results.")
        else:
            logger.info(f"Cache miss for job {job_id}. Running analysis.")
            file_bytes = Path(job.file_path).read_bytes()
            results = analyze_dataset(file_bytes, job.filename)
            save_cache(job.file_hash, results)
        
        job.status = "finished"
        logger.info(f"Job {job_id} finished successfully.")
    except Exception as e:
        job.status = "failed"
        logger.exception(f"Job {job_id} failed: {e}")
    finally:
        job.updated_at = datetime.now(timezone.utc)

# --- Analysis Config Management ---
def get_runtime_config() -> Dict[str, Any]:
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    return {
        "included_columns": DEFAULT_INCLUDED_COLUMNS,
        "excluded_columns": DEFAULT_EXCLUDED_COLUMNS,
        "identifier_patterns": DEFAULT_IDENTIFIER_PATTERNS,
        "unique_ratio_threshold": DEFAULT_UNIQUE_RATIO_THRESHOLD,
    }

def update_runtime_config(payload: Dict[str, Any]) -> Dict[str, Any]:
    current_config = get_runtime_config()
    current_config.update(payload)
    CONFIG_PATH.write_text(json.dumps(current_config, indent=2), encoding="utf-8")
    logger.info(f"Updated runtime config: {payload}")
    return current_config

def export_config_json() -> JSONResponse:
    config = get_runtime_config()
    headers = {
        "Content-Disposition": f"attachment; filename=\"analysis_config_{datetime.now(timezone.utc).strftime('%Y%m%d')}.json\""
    }
    return JSONResponse(content=config, headers=headers)

def import_config_json(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Here you might add validation against a schema to ensure the payload is valid
    CONFIG_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("Imported and overwrote runtime config from file.")
    return payload

# --- Analysis Pipeline ---
def _is_identifier(s: pd.Series, patterns: List[str], threshold: float) -> Tuple[bool, str]:
    if not pd.api.types.is_object_dtype(s) and not pd.api.types.is_string_dtype(s):
        return False, "Not text"
    
    s_valid = s.dropna()
    if len(s_valid) == 0:
        return False, "Empty column"
        
    if s_valid.nunique() / len(s_valid) < threshold:
        return False, "Not unique enough"
        
    name = s.name.lower()
    if any(re.search(p, name) for p in patterns):
        return True, "Name pattern match"
        
    return False, "High unique ratio"

def compute_filters_for_job(job_id: str) -> Dict[str, Any]:
    df = _load_df_from_upload(job_id)
    config = get_runtime_config()
    filters = {"auto_excluded": {}, "user_excluded": config["excluded_columns"]}
    
    for col in df.columns:
        if col in config["included_columns"] or col in config["excluded_columns"]:
            continue
        is_id, reason = _is_identifier(df[col], config["identifier_patterns"], config["unique_ratio_threshold"])
        if is_id:
            filters["auto_excluded"][col] = reason
    return filters

def _get_filtered_df(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    excluded = set(filters["auto_excluded"].keys()) | set(filters["user_excluded"])
    return df.drop(columns=[c for c in excluded if c in df.columns])

def compute_quality(df: pd.DataFrame) -> Dict[str, Any]:
    total_cells = df.size
    missing_cells = df.isnull().sum().sum()
    return {
        "completeness": float((1 - missing_cells / total_cells) if total_cells > 0 else 1.0),
        "n_duplicates": int(df.duplicated().sum()),
        "memory_usage_mb": float(df.memory_usage(deep=True).sum() / (1024 * 1024)),
    }

def compute_insights(df: pd.DataFrame) -> Dict[str, Any]:
    """Computes time-series trend and top categorical value counts."""
    # 1. Time-series analysis
    time_series_analysis = None
    df_copy = df.copy()

    # Attempt to find and convert a date column
    dt_col_name = None
    potential_date_cols = [col for col in df_copy.columns if 'date' in col.lower() or 'time' in col.lower()]
    
    # First, check for actual datetime types
    dt_cols = df_copy.select_dtypes(include=['datetime64[ns]']).columns
    if not dt_cols.empty:
        dt_col_name = dt_cols[0]
    # If not found, try to convert potential date columns from object/string type
    elif potential_date_cols:
        for col in potential_date_cols:
            if df_copy[col].dtype == 'object':
                try:
                    # Use dayfirst=False for MM/DD/YYYY format, coerce errors to NaT
                    df_copy[col] = pd.to_datetime(df_copy[col], dayfirst=False, errors='coerce')
                    if not df_copy[col].isna().all():
                        dt_col_name = col
                        logger.info(f"Successfully converted column '{col}' to datetime.")
                        break
                except Exception as e:
                    logger.warning(f"Could not convert column '{col}' to datetime: {e}")
                    continue
    
    # Check if 'Quantity' column exists and is numeric
    quantity_col_name = None
    if 'Quantity' in df_copy.columns and is_numeric_dtype(df_copy['Quantity']):
        quantity_col_name = 'Quantity'

    if dt_col_name and quantity_col_name:
        logger.info(f"Performing time-series analysis on '{dt_col_name}' with '{quantity_col_name}'")
        df_ts = df_copy.dropna(subset=[dt_col_name, quantity_col_name])
        df_ts = df_ts.set_index(dt_col_name)
        
        try:
            # Resample by day and sum the quantities
            ts_agg = df_ts[[quantity_col_name]].resample('D').sum()
            ts_agg = ts_agg[ts_agg[quantity_col_name] > 0]  # Keep only days with sales

            if not ts_agg.empty:
                time_series_analysis = {
                    "datetime_column": dt_col_name,
                    "value_column": quantity_col_name,
                    "frequency": "Daily",
                    "trend_data": {
                        'index': [i.strftime('%Y-%m-%d') for i in ts_agg.index],
                        'columns': [quantity_col_name],
                        'data': ts_agg.values.tolist()
                    }
                }
        except Exception as e:
            logger.warning(f"Time-series analysis failed for column '{dt_col_name}': {e}")

    # 2. Top categorical value counts
    top_categorical_counts = {}
    cat_cols = df.select_dtypes(include=['object', 'category']).columns
    for col in cat_cols:
        if 1 < df[col].nunique() < (len(df) * 0.5):
            counts = df[col].value_counts().nlargest(10)
            if not counts.empty:
                top_categorical_counts[col] = {str(k): int(v) for k, v in counts.to_dict().items()}

    return {
        "time_series_analysis": time_series_analysis,
        "top_categorical_counts": top_categorical_counts
    }

def compute_correlation(df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    numeric_df = df.select_dtypes(include=np.number)
    if numeric_df.shape[1] < 2:
        return None
    corr = numeric_df.corr().round(2).reset_index().to_dict(orient='records')
    return {"matrix": corr, "columns": list(numeric_df.columns)}

def analyze_dataset(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    df = _load_df_from_bytes(file_bytes, filename)
    file_hash = _md5_bytes(file_bytes)
    
    # --- Run full analysis pipeline ---
    overview = compute_overview(df, file_hash)
    quality = compute_quality(df)
    insights = compute_insights(df)
    correlation = compute_correlation(df)
    
    return {
        "version": PIPELINE_VERSION,
        "filename": filename,
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "overview": overview, # Renamed from summary for clarity
        "quality": quality,
        "insights": insights,
        "correlation": correlation,
    }

def compute_overview(df: pd.DataFrame, file_hash: str) -> Dict[str, Any]:
    columns_data = []
    for col in df.columns:
        s = df[col]
        col_data = {
            "name": col,
            "dtype": str(s.dtype),
            "null_count": int(s.isnull().sum()),
            "unique_count": int(s.nunique()),
            "min": None,
            "max": None,
            "mean": None,
            "median": None,
        }

        if is_numeric_dtype(s):
            stats = s.describe()
            col_data.update({
                "min": float(stats.get("min")) if pd.notna(stats.get("min")) else None,
                "max": float(stats.get("max")) if pd.notna(stats.get("max")) else None,
                "mean": float(stats.get("mean")) if pd.notna(stats.get("mean")) else None,
                "median": float(stats.get("50%")) if pd.notna(stats.get("50%")) else None,
            })
        elif is_datetime64_any_dtype(s):
            # For older pandas versions, describe() on datetime columns doesn't take
            # datetime_is_numeric and returns 'first'/'last' instead of 'min'/'max'.
            stats = s.describe()
            col_data.update({
                "min": str(stats.get("first")) if pd.notna(stats.get("first")) else None,
                "max": str(stats.get("last")) if pd.notna(stats.get("last")) else None,
            })

        # Ensure values are JSON serializable (no NaN, NaT)
        for key, value in col_data.items():
            if pd.isna(value):
                col_data[key] = None

        columns_data.append(col_data)

    return {
        "file_hash": file_hash,
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "n_duplicates": int(df.duplicated().sum()),
        "total_missing": int(df.isnull().sum().sum()),
        "columns": columns_data,
        "memory_usage": int(df.memory_usage(deep=True).sum()),
    }

# --- On-Demand Analysis Endpoints ---
def get_cached_result_by_job(job_id: str) -> Optional[Dict[str, Any]]:
    job = get_job(job_id)
    return load_cache(job.file_hash) if job else None

def _load_df_from_upload(job_id: str) -> pd.DataFrame:
    job = get_job(job_id)
    if not job:
        raise FileNotFoundError(f"Job '{job_id}' not found.")
    return _load_df_from_bytes(Path(job.file_path).read_bytes(), job.filename)

def compute_overview_for_job(job_id: str) -> Dict[str, Any]:
    df = _load_df_from_upload(job_id)
    filters = compute_filters_for_job(job_id)
    df_filtered = _get_filtered_df(df, filters)
    job = get_job(job_id)
    return compute_overview(df_filtered, job.file_hash if job else "")

def column_detail(job_id: str, column: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
    df = _load_df_from_upload(job_id)
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in dataset.")
    s = df[column]
    res = {"name": column, "dtype": str(s.dtype), "null_pct": float(s.isna().mean())}

    if is_numeric_dtype(s):
        desc = s.describe()
        s_valid = s.dropna()
        counts, bin_edges = np.histogram(s_valid, bins=20) if not s_valid.empty else ([], [])
        res.update({
            "type": "numeric",
            "stats": {k: float(v) if pd.notna(v) else None for k, v in desc.to_dict().items()},
            "histogram": {"counts": counts.tolist(), "bin_edges": bin_edges.tolist()}
        })
        # Also provide value counts for numeric types to allow categorical-style display
        counts = s.value_counts()
        total_counts = len(counts)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_counts = counts.iloc[start_index:end_index]

        res.update({
            "n_unique": int(s.nunique()),
            "value_counts": {str(k): int(v) for k, v in paginated_counts.to_dict().items()},
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_counts,
                "total_pages": (total_counts + page_size - 1) // page_size if page_size > 0 else 0
            }
        })
        # Also provide value counts for numeric types to allow categorical-style display
        counts = s.value_counts()
        total_counts = len(counts)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_counts = counts.iloc[start_index:end_index]

        res.update({
            "n_unique": int(s.nunique()),
            "value_counts": {str(k): int(v) for k, v in paginated_counts.to_dict().items()},
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_counts,
                "total_pages": (total_counts + page_size - 1) // page_size if page_size > 0 else 0
            }
        })
    elif is_datetime64_any_dtype(s):
        # For datetime columns, describe() can produce NaT which is not JSON serializable.
        # We convert all values to string representations safely.
        desc = s.describe()
        stats_dict = desc.to_dict()
        serializable_stats = {}
        for k, v in stats_dict.items():
            if pd.isna(v):
                serializable_stats[k] = None
            else:
                # Convert Timestamps and other objects to ISO format string
                serializable_stats[k] = str(v)
        res.update({"type": "datetime", "stats": serializable_stats})
    else:
        n_unique = s.nunique()
        res.update({"type": "categorical", "n_unique": int(n_unique)})
        
        if n_unique > 50000:
            res["warning"] = f"Cột '{column}' có quá nhiều giá trị ({n_unique}) để hiển thị chi tiết. Chỉ hiển thị thông tin tóm tắt."
            return res

        # If 'Quantity' column exists and is numeric, group by the selected column and sum 'Quantity'.
        # Otherwise, fall back to counting frequencies.
        if 'Quantity' in df.columns and is_numeric_dtype(df['Quantity']):
            logger.info(f"Calculating sum of 'Quantity' for categorical column '{column}'")
            counts = df.groupby(column)['Quantity'].sum().sort_values(ascending=False)
        else:
            logger.info(f"'Quantity' column not found or not numeric. Falling back to value_counts for '{column}'.")
            counts = s.value_counts()
        total_counts = len(counts)
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        paginated_counts = counts.iloc[start_index:end_index]

        res.update({
            "type": "categorical",
            "n_unique": int(s.nunique()),
            "value_counts": {str(k): int(v) for k, v in paginated_counts.to_dict().items()},
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_counts,
                "total_pages": (total_counts + page_size - 1) // page_size if page_size > 0 else 0
            }
        })
    return res
