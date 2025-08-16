# Demand Forecasting Web App

Web app đơn giản dự báo nhu cầu với 2 chức năng:
- Dự báo theo sản phẩm
- Dự báo theo sản phẩm & khách hàng

## Kiến trúc
- Frontend: React + Vite (port 3003)
- Backend: FastAPI modular (port 8008)
- ML: statsmodels (ARIMA), scikit-learn (Linear Regression, RandomForestRegressor)
- Database: SQLite (lưu dữ liệu mẫu khi upload)
- Logging: `backend/logs/app.log`

## Cấu trúc thư mục
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
    product_sales_sample.csv
    product_customer_sales_sample.csv
  logs/
    app.log
  requirements.txt
frontend/
  index.html
  vite.config.js
  package.json
  .env.development
  public/
    samples/
      product_sales_sample.csv
      product_customer_sales_sample.csv
  src/
    main.jsx
    App.jsx
    api.js
    styles.css
    components/
      ForecastForm.jsx
      ForecastTable.jsx
      ForecastChart.jsx
```

## Yêu cầu hệ thống
- Python 3.9+
- Node.js 18+

## Thiết lập và chạy
1) Tạo Python venv và cài backend deps (tại root repo):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

2) Chạy backend (8008):
```bash
# Cách A: dùng uvicorn module
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8008 --reload
# Cách B: chạy file main (đường dẫn làm việc là root repo)
.venv/bin/python backend/app/main.py
```

3) Cài frontend và chạy dev server (3003):
```bash
cd frontend
npm install
npm run dev
```

4) Mở UI tại http://localhost:3003 và upload CSV mẫu trong `frontend/public/samples/` hoặc tạo file CSV của bạn.

## Định dạng CSV
- Bài toán 1: `product_id,date,quantity_sold`
- Bài toán 2: `product_id,customer_id,date,quantity_sold`

## API
- `POST /forecast/product` (multipart form):
  - file: CSV
  - horizon: số ngày dự báo (mặc định 7)
  - model: `arima` | `linreg` | `rf`
- `POST /forecast/product_customer` (multipart form), tương tự.

## Logging
- Backend ghi log vào `backend/logs/app.log` với request, lỗi, và tiến trình dự báo.

## Ghi chú
- Mô hình và pipeline được tối giản để demo. Có thể thay bằng mô hình phức tạp hơn (SARIMA, Prophet, XGBoost, LSTM, ...).
