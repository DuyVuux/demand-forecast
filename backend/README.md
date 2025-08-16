# Backend - Demand Forecast API (FastAPI)

## Chức năng
- API dự báo theo sản phẩm và theo sản phẩm & khách hàng
- Upload CSV, lưu mẫu vào SQLite và trả kết quả JSON
- Logging đầy đủ vào `backend/logs/app.log`

## Cấu trúc
```
backend/
  app/
    main.py
    db.py
    routers/forecast.py
    services/forecast_service.py
    utils/logger.py
    models/schemas.py
  data/
    app.db (tự tạo khi chạy)
    product_sales_sample.csv
    product_customer_sales_sample.csv
  logs/
    app.log
  requirements.txt
```

## Chạy local
1) Tạo Python venv tại gốc repo (khuyến nghị `.venv`):
```
python3 -m venv .venv
source .venv/bin/activate
```

2) Cài dependencies:
```
pip install -r backend/requirements.txt
```

3) Chạy server (khuyến nghị port 8010) bằng uvicorn:
```
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8010 --reload
```

Nếu cần chạy trên 8008:
```
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8008 --reload
```

4) Kiểm tra health bằng việc gọi hai endpoint sau từ frontend hoặc Postman:
- `POST http://localhost:8010/forecast/product`
- `POST http://localhost:8010/forecast/product_customer`

## Lưu ý Frontend
- Frontend dev server chạy trên port `3004`.
- Cấu hình API qua biến môi trường `VITE_API_BASE` trong file `frontend/.env.development`:
```
VITE_API_BASE=http://localhost:8010
```

## Module Phân Tích Dữ Liệu (Analysis)
Module mới cung cấp các API để upload file dữ liệu raw (CSV/Excel/Parquet) và trả về kết quả phân tích tổng quan, chất lượng dữ liệu, insight và ma trận tương quan.

### Bảo mật & JWT
Các API Analysis yêu cầu JWT hợp lệ (không còn cung cấp token demo).
Sử dụng header `Authorization: Bearer <token>` khi gọi API.
 - Phân quyền:
  - Upload cần role: `analyst` hoặc `admin`.
  - Các GET khác: `viewer`/`analyst`/`admin`.

### Endpoints
- `POST /analysis/upload` (form-data: file)
  - Tạo job phân tích async, trả `{ job_id, status }`.
- `GET /analysis/status/{job_id}`
  - Tra cứu trạng thái job: `queued | processing | done | error`.
- `GET /analysis/summary?job_id=...`
- `GET /analysis/quality?job_id=...`
- `GET /analysis/insights?job_id=...`
- `GET /analysis/correlation?job_id=...`
- `GET /analysis/columns/{name}?job_id=...`
- `GET /analysis/export/json?job_id=...`
- `GET /analysis/export/csv?job_id=...` (xuất overview.columns)

### Ví dụ sử dụng bằng curl
```
# 1) Chuẩn bị JWT hợp lệ từ hệ thống xác thực của bạn
# export TOKEN="<JWT của bạn>"

# 2) Upload file để phân tích
JOB=$(curl -s -H "Authorization: Bearer $TOKEN" -F "file=@backend/data/mock_data/product_sales_sample.csv" http://localhost:8010/analysis/upload)
JOB_ID=$(echo "$JOB" | jq -r .job_id)

# 3) Kiểm tra trạng thái đến khi done
curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8010/analysis/status/$JOB_ID

# 4) Lấy summary / quality / insights / correlation
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8010/analysis/summary?job_id=$JOB_ID"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8010/analysis/quality?job_id=$JOB_ID"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8010/analysis/insights?job_id=$JOB_ID"
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8010/analysis/correlation?job_id=$JOB_ID"
```

## Định dạng CSV
- Bài toán 1: `product_id, date, quantity_sold`
- Bài toán 2: `product_id, customer_id, date, quantity_sold`

Lưu ý: cột `date` cần parse được dạng ngày (YYYY-MM-DD).
