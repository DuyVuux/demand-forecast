# **Chương 3: Phân tích và Thiết kế Hệ thống**

Chương này trình bày chi tiết quá trình phân tích các yêu cầu, thiết kế kiến trúc tổng thể và thiết kế chi tiết các thành phần của hệ thống "Demand Forecasting Portal". Mục tiêu của chương là cung cấp một cái nhìn toàn diện và sâu sắc về mặt kỹ thuật, làm rõ cách hệ thống được xây dựng để giải quyết bài toán dự báo nhu cầu cho doanh nghiệp.

---

## **3.1. Phân tích yêu cầu**

Phân tích yêu cầu là giai đoạn nền tảng, xác định rõ các chức năng, dữ liệu và ràng buộc của hệ thống. Kết quả của giai đoạn này là cơ sở để định hình kiến trúc và các quyết định thiết kế sau này.

### **3.1.1. Dữ liệu đầu vào (Input)**

Hệ thống được thiết kế để xử lý dữ liệu bán hàng lịch sử do người dùng cung cấp. Dữ liệu này là yếu tố cốt lõi để các mô hình dự báo hoạt động.

*   **Nguồn dữ liệu**: Người dùng sẽ tải lên (upload) một tệp tin chứa dữ liệu bán hàng.
*   **Định dạng tệp**: Hệ thống chấp nhận định dạng tệp `CSV (Comma-Separated Values)`. Đây là định dạng phổ biến, dễ dàng xuất ra từ các hệ thống quản lý bán hàng (POS), ERP hoặc các phần mềm bảng tính như Microsoft Excel.
*   **Cấu trúc dữ liệu**: Tệp CSV đầu vào phải tuân thủ một cấu trúc cột nghiêm ngặt để đảm bảo tính nhất quán và khả năng xử lý tự động. Cụ thể, các trường sau được yêu cầu:
    *   `date`: Ngày phát sinh giao dịch (định dạng `YYYY-MM-DD`).
    *   `product_id`: Mã định danh duy nhất cho sản phẩm (SKU).
    *   `customer_id`: Mã định danh duy nhất cho khách hàng. Đối với dự báo chỉ theo sản phẩm, cột này có thể để trống hoặc không tồn tại.
    *   `quantity_sold`: Số lượng sản phẩm đã bán trong giao dịch.
    *   Các trường tùy chọn khác như `price` (giá bán), `region` (khu vực) có thể được bao gồm. Hệ thống sẽ lưu trữ nhưng không sử dụng trong các mô hình dự báo ở phiên bản hiện tại.

*   **Cách cung cấp**: Người dùng tương tác với giao diện web, chọn tệp CSV từ máy tính cá nhân và tải lên hệ thống thông qua một API endpoint chuyên dụng. Hệ thống sẽ tự động phân tích và bắt đầu một quy trình xử lý ngầm (asynchronously).

### **3.1.2. Dữ liệu đầu ra (Output)**

Kết quả đầu ra của hệ thống là các thông tin dự báo và phân tích được trình bày một cách trực quan, dễ hiểu, hỗ trợ việc ra quyết định.

*   **Dự báo nhu cầu (Demand Forecast)**:
    *   **PC Forecast**: Bảng dữ liệu và biểu đồ dự báo số lượng bán theo từng cặp Sản phẩm - Khách hàng (`product_id`, `customer_id`) cho một khoảng thời gian trong tương lai (ví dụ: 30, 60, 90 ngày tới).
    *   **SKU Forecast**: Bảng dữ liệu và biểu đồ dự báo tổng số lượng bán cho từng sản phẩm (`product_id`) trong tương lai.
*   **Tính toán Safety Stock (Hàng tồn kho an toàn)**:
    *   Hệ thống cung cấp công cụ cho phép người dùng nhập các tham số như `lead time` (thời gian chờ hàng) và `service level` (mức độ dịch vụ mong muốn).
    *   Dựa trên độ lệch của nhu cầu trong quá khứ, hệ thống sẽ tính toán và đề xuất mức tồn kho an toàn cần thiết để giảm thiểu rủi ro hết hàng.
*   **Hình thức trình bày**:
    *   **Báo cáo dạng bảng (Tabular Reports)**: Hiển thị chi tiết dữ liệu dự báo, cho phép sắp xếp, lọc và tìm kiếm.
    *   **Biểu đồ (Charts)**: Trực quan hóa dữ liệu lịch sử và kết quả dự báo trên cùng một biểu đồ đường (line chart), giúp người dùng dễ dàng so sánh và nhận diện xu hướng.
    *   **Dashboard trực quan**: Một trang tổng quan, hiển thị các chỉ số hiệu suất chính (KPIs), các biểu đồ tóm tắt và các thông tin nổi bật từ kết quả phân tích.
    *   **Export báo cáo**: Người dùng có thể xuất kết quả dự báo ra tệp `CSV` để lưu trữ hoặc sử dụng trong các công cụ phân tích khác.

