"""クラシックOutlook向けのCOM実装（pywin32）。

Outlookが起動しているWindows上でのみ動く。認証やアプリ登録は不要で、
ログイン中のプロファイルをそのまま操作する。

注意:
  - **開発機（Mac）では動作確認できない。** 実行検証は社用PCで行うこと。
  - 「新しいOutlook」はWebアプリのためCOMが効かない。その場合は
    Graph API実装を別途 adapters/graph_outlook.py として追加する。
  - Pythonのビット数をOutlookのビット数と合わせること（不一致だとDispatchが失敗する）。
"""

from __future__ import annotations

from datetime import datetime, timedelta

from .base import (
    Appointment,
    Busy,
    CalendarPort,
    MailDraft,
    MailPort,
    Person,
    SentMail,
)

# --- Outlookの列挙定数（pywin32では数値で渡す） ---
OL_MAIL_ITEM = 0
OL_APPOINTMENT_ITEM = 1
OL_FOLDER_CALENDAR = 9
OL_FOLDER_SENT_MAIL = 5

OL_NON_MEETING = 0
OL_MEETING = 1

_BUSY_STATUS = {Busy.FREE: 0, Busy.TENTATIVE: 1, Busy.BUSY: 2}

# Outlookの Restrict/Find に渡す日時書式。
# Outlook側のロケール設定に依存するため、社用PCで最初に検証すべき箇所。
_FILTER_FORMAT = "%m/%d/%Y %H:%M"


def _connect():
    """Outlookアプリケーションと MAPI 名前空間を取得する。"""
    import win32com.client  # Windows専用のため関数内でimportする

    app = win32com.client.Dispatch("Outlook.Application")
    return app, app.GetNamespace("MAPI")


class ComOutlookCalendar(CalendarPort):
    def create_tentative(self, appointment: Appointment) -> Appointment:
        app, _ = _connect()
        item = app.CreateItem(OL_APPOINTMENT_ITEM)
        item.Subject = appointment.subject
        item.Start = appointment.start.strftime("%Y-%m-%d %H:%M")
        item.Duration = int(
            (appointment.end - appointment.start).total_seconds() // 60
        )
        item.Location = appointment.location
        item.Body = appointment.body
        item.BusyStatus = _BUSY_STATUS[appointment.status]

        # 出席者は登録するが、この時点では送信しない（Saveのみ）。
        # MeetingStatus を olMeeting にしておくと、後から Send() で招待になる。
        if appointment.attendees:
            item.MeetingStatus = OL_MEETING
            for person in appointment.attendees:
                item.Recipients.Add(person.address or person.name)
            item.Recipients.ResolveAll()
        else:
            item.MeetingStatus = OL_NON_MEETING

        item.Save()
        return Appointment(
            subject=appointment.subject,
            start=appointment.start,
            end=appointment.end,
            attendees=appointment.attendees,
            body=appointment.body,
            location=appointment.location,
            status=appointment.status,
            entry_id=item.EntryID,
        )

    def send_invitation(self, entry_id: str) -> None:
        """仮予定を招待として送信する。取り消せないので呼び出し側で承認を取ること。"""
        _, ns = _connect()
        item = ns.GetItemFromID(entry_id)
        if not item.Recipients.Count:
            raise ValueError("出席者が登録されていないため招待を送信できません")
        item.MeetingStatus = OL_MEETING
        item.Recipients.ResolveAll()
        item.Send()

    def find_free_slots(
        self, start: datetime, end: datetime, duration_minutes: int
    ) -> list[tuple[datetime, datetime]]:
        """自分のカレンダーの予定を除いた空き枠を返す。"""
        _, ns = _connect()
        items = ns.GetDefaultFolder(OL_FOLDER_CALENDAR).Items
        items.IncludeRecurrences = True
        items.Sort("[Start]")
        restricted = items.Restrict(
            f"[Start] < '{end.strftime(_FILTER_FORMAT)}' "
            f"AND [End] > '{start.strftime(_FILTER_FORMAT)}'"
        )

        busy: list[tuple[datetime, datetime]] = sorted(
            (
                (
                    datetime.fromtimestamp(item.Start.timestamp()),
                    datetime.fromtimestamp(item.End.timestamp()),
                )
                for item in restricted
            ),
            key=lambda span: span[0],
        )

        slots: list[tuple[datetime, datetime]] = []
        cursor = start
        need = timedelta(minutes=duration_minutes)
        for busy_start, busy_end in busy:
            if busy_start - cursor >= need:
                slots.append((cursor, busy_start))
            cursor = max(cursor, busy_end)
        if end - cursor >= need:
            slots.append((cursor, end))
        return slots


class ComOutlookMail(MailPort):
    def create_draft(self, draft: MailDraft) -> MailDraft:
        """下書きフォルダに保存する。Send() は呼ばない。"""
        app, _ = _connect()
        item = app.CreateItem(OL_MAIL_ITEM)
        item.To = "; ".join(p.address or p.name for p in draft.to)
        if draft.cc:
            item.CC = "; ".join(p.address or p.name for p in draft.cc)
        item.Subject = draft.subject
        item.Body = draft.body
        item.Save()  # 下書きとして保存するのみ
        return MailDraft(
            to=draft.to,
            subject=draft.subject,
            body=draft.body,
            cc=draft.cc,
            entry_id=item.EntryID,
        )

    def recent_sent(self, limit: int = 20) -> list[SentMail]:
        """送信済みアイテムを新しい順に取得する。本文は保存せずメモリ上で使うこと。"""
        _, ns = _connect()
        items = ns.GetDefaultFolder(OL_FOLDER_SENT_MAIL).Items
        items.Sort("[SentOn]", True)

        results: list[SentMail] = []
        for item in items:
            if len(results) >= limit:
                break
            if getattr(item, "Class", None) != 43:  # olMail 以外は除外
                continue
            results.append(
                SentMail(
                    subject=item.Subject or "",
                    body=item.Body or "",
                    to=(Person(name=item.To or ""),),
                    sent_at=datetime.fromtimestamp(item.SentOn.timestamp()),
                )
            )
        return results

    def resolve_person(self, name: str) -> list[Person]:
        """表示名からSMTPアドレスを解決する。候補が絞れない場合は複数返る。"""
        app, _ = _connect()
        item = app.CreateItem(OL_MAIL_ITEM)
        recipient = item.Recipients.Add(name)
        if not recipient.Resolve():
            return []

        entry = recipient.AddressEntry
        address = None
        try:
            exchange_user = entry.GetExchangeUser()
            if exchange_user is not None:
                address = exchange_user.PrimarySmtpAddress
        except Exception:
            address = None
        return [Person(name=entry.Name, address=address or entry.Address)]
