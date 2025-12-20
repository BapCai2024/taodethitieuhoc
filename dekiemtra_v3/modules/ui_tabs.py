# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Dict, List, Optional

import streamlit as st

from .ai_client import GeminiClient
from .data_loader import CurriculumDB
from .docx_export import export_exam_docx
from .matrix_parser import parse_matrix_file
from .validators import validate_points_sum, validate_question_schema

QUESTION_TYPES_BASE = [
    "Trắc nghiệm (4 lựa chọn)",
    "Đúng/Sai",
    "Ghép nối (Nối cột)",
    "Điền khuyết (Hoàn thành câu)",
    "Tự luận",
]

LEVELS = ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"]

def _init_state():
    st.session_state.setdefault("questions", [])
    st.session_state.setdefault("tab1_exam_text", "")
    st.session_state.setdefault("api_key", "")
    st.session_state.setdefault("ai_enabled", False)
    st.session_state.setdefault("last_ai_status", "")
    st.session_state.setdefault("matrix_df", None)

def render_sidebar(ai: GeminiClient):
    st.sidebar.header("Cấu hình")
    st.sidebar.caption("Để app không lỗi trước giao diện: nếu thiếu API key, AI sẽ tự tắt và bạn vẫn dùng được phần còn lại.")
    st.session_state.api_key = st.sidebar.text_input("Gemini API Key (tùy chọn)", type="password", value=st.session_state.api_key)
    if st.sidebar.button("🔎 Kiểm tra API"):
        ai.api_key = st.session_state.api_key.strip()
        stt = ai.check_api()
        st.session_state.ai_enabled = stt.ok
        st.session_state.last_ai_status = stt.message
    if st.session_state.last_ai_status:
        (st.sidebar.success if st.session_state.ai_enabled else st.sidebar.warning)(st.session_state.last_ai_status)

def tab1_matrix_exam(ai: GeminiClient):
    st.subheader("Tab 1 — Tạo đề từ ma trận")
    st.caption("Mục tiêu: Upload ma trận → xem đẹp + kiểm tra nhanh → (tùy chọn) AI sinh đề.")
    colL, colR = st.columns([1.2, 1])
    with colL:
        up = st.file_uploader("Tải ma trận (.xlsx/.xls/.csv)", type=["xlsx","xls","csv"])
        if st.button("📥 Đọc & hiển thị ma trận", type="primary", use_container_width=True):
            res = parse_matrix_file(up)
            if not res.ok:
                st.error(res.message)
                st.session_state.matrix_df = None
            else:
                st.session_state.matrix_df = res.df
                st.success(res.message)
        if st.session_state.matrix_df is not None:
            df = st.session_state.matrix_df
            st.markdown("**Xem trước ma trận (có thể kéo/zoom):**")
            st.dataframe(df, use_container_width=True, height=360)
            with st.expander("Kiểm tra nhanh (logic)"):
                st.write({"Số dòng": df.shape[0], "Số cột": df.shape[1], "Tên cột": list(df.columns)})

    with colR:
        st.markdown("**Sinh đề (tùy chọn AI):**")
        school = st.text_input("Tên trường (tùy chọn)", value="")
        subject = st.text_input("Môn", value="")
        grade = st.text_input("Lớp", value="")
        term = st.text_input("Kì", value="Cuối học kì")
        use_ai = st.checkbox("Dùng AI để sinh đề", value=st.session_state.ai_enabled)
        if st.button("✨ Sinh đề", use_container_width=True):
            if st.session_state.matrix_df is None:
                st.error("Bạn cần đọc ma trận trước.")
            else:
                if use_ai:
                    ai.api_key = st.session_state.api_key.strip()
                    prompt = _prompt_from_matrix(st.session_state.matrix_df, subject, grade, term)
                    stt = ai.generate(prompt)
                    if stt.ok:
                        st.session_state.tab1_exam_text = stt.message
                        st.success(f"Đã sinh đề bằng: {stt.used_model}")
                    else:
                        st.error(stt.message)
                else:
                    st.session_state.tab1_exam_text = "Chế độ không AI: Tab 1 hiện chỉ hiển thị ma trận. Bạn có thể dùng Tab 2 để soạn câu và Tab 3 để xuất."
        if st.session_state.tab1_exam_text:
            st.text_area("Đề (có thể sửa)", value=st.session_state.tab1_exam_text, height=420)

