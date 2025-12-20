# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, Tuple

def ensure_app_path() -> Path:
    """Ensure the folder containing app.py is on sys.path, preventing ModuleNotFoundError."""
    here = Path(__file__).resolve().parent.parent  # project root (contains app.py)
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    return here

def safe_import_genai() -> Tuple[bool, Optional[object], str]:
    """Try import google.generativeai. Return (ok, module, error_message)."""
    try:
        import google.generativeai as genai  # type: ignore
        return True, genai, ""
    except Exception as e:
        return False, None, f"Không import được google.generativeai: {e}"
