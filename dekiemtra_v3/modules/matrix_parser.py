# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

@dataclass
class MatrixParseResult:
    ok: bool
    message: str
    df: Optional[pd.DataFrame] = None
    summary: Optional[Dict[str, object]] = None

def parse_matrix_file(uploaded_file) -> MatrixParseResult:
    """Đọc ma trận từ Excel; trả về DF + summary.
    Chú ý: Tab1 chỉ cần 'có thể xem đẹp' + kiểm tra nhanh.
    """
    try:
        if uploaded_file is None:
            return MatrixParseResult(False, "Chưa tải file ma trận.")
        name = uploaded_file.name.lower()
        if name.endswith(".xlsx") or name.endswith(".xls"):
            df = pd.read_excel(uploaded_file)
        elif name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            return MatrixParseResult(False, "Hiện Tab 1 hỗ trợ .xlsx/.xls/.csv. Nếu bạn dùng Word, hãy chuyển bảng sang Excel.")
        # chuẩn hóa cột
        df.columns = [str(c).strip() for c in df.columns]
        # summary nhẹ
        summary = {
            "rows": int(df.shape[0]),
            "cols": int(df.shape[1]),
            "columns": df.columns.tolist(),
        }
        return MatrixParseResult(True, "Đã đọc ma trận.", df=df, summary=summary)
    except Exception as e:
        return MatrixParseResult(False, f"Lỗi đọc ma trận: {e}")
