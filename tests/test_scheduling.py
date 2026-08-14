"""空き時間計算の純粋ロジック。Outlook無しで検証できる部分。"""

from __future__ import annotations

import unittest
from datetime import datetime

from outlook_assistant.scheduling import (
    free_gaps,
    merge_spans,
    parse_free_busy,
    within_business_hours,
)


def dt(hour: int, minute: int = 0, day: int = 19) -> datetime:
    return datetime(2026, 8, day, hour, minute)


class MergeSpansTest(unittest.TestCase):
    def test_重なる予定はひとつにまとまる(self) -> None:
        merged = merge_spans([(dt(10), dt(12)), (dt(11), dt(13))])
        self.assertEqual(merged, [(dt(10), dt(13))])

    def test_連続する予定もまとまる(self) -> None:
        merged = merge_spans([(dt(10), dt(11)), (dt(11), dt(12))])
        self.assertEqual(merged, [(dt(10), dt(12))])

    def test_離れた予定は別のまま(self) -> None:
        merged = merge_spans([(dt(10), dt(11)), (dt(14), dt(15))])
        self.assertEqual(merged, [(dt(10), dt(11)), (dt(14), dt(15))])

    def test_長さのない予定は無視する(self) -> None:
        self.assertEqual(merge_spans([(dt(10), dt(10))]), [])


class FreeGapsTest(unittest.TestCase):
    def test_必要な長さに満たない隙間は返さない(self) -> None:
        gaps = free_gaps([(dt(10), dt(11)), (dt(11, 30), dt(13))], dt(9), dt(18), 60)
        # 11:00-11:30 は30分しかないので候補にならない
        self.assertEqual(gaps, [(dt(9), dt(10)), (dt(13), dt(18))])

    def test_期間外の予定は無視する(self) -> None:
        gaps = free_gaps([(dt(6), dt(7))], dt(9), dt(18), 60)
        self.assertEqual(gaps, [(dt(9), dt(18))])

    def test_所要時間が0以下なら拒否する(self) -> None:
        with self.assertRaises(ValueError):
            free_gaps([], dt(9), dt(18), 0)


class BusinessHoursTest(unittest.TestCase):
    def test_業務時間の外を切り落とす(self) -> None:
        clipped = within_business_hours([(dt(7), dt(20))])
        self.assertEqual(clipped, [(dt(9), dt(18))])

    def test_日をまたぐ枠は日ごとに分割する(self) -> None:
        clipped = within_business_hours([(dt(15), dt(11, 0, day=20))])
        self.assertEqual(
            clipped,
            [(dt(15), dt(18)), (dt(9, 0, day=20), dt(11, 0, day=20))],
        )


class ParseFreeBusyTest(unittest.TestCase):
    """OutlookのFreeBusy文字列は、指定日の午前0時起点・1文字30分。"""

    def test_予定ありの区間を時間帯に変換する(self) -> None:
        # 0:00 から30分刻み。index 20-21 が 10:00-11:00
        pattern = "0" * 20 + "22" + "0" * 26
        spans = parse_free_busy(pattern, dt(9), 30)
        self.assertEqual(spans, [(dt(10), dt(11))])

    def test_仮の予定も埋まっている扱いにする(self) -> None:
        pattern = "0" * 20 + "11" + "0" * 26
        spans = parse_free_busy(pattern, dt(9), 30)
        self.assertEqual(spans, [(dt(10), dt(11))])

    def test_別の場所で勤務は空き扱い(self) -> None:
        pattern = "0" * 20 + "44" + "0" * 26
        spans = parse_free_busy(pattern, dt(9), 30)
        self.assertEqual(spans, [])

    def test_全部空きなら何も返さない(self) -> None:
        self.assertEqual(parse_free_busy("0" * 48, dt(9), 30), [])


if __name__ == "__main__":
    unittest.main()
