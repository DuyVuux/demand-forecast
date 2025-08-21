# Chương 4: Triển khai và Kiểm thử Hệ thống

Chương này trình bày chi tiết về quá trình triển khai các thành phần của hệ thống Demand Forecasting Portal, từ việc tính toán các chỉ số tồn kho, xây dựng ứng dụng web, cho đến các phương pháp kiểm thử đã được áp dụng để đảm bảo chất lượng.

## 4.3. Tính toán tồn kho tối ưu

Một trong những mục tiêu cốt lõi của hệ thống là cung cấp các chỉ số quan trọng giúp tối ưu hóa lượng hàng tồn kho. Việc duy trì tồn kho hợp lý giúp doanh nghiệp cân bằng giữa chi phí lưu trữ và rủi ro hết hàng, từ đó tối đa hóa lợi nhuận và sự hài lòng của khách hàng. Hệ thống tập trung vào hai chỉ số chính: Tồn kho an toàn (Safety Stock) và Điểm tái đặt hàng (Reorder Point).

### **4.3.1. Tồn kho an toàn (Safety Stock)**

**Ý nghĩa nghiệp vụ:**
Tồn kho an toàn là lượng hàng tồn kho "đệm" được duy trì để đối phó với sự không chắc chắn từ nhu cầu của khách hàng và sự biến động trong thời gian giao hàng của nhà cung cấp. Nếu không có tồn kho an toàn, bất kỳ sự gia tăng đột biến nào về nhu cầu hoặc sự chậm trễ trong giao hàng đều có thể dẫn đến tình trạng hết hàng (stockout), gây mất doanh thu và ảnh hưởng đến uy tín.

**Công thức tính toán:**
Hệ thống triển khai công thức tính tồn kho an toàn trong trường hợp cả nhu cầu và thời gian giao hàng (lead time) đều có sự biến động. Đây là phương pháp toàn diện, phản ánh đúng rủi ro trong chuỗi cung ứng thực tế.

Công thức được lập trình trong `services/inventory_service.py` như sau:

```
Safety Stock = Z * sqrt((σD² * LT) + (μD² * σLT²))
```

Trong đó:
*   `Z`: Là Z-score, đại diện cho mức độ tin cậy thống kê, được tính từ Mức độ dịch vụ (Service Level) mong muốn. Ví dụ, Service Level 95% (chấp nhận 5% rủi ro hết hàng) tương ứng Z ≈ 1.645. Hệ thống sử dụng thư viện `scipy.stats.norm` để tự động tính toán giá trị này.
*   `μD` (demand_mean): Nhu cầu trung bình trong một đơn vị thời gian (ví dụ: số sản phẩm bán ra mỗi ngày).
*   `σD` (demand_std): Độ lệch chuẩn của nhu cầu, đo lường mức độ biến động của nhu cầu so với giá trị trung bình.
*   `LT` (lead_time): Thời gian chờ giao hàng trung bình, tính từ lúc đặt hàng đến lúc nhận hàng.
*   `σLT` (lead_time_std): Độ lệch chuẩn của thời gian chờ, đo lường sự không chắc chắn trong thời gian giao hàng.

**Ví dụ minh họa:**
Giả sử một sản phẩm có các thông số sau:
*   Nhu cầu trung bình (`μD`): 100 sản phẩm/ngày
*   Độ lệch chuẩn nhu cầu (`σD`): 15 sản phẩm
*   Thời gian chờ trung bình (`LT`): 5 ngày
*   Độ lệch chuẩn thời gian chờ (`σLT`): 1 ngày
*   Mức độ dịch vụ mong muốn: 95% (Z ≈ 1.645)

Áp dụng công thức:
`Safety Stock = 1.645 * sqrt((15² * 5) + (100² * 1²)) ≈ 255`
Vậy, doanh nghiệp cần duy trì khoảng 255 sản phẩm làm tồn kho an toàn.

### **4.3.2. Điểm tái đặt hàng (Reorder Point - ROP)**

**Ý nghĩa nghiệp vụ:**
Điểm tái đặt hàng là mức tồn kho mà khi số lượng hàng trong kho giảm xuống đến mức này, doanh nghiệp cần phải đặt một đơn hàng mới. Mục tiêu của ROP là đảm bảo đơn hàng mới sẽ về đến kho ngay trước khi lượng tồn kho an toàn bị sử dụng hết, giúp chuỗi cung ứng hoạt động liên tục.

**Công thức tính toán:**
Mặc dù hệ thống không có một API riêng để trả về ROP, chỉ số này được tính toán ở phía giao diện người dùng (Frontend) dựa trên các kết quả có sẵn từ backend. Công thức được áp dụng là:

