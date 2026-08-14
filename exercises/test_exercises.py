"""演習の答え合わせ。全部 NotImplementedError で落ちるところから始める。

    PYTHONPATH=src:exercises python3 -m unittest discover -s exercises -t exercises

解答例に対して走らせる場合:

    EX_SOLUTIONS=1 PYTHONPATH=src:exercises python3 -m unittest discover -s exercises -t exercises
"""

from __future__ import annotations

import importlib
import os
import unittest
from datetime import datetime

from outlook_assistant.adapters.base import MailDraft, Person, SentMail

_PREFIX = "solutions." if os.environ.get("EX_SOLUTIONS") else ""

ex01 = importlib.import_module(f"{_PREFIX}ex01_spans")
ex02 = importlib.import_module(f"{_PREFIX}ex02_errors")
ex03 = importlib.import_module(f"{_PREFIX}ex03_dataclass")
ex04 = importlib.import_module(f"{_PREFIX}ex04_port")
ex05 = importlib.import_module(f"{_PREFIX}ex05_text")


def dt(hour: int, minute: int = 0, day: int = 19) -> datetime:
    return datetime(2026, 8, day, hour, minute)


def _need(module, name: str):
    """未定義なら「何を定義すべきか」を言って落ちる。"""
    if not hasattr(module, name):
        raise AssertionError(f"{module.__name__} に {name} を定義してください")
    return getattr(module, name)


# --------------------------------------------------------------------------
# 演習1
# --------------------------------------------------------------------------
class Ex01IntersectSpansTest(unittest.TestCase):
    def test_重なる部分だけを返す(self) -> None:
        a = [(dt(9), dt(12)), (dt(14), dt(18))]
        b = [(dt(11), dt(15))]
        self.assertEqual(
            ex01.intersect_spans(a, b),
            [(dt(11), dt(12)), (dt(14), dt(15))],
        )

    def test_重なりが無ければ空(self) -> None:
        a = [(dt(9), dt(10))]
        b = [(dt(11), dt(12))]
        self.assertEqual(ex01.intersect_spans(a, b), [])

    def test_接しているだけは重なりとみなさない(self) -> None:
        a = [(dt(9), dt(11))]
        b = [(dt(11), dt(13))]
        self.assertEqual(ex01.intersect_spans(a, b), [])

    def test_片方が空なら空(self) -> None:
        self.assertEqual(ex01.intersect_spans([], [(dt(9), dt(18))]), [])

    def test_入力が順不同でも開始時刻順に返す(self) -> None:
        a = [(dt(14), dt(18)), (dt(9), dt(12))]
        b = [(dt(10), dt(11)), (dt(16), dt(17))]
        self.assertEqual(
            ex01.intersect_spans(a, b),
            [(dt(10), dt(11)), (dt(16), dt(17))],
        )

    def test_片方に重なりが分かれて入る(self) -> None:
        a = [(dt(9), dt(18))]
        b = [(dt(10), dt(11)), (dt(13), dt(14))]
        self.assertEqual(
            ex01.intersect_spans(a, b),
            [(dt(10), dt(11)), (dt(13), dt(14))],
        )


