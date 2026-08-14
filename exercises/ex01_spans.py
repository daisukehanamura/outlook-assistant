"""演習1（🌱 第1〜3章）: リスト・タプル・ループ

`scheduling.merge_spans` の兄弟にあたる関数を書く。

merge_spans は「誰か一人でも埋まっていれば埋まり」を作る和集合だった。
今回はその逆、「両方に共通して存在する時間帯」＝ 積集合を求める。

    A: 09:00-12:00, 14:00-18:00
    B: 11:00-15:00
    ->  11:00-12:00, 14:00-15:00

ヒント:
  - 先に merge_spans() で両方を整理しておくと、重なりの場合分けが減る
  - 2つの時間帯 (a1,a2) と (b1,b2) の共通部分は (max(a1,b1), min(a2,b2))
    これが「開始 < 終了」を満たすときだけ共通部分が存在する
  - 二重ループで書いてよい。まず正しく動かし、余裕があれば
    「両方が開始時刻順に並んでいる」性質を使って一重にできないか考える
"""

from __future__ import annotations

from outlook_assistant.scheduling import Span, merge_spans  # noqa: F401  ヒント


def intersect_spans(a: list[Span], b: list[Span]) -> list[Span]:
    """2つの時間帯リストに共通する時間帯を、開始時刻順に返す。

    重なりが無ければ空リストを返す。長さ0の重なり（接しているだけ）は含めない。
    """
    raise NotImplementedError("ここを実装する")
