# ADY201m — Tìm hiểu quy trình xây dựng mô hình Machine Learning

Đây là **dự án học tập dành cho sinh viên năm nhất**, giúp làm quen với một quy trình Machine Learning từ **Business Understanding** đến **Model Evaluation**. Mục tiêu là hiểu cách đặt bài toán, xử lý dữ liệu, tìm bằng chứng và đánh giá mô hình, thay vì chỉ chạy thuật toán để lấy một con số Accuracy.

Dự án sử dụng dữ liệu khảo sát sức khỏe **CDC BRFSS2015**, tập trung vào người **30–59 tuổi**, để phân tích và phân loại nhãn **tiền tiểu đường/tiểu đường**. Nội dung phục vụ học tập; đây không phải công cụ chẩn đoán y khoa hoặc mô hình dự báo phát bệnh trong tương lai.

## Quy trình học tập

| Bước | Nội dung thực hành |
|---|---|
| **1. Business Understanding** | Xác định vấn đề, đối tượng, câu hỏi nghiên cứu và mục tiêu đánh giá |
| **2. Data Understanding** | Tìm hiểu nguồn dữ liệu, ý nghĩa biến, nhãn, phân bố và chất lượng dữ liệu |
| **3. Data Preparation** | Xử lý missing và mã khảo sát, chuẩn hóa dữ liệu, kiểm tra ngoại lệ và đối chiếu giữ/bỏ duplicate |
| **4. Exploratory Data Analysis** | Dùng SQL và Python để tìm xu hướng; trực quan bằng histogram, biểu đồ tròn, boxplot và heatmap |
| **5. Feature Engineering & Selection** | Tạo biến từ giả thuyết EDA; đọc tương quan, kiểm định đơn biến và VIF trước khi đề xuất giữ/bỏ biến |
| **6. Model Training** | Xây dựng Pipeline với Logistic Regression, Decision Tree, Random Forest và XGBoost; thử trọng số lớp, NearMiss và SMOTENC |
| **7. Model Evaluation** | So sánh Accuracy, Precision, Recall, F1 và confusion matrix; giải thích đánh đổi và giới hạn của kết quả |

## Cấu trúc repository

```text
.
├── data_đầu_vào/
│   └── LLCP2015XPT.zip
├── on_going1/
│   └── On_going_1_nhom_6_age30_59.ipynb
└── on_going2/
    ├── Ongoing2_5_file_dau_vao/
    │   ├── data/
    │   │   ├── cleaned_cdc2015_keep_duplicates.csv
    │   │   ├── cleaned_cdc2015_no_duplicates.csv
    │   │   └── dataset_metadata.json
    │   ├── split_manifest.csv
    │   └── split_metadata.json
    └── final_da_chinh_sua.ipynb
```

- **Ongoing 1:** hiểu bài toán, đọc ZIP nguồn, khảo sát chất lượng dữ liệu, làm sạch và so sánh trước/sau preprocessing.
- **Ongoing 2:** nhập dữ liệu sạch vào SQLite, EDA trên Train, tạo/chọn feature, huấn luyện và đánh giá. Năm file đầu vào đã được chuẩn bị sẵn; có thể chạy Ongoing 2 mà không chạy Ongoing 1 trước.
- **`.runtime/`:** được tạo trong `on_going2` khi chạy để lưu mã hỗ trợ, bảng, hình, cache và model. Mã hỗ trợ cần thiết đã được nhúng trong notebook. Thư mục này không được đẩy lên GitHub.

## Cài đặt và chạy

Cần có **Git**, **Python 3** và trình mở notebook như **JupyterLab** hoặc **VS Code với extension Python/Jupyter**. Phiên bản Python đã dùng để kiểm tra dự án là **3.14.1**.

### 1. Clone dự án

```bash
git clone https://github.com/HipNgx/ADY201m_nh-m_6.git
cd ADY201m_nh-m_6
```

### 2. Tạo môi trường và cài thư viện

