from __future__ import annotations
from fastapi import APIRouter, Body, Depends, File, Form, UploadFile, Query, HTTPException
from pydantic import BaseModel, Field, condecimal
from typing import Optional, List
from time import perf_counter
from sqlalchemy.orm import Session

from ..db import get_db
from ..services.forecast_service import (
    forecast_by_product,
    forecast_by_product_customer,
)
from ..services.rf_pc_results import load_rf_pc_records
from ..services.pc_forecast_service import find_pc_forecast_record, get_pc_models
from ..services.sku_forecast_service import find_sku_forecast_record, get_sku_models
from ..services.inventory_service import calculate_safety_stock, get_pc_demand_stats, get_demand_stats
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("router.forecast")


@router.post("/forecast/product")
async def product_forecast(
    file: UploadFile = File(...),
    horizon: int = Form(7),
    model: str = Form("arima"),
    db: Session = Depends(get_db),
):
    log.info(
        f"/forecast/product called - model={model}, horizon={horizon}, file={file.filename}"
    )
    result = await forecast_by_product(file, horizon=horizon, model_type=model, db=db)
    return result


@router.post("/forecast/product_customer")
async def product_customer_forecast(
    file: UploadFile = File(...),
    horizon: int = Form(7),
    model: str = Form("arima"),
    db: Session = Depends(get_db),
):
    log.info(
        f"/forecast/product_customer called - model={model}, horizon={horizon}, file={file.filename}"
    )
    result = await forecast_by_product_customer(
        file, horizon=horizon, model_type=model, db=db
    )
    return result


@router.get("/forecast/product-customer/randomforest")
def get_product_customer_randomforest(
    customer_code: Optional[str] = None,
    product_code: Optional[str] = None,
    limit: Optional[int] = Query(None, ge=1, le=10000),
):
    """Đọc kết quả RandomForest (Product-Customer) từ file JSON đã sinh sẵn.

    Hỗ trợ filter theo customer_code, product_code và giới hạn số bản ghi trả về.
    Trả về định dạng:
    {
      "model": "RandomForest",
      "metrics": { "MAE": ..., "RMSE": ..., "MAPE": ... },  # trung bình trên tập trả về
      "count": N,
      "data": [
        {
          "customer_code": "...",
          "product_code": "...",
          "metrics": { "MAE": ..., "RMSE": ..., "MAPE": ... },
          "history": [],
          "forecast": [ { "date": "YYYY-MM-DD", "yhat": ..., "yhat_lower_80": ..., "yhat_upper_80": ... } ]
        }
      ]
    }
    """
    t0 = perf_counter()
    records = load_rf_pc_records()

    def _match(v: Optional[str], q: Optional[str]) -> bool:
        if not q:
            return True
        return (v or "").strip().upper() == q.strip().upper()

    filtered = [
        r
        for r in records
        if _match(r.get("customer_code"), customer_code)
        and _match(r.get("product_code"), product_code)
    ]

    if limit is not None:
        filtered = filtered[: limit]

    # Tính metrics trung bình trên tập trả về (nếu có)
    mae_vals = [r.get("metrics", {}).get("MAE") for r in filtered if r.get("metrics", {}).get("MAE") is not None]
    rmse_vals = [r.get("metrics", {}).get("RMSE") for r in filtered if r.get("metrics", {}).get("RMSE") is not None]
    mape_vals = [r.get("metrics", {}).get("MAPE") for r in filtered if r.get("metrics", {}).get("MAPE") is not None]

    def _avg(xs):
        return float(sum(xs) / len(xs)) if xs else None

    agg_metrics = {
        "MAE": _avg(mae_vals),
        "RMSE": _avg(rmse_vals),
        "MAPE": _avg(mape_vals),
    }

    dur = (perf_counter() - t0) * 1000
    log.info(
        f"GET /forecast/product-customer/randomforest returned count={len(filtered)} (filter: customer={customer_code}, product={product_code}, limit={limit}) in {dur:.1f} ms"
    )

    return {
        "model": "RandomForest",
        "metrics": agg_metrics,
        "count": len(filtered),
        "data": filtered,
    }


