# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

@dataclass
class LessonItem:
    topic: str
    lesson: str
    yccd: str

class CurriculumDB:
    """DB CT2018 (từ file DOCX bạn cung cấp) — dùng cho Tab 2."""

    def __init__(self, data: Dict[str, Dict[str, List[Dict[str, str]]]]):
        # data[subject][grade] = list of {topic, lesson, yccd}
        self.data = data

    @classmethod
    def from_json_file(cls, path: Path) -> "CurriculumDB":
        obj = json.loads(path.read_text(encoding="utf-8"))
        return cls(obj)

    def subjects(self) -> List[str]:
        return sorted(self.data.keys())

    def grades(self, subject: str) -> List[str]:
        return sorted(self.data.get(subject, {}).keys(), key=lambda x: int(x))

    def topics(self, subject: str, grade: str) -> List[str]:
        items = self.data.get(subject, {}).get(grade, [])
        topics = []
        seen = set()
        for it in items:
            t = (it.get("topic") or "").strip()
            if t and t not in seen:
                seen.add(t)
                topics.append(t)
        return topics

    def lessons(self, subject: str, grade: str, topic: Optional[str] = None) -> List[LessonItem]:
        items = self.data.get(subject, {}).get(grade, [])
        out: List[LessonItem] = []
        for it in items:
            if topic and (it.get("topic") or "").strip() != topic:
                continue
            out.append(LessonItem(
                topic=(it.get("topic") or "").strip(),
                lesson=(it.get("lesson") or "").strip(),
                yccd=(it.get("yccd") or "").strip(),
            ))
        return out

    def find_yccd(self, subject: str, grade: str, topic: str, lesson: str) -> str:
        for it in self.lessons(subject, grade, topic):
            if it.lesson == lesson:
                return it.yccd
        return ""

def load_default_db() -> CurriculumDB:
    here = Path(__file__).resolve().parent.parent
    data_path = here / "data" / "curriculum_ct2018.json"
    return CurriculumDB.from_json_file(data_path)