### **3.1.3. Yêu cầu chức năng (Functional Requirements)**

*   **FR1: Quản lý dữ liệu**: Người dùng có khả năng tải lên tệp dữ liệu bán hàng (định dạng CSV).
*   **FR2: Xử lý và Phân tích**: Hệ thống phải tự động xử lý (làm sạch, tổng hợp) dữ liệu, sau đó chạy các mô hình dự báo để tạo ra kết quả.
*   **FR3: Theo dõi tiến trình**: Người dùng có thể theo dõi trạng thái của tác vụ phân tích (ví dụ: "Đang xử lý", "Hoàn thành", "Lỗi") thông qua một mã định danh tác vụ (Job ID).
*   **FR4: Hiển thị kết quả**: Hệ thống phải hiển thị kết quả dự báo dưới dạng bảng và biểu đồ trực quan.
*   **FR5: Tương tác với kết quả**: Người dùng có thể lọc, sắp xếp dữ liệu dự báo theo sản phẩm, khách hàng.
*   **FR6: Tính toán Safety Stock**: Cung cấp giao diện để người dùng nhập tham số và nhận về kết quả tồn kho an toàn.
*   **FR7: Xuất báo cáo**: Cho phép người dùng xuất các bảng dữ liệu dự báo ra tệp tin.

### **3.1.4. Yêu cầu phi chức năng (Non-functional Requirements)**

*   **NFR1: Hiệu năng (Performance)**: Thời gian xử lý từ lúc upload file đến khi có kết quả phải được tối ưu. Với tập dữ liệu trung bình (<100,000 dòng), quá trình xử lý không nên kéo dài quá 5 phút. Điều này đạt được thông qua việc xử lý bất đồng bộ (background tasks) và sử dụng các thư viện tính toán hiệu năng cao như Pandas.
*   **NFR2: Tính dễ sử dụng (Usability)**: Giao diện người dùng (UI) phải được thiết kế sạch sẽ, trực quan. Luồng công việc logic, dễ dàng cho cả người dùng không chuyên về kỹ thuật.
*   **NFR3: Khả năng mở rộng (Scalability)**: Kiến trúc hệ thống được thiết kế theo dạng mô-đun, cho phép dễ dàng bổ sung các mô hình dự báo mới (ví dụ: Prophet, XGBoost, LSTM) trong tương lai mà không ảnh hưởng lớn đến các thành phần hiện có.
*   **NFR4: Tính bảo mật (Security)**: Hệ thống có sẵn cơ chế xác thực người dùng dựa trên token (JWT) và phân quyền (role-based access control), đảm bảo dữ liệu của người dùng được bảo vệ.

---

## **3.2. Kiến trúc tổng thể**

Hệ thống được thiết kế theo kiến trúc 3 lớp (3-Tier Architecture) hiện đại, tách biệt rõ ràng giữa giao diện, logic nghiệp vụ và lưu trữ dữ liệu.

### **3.2.1. Mô hình kiến trúc 3 lớp**

1.  **Lớp Trình diễn (Presentation Layer - Frontend)**:
    *   **Công nghệ**: `React` (sử dụng `Vite` làm công cụ xây dựng).
    *   **Vai trò**: Chịu trách nhiệm hiển thị dữ liệu và tương tác với người dùng. Lớp này gọi các API từ Backend để lấy hoặc gửi dữ liệu.

2.  **Lớp Ứng dụng (Application Layer - Backend & ML Engine)**:
    *   **Công nghệ**: `FastAPI` (Python).
    *   **Vai trò**: Là bộ não của hệ thống, xử lý các yêu cầu HTTP từ Frontend, điều phối luồng công việc, và thực thi logic dự báo. Thành phần này bao gồm:
        *   **Web Application (Backend)**: Xử lý API, quản lý tác vụ.
        *   **Processing Engine**: Chứa các mô-đun xử lý, phân tích và tổng hợp dữ liệu từ tệp người dùng tải lên. Công cụ này sử dụng các thư viện như `Pandas` để thực hiện thống kê mô tả, xác định kiểu dữ liệu và phát hiện chuỗi thời gian.

