"""過去の送信メールから文体プロファイルを作る。

やっていることは機械的な抽出だけで、文章の生成はしない。
「どう書くか」はAIエージェントの仕事、「その人がどう書いてきたか」を
観測可能な形にするのがこのモジュールの仕事。

抽出結果には業務情報が含まれるため、出力先は .gitignore の対象に置くこと。
本文をまるごと保存せず、書き出し・結び・署名といった定型部分と統計値に
落とすのも、そのままの業務メールを file に残さないため。
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field

from .adapters.base import SentMail

# 返信・転送で引用される部分の目印。ここから下は自分が書いた文ではない。
_QUOTE_MARKERS = (
    "-----Original Message-----",
    "-----元のメッセージ-----",
    "________________________________",
)
_QUOTE_HEADER = re.compile(r"^\s*(差出人|送信者|From|宛先|To|件名|Subject)\s*[:：]")

# 敬語の丁寧さを測るための目印。多いほど改まった文体。
_POLITE_MARKERS = (
    "恐れ入り",
    "誠に",
    "何卒",
    "いただけますでしょうか",
    "ございます",
    "存じます",
    "幸いです",
    "お手数",
)


@dataclass
class StyleProfile:
    """観測された書き癖。"""

    sample_count: int = 0
    greetings: list[tuple[str, int]] = field(default_factory=list)
    """よく使う書き出しと、その出現回数。"""

    closings: list[tuple[str, int]] = field(default_factory=list)
    """よく使う結びと、その出現回数。"""

    signature: str = ""
    """全メール共通の末尾ブロック（署名）。"""

    avg_line_length: float = 0.0
    blank_line_between_paragraphs: bool = False
    politeness_per_mail: float = 0.0
    """1通あたりの敬語表現の出現数。文体の硬さの目安。"""

    def to_markdown(self) -> str:
        lines = [
            "# 文体プロファイル",
            "",
            "過去の送信メールから機械的に抽出した書き癖。",
            "メール下書きを作る際は、この特徴に寄せること。",
            "",
            f"- 参照した送信メール: {self.sample_count} 通",
            f"- 1行の平均文字数: {self.avg_line_length:.0f} 文字",
            f"- 段落間に空行を入れる: {'はい' if self.blank_line_between_paragraphs else 'いいえ'}",
            f"- 1通あたりの敬語表現: {self.politeness_per_mail:.1f} 個",
            "",
            "## よく使う書き出し",
            "",
        ]
        lines += [f"- 「{text}」（{count}回）" for text, count in self.greetings] or [
            "- （抽出できませんでした）"
        ]
        lines += ["", "## よく使う結び", ""]
        lines += [f"- 「{text}」（{count}回）" for text, count in self.closings] or [
            "- （抽出できませんでした）"
        ]

        if self.signature:
            lines += ["", "## 署名", "", "```", self.signature, "```"]
        return "\n".join(lines) + "\n"


def strip_quoted(body: str) -> str:
    """返信・転送の引用部分を落として、自分が書いた本文だけにする。

    引用を残したまま統計を取ると、相手の文体を自分の癖として学習してしまう。
    """
    lines: list[str] = []
    for line in body.splitlines():
        if any(marker in line for marker in _QUOTE_MARKERS):
            break
        if _QUOTE_HEADER.match(line):
            break
        if line.lstrip().startswith(">"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _content_lines(body: str) -> list[str]:
    return [line.strip() for line in body.splitlines() if line.strip()]


def find_signature(bodies: list[str]) -> str:
    """全メールに共通する末尾ブロックを署名とみなす。

    末尾から1行ずつ遡り、すべてのメールで一致する範囲を署名として切り出す。
    """
    if len(bodies) < 2:
        return ""

    line_sets = [_content_lines(body) for body in bodies if _content_lines(body)]
    if len(line_sets) < 2:
        return ""

    common: list[str] = []
    for offset in range(1, min(len(lines) for lines in line_sets) + 1):
        candidates = {lines[-offset] for lines in line_sets}
        if len(candidates) != 1:
            break
        common.append(candidates.pop())
    return "\n".join(reversed(common))


def build_profile(mails: list[SentMail], top_n: int = 3) -> StyleProfile:
    """送信済みメールの一覧から文体プロファイルを組み立てる。"""
    bodies = [strip_quoted(mail.body) for mail in mails]
    bodies = [body for body in bodies if body]
    if not bodies:
        return StyleProfile()

    signature = find_signature(bodies)
    signature_lines = set(_content_lines(signature))

    greetings: Counter[str] = Counter()
    closings: Counter[str] = Counter()
    line_lengths: list[int] = []
    blank_line_mails = 0
    politeness = 0

    for body in bodies:
        lines = [line for line in _content_lines(body) if line not in signature_lines]
        if not lines:
            continue

        greetings[lines[0]] += 1
        if len(lines) > 1:
            closings[lines[-1]] += 1

        line_lengths.extend(len(line) for line in lines)
        politeness += sum(body.count(marker) for marker in _POLITE_MARKERS)

        # 本文中に空行があれば「段落を空行で区切る」癖とみなす
        stripped = body.splitlines()
        if any(
            not stripped[i].strip() and stripped[i - 1].strip() and i + 1 < len(stripped)
            for i in range(1, len(stripped))
        ):
            blank_line_mails += 1

    return StyleProfile(
        sample_count=len(bodies),
        greetings=greetings.most_common(top_n),
        closings=closings.most_common(top_n),
        signature=signature,
        avg_line_length=sum(line_lengths) / len(line_lengths) if line_lengths else 0.0,
        blank_line_between_paragraphs=blank_line_mails * 2 >= len(bodies),
        politeness_per_mail=politeness / len(bodies),
    )
