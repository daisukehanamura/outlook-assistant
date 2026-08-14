"""演習2 解答例。"""

from __future__ import annotations

import re

# (?:...) は「グループとして取り出さない括弧」。? は 0 個か 1 個。
# h の部分も m の部分も省略できるので、両方省略された空文字にも一致してしまう。
# その穴は「どちらのグループも None なら不正」で塞ぐ。
_DURATION = re.compile(r"(?:(\d+)h)?(?:(\d+)m)?")


def parse_duration(text: str) -> int:
    """所要時間の文字列を分に変換する。"""
    normalized = "".join(text.split())  # 空白をすべて除去

    try:
        minutes = int(normalized)  # "90" のように単位が無い場合
    except ValueError as exc:
        matched = _DURATION.fullmatch(normalized)
        if not matched or not (matched.group(1) or matched.group(2)):
            # 原因を鎖につないでおく（cli._parse_datetime と同じ作法）
            raise ValueError(
                f"所要時間の書式が読めません: {text!r}（例: 90, 30m, 1h30m）"
            ) from exc
        hours = int(matched.group(1) or 0)
        rest = int(matched.group(2) or 0)
        minutes = hours * 60 + rest

    if minutes <= 0:
        raise ValueError(f"所要時間は1分以上で指定してください: {text!r}")
    return minutes
