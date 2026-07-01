# TADICO Review Care - RAG System

## Mô tả dự án 

Đây là một dự án khung (skeleton project) xây dựng hệ thống Retrieval-Augmented Generation (RAG) nhằm tự động hóa quy trình chăm sóc khách hàng. Hệ thống tiếp nhận các đánh giá (reviews), phân tích cảm xúc (sentiment analysis) và tự động sinh ra các câu trả lời chuyên nghiệp dựa trên tài liệu chính sách hoặc câu hỏi thường gặp của công ty.

## Tính năng chính 

* **Phân tích cảm xúc :** Sử dụng mô hình AI định dạng ONNX để phân loại đánh giá thành Tích cực, Tiêu cực hoặc Trung lập.


* **Tạo câu trả lời tự động :** Xây dựng luồng RAG kết hợp với Google Gemini API để soạn thảo phản hồi dựa trên ngữ cảnh được trích xuất.


* **Giao diện quản lý :** Cung cấp giao diện hộp thư duyệt bài  để người quản trị kiểm duyệt và chỉnh sửa phản hồi trước khi gửi.


* **Xử lý bất đồng bộ :** Hỗ trợ đẩy các tác vụ nặng  ra nền thông qua hàng đợi Redis và RQ để tối ưu hiệu suất máy chủ.



## Kiến trúc và Công nghệ (Architecture & Technologies)

Dự án được xây dựng theo kiến trúc Microservices .

* **Giao diện người dùng :** Ứng dụng Streamlit hiển thị Dashboard và trình giả lập (Mock UI).


* **Máy chủ giao tiếp :** Framework FastAPI kết hợp Uvicorn.


* **Cơ sở dữ liệu :**
* SQLite (thông qua `aiosqlite`) để lưu trữ trạng thái đánh giá và câu trả lời nháp.


* ChromaDB đóng vai trò cơ sở dữ liệu Vector (Vector DB) lưu trữ tài liệu đã được phân mảnh .




* **Mô hình Trí tuệ nhân tạo :**
* `intfloat/multilingual-e5-large` cho Embedding.


* `BAAI/bge-reranker-base` để xếp hạng lại tài liệu (Reranking).


* `gemini-2.5-flash` cho quá trình sinh ngôn ngữ.





## Hướng dẫn cài đặt 

### 1. Chuẩn bị dữ liệu 

* Đặt các tài liệu văn bản thô (raw text documents) vào thư mục `data/raw/`. Các tệp này có thể ở định dạng `.txt` hoặc `.pdf`.



### 2. Cấu hình môi trường 

* Thiết lập các biến môi trường cần thiết từ tệp `.env.example`.


* Bạn bắt buộc phải cung cấp khóa `GOOGLE_API_KEY` hợp lệ.



### 3. Cài đặt thư viện 

* Cài đặt các gói phụ thuộc (dependencies) cần thiết và khởi chạy API.


* Các thư viện này được liệt kê chi tiết trong tệp `requirements.txt`.



## Hướng dẫn sử dụng 

* **Khởi chạy Backend :** Bật máy chủ Uvicorn để chạy tệp API `src/api/server.py`.


* **Khởi chạy Frontend :** Chạy ứng dụng giao diện bằng lệnh `streamlit run frontend/deploy.py`.


* **Khởi chạy Worker :** Nếu cấu hình `USE_RQ=true`, bạn cần đảm bảo Redis đang hoạt động và chạy tệp `worker.py` để xử lý các tác vụ trong hàng đợi (queue).