"""演習3（🌿 第5章）: dataclass と Enum

adapters/base.py の Appointment / Busy に倣って、
「これから押さえたい打ち合わせの希望」を表す型を自分で定義する。

作るもの:

  class Priority(str, Enum)
      LOW = "low" / NORMAL = "normal" / HIGH = "high"

  @dataclass(frozen=True)
  class MeetingRequest
      subject: str                              必須
      duration_minutes: int                     必須
      attendees: tuple[Person, ...] = ()        既定は空
      priority: Priority = Priority.NORMAL      既定は NORMAL
      notes: dict[str, str] = ...               既定は空の辞書（インスタンスごとに別物）

      def scheduled_end(self, start: datetime) -> datetime
          start から duration_minutes 後の時刻を返す

考えどころ:
  - notes を `= {}` と書くと dataclass が拒否する。なぜか（第2章）
  - attendees は `= ()` でよい。notes との違いは何か
  - frozen=True にすると何ができなくなるか
"""

from __future__ import annotations

from dataclasses import dataclass, field  # noqa: F401  ヒント
from datetime import datetime, timedelta  # noqa: F401  ヒント
from enum import Enum  # noqa: F401  ヒント

from outlook_assistant.adapters.base import Person  # noqa: F401  ヒント


# TODO: Priority を定義する


# TODO: MeetingRequest を定義する
