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

## Cấu trúc thư mục (chính)
```
backend/
  app/
  data/
    raw_data/raw_data.csv        # Dữ liệu bán hàng gốc
    model_result/                # Kết quả dự báo đã được tính toán sẵn
  requirements.txt
frontend/
  src/
  .env.development               # File cấu hình môi trường (cần tạo)
  package.json
.gitignore
README.md
```

## Yêu cầu hệ thống
- Python 3.9+
- Node.js 18+

## Thiết lập và chạy

**Ghi chú quan trọng:** Dự án đã bao gồm sẵn dữ liệu (`backend/data/raw_data/raw_data.csv`) và kết quả dự báo (`backend/data/model_result/`). Bạn có thể xem kết quả ngay sau khi chạy ứng dụng mà không cần upload lại dữ liệu.

### 1. Backend

Từ thư mục gốc của dự án:

```bash
# Tạo và kích hoạt môi trường ảo
python3 -m venv .venv
source .venv/bin/activate

# Cài đặt các thư viện cần thiết
pip install -r backend/requirements.txt

# Chạy backend server trên cổng 8008
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8008 --reload
```

### 2. Frontend

Mở một terminal khác, từ thư mục gốc của dự án:

```bash
# Di chuyển vào thư mục frontend
cd frontend

# Tạo file môi trường cho frontend
echo "VITE_API_BASE_URL=http://localhost:8008" > .env.development

# Cài đặt các gói npm
npm install

# Khởi động dev server trên cổng 3003
npm run dev
```

### 3. Truy cập ứng dụng

Mở trình duyệt và truy cập vào `http://localhost:3003`.

## Chức năng

- **Xem kết quả có sẵn:** Ứng dụng sẽ tự động tải và hiển thị các kết quả dự báo đã được tính toán trước.
- **Upload và dự báo mới:** Bạn có thể upload tệp CSV của riêng mình để thực hiện dự báo mới. Định dạng file phải tuân thủ:
  - **Dự báo theo SKU:** `product_id,date,quantity_sold`
  - **Dự báo theo SKU & Khách hàng:** `product_id,customer_id,date,quantity_sold`

## Ghi chú
- Các mô hình và pipeline được tối giản cho mục đích demo. Chúng có thể được mở rộng với các thuật toán phức tạp hơn như SARIMA, Prophet, XGBoost, LSTM, v.v.
