"""演習2（🌿 第4・7章）: 例外の設計と正規表現

CLI の --duration は今のところ「分」の整数しか受け付けない（cli.py:156）。
"1h30m" のような書き方も通したい。

    "90"     -> 90
    "30m"    -> 30
    "1h"     -> 60
    "1h30m"  -> 90
    "2h 15m" -> 135   （空白は無視してよい）

不正な入力は ValueError にする。ただし失敗の理由が利用者に分かる文言にすること。
`cli.py:25-31` の _parse_datetime が手本になる。

条件:
  1. 数値に変換できない・書式に合わない -> ValueError
  2. 結果が 0 以下 -> ValueError（scheduling.free_gaps と同じ方針）
  3. 内部で別の例外（int() の ValueError など）を捕まえて包み直す場合は
     必ず `raise ... from exc` で原因を鎖につなぐ

ヒント:
  - re.fullmatch() はパターンが文字列全体に一致するときだけマッチする
  - グループが一致しなかった場合、match.group(n) は None を返す
"""

from __future__ import annotations

import re  # noqa: F401  ヒント


def parse_duration(text: str) -> int:
    """所要時間の文字列を分に変換する。"""
    raise NotImplementedError("ここを実装する")
