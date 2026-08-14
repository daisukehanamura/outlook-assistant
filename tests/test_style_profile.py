"""文体プロファイルの抽出。Outlook無しで検証できる。"""

from __future__ import annotations

import unittest
from datetime import datetime

from outlook_assistant.adapters.base import Person, SentMail
from outlook_assistant.style_profile import build_profile, find_signature, strip_quoted

SIGNATURE = "----------------\n花村 大輔\n開発本部"


def mail(body: str, subject: str = "件名") -> SentMail:
    return SentMail(
        subject=subject,
        body=body,
        to=(Person(name="山田太郎"),),
        sent_at=datetime(2026, 8, 1, 10, 0),
    )


class StripQuotedTest(unittest.TestCase):
    def test_引用記号の行を落とす(self) -> None:
        body = "お疲れ様です。\n> 前のメールの内容\n確認しました。"
        self.assertEqual(strip_quoted(body), "お疲れ様です。\n確認しました。")

    def test_元のメッセージ以降を落とす(self) -> None:
        body = "了解しました。\n\n-----元のメッセージ-----\n差出人: 山田\n本文"
        self.assertEqual(strip_quoted(body), "了解しました。")

    def test_ヘッダ行以降を落とす(self) -> None:
        body = "承知しました。\n差出人: 山田太郎\n件名: 打ち合わせ"
        self.assertEqual(strip_quoted(body), "承知しました。")


class SignatureTest(unittest.TestCase):
    def test_全メール共通の末尾を署名とみなす(self) -> None:
        bodies = [
            f"お疲れ様です。\n本文A\n{SIGNATURE}",
            f"お疲れ様です。\n本文B\n{SIGNATURE}",
        ]
        self.assertEqual(find_signature(bodies), SIGNATURE)

    def test_1通だけでは署名を判定しない(self) -> None:
        """共通部分が取れないので、本文を丸ごと署名扱いしないこと。"""
        self.assertEqual(find_signature([f"本文\n{SIGNATURE}"]), "")

    def test_共通部分が無ければ空(self) -> None:
        self.assertEqual(find_signature(["本文A\n署名A", "本文B\n署名B"]), "")


class BuildProfileTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mails = [
            mail(f"お疲れ様です。花村です。\n\n件名の件、承知しました。\n\nよろしくお願いいたします。\n{SIGNATURE}"),
            mail(f"お疲れ様です。花村です。\n\n資料を送付します。\n\nよろしくお願いいたします。\n{SIGNATURE}"),
            mail(f"お疲れ様です。花村です。\n\n恐れ入りますが、ご確認をお願いいたします。\n\n何卒よろしくお願いいたします。\n{SIGNATURE}"),
        ]

    def test_よく使う書き出しを抽出する(self) -> None:
        profile = build_profile(self.mails)
        self.assertEqual(profile.greetings[0], ("お疲れ様です。花村です。", 3))

    def test_よく使う結びを抽出する(self) -> None:
        profile = build_profile(self.mails)
        self.assertEqual(profile.closings[0][0], "よろしくお願いいたします。")
        self.assertEqual(profile.closings[0][1], 2)

    def test_署名は書き出しや結びに混ざらない(self) -> None:
        """署名行を統計から除外できていること。"""
        profile = build_profile(self.mails)
        self.assertEqual(profile.signature, SIGNATURE)
        collected = [text for text, _ in profile.greetings + profile.closings]
        self.assertNotIn("開発本部", collected)

    def test_段落を空行で区切る癖を検出する(self) -> None:
        profile = build_profile(self.mails)
        self.assertTrue(profile.blank_line_between_paragraphs)

    def test_敬語の量を数える(self) -> None:
        profile = build_profile(self.mails)
        self.assertGreater(profile.politeness_per_mail, 0)

    def test_空のメールしか無ければ空のプロファイル(self) -> None:
        profile = build_profile([mail("")])
        self.assertEqual(profile.sample_count, 0)

    def test_Markdownに出力できる(self) -> None:
        markdown = build_profile(self.mails).to_markdown()
        self.assertIn("# 文体プロファイル", markdown)
        self.assertIn("お疲れ様です。花村です。", markdown)
        self.assertIn("## 署名", markdown)


if __name__ == "__main__":
    unittest.main()
