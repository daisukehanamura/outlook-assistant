"""演習5（🌿 第7章）: 文字列処理と Counter

style_profile.build_profile() の一部を、自分で書き直す演習。
引用の除去は本物（strip_quoted）を再利用してよい ── 車輪の再発明はしない。

    frequent_closings(bodies, top_n=3)
        送信メール本文のリストから「よく使う結び」を多い順に返す。
        戻り値は [(文字列, 回数), ...]。

規則:
  1. 各本文から引用部分を落とす（strip_quoted）
  2. 空白だけの行は無いものとして扱う
  3. 残った行が 2 行以上あるときだけ、最終行を「結び」として数える
     （1 行しかない本文は、書き出しと結びの区別が付かないので数えない）
  4. 出現回数の多い順に top_n 件を返す

ヒント:
  - collections.Counter の most_common(n) がそのまま答えの形になる
  - 「空白だけの行を除いた行のリスト」は内包表記 1 行で作れる
    （style_profile._content_lines が手本）

余力があれば:
  build_profile が politeness_per_mail を出しているのと同じ要領で、
  1通あたりの平均行長を返す関数も書いてみる。
"""

from __future__ import annotations

from collections import Counter  # noqa: F401  ヒント

from outlook_assistant.style_profile import strip_quoted  # noqa: F401  ヒント


def frequent_closings(bodies: list[str], top_n: int = 3) -> list[tuple[str, int]]:
    """よく使う結びを、出現回数の多い順に返す。"""
    raise NotImplementedError("ここを実装する")