# --------------------------------------------------------------------------
# 演習2
# --------------------------------------------------------------------------
class Ex02ParseDurationTest(unittest.TestCase):
    def test_数字だけなら分として読む(self) -> None:
        self.assertEqual(ex02.parse_duration("90"), 90)

    def test_分の単位付き(self) -> None:
        self.assertEqual(ex02.parse_duration("30m"), 30)

    def test_時間の単位付き(self) -> None:
        self.assertEqual(ex02.parse_duration("1h"), 60)

    def test_時間と分の組み合わせ(self) -> None:
        self.assertEqual(ex02.parse_duration("1h30m"), 90)

    def test_空白は無視する(self) -> None:
        self.assertEqual(ex02.parse_duration("2h 15m"), 135)

    def test_書式に合わなければ拒否する(self) -> None:
        for bad in ("", "abc", "1時間", "m30", "1h30"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    ex02.parse_duration(bad)

    def test_0以下は拒否する(self) -> None:
        for bad in ("0", "0m", "0h0m"):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    ex02.parse_duration(bad)

    def test_エラーメッセージに入力値が含まれる(self) -> None:
        """利用者が何を直せばよいか分かること。"""
        with self.assertRaises(ValueError) as caught:
            ex02.parse_duration("1時間")
        self.assertIn("1時間", str(caught.exception))


# --------------------------------------------------------------------------
# 演習3
# --------------------------------------------------------------------------
class Ex03DataclassTest(unittest.TestCase):
    def setUp(self) -> None:
        self.Priority = _need(ex03, "Priority")
        self.MeetingRequest = _need(ex03, "MeetingRequest")

    def test_優先度は文字列としても振る舞う(self) -> None:
        self.assertEqual(self.Priority.HIGH, "high")
        self.assertEqual(self.Priority.LOW, "low")
        self.assertEqual(self.Priority.NORMAL, "normal")

    def test_必須項目だけで作れる(self) -> None:
        req = self.MeetingRequest(subject="定例", duration_minutes=60)
        self.assertEqual(req.attendees, ())
        self.assertEqual(req.priority, self.Priority.NORMAL)
        self.assertEqual(req.notes, {})

    def test_中身が同じなら等しい(self) -> None:
        a = self.MeetingRequest(subject="定例", duration_minutes=60)
        b = self.MeetingRequest(subject="定例", duration_minutes=60)
        self.assertEqual(a, b)

    def test_作った後は書き換えられない(self) -> None:
        req = self.MeetingRequest(subject="定例", duration_minutes=60)
        with self.assertRaises(Exception):
            req.subject = "別件"  # type: ignore[misc]

    def test_notesはインスタンスごとに別物(self) -> None:
        """既定値の落とし穴（第2章）を踏んでいないこと。"""
        a = self.MeetingRequest(subject="A", duration_minutes=30)
        b = self.MeetingRequest(subject="B", duration_minutes=30)
        a.notes["room"] = "会議室A"
        self.assertEqual(b.notes, {})

    def test_出席者を渡せる(self) -> None:
        req = self.MeetingRequest(
            subject="定例",
            duration_minutes=60,
            attendees=(Person(name="山田太郎"),),
            priority=self.Priority.HIGH,
        )
        self.assertEqual(req.attendees[0].name, "山田太郎")
        self.assertEqual(req.priority, self.Priority.HIGH)

    def test_終了時刻を計算できる(self) -> None:
        req = self.MeetingRequest(subject="定例", duration_minutes=90)
        self.assertEqual(req.scheduled_end(dt(14)), dt(15, 30))


# --------------------------------------------------------------------------
# 演習4
# --------------------------------------------------------------------------
class Ex04FakeMailTest(unittest.TestCase):
    def test_下書きを記録し予定IDを採番する(self) -> None:
        mail = ex04.FakeMail()
        first = mail.create_draft(
            MailDraft(to=(Person(name="山田太郎"),), subject="件名", body="本文")
        )
        second = mail.create_draft(
            MailDraft(to=(Person(name="佐藤花子"),), subject="件名2", body="本文2")
        )
        self.assertEqual(first.entry_id, "DRAFT-0")
        self.assertEqual(second.entry_id, "DRAFT-1")
        self.assertEqual(len(mail.created), 2)

    def test_送信済みメールを件数で絞れる(self) -> None:
        sent = [
            SentMail(
                subject=f"件名{i}",
                body="本文",
                to=(Person(name="山田太郎"),),
                sent_at=dt(10),
            )
            for i in range(5)
        ]
        mail = ex04.FakeMail(sent=sent)
        self.assertEqual(len(mail.recent_sent(limit=3)), 3)

    def test_名簿から宛先を解決する(self) -> None:
        mail = ex04.FakeMail(
            directory=[Person(name="山田太郎", address="yamada@example.com")]
        )
        self.assertEqual(len(mail.resolve_person("山田太郎")), 1)
        self.assertEqual(mail.resolve_person("居ない人"), [])


class Ex04DraftReplyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mail = ex04.FakeMail(
            directory=[
                Person(name="山田太郎", address="taro.yamada@example.com"),
                Person(name="佐藤花子", address="hanako.sato@example.com"),
                Person(name="佐藤花子", address="h.sato@example.co.jp"),
            ]
        )

    def test_一意に解決できれば下書きを作る(self) -> None:
        draft = ex04.draft_reply(self.mail, "山田太郎", "ご相談", "本文です")
        self.assertEqual(draft.to[0].address, "taro.yamada@example.com")
        self.assertEqual(draft.subject, "ご相談")
        self.assertEqual(draft.entry_id, "DRAFT-0")
        self.assertEqual(len(self.mail.created), 1)

    def test_宛先が見つからなければ下書きを作らない(self) -> None:
        with self.assertRaises(ValueError):
            ex04.draft_reply(self.mail, "居ない人", "件名", "本文")
        self.assertEqual(self.mail.created, [])

    def test_同名が複数なら人間に判断を返す(self) -> None:
        with self.assertRaises(ValueError) as caught:
            ex04.draft_reply(self.mail, "佐藤花子", "件名", "本文")
        self.assertIn("佐藤花子", str(caught.exception))
        self.assertEqual(self.mail.created, [])

    def test_送信手段が存在しない(self) -> None:
        """MailPort に send が無いこと自体が安全策（第12章）。"""
        self.assertFalse(hasattr(self.mail, "send"))


# --------------------------------------------------------------------------
# 演習5
# --------------------------------------------------------------------------
class Ex05FrequentClosingsTest(unittest.TestCase):
    def test_多い順に返す(self) -> None:
        bodies = [
            "お世話になっております。\n承知しました。\nよろしくお願いいたします。",
            "お世話になっております。\n確認します。\nよろしくお願いいたします。",
            "お疲れ様です。\n了解です。\n引き続きよろしくお願いします。",
        ]
        self.assertEqual(
            ex05.frequent_closings(bodies),
            [
                ("よろしくお願いいたします。", 2),
                ("引き続きよろしくお願いします。", 1),
            ],
        )

    def test_件数を絞れる(self) -> None:
        bodies = [
            "書き出し\n結びA",
            "書き出し\n結びA",
            "書き出し\n結びB",
            "書き出し\n結びC",
        ]
        self.assertEqual(len(ex05.frequent_closings(bodies, top_n=2)), 2)

    def test_引用部分は数えない(self) -> None:
        bodies = [
            "お世話になっております。\n承知しました。\nよろしくお願いいたします。"
            "\n\n-----Original Message-----\n差出人: 山田太郎\n相手の結びです。",
            "お世話になっております。\n了解です。\nよろしくお願いいたします。",
        ]
        self.assertEqual(
            ex05.frequent_closings(bodies),
            [("よろしくお願いいたします。", 2)],
        )

    def test_空行は行として数えない(self) -> None:
        bodies = ["書き出し\n\n本文\n\n結びです。\n\n"]
        self.assertEqual(ex05.frequent_closings(bodies), [("結びです。", 1)])

    def test_一行しかない本文は数えない(self) -> None:
        self.assertEqual(ex05.frequent_closings(["承知しました。"]), [])

    def test_本文が無ければ空(self) -> None:
        self.assertEqual(ex05.frequent_closings([]), [])


if __name__ == "__main__":
    unittest.main()
