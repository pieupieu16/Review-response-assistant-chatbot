# PIEUPIEU Review Care - RAG System

## Mô tả dự án 
PIIEUPIEU Review Care là một dự án nền tảng xây dựng hệ thống tự động hóa quy trình chăm sóc và phản hồi khách hàng dựa trên công nghệ tạo văn bản tăng cường tra cứu dữ liệu. Hệ thống có khả năng tự động tiếp nhận các đánh giá trực tuyến, phân tích chuyên sâu cảm xúc của người dùng (Tích cực, Tiêu cực, Trung lập), từ đó tự động biên soạn các câu trả lời nháp chuyên nghiệp, chính xác và nhất quán dựa trên tài liệu chính sách nội bộ hoặc danh mục câu hỏi thường gặp của doanh nghiệp.

Giải pháp này giúp các doanh nghiệp—đặc biệt là trong lĩnh vực thương mại điện tử(Quần áo)—tối ưu hóa triệt để tốc độ phản hồi, giảm thiểu áp lực vận hành cho đội ngũ nhân sự trực tổng đài, đồng thời nâng cao độ hài lòng và trải nghiệm tổng thể của khách hàng.
## Tính năng chính 

* **Phân tích cảm xúc :** Sử dụng mô hình AI định dạng ONNX để phân loại đánh giá thành Tích cực, Tiêu cực hoặc Trung lập.


* **Tạo câu trả lời tự động :** Xây dựng luồng RAG kết hợp với Google Gemini API để soạn thảo phản hồi dựa trên ngữ cảnh được trích xuất.


* **Giao diện quản lý :** Cung cấp giao diện hộp thư duyệt bài  để người quản trị kiểm duyệt và chỉnh sửa phản hồi trước khi gửi.


* **Xử lý bất đồng bộ :** Hỗ trợ đẩy các tác vụ nặng  ra nền thông qua hàng đợi Redis và RQ để tối ưu hiệu suất máy chủ.



## Kiến trúc và Công nghệ 

Dự án được xây dựng theo kiến trúc Microservices .

* **Giao diện người dùng :** Ứng dụng Streamlit hiển thị Dashboard và trình giả lập (Mock UI).


* **Máy chủ giao tiếp :** Framework FastAPI kết hợp Uvicorn.


* **Cơ sở dữ liệu :**
* SQLite (thông qua `aiosqlite`) để lưu trữ trạng thái đánh giá và câu trả lời nháp.


* ChromaDB đóng vai trò cơ sở dữ liệu Vector (Vector DB) lưu trữ tài liệu đã được phân mảnh .




* **Mô hình Trí tuệ nhân tạo :**
* `intfloat/multilingual-e5-large` cho Embedding.


* `BAAI/bge-reranker-base` để xếp hạng lại tài liệu .


* `gemini-2.5-flash` cho quá trình sinh ngôn ngữ.





## Hướng dẫn cài đặt 

### 1. Chuẩn bị dữ liệu 

* Đặt các tài liệu văn bản thô  vào thư mục `data/raw/`. Các tệp này có thể ở định dạng `.txt` hoặc `.pdf`.



### 2. Cấu hình môi trường 

* Thiết lập các biến môi trường cần thiết từ tệp `.env.example`.


* Bạn bắt buộc phải cung cấp khóa `GOOGLE_API_KEY` hợp lệ.



### 3. Cài đặt thư viện 

* Cài đặt các gói phụ thuộc bằng pip install requirements.txt  cần thiết và khởi chạy API.


* Các thư viện này được liệt kê chi tiết trong tệp `requirements.txt`.



## Hướng dẫn sử dụng 

* **Khởi chạy Backend :** Bật máy chủ Uvicorn để chạy tệp API `src/api/server.py`.


* **Khởi chạy Frontend :** Chạy ứng dụng giao diện bằng lệnh `streamlit run frontend/deploy.py`.


* **Khởi chạy Worker :** Nếu cấu hình `USE_RQ=true`, bạn cần đảm bảo Redis đang hoạt động và chạy tệp `worker.py` để xử lý các tác vụ trong hàng đợi (queue).

## Cấu hình đề cử 
### 1. Cấu hình tối thiểu (Chạy thuần CPU)
Mức này phù hợp để bạn chạy kiểm thử , nhưng tốc độ trích xuất RAG (đặc biệt là bước embedding và reranking) sẽ có độ trễ vài giây cho mỗi yêu cầu.

CPU: Intel Core i5 (Gen 10+) hoặc AMD Ryzen 5.

RAM: 8GB. (Nếu ChromaDB chứa lượng lớn tài liệu, mức RAM này có thể bị nghẽn).

GPU: Không bắt buộc (sử dụng CPU để chạy mô hình).

Lưu trữ: SSD 256GB.

### 2. Cấu hình lý tưởng (Tối ưu xử lý song song)
CPU: Intel Core i5/i7 (Gen 12+ dòng H) hoặc AMD Ryzen 5/7.

RAM: 16GB .

GPU: NVIDIA GeForce RTX có VRAM khoảng 6GB (ví dụ: các dòng RTX 3050, RTX 4050). 

Lưu trữ: SSD NVMe 512GB.

# NOTE : Tất cả tài liệu đều là nguồn tự thu thập trên internet, không vi phạm bản quyền. Dự án này được phát triển nhằm mục đích nghiên cứu và học tập, không phục vụ mục đích thương mại.