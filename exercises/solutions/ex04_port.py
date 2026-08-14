"""演習4 解答例。"""

from __future__ import annotations

from outlook_assistant.adapters.base import MailDraft, MailPort, Person, SentMail


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

    def create_draft(self, draft: MailDraft) -> MailDraft:
        # MailDraft は frozen なので entry_id を後から代入できない。
        # ComOutlookMail.create_draft と同じく、埋めた新しい値を組み立てる。
        stored = MailDraft(
            to=draft.to,
            subject=draft.subject,
            body=draft.body,
            cc=draft.cc,
            entry_id=f"DRAFT-{len(self.created)}",
        )
        self.created.append(stored)
        return stored

    def recent_sent(self, limit: int = 20) -> list[SentMail]:
        return self._sent[:limit]

    def resolve_person(self, name: str) -> list[Person]:
        # 同名が複数いれば複数返る。絞るのはここの仕事ではない。
        return [person for person in self._directory if person.name == name]


def draft_reply(mail: MailPort, to_name: str, subject: str, body: str) -> MailDraft:
    """宛先名を解決して下書きを作る。送信はしない。"""
    candidates = mail.resolve_person(to_name)

    if not candidates:
        raise ValueError(f"宛先を解決できませんでした: {to_name!r}")
    if len(candidates) > 1:
        listed = ", ".join(person.address or person.name for person in candidates)
        raise ValueError(
            f"宛先の候補が複数あります。どれか確認してください: {to_name!r} -> {listed}"
        )

    return mail.create_draft(
        MailDraft(to=(candidates[0],), subject=subject, body=body)
    )
