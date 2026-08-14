"""演習1 解答例。"""

from __future__ import annotations

from outlook_assistant.scheduling import Span, merge_spans


def intersect_spans(a: list[Span], b: list[Span]) -> list[Span]:
    """2つの時間帯リストに共通する時間帯を、開始時刻順に返す。"""
    # 先に整理しておくと「A の中で重なっている2本が別々に拾われる」心配が消える。
    merged_a = merge_spans(a)
    merged_b = merge_spans(b)

    result: list[Span] = []
    for a_start, a_end in merged_a:
        for b_start, b_end in merged_b:
            start = max(a_start, b_start)
            end = min(a_end, b_end)
            if start < end:  # 接しているだけ（start == end）は重なりではない
                result.append((start, end))
    return sorted(result)


# 別解: 両方が開始時刻順に並んでいる性質を使えば、二重ループを一重にできる。
# 走査の計算量が O(len(a) * len(b)) から O(len(a) + len(b)) に落ちる。
def intersect_spans_linear(a: list[Span], b: list[Span]) -> list[Span]:
    merged_a = merge_spans(a)
    merged_b = merge_spans(b)

    result: list[Span] = []
    i = j = 0
    while i < len(merged_a) and j < len(merged_b):
        start = max(merged_a[i][0], merged_b[j][0])
        end = min(merged_a[i][1], merged_b[j][1])
        if start < end:
            result.append((start, end))
        # 先に終わる方を進める。まだ終わっていない側は次の相手とも重なりうる。
        if merged_a[i][1] < merged_b[j][1]:
            i += 1
        else:
            j += 1
    return result
