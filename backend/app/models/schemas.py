from __future__ import annotations
from typing import Dict, List, Optional

from pydantic import BaseModel


class ForecastItemProduct(BaseModel):
    product_id: str
    date: str
    forecast: float


class ForecastItemProductCustomer(BaseModel):
    product_id: str
    customer_id: str
    date: str
    forecast: float


class ForecastResponse(BaseModel):
    forecast: List[Dict]
    meta: Dict


class AnalysisConfigUpdate(BaseModel):
    excluded_columns: Optional[List[str]] = None
    included_columns: Optional[List[str]] = None
    identifier_patterns: Optional[List[str]] = None
    unique_ratio_threshold: Optional[float] = None