3.  **Lớp Dữ liệu (Data Layer)**:
    *   **Công nghệ**: `SQLite` và hệ thống tệp (File System).
    *   **Vai trò**: Chịu trách nhiệm lưu trữ và quản lý dữ liệu. Sử dụng một phương pháp hybrid:
        *   **Hệ thống tệp**: Lưu trữ các tệp CSV gốc, dữ liệu trung gian và các kết quả phân tích/dự báo dưới dạng file.
        *   **Cơ sở dữ liệu SQLite**: Lưu trữ dữ liệu có cấu trúc như thông tin người dùng và dữ liệu bán hàng đã được chuẩn hóa để truy vấn nhanh.

### **3.2.2. Sơ đồ kiến trúc hệ thống**

Sơ đồ mô tả sự tương tác giữa các thành phần:

```text
[Người dùng] <--> [Trình duyệt Web: React Frontend]
      |
      | (1. HTTP Request: /analysis/upload + file.csv)
      v
[Backend: FastAPI]
      |--> (2. Tạo Job ID, lưu file vào File System)
      |--> (3. Khởi chạy Background Task cho Job ID)
      |--> (4. Trả Job ID về cho Frontend)
      |
[Background Task: Processing Engine]
      |--> (5. Đọc file dữ liệu từ File System)
      |--> (6. Phân tích dữ liệu: thống kê, xác định kiểu cột, v.v.)
      |--> (7. Lưu kết quả phân tích (dạng cache) vào File System)
      |--> (8. Cập nhật trạng thái Job: "finished")

[Frontend] <--> (10. Định kỳ kiểm tra: /analysis/status/{job_id})
[Frontend] <--> (11. Khi Job hoàn thành, lấy kết quả: /forecast/pc?job_id=...)
```

### **3.2.3. Luồng dữ liệu (Data Flow)**

1.  **Upload**: Người dùng tải tệp CSV lên. Frontend gửi request `POST /analysis/upload`.
2.  **Khởi tạo Job**: Backend nhận tệp, tạo một `job_id` duy nhất (dựa trên hash của file để tận dụng cache), lưu tệp gốc và khởi chạy một tác vụ nền (background task) để phân tích, đồng thời trả ngay `job_id` về cho Frontend.
3.  **Xử lý ngầm**: Tác vụ nền đọc và phân tích dữ liệu từ tệp gốc. Quá trình này bao gồm việc xác định các đặc trưng của cột (ví dụ: cột định danh, cột số liệu, cột ngày tháng), tính toán các thống kê mô tả, và lưu kết quả phân tích vào một bộ đệm (cache) để truy xuất nhanh sau này.
4.  **Lưu kết quả**: Kết quả dự báo và các phân tích khác được lưu vào các tệp tin trong một thư mục tương ứng với `job_id`.
5.  **Theo dõi và Hiển thị**: Frontend sử dụng `job_id` để định kỳ gọi API `GET /analysis/status/{job_id}`. Khi trạng thái là "finished", Frontend sẽ gọi các API khác (`/forecast/pc`, `/forecast/sku`) để lấy và hiển thị dữ liệu kết quả.

---

## **3.3. Thiết kế thành phần**

### **3.3.1. Thiết kế dữ liệu**

Thiết kế dữ liệu của hệ thống kết hợp giữa cơ sở dữ liệu quan hệ và lưu trữ dựa trên tệp để tối ưu cho từng loại dữ liệu.

*   **Cơ sở dữ liệu (SQLite)**: Lưu trữ dữ liệu cần truy vấn và có cấu trúc rõ ràng.
    *   **Bảng `users`**: Quản lý thông tin người dùng.
        *   `id` (INTEGER, PK): Khóa chính.
        *   `username` (STRING): Tên đăng nhập.
        *   `email` (STRING): Email.
        *   `password_hash` (STRING): Mật khẩu đã được băm.
        *   `role` (STRING): Vai trò (ví dụ: 'user', 'admin').
        *   `is_active` (BOOLEAN): Trạng thái hoạt động.
    *   **Bảng `product_sales`**: Lưu dữ liệu bán hàng đã chuẩn hóa theo sản phẩm.
        *   `id` (INTEGER, PK): Khóa chính.
        *   `product_id` (STRING): Mã sản phẩm.
        *   `date` (DATE): Ngày bán.
        *   `quantity_sold` (FLOAT): Số lượng bán.
    *   **Bảng `product_customer_sales`**: Lưu dữ liệu bán hàng đã chuẩn hóa theo sản phẩm và khách hàng.
        *   `id` (INTEGER, PK): Khóa chính.
        *   `product_id` (STRING): Mã sản phẩm.
        *   `customer_id` (STRING): Mã khách hàng.
        *   `date` (DATE): Ngày bán.
        *   `quantity_sold` (FLOAT): Số lượng bán.

