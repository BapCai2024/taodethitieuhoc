# -*- coding: utf-8 -*-
"""
Đề kiểm tra CT2018/TT27 — V3 (ổn định triển khai Streamlit)
- Giữ 3 tab như V1: Tab1 (ma trận), Tab2 (soạn câu), Tab3 (xuất).
- Triết lý: KHÔNG để lỗi import/API làm app chết trước khi hiện UI.
"""

from __future__ import annotations

import streamlit as st

# --- Bootstrapping để tránh ModuleNotFoundError khi deploy dưới thư mục con
try:
    from modules.bootstrap import ensure_app_path
    ensure_app_path()
except Exception:
    # vẫn tiếp tục; Streamlit có thể đã add path
    pass

# --- Safe imports: nếu lỗi thì vẫn lên UI với thông báo rõ ràng
MODULES_OK = True
IMPORT_ERR = ""

try:
    from modules.ai_client import GeminiClient
    from modules.data_loader import load_default_db
    from modules.ui_tabs import _init_state, render_sidebar, tab1_matrix_exam, tab2_build_question, tab3_review_export
except Exception as e:
    MODULES_OK = False
    IMPORT_ERR = str(e)

st.set_page_config(page_title="Đề kiểm tra CT2018/TT27", layout="wide")

st.title("📝 Tool ra đề kiểm tra (CT GDPT 2018 • TT27)")
st.caption("V3 ưu tiên: chạy ổn định trên Streamlit Cloud, không lỗi import/API trước khi thấy giao diện.")

if not MODULES_OK:
    st.error("App chưa chạy được do thiếu module / sai cấu trúc thư mục.")
    st.code(IMPORT_ERR)
    st.markdown("""**Cách khắc phục nhanh (chuẩn Streamlit Cloud):**
1. Đặt `app.py` và thư mục `modules/` cùng cấp (cùng 1 thư mục).
2. Trong `modules/` phải có `__init__.py`.
3. Nếu bạn chạy app trong thư mục con, đảm bảo đường dẫn app trỏ đúng: `dekiemtra_v3/app.py`.
4. Xoá cache deploy và redeploy.
""")
    st.stop()

# --- Normal flow
_init_state()

ai = GeminiClient(api_key=st.session_state.get("api_key",""))
db = load_default_db()

render_sidebar(ai)

tab1, tab2, tab3 = st.tabs(["Tab 1: Tạo đề từ ma trận", "Tab 2: Tạo câu hỏi theo bài/YCCĐ", "Tab 3: Ghép & Xuất đề"])

with tab1:
    tab1_matrix_exam(ai)

with tab2:
    tab2_build_question(ai, db)

with tab3:
    tab3_review_export()
