"""予定の仮抑えと、そこからの招待送信。

承認フローは「コマンド2本に分離」方式（D9）。
    1. hold()   … 自分の枠だけTentativeで押さえる。招待は飛ばない。予定IDを返す
    2. invite() … 内容を確認した後で、予定IDを指定して出席者へ招待を送る

1と2の間には時間が空いてよい（翌日でもよい）。この分離自体が承認の仕組みなので、
invite() に暗黙の確認プロンプトを足さないこと。プロンプトを足すと承認が二重になり、
「確認してから送る」という本来の運用が形骸化する。

日時の自然言語解釈（「来週の水曜あたり」等）はこの層では行わない。
呼び出し側のAIエージェントが確定した datetime に変換して渡す。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from .adapters.base import Appointment, Busy, CalendarPort, Person
from .scheduling import free_gaps, within_business_hours


def hold(
    calendar: CalendarPort,
    subject: str,
    start: datetime,
    duration_minutes: int,
    attendees: list[Person] | None = None,
    location: str = "",
    body: str = "",
) -> Appointment:
    """予定を仮（Tentative）で押さえる。出席者への招待は送らない。

    出席者を渡した場合も、この時点では登録するだけで送信しない。
    後から invite() で招待に昇格させられる状態にしておく。
    """
    if duration_minutes <= 0:
        raise ValueError("所要時間は1分以上で指定してください")

    appointment = Appointment(
        subject=subject,
        start=start,
        end=start + timedelta(minutes=duration_minutes),
        attendees=tuple(attendees or ()),
        body=body,
        location=location,
        status=Busy.TENTATIVE,
    )
    return calendar.create_tentative(appointment)


def invite(calendar: CalendarPort, entry_id: str) -> None:
    """仮予定を出席者への招待として送信する。

    取り消せない操作。この関数を呼ぶこと自体が「確認済み」の意思表示にあたる。
    """
    if not entry_id:
        raise ValueError("予定IDが空です")
    calendar.send_invitation(entry_id)


def suggest_slots(
    calendar: CalendarPort,
    start: datetime,
    end: datetime,
    duration_minutes: int,
    limit: int = 5,
) -> list[tuple[datetime, datetime]]:
    """指定期間から、自分の空き枠の候補を返す。

    出席者の空き状況も見たい場合は find_common_slots() を使う。
    """
    slots = calendar.find_free_slots(start, end, duration_minutes)
    return slots[:limit]


@dataclass(frozen=True)
class CommonSlots:
    """全員の空き枠と、照会できなかった相手。"""

    slots: list[tuple[datetime, datetime]]
    unavailable: list[Person]
    """空き時間情報を取得できなかった相手。

    この人たちの予定は考慮されていない。空きが無いのではなく「分からない」ので、
    候補を提示する際は必ずその旨を添えること。
    """


def find_common_slots(
    calendar: CalendarPort,
    people: list[Person],
    start: datetime,
    end: datetime,
    duration_minutes: int,
    limit: int = 5,
    include_self: bool = True,
    business_hours: tuple[int, int] | None = (9, 18),
) -> CommonSlots:
    """自分と出席者全員が空いている時間帯を探す。

    誰か一人でも埋まっていればその時間は候補から外す。
    照会できない相手がいても処理は止めず、誰が照会できなかったかを返す。
    「一部の人しか確認できていない候補」と「全員確認済みの候補」を
    黙って混ぜないため。
    """
    busy: list[tuple[datetime, datetime]] = []
    unavailable: list[Person] = []

    if include_self:
        # 自分の予定は「空き枠の裏返し」として取り出す
        own_free = calendar.find_free_slots(start, end, 1)
        busy.extend(_invert(own_free, start, end))

    for person in people:
        try:
            busy.extend(calendar.busy_spans(person, start, end))
        except Exception:  # noqa: BLE001 - 一人の失敗で全体を止めない
            unavailable.append(person)

    slots = free_gaps(busy, start, end, duration_minutes)
    if business_hours is not None:
        slots = within_business_hours(slots, *business_hours)
        slots = [
            (slot_start, slot_end)
            for slot_start, slot_end in slots
            if slot_end - slot_start >= timedelta(minutes=duration_minutes)
        ]

    return CommonSlots(slots=slots[:limit], unavailable=unavailable)


def _invert(
    free: list[tuple[datetime, datetime]], start: datetime, end: datetime
) -> list[tuple[datetime, datetime]]:
    """空き時間の一覧を、埋まっている時間の一覧に反転する。"""
    busy: list[tuple[datetime, datetime]] = []
    cursor = start
    for free_start, free_end in sorted(free):
        if free_start > cursor:
            busy.append((cursor, free_start))
        cursor = max(cursor, free_end)
    if cursor < end:
        busy.append((cursor, end))
    return busy
