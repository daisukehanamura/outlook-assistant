"""演習5 解答例。"""

from __future__ import annotations

from collections import Counter

from outlook_assistant.style_profile import strip_quoted


def frequent_closings(bodies: list[str], top_n: int = 3) -> list[tuple[str, int]]:
    """よく使う結びを、出現回数の多い順に返す。"""
    closings: Counter[str] = Counter()

    for body in bodies:
        lines = [line.strip() for line in strip_quoted(body).splitlines() if line.strip()]
        # 1行しかない本文は、書き出しと結びを区別できないので数えない
        if len(lines) >= 2:
            closings[lines[-1]] += 1

    return closings.most_common(top_n)


def average_line_length(bodies: list[str]) -> float:
    """おまけ: 引用を除いた本文の平均行長。build_profile と同じ計算。"""
    lengths = [
        len(line.strip())
        for body in bodies
        for line in strip_quoted(body).splitlines()
        if line.strip()
    ]
    return sum(lengths) / len(lengths) if lengths else 0.0