@router.get("/pc-forecast")
def get_pc_forecast(
    customer_code: str = Query(..., description="Customer code is required"),
    product_code: str = Query(..., description="Product code is required"),
    model: str = Query(..., description="Model name is required, e.g., Random Forest, Prophet"),
    forecast_weeks: int = Query(4, ge=1, le=4, description="Number of forecast weeks (1-4)"),
):
    """Get Product-Customer forecast from the specific model's result file."""
    t0 = perf_counter()
    log.info(f"GET /pc-forecast called with: C='{customer_code}', P='{product_code}', M='{model}', Weeks='{forecast_weeks}'")

    result_record = find_pc_forecast_record(
        customer_code=customer_code,
        product_code=product_code,
        model=model
    )

    if not result_record:
        log.warning(f"No data found for C={customer_code}, P={product_code}, M={model}")
        return {"count": 0, "data": None}

    # Trim the forecast to the requested number of weeks
    forecast_days = forecast_weeks * 7
    if 'forecast' in result_record and isinstance(result_record['forecast'], list):
        # The service already sorts the data, but let's be safe.
        sorted_forecast = sorted(result_record['forecast'], key=lambda x: x.get('date', ''))
        result_record['forecast'] = sorted_forecast[:forecast_days]

    dur = (perf_counter() - t0) * 1000
    log.info(
        f"GET /pc-forecast returned 1 record for C={customer_code}, P={product_code}, M={model} in {dur:.1f} ms"
    )

    return {"count": 1, "data": result_record}