def _prompt_from_matrix(df, subject: str, grade: str, term: str) -> str:
    # Chỉ gửi 200 dòng đầu để tránh prompt quá dài
    sample = df.head(200).to_csv(index=False)
    return f"""Đóng vai giáo viên Tiểu học theo CT GDPT 2018 và TT27.
Hãy tạo đề kiểm tra {term} môn {subject} lớp {grade} dựa trên MA TRẬN bên dưới (CSV).
- Bám sát số câu, mức độ, điểm theo ma trận.
- Đa dạng dạng câu hỏi: Trắc nghiệm 4 lựa chọn, Đúng/Sai, Ghép nối, Điền khuyết, Tự luận (tuỳ nội dung).
- Xuất đúng định dạng:
Câu [n] ([điểm] đ) - [Mức 1/2/3]: ...
Nếu là trắc nghiệm: A. ...\nB. ...\nC. ...\nD. ...\nĐáp án: ...
Nếu là đúng/sai: liệt kê mệnh đề a/b/c..., ghi đáp án cuối.
Nếu là nối cột: Cột A (1..), Cột B (a..), Đáp án: 1-b, ...
Nếu là điền khuyết: dùng '........' để chừa chỗ trống; Đáp án: ...
KHÔNG viết lời dẫn dài.

MA TRẬN (CSV):
{sample}
"""

def tab2_build_question(ai: GeminiClient, db: CurriculumDB):
    st.subheader("Tab 2 — Soạn từng câu (tự động lấy Chủ đề/Bài/YCCĐ)")
    st.caption("Chọn Lớp/Môn → chọn Chủ đề → chọn Bài/Nội dung → YCCĐ tự đổ ra. GV chỉ cần chọn dạng/mức/điểm và bấm tạo.")
    colA, colB = st.columns([1, 1])

    with colA:
        subject = st.selectbox("Môn", db.subjects(), key="t2_subject")
        grades = db.grades(subject)
        grade = st.selectbox("Lớp", grades, key="t2_grade")
        topics = db.topics(subject, grade)
        topic = st.selectbox("Chủ đề / Mạch nội dung", topics, key="t2_topic")

        lessons = db.lessons(subject, grade, topic)
        lesson_names = [it.lesson for it in lessons]
        lesson = st.selectbox("Bài học / Nội dung", lesson_names, key="t2_lesson")

        yccd = db.find_yccd(subject, grade, topic, lesson)
        yccd_input = st.text_area("YCCĐ (tự điền — bạn có thể chỉnh)", value=yccd, height=110, key="t2_yccd")

    with colB:
        q_types = QUESTION_TYPES_BASE.copy()
        if subject == "Tin học":
            q_types.append("Thực hành trên máy tính")
        q_type = st.selectbox("Dạng câu hỏi", q_types, key="t2_type")
        level = st.selectbox("Mức độ", LEVELS, key="t2_level")
        points = st.number_input("Điểm", min_value=0.25, max_value=10.0, value=1.0, step=0.25, key="t2_points")
        use_ai = st.checkbox("Dùng AI gợi ý nội dung câu hỏi", value=st.session_state.ai_enabled)

        if st.button("➕ Thêm câu vào Tab 3", type="primary", use_container_width=True):
            # Tạo nội dung
            content = ""
            if use_ai:
                ai.api_key = st.session_state.api_key.strip()
                prompt = _prompt_one_question(subject, grade, topic, lesson, yccd_input, q_type, level, points)
                stt = ai.generate(prompt)
                if stt.ok:
                    content = stt.message
                    st.success(f"AI OK ({stt.used_model})")
                else:
                    st.warning("AI lỗi → chuyển sang chế độ nhập tay. " + stt.message)
            if not content:
                content = st.text_area("Nội dung (nếu không dùng AI, hãy nhập ở đây rồi bấm lại)", value="", height=120, key="t2_manual_content")

            q = {
                "subject": subject,
                "grade": grade,
                "topic": topic,
                "lesson": lesson,
                "yccd": yccd_input,
                "type": q_type,
                "level": level,
                "points": float(points),
                "content": content.strip(),
                "answer": "",  # GV có thể nhập ở Tab 3 nếu muốn
            }
            issues = validate_question_schema(q)
            fatal = any(i.level == "error" for i in issues)
            if fatal:
                for i in issues:
                    (st.error if i.level == "error" else st.warning)(i.message)
            else:
                st.session_state.questions.append(q)
                st.success(f"Đã thêm: {subject} lớp {grade} — {lesson}")

