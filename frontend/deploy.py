import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# --- CẤU HÌNH (CONFIGURATION) ---
st.set_page_config(page_title="TADICO Review Care", page_icon="🎧", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000/api"
JOB_POLL_INTERVAL_MS = 2000
JOB_POLL_MAX_ATTEMPTS = 60


def _init_session_state():
    defaults = {
        "pending_job_id": None,
        "job_poll_attempts": 0,
        "job_flash_message": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# --- CÁC HÀM GỌI API (API CALLER FUNCTIONS) ---

def api_process_review(customer_name, review_text):
    url = f"{API_BASE_URL}/process_review"
    payload = {"customer_name": customer_name, "review_text": review_text}
    return requests.post(url, json=payload, timeout=120)


def api_get_job_status(job_id):
    """Một request duy nhất — không block main thread."""
    url = f"{API_BASE_URL}/job/{job_id}"
    try:
        return requests.get(url, timeout=30)
    except requests.exceptions.RequestException:
        return None


def api_get_pending_reviews():
    url = f"{API_BASE_URL}/pending_reviews"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except requests.exceptions.ConnectionError:
        st.error("Không thể kết nối tới Server API. Vui lòng kiểm tra xem uvicorn đã chạy chưa!")
        return []


def api_approve_review(review_id, final_reply):
    url = f"{API_BASE_URL}/approve_review/{review_id}"
    payload = {"final_reply": final_reply}
    return requests.put(url, json=payload)


def _set_flash_message(level: str, message: str):
    st.session_state.job_flash_message = (level, message)


def _clear_pending_job():
    st.session_state.pending_job_id = None
    st.session_state.job_poll_attempts = 0


def check_pending_job():
    """Poll một lần mỗi lần script chạy; st_autorefresh trigger rerun tiếp theo."""
    job_id = st.session_state.pending_job_id
    if not job_id:
        return

    st.info(f"⏳ Đang xử lý job `{job_id}`... (lần kiểm tra {st.session_state.job_poll_attempts + 1})")
    response = api_get_job_status(job_id)

    if response is None or response.status_code != 200:
        st.session_state.job_poll_attempts += 1
        if st.session_state.job_poll_attempts >= JOB_POLL_MAX_ATTEMPTS:
            _set_flash_message("error", "Hết thời gian chờ xử lý job hoặc không thể kết nối API!")
            _clear_pending_job()
        return

    payload = response.json()
    status = payload.get("status")

    if status == "success":
        _set_flash_message("success", "Đã phân tích cảm xúc và tạo câu trả lời tự động thành công!")
        _clear_pending_job()
        return

    if status == "failed":
        _set_flash_message("error", f"Job thất bại: {payload.get('error', 'Unknown error')}")
        _clear_pending_job()
        return

    st.session_state.job_poll_attempts += 1
    if st.session_state.job_poll_attempts >= JOB_POLL_MAX_ATTEMPTS:
        _set_flash_message("error", "Hết thời gian chờ xử lý job!")
        _clear_pending_job()


_init_session_state()

st.title("🎧 Hệ Thống Chăm Sóc Khách Hàng - TADICO Review Care")
st.markdown("*Kiến trúc Microservices: Streamlit Frontend tích hợp FastAPI Backend*")

tab1, tab2 = st.tabs(["📥 Hộp thư Duyệt Bài (Approval Inbox)", "🛒 Giả lập Đánh giá (Simulate Review)"])

# ==========================================
# TAB 1: KHU VỰC QUẢN LÝ (ADMIN DASHBOARD)
# ==========================================
with tab1:
    st.markdown("### Danh sách đánh giá cần xử lý (Pending Reviews)")

    pending_data = api_get_pending_reviews()

    if not pending_data:
        st.success("Tuyệt vời! Hiện tại không có đánh giá nào cần duyệt. (No pending reviews!)")
    else:
        st.info(f"Có **{len(pending_data)}** đánh giá đang chờ duyệt.")

        for item in pending_data:
            review_id = item['review_id']
            customer_name = item['customer_name']
            sentiment = item['sentiment']
            icon = "🔴" if "Tiêu cực" in sentiment else ("🟢" if "Tích cực" in sentiment else "🟡")

            with st.expander(
                f"{icon} Review #{review_id} - Khách hàng: {customer_name} | Cảm xúc: {sentiment}",
                expanded=False,
            ):
                st.markdown(f"**Ý kiến khách hàng (Customer Feedback):**\n> {item['review_text']}")

                edited_reply = st.text_area(
                    "Đề xuất từ AI (Bạn có thể chỉnh sửa trước khi gửi):",
                    value=item['ai_reply_draft'],
                    height=100,
                    key=f"text_{review_id}",
                )

                if st.button("Phê duyệt & Gửi (Approve & Send)", key=f"btn_{review_id}", type="primary"):
                    res = api_approve_review(review_id, edited_reply)
                    if res.status_code == 200:
                        st.success(f"Đã duyệt thành công Review #{review_id}!")
                        st.rerun()
                    else:
                        st.error(f"Có lỗi xảy ra: {res.text}")

# ==========================================
# TAB 2: KHU VỰC GIẢ LẬP KHÁCH HÀNG (SIMULATOR)
# ==========================================
with tab2:
    if st.session_state.job_flash_message:
        level, message = st.session_state.job_flash_message
        if level == "success":
            st.success(message)
        else:
            st.error(message)
        st.session_state.job_flash_message = None

    if st.session_state.pending_job_id:
        st_autorefresh(interval=JOB_POLL_INTERVAL_MS, key="job_poll_autorefresh")
        check_pending_job()

    st.markdown("### Giao diện giả lập (Mock UI) của Sàn Thương Mại Điện Tử")
    st.write("Sử dụng form này để tạo dữ liệu test thay vì dùng Swagger UI.")

    with st.form("new_review_form", clear_on_submit=True):
        col1, col2 = st.columns([1, 2])
        with col1:
            input_name = st.text_input("Tên khách hàng (Customer Name):")
        with col2:
            input_review = st.text_input("Nội dung đánh giá (Review Text):")

        submit_btn = st.form_submit_button("Gửi đánh giá (Submit Feedback)")

        if submit_btn:
            if input_name and input_review:
                res = api_process_review(input_name, input_review)
                if res.status_code == 200:
                    payload = res.json()
                    if payload.get("status") == "queued":
                        st.session_state.pending_job_id = payload.get("job_id")
                        st.session_state.job_poll_attempts = 0
                        st.rerun()
                    else:
                        _set_flash_message(
                            "success",
                            "Đã phân tích cảm xúc và tạo câu trả lời tự động thành công!",
                        )
                        st.rerun()
                else:
                    st.error("Lỗi khi kết nối với API!")
            else:
                st.warning("Vui lòng điền đầy đủ tên và nội dung!")