**Windows — PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install jupyterlab ipykernel pandas numpy scipy matplotlib seaborn scikit-learn xgboost imbalanced-learn sklearn-compat joblib threadpoolctl
.\.venv\Scripts\python.exe -m jupyterlab
```

**macOS/Linux:**

```bash
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install jupyterlab ipykernel pandas numpy scipy matplotlib seaborn scikit-learn xgboost imbalanced-learn sklearn-compat joblib threadpoolctl
.venv/bin/python -m jupyterlab
```

Nếu dùng VS Code, mở thư mục repository, mở notebook và chọn kernel Python thuộc môi trường `.venv` vừa tạo. Không cần cài riêng database server: SQLite đi kèm Python.

### 3. Chọn notebook

**Muốn xem toàn bộ quá trình từ dữ liệu thô:**

1. Mở `on_going1/On_going_1_nhom_6_age30_59.ipynb`.
2. Chạy các cell từ trên xuống. Notebook tìm ZIP trong `data_đầu_vào/` và tạo file làm việc dưới `data_đầu_vào/.work/`.
3. Dữ liệu sạch được xuất vào `on_going2/Ongoing2_5_file_dau_vao/data/`. Các bước đọc/ghi dữ liệu thô cần thêm RAM và dung lượng đĩa.

**Muốn bắt đầu ngay với EDA và huấn luyện:**

1. Mở `on_going2/final_da_chinh_sua.ipynb`.
2. Giữ nguyên vị trí năm file input như sơ đồ. Không cần ZIP nguồn cho riêng Ongoing 2.
3. Chạy từ thư mục gốc repository hoặc thư mục `on_going2`.
4. Chạy các cell khởi tạo trước, sau đó lần lượt EDA, feature engineering và huấn luyện/đánh giá.

**Chỉ muốn đọc báo cáo:** các bảng và biểu đồ đã được lưu trong notebook; có thể mở xem mà không chạy lại. Nếu chạy toàn bộ trên một bản clone mới, các cell huấn luyện sẽ thực hiện lại các thí nghiệm vì model/cache không nằm trên GitHub. Kết quả đã được xác minh trong `.runtime` sẽ được tái dùng ở những cell có cơ chế cache.

Khi chạy lại một phiên phân tích, nên **Restart Kernel** rồi chạy theo thứ tự để tránh bảng/view SQLite từ lần trước còn tồn tại. Chạy các cell SQL hoặc EDA không yêu cầu chạy lại toàn bộ phần huấn luyện.

## Dữ liệu và cách đọc kết quả

- Bản sạch chính có **116.662 hồ sơ, 21 feature và một nhãn**. Bản đối chiếu bỏ duplicate có **102.826 hồ sơ**.
- Nhãn `1` gộp `DIABETE3=1/4`; nhãn `0` là `DIABETE3=3`. Loại trường hợp chỉ tiểu đường khi mang thai trước khi gộp nhãn.
- Train/Test được chia theo nhóm profile 21 feature. EDA, preprocessing và resampling sử dụng Train; Test không được cân bằng lại bằng NearMiss/SMOTENC.
- `Age` là **mã nhóm tuổi 3–8**, tương ứng 30–34 đến 55–59, không phải tuổi chính xác.
- Dữ liệu mất cân bằng: luôn đoán lớp 0 vẫn có Accuracy cao nhưng không phát hiện được lớp 1. Vì vậy cần đọc Precision, Recall và F1 cùng Accuracy.
- Các kết quả Test đã được xem trong quá trình phát triển. Thứ hạng mô hình là đối chiếu khám phá, chưa phải xác nhận độc lập hoặc bằng chứng nhân quả.
- Baseline mô hình cũ được giữ với đúng nguồn và loại trọng số; không gọi kết quả weighted là đối chứng unweighted.

## Công cụ và phạm vi

Python với pandas, NumPy, scipy, matplotlib, seaborn, scikit-learn, XGBoost và imbalanced-learn; SQLite xử lý truy vấn và tổng hợp dữ liệu. Logistic Regression phục vụ bài toán phân loại nhị phân, không đồng nghĩa với dự báo chuỗi thời gian. Dashboard Power BI/Looker và phần diễn giải hệ số hồi quy chi tiết là hướng mở rộng, chưa phải sản phẩm đã hoàn thành trong repository.

## Nhóm thực hiện

**Nhóm 6 — AI2104 — ADY201m**

| Thành viên | Mã sinh viên |
|---|---|
| Trần Tuấn Hiệp | HE211144 |
| Nguyễn Thế Hải | HE211655 |
| Trần Công Du | HE211007 |
