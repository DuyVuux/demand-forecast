from __future__ import annotations
from typing import Dict, Optional
import numpy as np
from scipy.stats import norm

from .sku_forecast_service import find_sku_forecast_record
from .pc_forecast_service import find_pc_forecast_record
from ..utils.logger import get_logger

log = get_logger("service.inventory")

def get_demand_stats(product_code: str, model: str) -> Optional[Dict[str, float]]:
    """Lấy dữ liệu lịch sử từ bản ghi dự báo và tính toán các chỉ số nhu cầu."""
    record = find_sku_forecast_record(product_code, model)
    if not record or not record.get("history"):
        log.warning(f"Không tìm thấy dữ liệu lịch sử cho SKU {product_code} với model {model}")
        return None

    history = record["history"]
    actuals = [item.get("actual") for item in history if item.get("actual") is not None]

    if len(actuals) < 2: # Cần ít nhất 2 điểm dữ liệu để tính độ lệch chuẩn
        log.warning(f"Không đủ dữ liệu lịch sử ({len(actuals)} điểm) để tính toán cho SKU {product_code}")
        return None

    demand_mean = np.mean(actuals)
    demand_std = np.std(actuals, ddof=1) # ddof=1 for sample standard deviation

    return {"demand_mean": demand_mean, "demand_std": demand_std}

def calculate_safety_stock(
    demand_std: float,
    demand_mean: float,
    service_level: float,
    lead_time: float,
    lead_time_std: float,
) -> float:
    """Tính toán Tồn kho an toàn (Safety Stock)."""
    if not (0 < service_level < 1):
        raise ValueError("Service Level phải nằm trong khoảng (0, 1)")

    z_score = norm.ppf(service_level)
    
    safety_stock = z_score * ((demand_std**2 * lead_time) + (demand_mean**2 * lead_time_std**2))**0.5
    
    return round(safety_stock, 2)

def get_pc_demand_stats(customer_code: str, product_code: str, model: str) -> Optional[Dict[str, float]]:
    """Lấy các chỉ số nhu cầu đã tính toán trước từ bản ghi dự báo PC."""
    record = find_pc_forecast_record(customer_code, product_code, model)
    if not record:
        log.warning(f"Không tìm thấy bản ghi cho C={customer_code}, P={product_code}, M={model}")
        return None

    demand_mean = record.get("demand_mean")
    demand_std = record.get("demand_std_dev")

    if demand_mean is None or demand_std is None:
        log.warning(f"Thiếu demand_mean hoặc demand_std_dev cho C={customer_code}, P={product_code}, M={model}")
        return None

    return {"demand_mean": demand_mean, "demand_std": demand_std}