```
ROP = (Nhu cầu trung bình * Thời gian chờ trung bình) + Tồn kho an toàn

### 4.2.1. Kiểm thử API Backend

Sử dụng các công cụ như **Swagger UI** (tự động tích hợp trong FastAPI) và **Postman** để kiểm tra từng API một cách độc lập.

*   **Mục tiêu**: Xác minh rằng mỗi API hoạt động đúng như đặc tả, bao gồm việc xử lý các đầu vào hợp lệ, trả về mã trạng thái chính xác, và xử lý các trường hợp lỗi một cách an toàn.
*   **Kịch bản ví dụ (`POST /forecast/safety-stock`)**: 
    1.  **Thành công**: Gửi một request với đầy đủ các tham số hợp lệ. Mong đợi nhận về status 200 và một đối tượng JSON chứa giá trị `safety_stock`.
    2.  **Lỗi validation**: Gửi một request với `service_level` > 1. Mong đợi nhận về status 422 (Unprocessable Entity) và thông báo lỗi rõ ràng.
    3.  **Dữ liệu không tồn tại**: Gửi request cho một `product_code` không có trong dữ liệu. Mong đợi nhận về status 404 (Not Found).

### 4.2.2. Kiểm thử Giao diện Người dùng (UI)

Kiểm thử các luồng hoạt động của người dùng trực tiếp trên trình duyệt để đảm bảo trải nghiệm người dùng là nhất quán và không có lỗi.

*   **Mục tiêu**: Đảm bảo giao diện hiển thị chính xác, các nút bấm và form hoạt động đúng chức năng, và luồng dữ liệu từ người dùng đến máy chủ và ngược lại là thông suốt.
*   **Kịch bản ví dụ (Luồng tính toán tồn kho)**:
    1.  Điều hướng đến trang xem dự báo SKU.
    2.  Chọn một sản phẩm và một mô hình từ danh sách.
    3.  Kiểm tra xem biểu đồ dự báo và các số liệu thống kê có được tải và hiển thị chính xác không.
    4.  Nhập các giá trị vào form tính toán Safety Stock (ví dụ: Service Level = 0.95, Lead Time = 10).
    5.  Nhấn nút "Calculate" và xác minh rằng kết quả Safety Stock được hiển thị trên giao diện.
    6.  Thử nhập một giá trị không hợp lệ (ví dụ: chữ cái vào ô Lead Time) và kiểm tra xem hệ thống có hiển thị thông báo lỗi phù hợp không.

### 4.2.3. Kiểm thử Dữ liệu và Logic nghiệp vụ

Đây là bước kiểm thử quan trọng nhằm xác thực tính chính xác của các thuật toán và công thức tính toán cốt lõi.

*   **Mục tiêu**: Đảm bảo rằng các kết quả tính toán (ví dụ: Safety Stock, các chỉ số thống kê) của hệ thống khớp với kết quả được tính toán thủ công.
*   **Phương pháp**: Sử dụng một bộ dữ liệu mẫu nhỏ và đơn giản. Thực hiện các phép tính tương tự bằng một công cụ đáng tin cậy (như Microsoft Excel hoặc viết script Python nhỏ). So sánh kết quả của hệ thống với kết quả tính tay để tìm ra bất kỳ sai lệch nào.

*   **Mục tiêu**: Xác minh tính đúng đắn tuyệt đối của các thuật toán phân tích và tính toán tồn kho, vốn là cốt lõi của hệ thống.
*   **Quy trình**:
    1.  **Chuẩn bị bộ dữ liệu mẫu**: Tạo một file CSV nhỏ với khoảng 10-15 dòng dữ liệu bán hàng đơn giản.
    2.  **Tính toán thủ công**: Sử dụng Microsoft Excel hoặc Google Sheets, tính toán các giá trị: tổng doanh số, nhu cầu trung bình hàng ngày (`AVERAGE`), độ lệch chuẩn nhu cầu (`STDEV.S`).
    3.  **Tải lên hệ thống**: Tải file CSV này lên ứng dụng.
    4.  **So sánh kết quả**: Đối chiếu các giá trị thống kê mà hệ thống hiển thị với kết quả đã tính toán thủ công. Sai số phải bằng 0 hoặc rất nhỏ (do làm tròn).
    5.  **Xác thực Safety Stock**: Nhập các tham số (service level, lead time) vào hệ thống. Đồng thời, sử dụng cùng các tham số đó và kết quả thống kê đã tính tay để tính Safety Stock thủ công. So sánh hai kết quả để đảm bảo logic thuật toán là chính xác.