*   **Hệ thống tệp (File System)**: Dùng cho dữ liệu lớn, dữ liệu trung gian và kết quả.
    *   `data/raw_data/`: Lưu các tệp CSV gốc người dùng tải lên.
    *   `data/jobs/{job_id}/`: Mỗi tác vụ có một thư mục riêng chứa:
        *   `status.json`: Tệp tin lưu trạng thái hiện tại của job (ví dụ: `{"status": "processing"}`).
        *   `results.json`: Tệp tin chứa kết quả phân tích tổng hợp, insights, chất lượng dữ liệu.
        *   `pc_forecast.csv`: Kết quả dự báo theo sản phẩm-khách hàng.
        *   `sku_forecast.csv`: Kết quả dự báo theo sản phẩm.

### **3.3.2. Thiết kế API**

Các API được thiết kế theo chuẩn RESTful, sử dụng JSON làm định dạng trao đổi dữ liệu.

*   **Authentication (`/auth`)**
    *   `POST /auth/token`: Đăng nhập, nhận về JWT token.
    *   `POST /auth/register`: Đăng ký người dùng mới.

*   **Analysis (`/analysis`)**
    *   `POST /analysis/upload`: Tải lên tệp dữ liệu. 
        *   **Input**: `UploadFile`.
        *   **Output**: `{"job_id": "...", "filename": "..."}`.
    *   `GET /analysis/status/{job_id}`: Lấy trạng thái của một tác vụ.
        *   **Input**: `job_id` (path parameter).
        *   **Output**: `{"status": "...", "progress": ...}`.
    *   `GET /analysis/summary?job_id=...`: Lấy thông tin tóm tắt về dữ liệu đã phân tích.
    *   `GET /analysis/insights?job_id=...`: Lấy các phát hiện tự động từ dữ liệu.

*   **Forecast (`/forecast`)**
    *   `GET /forecast/pc?job_id=...`: Lấy kết quả dự báo theo Sản phẩm-Khách hàng.
        *   **Input**: `job_id` (query parameter).
        *   **Output**: JSON chứa danh sách các điểm dữ liệu dự báo.
    *   `GET /forecast/sku?job_id=...`: Lấy kết quả dự báo theo Sản phẩm.
        *   **Input**: `job_id` (query parameter).
        *   **Output**: JSON chứa danh sách các điểm dữ liệu dự báo.
    *   `POST /forecast/safety-stock`: Tính toán tồn kho an toàn.
        *   **Input**: `{"historical_data": [...], "lead_time": 30, "service_level": 0.95}`.
        *   **Output**: `{"safety_stock": ...}`.

*   **Export (`/export`)**
    *   `GET /export/report?job_id=...&type=pc`: Xuất báo cáo dự báo ra file CSV.
        *   **Input**: `job_id`, `type` (loại báo cáo).
        *   **Output**: File `CSV`.

### **3.3.3. Thiết kế giao diện web**

Giao diện người dùng được xây dựng bằng React, tập trung vào trải nghiệm người dùng rõ ràng và hiệu quả.

*   **Trang Home/Dashboard**: Trang chủ sau khi đăng nhập, hiển thị các thông tin tổng quan, danh sách các tác vụ đã thực hiện gần đây và điều hướng nhanh đến các chức năng chính.
*   **Trang Data Analysis**: 
    *   Khu vực upload file trực quan, cho phép kéo-thả (drag-and-drop).
    *   Sau khi phân tích xong, trang này sẽ hiển thị các kết quả tổng quan về chất lượng dữ liệu, các insight chính và cấu hình phân tích.
*   **Trang PC Forecast**: 
    *   Hiển thị bảng dữ liệu dự báo chi tiết theo từng cặp sản phẩm-khách hàng, có chức năng tìm kiếm và lọc.
    *   Biểu đồ đường cho phép chọn một hoặc nhiều cặp sản phẩm-khách hàng để so sánh dữ liệu lịch sử và dự báo.
*   **Trang SKU Forecast**:
    *   Tương tự trang PC Forecast nhưng dữ liệu được tổng hợp theo từng sản phẩm.
    *   Tích hợp form nhập liệu để tính toán Safety Stock. Kết quả sẽ được hiển thị ngay bên cạnh.
*   **Các yếu tố UI/UX**: Hệ thống sử dụng một bộ quy tắc thiết kế nhất quán về `spacing` (khoảng cách), `typography` (kiểu chữ), và `color scheme` (bảng màu) để tạo cảm giác chuyên nghiệp. Thiết kế đáp ứng (responsive design) đảm bảo trải nghiệm tốt trên các kích thước màn hình khác nhau.