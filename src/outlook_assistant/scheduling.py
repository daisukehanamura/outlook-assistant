"""空き時間の計算。Outlookに依存しない純粋なロジック。

Outlookから取得した「埋まっている時間帯」の集合を受け取り、
空き枠を割り出す部分だけを切り出してある。ここが純粋関数なので、
Outlookの無い開発機でも検証できる。
"""

from __future__ import annotations

from datetime import datetime, timedelta

Span = tuple[datetime, datetime]


def merge_spans(spans: list[Span]) -> list[Span]:
    """重なり合う・隣接する時間帯をひとつにまとめる。

    複数人の予定を合成するときに使う。誰か一人でも埋まっていれば
    その時間は使えないため、全員分をまとめて1本の「埋まっている帯」にする。
    """
    ordered = sorted(span for span in spans if span[0] < span[1])
    if not ordered:
        return []

    merged = [ordered[0]]
    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end:  # 重なるか、ちょうど連続している
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))
    return merged


def free_gaps(
    busy: list[Span], start: datetime, end: datetime, duration_minutes: int
) -> list[Span]:
    """埋まっている時間帯を除いて、指定の長さが取れる空き枠を返す。"""
    if duration_minutes <= 0:
        raise ValueError("所要時間は1分以上で指定してください")

    need = timedelta(minutes=duration_minutes)
    gaps: list[Span] = []
    cursor = start

    for busy_start, busy_end in merge_spans(busy):
        if busy_end <= start or busy_start >= end:
            continue  # 対象期間の外
        if busy_start - cursor >= need:
            gaps.append((cursor, busy_start))
        cursor = max(cursor, busy_end)

    if end - cursor >= need:
        gaps.append((cursor, end))
    return gaps


def within_business_hours(
    spans: list[Span], start_hour: int = 9, end_hour: int = 18
) -> list[Span]:
    """空き枠を業務時間帯に絞り込む。

    「深夜3時が空いています」と提案しないためのフィルタ。
    日をまたぐ枠は日ごとに切り分ける。
    """
    result: list[Span] = []
    for span_start, span_end in spans:
        cursor = span_start
        while cursor < span_end:
            day_start = cursor.replace(hour=start_hour, minute=0, second=0, microsecond=0)
            day_end = cursor.replace(hour=end_hour, minute=0, second=0, microsecond=0)
            clipped_start = max(cursor, day_start)
            clipped_end = min(span_end, day_end)
            if clipped_start < clipped_end:
                result.append((clipped_start, clipped_end))
            # 翌日の頭へ進める
            cursor = (cursor + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
    return result


def parse_free_busy(
    pattern: str,
    start: datetime,
    minutes_per_char: int,
    busy_codes: str = "123",
) -> list[Span]:
    """OutlookのFreeBusy文字列を、埋まっている時間帯の一覧に変換する。

    OutlookのRecipient.FreeBusyは、指定日の午前0時を起点に、
    1文字＝minutes_per_char分 の粒度で状態を並べた文字列を返す。

        '0' 空き / '1' 仮の予定 / '2' 予定あり / '3' 外出中 / '4' 別の場所で勤務

    既定では仮の予定('1')も「埋まっている」扱いにする。仮でも先約は先約なので、
    そこへ重ねて提案すると調整の手間が増えるため。
    """
    origin = start.replace(hour=0, minute=0, second=0, microsecond=0)
    step = timedelta(minutes=minutes_per_char)

    spans: list[Span] = []
    for index, code in enumerate(pattern):
        if code in busy_codes:
            spans.append((origin + step * index, origin + step * (index + 1)))
    return merge_spans(spans)
