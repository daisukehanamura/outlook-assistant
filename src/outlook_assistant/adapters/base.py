"""Outlook操作の抽象インタフェース。

業務ロジックはこのモジュールの型にのみ依存し、具体的な実装
（pywin32のCOM / 将来のMicrosoft Graph）を直接importしない。

クラシックOutlookが使えなくなった場合に差し替えるのはこの下の層だけで、
calendar_hold.py / mail_draft.py には手を入れずに済む状態を保つこと。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Busy(str, Enum):
    """予定の公開ステータス。仮抑えでは TENTATIVE を使う。"""

    FREE = "free"
    TENTATIVE = "tentative"
    BUSY = "busy"


@dataclass(frozen=True)
class Person:
    """宛先・出席者。表示名しか分からない段階を許容するため address は任意。"""

    name: str
    address: str | None = None


@dataclass(frozen=True)
class Appointment:
    """カレンダー上の予定。"""

    subject: str
    start: datetime
    end: datetime
    attendees: tuple[Person, ...] = ()
    body: str = ""
    location: str = ""
    status: Busy = Busy.TENTATIVE
    entry_id: str | None = None
    """Outlookが採番する識別子。作成後に埋まる。招待送信時の指定に使う。"""


@dataclass(frozen=True)
class MailDraft:
    """メールの下書き。送信は行わない。"""

    to: tuple[Person, ...]
    subject: str
    body: str
    cc: tuple[Person, ...] = ()
    entry_id: str | None = None


@dataclass(frozen=True)
class SentMail:
    """文体学習のために読み取った過去の送信メール。

    本文は業務情報そのものなので、リポジトリに書き出さないこと。
    """

    subject: str
    body: str
    to: tuple[Person, ...]
    sent_at: datetime
    metadata: dict[str, str] = field(default_factory=dict)


class CalendarPort(ABC):
    """カレンダー操作。"""

    @abstractmethod
    def create_tentative(self, appointment: Appointment) -> Appointment:
        """予定を「仮」として自分のカレンダーに作る。

        この時点では出席者に招待を送らない。entry_id を埋めた
        Appointment を返し、後続の send_invitation で参照できるようにする。
        """

    @abstractmethod
    def send_invitation(self, entry_id: str) -> None:
        """既存の仮予定を、出席者への招待として送信する。

        破壊的かつ取り消せない操作。呼び出し側で必ず人間の承認を挟むこと。
        """

    @abstractmethod
    def find_free_slots(
        self, start: datetime, end: datetime, duration_minutes: int
    ) -> list[tuple[datetime, datetime]]:
        """指定期間から、自分の空き時間を返す。"""

    @abstractmethod
    def busy_spans(
        self, person: Person, start: datetime, end: datetime
    ) -> list[tuple[datetime, datetime]]:
        """指定した相手の、予定が埋まっている時間帯を返す。

        参照できるのは自分に見えている範囲だけ。相手が空き時間情報を
        公開していない場合は空リストが返り、「終日空き」と区別できない。
        呼び出し側はこの曖昧さを利用者に伝えること。
        """


class MailPort(ABC):
    """メール操作。送信機能は意図的に定義しない。"""

    @abstractmethod
    def create_draft(self, draft: MailDraft) -> MailDraft:
        """下書きフォルダにメールを作成する。送信はしない。"""

    @abstractmethod
    def recent_sent(self, limit: int = 20) -> list[SentMail]:
        """自分の送信済みメールを新しい順に取得する。文体の学習に使う。"""

    @abstractmethod
    def resolve_person(self, name: str) -> list[Person]:
        """表示名からアドレスを解決する。

        同名の候補が複数返りうるため list を返す。
        呼び出し側で候補が1件に絞れない場合は人間に確認すること。
        """
