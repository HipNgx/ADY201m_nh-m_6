# Thử nghiệm bổ sung về feature engineering

Thư mục này lưu thí nghiệm riêng để giải thích các phép thêm, thay và rút gọn feature. Không thay đổi hai notebook báo cáo hoặc dữ liệu đầu vào của nhóm.

## Đọc kết quả

- `Bao_cao_thu_nghiem_feature_ADY201m.docx`: báo cáo tiếng Việt 9 trang. Trang 5 phân tích bộ 10; trang 6 phân tích bộ 13 so với bộ 21; trang 7 có đoạn trình bày ngắn.
- `summary.csv`: kết quả trung bình, độ lệch chuẩn giữa các fold và delta so với bộ 21 ở cùng mô hình.
- `fold_metrics.csv`: đầy đủ 280 lượt fit, gồm AP, AUC, F1, Precision, Recall và Accuracy.
- `protocol.json`: danh sách 28 phương án, công thức, tham số mô hình, phiên bản thư viện và hash đầu vào.
- `fold_counts.csv`: kích thước phần fit và validation của từng fold.
- `*__oof.npz`: 56 file dự đoán ngoài fold, mỗi file gồm row_id, nhãn thật, fold, xác suất và cờ profile không trùng.
- `overview_ap.png`, `drop_one_ap.png`: hai hình trong báo cáo.
- `verification.json`, `source_hashes_before.json`, `source_hashes_after.json`: kiểm tra kết quả và bằng chứng nội dung các file nguồn được giữ nguyên khi chạy thí nghiệm ban đầu.
- `report_data.json`: dữ liệu tổng hợp dùng để dựng báo cáo.

## Phạm vi và giới hạn

28 phương án × 2 mô hình (Logistic Regression và XGBoost) × 5 fold = 280 lượt fit. Chỉ dùng 93.329 dòng Train từ manifest hiện có, giữ duplicate khi fit, tính trọng số lớp riêng trong từng fold và không resample. Test không được chấm hoặc dùng để chọn phương án.

Các ý tưởng feature đã được hình thành từ EDA trên toàn Train. Đây là kiểm tra phát triển, không phải xác nhận độc lập của toàn bộ quy trình lựa chọn. Không so trực tiếp điểm CV ở đây với điểm Test trong notebook. Độ lệch chuẩn giữa fold không phải khoảng tin cậy; số fold thắng không phải kiểm định thống kê.

Báo cáo bổ sung trang bộ 13 bằng kết quả đã có; không phát sinh lượt fit mới. Các file hash và commit nguồn trong protocol mô tả lần chạy gốc, trước khi thư mục này được đưa vào Git.

## Chạy và kiểm chứng

Các script dùng đường dẫn tương đối theo vị trí của chính script. Có thể chạy từ thư mục gốc repo:

```powershell
python -m pip install -r run_test_for_feature/requirements.txt
python run_test_for_feature/analyze_results.py
```

`analyze_results.py` tính lại chỉ số từ 56 file dự đoán và đối chiếu đủ 280 dòng metrics, sau đó dựng hình và dữ liệu báo cáo. Lệnh này không huấn luyện lại mô hình.

```powershell
python run_test_for_feature/run_experiments.py
```

`run_experiments.py` tái sử dụng kết quả đã đủ trong thư mục. Muốn huấn luyện lại từ đầu, trước tiên sao lưu các kết quả hiện tại, sau đó loại các file `*__oof.npz` và `fold_metrics.csv` trong thư mục này. Không cần thay đổi notebook hoặc dữ liệu nguồn. Hash bảo vệ nguồn loại trừ chính thư mục kết quả này để cho phép tái tạo các artifact.

```powershell
python run_test_for_feature/build_report.py
```

Lệnh cuối dựng lại DOCX từ kết quả đã có. Báo cáo đã commit được xuất kiểm tra bố cục bằng Microsoft Word và đọc đủ 9 trang; các file PDF/PNG kiểm tra trang không đưa vào repo.

Các phiên bản chính đã dùng: Python 3.14.1, NumPy 2.5.3, pandas 3.0.6, scikit-learn 1.9.1 và XGBoost 3.4.1. `requirements.txt` ghim các thư viện chính này; phiên bản công cụ vẽ hoặc Word khác nhau có thể làm bố cục hình và tài liệu thay đổi.