def _prompt_one_question(subject, grade, topic, lesson, yccd, q_type, level, points) -> str:
    return f"""Đóng vai giáo viên Tiểu học theo CT GDPT 2018 và TT27.
Soạn 1 câu hỏi kiểm tra môn {subject} lớp {grade}.
- Chủ đề: {topic}
- Bài/Nội dung: {lesson}
- YCCĐ: {yccd}
- Dạng: {q_type}; Mức: {level}; Điểm: {points}

YÊU CẦU ĐỊNH DẠNG:
- Trắc nghiệm: 4 lựa chọn A/B/C/D mỗi lựa chọn 1 dòng, cuối ghi 'Đáp án: X'
- Đúng/Sai: viết 3-4 mệnh đề a/b/c..., cuối ghi 'Đáp án: a-Đ, b-S, ...'
- Ghép nối: Cột A (1..), Cột B (a..), cuối ghi 'Đáp án: 1-b, 2-a,...'
- Điền khuyết: chừa chỗ trống bằng '........', cuối ghi 'Đáp án: ...'
- Tự luận: nêu yêu cầu rõ, có gợi ý đáp án ngắn cuối.

CHỈ TRẢ VỀ NỘI DUNG CÂU HỎI + DÒNG ĐÁP ÁN. Không viết lời dẫn.
"""

def tab3_review_export():
    st.subheader("Tab 3 — Danh sách câu & Xuất Word")
    qs: List[Dict[str, object]] = st.session_state.questions

    if not qs:
        st.info("Chưa có câu hỏi nào. Hãy tạo ở Tab 2 hoặc sinh ở Tab 1.")
        return

    # Kiểm tra tổng điểm
    issues = validate_points_sum(qs, expected_total=10.0)
    for it in issues:
        (st.warning if it.level == "warning" else st.error)(it.message)

    st.markdown("**Chỉnh nhanh:**")
    for idx, q in enumerate(qs):
        with st.expander(f"Câu {idx+1}: {q.get('subject')} lớp {q.get('grade')} — {q.get('lesson')}", expanded=False):
            q["points"] = st.number_input("Điểm", 0.25, 10.0, float(q.get("points",1.0)), 0.25, key=f"t3_pt_{idx}")
            q["type"] = st.text_input("Dạng", value=str(q.get("type","")), key=f"t3_ty_{idx}")
            q["level"] = st.text_input("Mức", value=str(q.get("level","")), key=f"t3_lv_{idx}")
            q["content"] = st.text_area("Nội dung", value=str(q.get("content","")), height=140, key=f"t3_ct_{idx}")
            q["answer"] = st.text_input("Đáp án (tùy chọn)", value=str(q.get("answer","")), key=f"t3_an_{idx}")
            if st.button("🗑️ Xóa câu này", key=f"t3_del_{idx}"):
                st.session_state.questions.pop(idx)
                st.rerun()

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        school = st.text_input("Trường", value="")
        title = st.text_input("Tiêu đề", value="ĐỀ KIỂM TRA CUỐI HỌC KÌ")
        term = st.text_input("Kì", value="Học kì I")
    with col2:
        subject = st.text_input("Môn (hiển thị)", value=str(qs[0].get("subject","")))
        grade = st.text_input("Lớp (hiển thị)", value=str(qs[0].get("grade","")))
        include_ans = st.checkbox("Kèm trang đáp án", value=True)

    if st.button("📄 Xuất Word", type="primary", use_container_width=True):
        meta = {
            "school": school,
            "title": title,
            "term": term,
            "subject": subject,
            "grade": grade,
            "subtitle": "",
        }
        data = export_exam_docx(meta, qs, include_answer_key=include_ans)
        st.download_button("Tải file .docx", data, file_name=f"De_{subject}_lop{grade}.docx", mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
