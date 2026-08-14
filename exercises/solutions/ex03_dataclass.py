"""演習3 解答例。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from outlook_assistant.adapters.base import Person


class Priority(str, Enum):
    """希望の優先度。str を継承しているので文字列としても比較できる。"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


@dataclass(frozen=True)
class MeetingRequest:
    """押さえたい打ち合わせの希望。"""

    subject: str
    duration_minutes: int
    attendees: tuple[Person, ...] = ()
    """タプルは変更できないので、既定値を直接書いてよい。"""

    priority: Priority = Priority.NORMAL
    """Enum のメンバも変更できないので、そのまま既定値にできる。"""

    notes: dict[str, str] = field(default_factory=dict)
    """辞書は変更できるので `= {}` は禁止。インスタンスごとに dict() を呼ばせる。"""

    def scheduled_end(self, start: datetime) -> datetime:
        return start + timedelta(minutes=self.duration_minutes)
