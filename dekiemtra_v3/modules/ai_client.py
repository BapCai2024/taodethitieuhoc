# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .bootstrap import safe_import_genai

DEFAULT_MODELS: List[str] = [
    # Thứ tự ưu tiên; sẽ tự thử lần lượt nếu model không khả dụng.
    "gemini-1.5-pro",
    "gemini-1.5-flash",
    "gemini-1.0-pro",
]

DEFAULT_GEN_CONFIG: Dict[str, object] = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

@dataclass
class AIStatus:
    ok: bool
    message: str
    used_model: Optional[str] = None

class GeminiClient:
    """Gemini client with strong failure handling (không làm app crash trước UI)."""

    def __init__(self, api_key: Optional[str] = None, models: Optional[List[str]] = None):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        self.models = models or DEFAULT_MODELS
        self._genai_ok, self._genai, self._genai_err = safe_import_genai()

    def check_api(self) -> AIStatus:
        if not self.api_key:
            return AIStatus(False, "Chưa có API key (GEMINI_API_KEY hoặc nhập trong Sidebar).")
        if not self._genai_ok or self._genai is None:
            return AIStatus(False, self._genai_err or "Thiếu thư viện google.generativeai.")
        try:
            self._genai.configure(api_key=self.api_key)
            # list_models là cách nhẹ nhất để kiểm tra key; nếu fail -> bắt exception
            _ = list(self._genai.list_models())
            return AIStatus(True, "API key hợp lệ và đã kết nối.")
        except Exception as e:
            return AIStatus(False, f"Không kết nối được API: {e}")

    def generate(self, prompt: str, gen_config: Optional[Dict[str, object]] = None) -> AIStatus:
        """Try multiple models; always returns AIStatus."""
        st = self.check_api()
        if not st.ok:
            return st

        assert self._genai is not None
        gen_config = gen_config or DEFAULT_GEN_CONFIG

        # seed nhẹ để đa dạng đề mà vẫn có thể lặp lại khi cần
        seed = random.randint(1, 10_000_000)
        prompt2 = f"{prompt}\n\n[seed:{seed}]"

        last_err: Optional[Exception] = None
        for m in self.models:
            try:
                model = self._genai.GenerativeModel(m)  # type: ignore[attr-defined]
                res = model.generate_content(prompt2, generation_config=gen_config)
                text = getattr(res, "text", None) or ""
                if text.strip():
                    return AIStatus(True, text.strip(), used_model=m)
                last_err = RuntimeError("Model trả về rỗng.")
            except Exception as e:
                last_err = e
                continue
        return AIStatus(False, f"AI thất bại sau khi thử {len(self.models)} model. Lỗi cuối: {last_err}")
