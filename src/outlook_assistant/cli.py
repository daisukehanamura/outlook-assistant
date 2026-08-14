"""コマンドラインインタフェース。

AIエージェント（Copilot / Claude Code）がスキルから呼び出す入口。
自然言語の解釈はエージェント側で済ませ、ここには確定値だけを渡す。

    python -m outlook_assistant hold   --subject "打ち合わせ" --start "2026-08-19 14:00" --duration 60
    python -m outlook_assistant invite --id <ENTRY_ID>
    python -m outlook_assistant slots  --from "2026-08-18 09:00" --to "2026-08-22 18:00" --duration 60
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from .adapters.base import Person
from .calendar_hold import find_common_slots, hold, invite, suggest_slots
from .style_profile import build_profile

_DATETIME_HINT = "YYYY-MM-DD HH:MM"


def _parse_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"日時は '{_DATETIME_HINT}' 形式で指定してください: {value!r}"
        ) from exc


def _calendar():
    """COM実装を遅延importする（Windows以外ではimport自体が失敗するため）。"""
    from .adapters.com_outlook import ComOutlookCalendar

    return ComOutlookCalendar()


def _mail():
    from .adapters.com_outlook import ComOutlookMail

    return ComOutlookMail()


def _cmd_hold(args: argparse.Namespace) -> int:
    attendees = [Person(name=name) for name in args.attendee]
    appointment = hold(
        _calendar(),
        subject=args.subject,
        start=args.start,
        duration_minutes=args.duration,
        attendees=attendees,
        location=args.location,
        body=args.body,
    )

    print("仮予定を作成しました（招待は送っていません）")
    print(f"  件名  : {appointment.subject}")
    print(f"  日時  : {appointment.start:%Y-%m-%d %H:%M} - {appointment.end:%H:%M}")
    if appointment.location:
        print(f"  場所  : {appointment.location}")
    if appointment.attendees:
        print(f"  出席者: {', '.join(p.name for p in appointment.attendees)}")
    print(f"  予定ID: {appointment.entry_id}")
    print()
    print("内容を確認したうえで招待を送る場合:")
    print(f"  python -m outlook_assistant invite --id {appointment.entry_id}")
    return 0


def _cmd_invite(args: argparse.Namespace) -> int:
    invite(_calendar(), args.id)
    print(f"招待を送信しました: {args.id}")
    return 0


def _cmd_slots(args: argparse.Namespace) -> int:
    calendar = _calendar()
    window_start = getattr(args, "from")

    if not args.attendee:
        slots = suggest_slots(
            calendar,
            start=window_start,
            end=args.to,
            duration_minutes=args.duration,
            limit=args.limit,
        )
        unavailable: list[Person] = []
        scope = "自分のカレンダーのみ"
    else:
        result = find_common_slots(
            calendar,
            people=[Person(name=name) for name in args.attendee],
            start=window_start,
            end=args.to,
            duration_minutes=args.duration,
            limit=args.limit,
        )
        slots = result.slots
        unavailable = result.unavailable
        confirmed = [n for n in args.attendee if n not in {p.name for p in unavailable}]
        scope = "自分 + " + (", ".join(confirmed) if confirmed else "（確認できた相手なし）")

    if not slots:
        print("全員が空いている枠は見つかりませんでした")
    else:
        print(f"空き枠の候補（{args.duration}分以上／{scope}）:")
        for slot_start, slot_end in slots:
            print(f"  {slot_start:%Y-%m-%d(%a) %H:%M} - {slot_end:%H:%M}")

    if unavailable:
        print()
        print("※ 次の方の空き時間は確認できませんでした（予定の有無は不明です）:")
        for person in unavailable:
            print(f"    - {person.name}")
        print("  上の候補にはこの方の予定が反映されていません。")

    return 0 if slots else 1


def _cmd_style(args: argparse.Namespace) -> int:
    mails = _mail().recent_sent(limit=args.limit)
    if not mails:
        print("送信済みメールが見つかりませんでした")
        return 1

    profile = build_profile(mails)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(profile.to_markdown(), encoding="utf-8")

    print(f"文体プロファイルを作成しました: {output}")
    print(f"  参照した送信メール: {profile.sample_count} 通")
    if profile.greetings:
        print(f"  よく使う書き出し  : 「{profile.greetings[0][0]}」")
    if profile.closings:
        print(f"  よく使う結び      : 「{profile.closings[0][0]}」")
    print()
    print("※ 業務情報を含むため、このファイルはコミットしないこと（.gitignore 済み）")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="outlook_assistant",
        description="Outlookの予定を仮抑えし、確認後に招待を送る",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_hold = sub.add_parser("hold", help="予定を仮（Tentative）で押さえる。招待は送らない")
    p_hold.add_argument("--subject", required=True, help="件名")
    p_hold.add_argument("--start", required=True, type=_parse_datetime, help=_DATETIME_HINT)
    p_hold.add_argument("--duration", required=True, type=int, help="所要時間（分）")
    p_hold.add_argument("--attendee", action="append", default=[], help="出席者（複数指定可）")
    p_hold.add_argument("--location", default="", help="場所")
    p_hold.add_argument("--body", default="", help="本文")
    p_hold.set_defaults(func=_cmd_hold)

    p_invite = sub.add_parser("invite", help="仮予定を出席者への招待として送信する")
    p_invite.add_argument("--id", required=True, help="hold が表示した予定ID")
    p_invite.set_defaults(func=_cmd_invite)

    p_style = sub.add_parser(
        "style", help="送信済みメールから文体プロファイルを作る"
    )
    p_style.add_argument("--limit", type=int, default=20, help="参照する送信メールの件数")
    p_style.add_argument(
        "--output",
        default="data/style_profile.md",
        help="出力先。業務情報を含むため .gitignore の対象に置くこと",
    )
    p_style.set_defaults(func=_cmd_style)

    p_slots = sub.add_parser(
        "slots", help="空き枠を探す。--attendee を付けると全員が空いている枠に絞る"
    )
    p_slots.add_argument("--from", required=True, type=_parse_datetime, help=_DATETIME_HINT)
    p_slots.add_argument("--to", required=True, type=_parse_datetime, help=_DATETIME_HINT)
    p_slots.add_argument("--duration", required=True, type=int, help="必要な長さ（分）")
    p_slots.add_argument(
        "--attendee",
        action="append",
        default=[],
        help="空き状況を確認する相手（複数指定可）。省略すると自分のみ",
    )
    p_slots.add_argument("--limit", type=int, default=5, help="候補の最大件数")
    p_slots.set_defaults(func=_cmd_slots)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001 - 利用者に読める形で失敗を伝える
        print(f"エラー: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
