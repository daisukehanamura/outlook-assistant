"""仮抑え・招待送信のロジックを、Outlook無しで検証する。

開発機（Mac）にはOutlookが無いため、CalendarPort の偽実装を差し込んで
「招待が意図せず飛んでいないか」を確認する。
アダプタ層を分離した目的のひとつがこれ。
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta

from outlook_assistant.adapters.base import Appointment, Busy, CalendarPort, Person
from outlook_assistant.calendar_hold import (
    find_common_slots,
    hold,
    invite,
    suggest_slots,
)


class FakeCalendar(CalendarPort):
    def __init__(
        self,
        busy: list[tuple[datetime, datetime]] | None = None,
        others: dict[str, list[tuple[datetime, datetime]]] | None = None,
        unreachable: set[str] | None = None,
    ) -> None:
        self.created: list[Appointment] = []
        self.invited: list[str] = []
        self._busy = busy or []
        self._others = others or {}
        self._unreachable = unreachable or set()

    def busy_spans(self, person, start, end):
        if person.name in self._unreachable:
            raise ValueError(f"空き時間を照会できません: {person.name}")
        return list(self._others.get(person.name, []))

    def create_tentative(self, appointment: Appointment) -> Appointment:
        stored = Appointment(
            subject=appointment.subject,
            start=appointment.start,
            end=appointment.end,
            attendees=appointment.attendees,
            body=appointment.body,
            location=appointment.location,
            status=appointment.status,
            entry_id=f"ENTRY-{len(self.created)}",
        )
        self.created.append(stored)
        return stored

    def send_invitation(self, entry_id: str) -> None:
        self.invited.append(entry_id)

    def find_free_slots(self, start, end, duration_minutes):
        need = timedelta(minutes=duration_minutes)
        slots = []
        cursor = start
        for busy_start, busy_end in sorted(self._busy):
            if busy_start - cursor >= need:
                slots.append((cursor, busy_start))
            cursor = max(cursor, busy_end)
        if end - cursor >= need:
            slots.append((cursor, end))
        return slots


class HoldTest(unittest.TestCase):
    def setUp(self) -> None:
        self.calendar = FakeCalendar()
        self.start = datetime(2026, 8, 19, 14, 0)

    def test_仮抑えではTentativeになる(self) -> None:
        appointment = hold(self.calendar, "打ち合わせ", self.start, 60)
        self.assertEqual(appointment.status, Busy.TENTATIVE)
        self.assertEqual(appointment.end, self.start + timedelta(minutes=60))

    def test_仮抑えの時点では招待を送らない(self) -> None:
        """出席者を指定しても、hold だけでは絶対に送信されないこと。"""
        hold(
            self.calendar,
            "打ち合わせ",
            self.start,
            60,
            attendees=[Person(name="山田太郎")],
        )
        self.assertEqual(self.calendar.invited, [])

    def test_予定IDが返る(self) -> None:
        appointment = hold(self.calendar, "打ち合わせ", self.start, 60)
        self.assertEqual(appointment.entry_id, "ENTRY-0")

    def test_所要時間が0以下なら拒否する(self) -> None:
        with self.assertRaises(ValueError):
            hold(self.calendar, "打ち合わせ", self.start, 0)


class InviteTest(unittest.TestCase):
    def test_招待は予定IDを指定した時だけ送られる(self) -> None:
        calendar = FakeCalendar()
        appointment = hold(calendar, "打ち合わせ", datetime(2026, 8, 19, 14, 0), 60)
        self.assertEqual(calendar.invited, [])

        invite(calendar, appointment.entry_id)
        self.assertEqual(calendar.invited, ["ENTRY-0"])

    def test_予定IDが空なら拒否する(self) -> None:
        with self.assertRaises(ValueError):
            invite(FakeCalendar(), "")


class SlotsTest(unittest.TestCase):
    def test_埋まっている時間を避けて空き枠を返す(self) -> None:
        calendar = FakeCalendar(
            busy=[(datetime(2026, 8, 19, 12, 0), datetime(2026, 8, 19, 13, 0))]
        )
        slots = suggest_slots(
            calendar,
            start=datetime(2026, 8, 19, 9, 0),
            end=datetime(2026, 8, 19, 18, 0),
            duration_minutes=60,
        )
        self.assertEqual(
            slots,
            [
                (datetime(2026, 8, 19, 9, 0), datetime(2026, 8, 19, 12, 0)),
                (datetime(2026, 8, 19, 13, 0), datetime(2026, 8, 19, 18, 0)),
            ],
        )

    def test_件数を制限できる(self) -> None:
        calendar = FakeCalendar(
            busy=[
                (datetime(2026, 8, 19, 10, 0), datetime(2026, 8, 19, 11, 0)),
                (datetime(2026, 8, 19, 13, 0), datetime(2026, 8, 19, 14, 0)),
            ]
        )
        slots = suggest_slots(
            calendar,
            start=datetime(2026, 8, 19, 9, 0),
            end=datetime(2026, 8, 19, 18, 0),
            duration_minutes=30,
            limit=2,
        )
        self.assertEqual(len(slots), 2)


class CommonSlotsTest(unittest.TestCase):
    """出席者全員の空き時間を突き合わせる部分。"""

    def setUp(self) -> None:
        self.window_start = datetime(2026, 8, 19, 9, 0)
        self.window_end = datetime(2026, 8, 19, 18, 0)

    def test_誰か一人でも埋まっていればその時間は候補から外れる(self) -> None:
        calendar = FakeCalendar(
            others={
                "山田太郎": [(datetime(2026, 8, 19, 10, 0), datetime(2026, 8, 19, 12, 0))],
                "佐藤花子": [(datetime(2026, 8, 19, 13, 0), datetime(2026, 8, 19, 14, 0))],
            }
        )
        result = find_common_slots(
            calendar,
            people=[Person(name="山田太郎"), Person(name="佐藤花子")],
            start=self.window_start,
            end=self.window_end,
            duration_minutes=60,
            include_self=False,
        )
        self.assertEqual(
            result.slots,
            [
                (datetime(2026, 8, 19, 9, 0), datetime(2026, 8, 19, 10, 0)),
                (datetime(2026, 8, 19, 12, 0), datetime(2026, 8, 19, 13, 0)),
                (datetime(2026, 8, 19, 14, 0), datetime(2026, 8, 19, 18, 0)),
            ],
        )
        self.assertEqual(result.unavailable, [])

    def test_照会できない相手がいても処理は止まらない(self) -> None:
        """一人失敗しても候補は出す。ただし誰が未確認かを必ず返す。"""
        calendar = FakeCalendar(
            others={
                "山田太郎": [(datetime(2026, 8, 19, 10, 0), datetime(2026, 8, 19, 11, 0))]
            },
            unreachable={"社外の人"},
        )
        result = find_common_slots(
            calendar,
            people=[Person(name="山田太郎"), Person(name="社外の人")],
            start=self.window_start,
            end=self.window_end,
            duration_minutes=60,
            include_self=False,
        )
        self.assertTrue(result.slots)
        self.assertEqual([p.name for p in result.unavailable], ["社外の人"])

    def test_自分の予定も考慮される(self) -> None:
        calendar = FakeCalendar(
            busy=[(datetime(2026, 8, 19, 9, 0), datetime(2026, 8, 19, 15, 0))],
            others={},
        )
        result = find_common_slots(
            calendar,
            people=[Person(name="山田太郎")],
            start=self.window_start,
            end=self.window_end,
            duration_minutes=60,
            include_self=True,
        )
        self.assertEqual(
            result.slots,
            [(datetime(2026, 8, 19, 15, 0), datetime(2026, 8, 19, 18, 0))],
        )

    def test_業務時間外は候補にしない(self) -> None:
        calendar = FakeCalendar(others={})
        result = find_common_slots(
            calendar,
            people=[Person(name="山田太郎")],
            start=datetime(2026, 8, 19, 0, 0),
            end=datetime(2026, 8, 20, 0, 0),
            duration_minutes=60,
            include_self=False,
        )
        self.assertEqual(
            result.slots,
            [(datetime(2026, 8, 19, 9, 0), datetime(2026, 8, 19, 18, 0))],
        )


if __name__ == "__main__":
    unittest.main()
