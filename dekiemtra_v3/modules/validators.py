# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

ALLOWED_LEVELS = ["Mức 1: Biết", "Mức 2: Hiểu", "Mức 3: Vận dụng"]
ALLOWED_TYPES = [
    "Trắc nghiệm (4 lựa chọn)",
    "Đúng/Sai",
    "Ghép nối (Nối cột)",
    "Điền khuyết (Hoàn thành câu)",
    "Tự luận",
    "Thực hành trên máy tính",
]

@dataclass
class ValidationIssue:
    level: str  # "error" | "warning"
    message: str

def validate_points_sum(questions: List[Dict[str, object]], expected_total: float = 10.0) -> List[ValidationIssue]:
    s = 0.0
    for q in questions:
        try:
            s += float(q.get("points", 0.0))
        except Exception:
            return [ValidationIssue("error", "Có câu hỏi có điểm không hợp lệ (không phải số).")]
    # tránh lỗi float
    if abs(s - expected_total) > 1e-6:
        return [ValidationIssue("warning", f"Tổng điểm hiện tại = {s:g}, chưa bằng {expected_total:g}. Bạn có thể điều chỉnh trước khi xuất.")]
    return []

def validate_question_schema(q: Dict[str, object]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not str(q.get("content","")).strip():
        issues.append(ValidationIssue("error","Nội dung câu hỏi đang trống."))
    if str(q.get("type","")) not in ALLOWED_TYPES:
        issues.append(ValidationIssue("warning","Dạng câu hỏi chưa nằm trong danh sách chuẩn (vẫn có thể xuất)."))
    if str(q.get("level","")) not in ALLOWED_LEVELS:
        issues.append(ValidationIssue("warning","Mức độ chưa đúng chuẩn Mức 1/2/3."))
    try:
        p=float(q.get("points",0))
        if p<=0:
            issues.append(ValidationIssue("warning","Điểm nên > 0."))
    except Exception:
        issues.append(ValidationIssue("error","Điểm không hợp lệ."))
    return issues
