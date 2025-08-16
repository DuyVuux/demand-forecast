from __future__ import annotations
from typing import Optional, List, Dict
from time import perf_counter
from fastapi import APIRouter, Query

from ..services.sku_forecast_service import load_sku_records
from ..utils.logger import get_logger

router = APIRouter()
log = get_logger("router.sku_forecast")


def _match_exact_str(val: Optional[str], q: Optional[str]) -> bool:
    if not q:
        return True
    if val is None:
        return False
    return str(val).strip().upper() == str(q).strip().upper()


def _sum_forecast_qty(forecast_list: Optional[List[Dict]]) -> float:
    if not forecast_list:
        return 0.0
    total = 0.0
    for it in forecast_list:
        try:
            v = it.get("forecast")
            if v is None:
                continue
            total += float(v)
        except Exception:
            continue
    return float(total)


@router.get("/forecast/sku")
def get_sku_forecast(
    product_code: Optional[str] = Query(None, description="Mã sản phẩm để lọc (tùy chọn)"),
    model: Optional[str] = Query(None, description="Tên mô hình để lọc (tùy chọn)"),
    limit: Optional[int] = Query(
        None,
        ge=1,
        le=10000,
        description="Giới hạn số điểm dự báo trên mỗi item (tùy chọn)",
    ),
    weeks: Optional[int] = Query(
        None,
        ge=1,
        le=4,
        description="Số tuần muốn dự báo (1-4). Nếu có, chỉ trả về số tuần đầu tiên trong forecast.",
    ),
):
    """Đọc kết quả dự báo SKU-level từ các file JSON và trả về danh sách bản ghi.

    - Đọc tất cả file JSON trong thư mục `data/model_result/DemandForecast_Skus/`.
    - Hỗ trợ lọc theo `product_code` và/hoặc `model`.
    - Nếu có `weeks` (1..4), chỉ lấy số tuần đầu tiên trong mảng `forecast` trên mỗi item.
    - Sau đó áp dụng `limit` để cắt bớt số điểm dự báo; nếu client KHÔNG truyền `limit`, hệ thống mặc định dùng `200`.

    Output dạng:
    {
      "count": N,
      "data": [
        {
          "product_code": "20100002",
          "model": "LightGBM",
          "metrics": {"MAE": ..., "RMSE": ..., "MAPE": ...},
          "train_end_date": "YYYY-MM-DD",
          "history": [{"date": "YYYY-MM-DD", "actual": ...}],
          "forecast": [
            {"date": "YYYY-MM-DD", "forecast": ..., "lower_80": ..., "upper_80": ...}
          ]
        }
      ]
    }
    """
    t0 = perf_counter()
    all_records: List[Dict] = load_sku_records()

    filtered = [
        r for r in all_records
        if _match_exact_str(r.get("product_code"), product_code)
        and _match_exact_str(r.get("model"), model)
    ]

    # Áp dụng weeks trước (nếu có)
    if weeks is not None:
        for r in filtered:
            fc = r.get("forecast") or []
            r["forecast"] = fc[: int(weeks)]

    # Sau đó áp dụng limit (mặc định 200 nếu client không truyền)
    eff_limit = 200 if limit is None else int(limit)
    for r in filtered:
        fc = r.get("forecast") or []
        r["forecast"] = fc[: eff_limit]

    # Tính tổng số lượng dự báo dựa trên danh sách forecast hiện có (sau khi cắt limit nếu có)
    for r in filtered:
        r["TotalForecastQty"] = _sum_forecast_qty(r.get("forecast"))

    dur = (perf_counter() - t0) * 1000
    log.info(
        f"GET /forecast/sku returned count={len(filtered)} (filter: product={product_code}, model={model}, weeks={weeks}, limit={limit}) in {dur:.1f} ms"
    )

    return {"count": len(filtered), "data": filtered}