@router.get("/pc-forecast/models")
def get_product_customer_models():
    """Returns a list of available models for product-customer forecasting."""
    try:
        models = get_pc_models()
        return {"models": models}
    except Exception as e:
        log.exception(f"Error getting product-customer models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class PCSafetyStockRequest(BaseModel):
    customerId: str
    productId: str
    model: str
    serviceLevel: condecimal(gt=0, lt=1) # type: ignore
    leadTime: float = Field(..., gt=0)
    leadTimeStd: float = Field(..., ge=0)

class ChartDataItem(BaseModel):
    date: str
    value: Optional[float]
    type: str # 'history' or 'forecast'

class PCSafetyStockResponse(BaseModel):
    safetyStock: float
    chartData: List[ChartDataItem]
    demandMean: float
    demandStd: float

@router.post("/pc-forecast/safety-stock", response_model=PCSafetyStockResponse)
async def get_pc_safety_stock(request: PCSafetyStockRequest):
    """Calculate Safety Stock for a given Product-Customer pair and return it with chart data."""
    log.info(f"Received safety stock request for P:{request.productId}, C:{request.customerId}, M:{request.model}")

    # 1. Get demand stats
    stats = get_pc_demand_stats(
        customer_code=request.customerId,
        product_code=request.productId,
        model=request.model
    )
    if not stats:
        raise HTTPException(
            status_code=404,
            detail=f"Demand statistics not found for P:{request.productId}, C:{request.customerId} with model {request.model}. History data might be missing or insufficient."
        )

    # 2. Calculate Safety Stock
    try:
        safety_stock = calculate_safety_stock(
            demand_std=stats["demand_std"],
            demand_mean=stats["demand_mean"],
            service_level=float(request.serviceLevel),
            lead_time=request.leadTime,
            lead_time_std=request.leadTimeStd,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Get full record for chart data
    record = find_pc_forecast_record(
        customer_code=request.customerId,
        product_code=request.productId,
        model=request.model
    )
    if not record:
         raise HTTPException(
            status_code=404, 
            detail=f"Forecast record disappeared for P:{request.productId}, C:{request.customerId}, M:{request.model}"
        )

    # 4. Prepare chart data
    chart_data = []
    for h in record.get("history", []):
        chart_data.append(ChartDataItem(date=h['date'], value=h.get('actual'), type='history'))
    for f in record.get("forecast", []):
        chart_data.append(ChartDataItem(date=f['date'], value=f.get('yhat'), type='forecast'))

    # Sort by date to ensure the chart line is continuous
    chart_data.sort(key=lambda x: x.date)

    return PCSafetyStockResponse(
        safetyStock=safety_stock,
        chartData=chart_data,
        demandMean=round(stats["demand_mean"], 2),
        demandStd=round(stats["demand_std"], 2),
    )


@router.get("/forecast/sku")
def get_sku_forecast(
    product_code: str = Query(..., description="Product code is required"),
    model: str = Query(..., description="Model name is required"),
):
    """Get SKU-level forecast from the specific model's result file."""
    t0 = perf_counter()
    log.info(f"GET /forecast/sku called with: P='{product_code}', M='{model}'")

    record = find_sku_forecast_record(product_code=product_code, model=model)

    if not record:
        log.warning(f"No data found for P={product_code}, M={model}")
        # Use 404 for not found
        raise HTTPException(status_code=404, detail=f"No forecast data available for product '{product_code}' with model '{model}'.")

    # --- Prepare data for frontend ---
    forecast_list = record.get("forecast", [])
    
    # 1. Calculate total forecast quantity
    total_forecast_qty = sum(item.get("forecast", 0) for item in forecast_list if item.get("forecast") is not None)

    # 2. Assemble chart_data object
    ci_lower = {item["date"]: item.get("lower_80") for item in forecast_list if item.get("date") and item.get("lower_80") is not None}
    ci_upper = {item["date"]: item.get("upper_80") for item in forecast_list if item.get("date") and item.get("upper_80") is not None}

    chart_data = {
        "history": record.get("history", []),
        "forecast": forecast_list,
        "confidence_interval": {
            "lower": ci_lower,
            "upper": ci_upper,
        },
        "train_end_date": record.get("train_end_date"),
    }

    # 3. Final response object
    response_data = {
        "product_code": record.get("product_code"),
        "model": record.get("model"),
        "metrics": record.get("metrics"),
        "forecast_quantity": total_forecast_qty,
        "chart_data": chart_data,
    }

    dur = (perf_counter() - t0) * 1000
    log.info(
        f"GET /forecast/sku returned 1 record for P={product_code}, M={model} in {dur:.1f} ms"
    )

    return response_data


@router.get("/forecast/sku/models")
def get_available_sku_models():
    """Returns a list of available models for SKU-level forecasting."""
    try:
        models = get_sku_models()
        return {"models": models}
    except Exception as e:
        log.info(f"Discovered SKU models: {models}")
    return models


class SafetyStockRequest(BaseModel):
    product_code: str
    model: str
    service_level: float = Field(..., gt=0, lt=1, description="Service Level must be between 0 and 1")
    lead_time: float = Field(..., gt=0, description="Lead Time must be positive")
    lead_time_std: float = Field(..., ge=0, description="Lead Time Std Dev must be non-negative")


@router.post("/forecast/safety-stock")
def get_safety_stock(request: SafetyStockRequest = Body(...)):
    """Tính toán tồn kho an toàn dựa trên dữ liệu lịch sử và các biến về thời gian chờ."""
    log.info(f"POST /forecast/safety-stock called with: {request.dict()}")

    # 1. Lấy các chỉ số thống kê về nhu cầu từ dữ liệu lịch sử
    demand_stats = get_demand_stats(product_code=request.product_code, model=request.model)
    if not demand_stats:
        raise HTTPException(
            status_code=404,
            detail=f"Không thể tính toán chỉ số nhu cầu cho sản phẩm '{request.product_code}' với mô hình '{request.model}'. Dữ liệu lịch sử có thể bị thiếu hoặc không đủ."
        )

    # 2. Tính toán tồn kho an toàn
    try:
        safety_stock = calculate_safety_stock(
            demand_std=demand_stats["demand_std"],
            demand_mean=demand_stats["demand_mean"],
            service_level=request.service_level,
            lead_time=request.lead_time,
            lead_time_std=request.lead_time_std,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Lấy lại dữ liệu biểu đồ gốc để trả về cùng kết quả
    original_record = find_sku_forecast_record(product_code=request.product_code, model=request.model)
    
    response = {
        "product_code": request.product_code,
        "safety_stock": safety_stock,
        "chart_data": original_record, # Trả về toàn bộ record gốc
    }

    log.info(f"Tồn kho an toàn cho {request.product_code}: {safety_stock}")
    return response

