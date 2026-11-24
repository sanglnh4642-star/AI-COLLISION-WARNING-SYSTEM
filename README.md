# AI COLLISION WARNING SYSTEM
## HỆ THỐNG MÔ PHỎNG CẢNH BÁO NGUY CƠ VA CHẠM

### 1. Giới thiệu

AI Collision Warning System là hệ thống mô phỏng cảnh báo nguy cơ va chạm giao thông giữa phương tiện và vật cản phía trước.

Chương trình sử dụng các thông số tốc độ, khoảng cách và thời gian va chạm dự kiến (TTC) để phân tích tình huống và đưa ra mức cảnh báo phù hợp.

Giao diện được xây dựng bằng Python và Streamlit, giúp người dùng dễ dàng theo dõi và điều chỉnh quá trình mô phỏng.

### 2. Chức năng chính

- Mô phỏng dữ liệu cảm biến tốc độ và khoảng cách.
- Tính toán thời gian va chạm dự kiến (TTC).
- Tính toán quãng đường phanh và quãng đường dừng.
- Phân tích nguy cơ va chạm dựa trên cơ sở tri thức và luật cảnh báo.
- Phân loại trạng thái: An toàn, Cảnh báo, Nguy hiểm.
- Mô phỏng các tình huống giao thông có sẵn.
- Điều chỉnh tốc độ và chế độ lái.
- Hiển thị trực quan quá trình mô phỏng và biểu đồ kết quả.
- Lưu trữ và theo dõi dữ liệu mô phỏng.

### 3. Cấu trúc thư mục

```text
AI_Collision_Warning/
│
├── modules/
│   ├── sensor_simulator.py
│   ├── collision_calculator.py
│   └── collision_engine.py
│
├── knowledge/
│   └── knowledge_base.py
│
├── simulation/
│   ├── scenarios.py
│   └── simulator.py
│
├── gui/
│   ├── dashboard.py
│   └── charts.py
│
├── data/
│
├── tests/
│   └── test_scenarios.py
│
├── main.py
├── RUN.bat
├── requirements.txt
└── README.md
```

### 4. Yêu cầu cài đặt

- Hệ điều hành: Windows 10/11.
- Python tương thích với các thư viện trong dự án.
- Các thư viện được khai báo trong file `requirements.txt`.

Cài đặt thư viện bằng lệnh:

```powershell
python -m pip install -r requirements.txt
```

Nếu chưa có môi trường ảo, tạo bằng lệnh:

```powershell
python -m venv .venv
```

### 5. Hướng dẫn khởi chạy

**Cách 1: Sử dụng RUN.bat**

1. Mở thư mục dự án.
2. Nhấn đúp vào file `RUN.bat`.
3. Chờ chương trình khởi động.
4. Giao diện mô phỏng sẽ được mở trên trình duyệt.

**Cách 2: Sử dụng main.py**

Mở PowerShell tại thư mục dự án và chạy:

```powershell
.\.venv\Scripts\python.exe main.py
```

Địa chỉ giao diện mặc định:

```text
http://localhost:8501
```

### 6. Hướng dẫn sử dụng và kiểm thử

**Sử dụng giao diện:**

1. Chọn tình huống mô phỏng trong thanh điều khiển.
2. Điều chỉnh tốc độ và khoảng cách ban đầu.
3. Chọn chế độ lái: Giữ tốc độ, Tăng tốc hoặc Giảm tốc.
4. Theo dõi mức cảnh báo, TTC và quãng đường dừng.
5. Quan sát biểu đồ và kết quả mô phỏng.

**Chạy kiểm thử:**

Sử dụng lệnh:

```powershell
.\.venv\Scripts\python.exe main.py --test
```

Hoặc chạy trực tiếp bộ kiểm thử:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

Bộ kiểm thử `test_scenarios.py` hiện có 9 trường hợp kiểm thử. Kết quả thực hiện:

```text
Ran 9 tests

OK
```

### 7. Kết luận

Dự án mô phỏng hệ thống cảnh báo nguy cơ va chạm giao thông, hỗ trợ phân tích tình huống dựa trên tốc độ, khoảng cách và thời gian va chạm dự kiến. Giao diện trực quan giúp người dùng dễ dàng theo dõi, điều chỉnh và đánh giá kết quả mô phỏng.