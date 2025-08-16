# Frontend - Demand Forecast UI (React + Vite)

## Yêu cầu
- Node.js >= 18

## Cấu hình API
Tạo/sửa file `.env.development` tại `frontend/`:
```
VITE_API_BASE=http://localhost:8010
```
Backend mặc định chạy cổng `8010` (đã bật CORS cho 3004).

## Chạy dev
```bash
npm install
npm run dev -- --port 3004
```
Truy cập: http://localhost:3004

### Trang Phân Tích Dữ Liệu `/data-analysis`
- Upload file CSV/Excel/Parquet (ví dụ: `public/samples/analysis_sample.csv`).
- Chờ job xử lý xong (trạng thái `done`).
- Xem Summary, Quality, Insights, Correlation, Column Detail.
- Có thể tải kết quả JSON/CSV.

Gợi ý:
- Nếu port 3004 bận, hãy dừng tiến trình cũ (`lsof -ti tcp:3004 | xargs -r kill -9`) hoặc chọn port khác (`--port 3005`).
- Nếu đổi cổng backend, cập nhật lại `VITE_API_BASE` tương ứng.

## Build & Preview (tùy chọn)
```bash
npm run build
# Preview có thể đổi port tùy ý
npx vite preview --port 3004 --strictPort
```

## Thư mục chính
```
frontend/
  public/samples/                    # CSV mẫu để test upload
    analysis_sample.csv
  src/api.js                         # cấu hình axios (đọc VITE_API_BASE)
  src/pages/DataAnalysis.jsx         # trang /data-analysis
  src/components/ForecastForm.jsx    # upload CSV, chọn model/horizon
  src/components/ForecastTable.jsx   # hiển thị bảng kết quả
  src/components/ForecastChart.jsx   # hiển thị biểu đồ (Chart.js)
  src/App.jsx, src/main.jsx, styles.css
```

## Cách sử dụng nhanh
1) Mở UI: http://localhost:3004
2) Chọn chế độ dự báo: theo sản phẩm hoặc theo sản phẩm & khách hàng
3) Upload CSV (mẫu có ở `public/samples/`)
4) Chọn model (ARIMA / Linear Regression / Random Forest) và horizon
5) Xem kết quả bảng + biểu đồ

## Định dạng CSV
- Bài toán 1: `product_id, date, quantity_sold`
- Bài toán 2: `product_id, customer_id, date, quantity_sold`

## Troubleshooting
- Port đang bận:
```
lsof -ti tcp:3004 | xargs -r kill -9
```
- Backend không phản hồi: kiểm tra `http://localhost:8010` (hoặc cổng bạn đang dùng) và log tại `backend/logs/app.log`.
