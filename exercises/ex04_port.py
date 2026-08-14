"""演習4（🌳 第6章）: 抽象インタフェースとテストダブル

test_calendar_hold.py の FakeCalendar に相当するものを、メール側で作る。
このリポジトリの背骨（依存性逆転）を自分の手でなぞる演習。

作るもの その1: FakeMail
    MailPort（adapters/base.py:110）を継承し、3つの抽象メソッドを実装する。
    Outlook には触らず、渡されたものを自分の中に記録するだけ。

      create_draft(draft)  -> entry_id を埋めた MailDraft を返し、self.created に記録
                              entry_id は "DRAFT-0", "DRAFT-1", ... と採番する
      recent_sent(limit)   -> コンストラクタで受け取った送信済みメールを limit 件返す
      resolve_person(name) -> コンストラクタで受け取った名簿から、名前が一致する
                              Person を全部返す（同名が複数いれば複数返る）

    ComOutlookMail.create_draft（com_outlook.py:149）が entry_id を埋めた
    新しい MailDraft を返しているのが手本。frozen なので書き換えではなく作り直す。

作るもの その2: draft_reply()
    宛先を名前で解決してから下書きを作る関数。

      - 候補が 0 件 -> ValueError（誰宛か分からないまま下書きを作らない）
      - 候補が 2 件以上 -> ValueError。メッセージに候補の名前を含めること
        （base.py:122-128 の「絞れない場合は人間に確認すること」に従う）
      - 候補が 1 件 -> MailDraft を作って mail.create_draft() に渡し、その戻り値を返す

    MailPort に send メソッドが存在しないので、この関数はどう書いても送信できない。
    それが設計上の安全策になっている（第12章）。
"""

from __future__ import annotations

from outlook_assistant.adapters.base import (  # noqa: F401  ヒント
    MailDraft,
    MailPort,
    Person,
    SentMail,
)


class FakeMail(MailPort):
    """テスト用の MailPort。送信の代わりに記録する。"""

    def __init__(
        self,
        directory: list[Person] | None = None,
        sent: list[SentMail] | None = None,
    ) -> None:
        self.created: list[MailDraft] = []
        self._directory = directory or []
        self._sent = sent or []

    # TODO: create_draft / recent_sent / resolve_person を実装する


def draft_reply(mail: MailPort, to_name: str, subject: str, body: str) -> MailDraft:
    """宛先名を解決して下書きを作る。送信はしない。"""
    raise NotImplementedError("ここを実装する")
