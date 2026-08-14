# outlook-assistant

Outlookの定型作業をAIエージェント経由で片付けるための道具立て。

1. **空き時間の確認** — 招待したい相手の空き状況を照会し、**全員が空いている時間帯**を出す
2. **予定の仮抑え** — 「来週の水曜あたりで1時間」程度の指示から、自分のカレンダーに仮予定（Tentative）を作る。内容を確認してから、別コマンドで出席者に招待を送る
3. **メールの下書き作成** — 抽象的な指示から、自分の過去メールの文体を模倣した下書きをOutlookに作る。**送信はしない**

## 使い方

```powershell
# 1. 全員が空いている枠を探す
python -m outlook_assistant slots --from "2026-08-18 09:00" --to "2026-08-22 18:00" `
    --duration 60 --attendee "山田太郎" --attendee "佐藤花子"

# 2. 枠を決めて仮抑え（この時点では招待は飛ばない。予定IDが表示される）
python -m outlook_assistant hold --subject "定例の相談" --start "2026-08-19 14:00" `
    --duration 60 --attendee "山田太郎" --attendee "佐藤花子"

# 3. 内容を確認したうえで、出席者へ招待を送る（翌日でもよい）
python -m outlook_assistant invite --id <予定ID>

# 文体プロファイルを作る（メール下書きの前に一度実行しておく）
python -m outlook_assistant style --limit 20
```

日時の自然言語解釈（「来週の水曜あたり」等）はAIエージェント側が担当し、
コマンドには確定した日時を渡す。曖昧さの解釈はLLMが得意で、
Python側に日本語日付パーサを抱えると保守対象が増えるため。

## 前提環境

| | |
|---|---|
| 実行環境 | **社用PC / Windows** |
| Outlook | **クラシック版**（新しいOutlookではない） |
| 連携方式 | `pywin32` によるCOM自動化。**アプリ登録・管理者承認・認証は一切不要** |
| AIエージェント | 社用PCは **GitHub Copilot**、開発機は Claude Code |

> **開発機（Mac）では動作しません。** MacにはOutlookもO365も無いため、実行検証は社用PC上でのみ可能です。
> Mac側では「叩き台」を書き、社用PCへ持っていって動かす運用を前提にしています。

## 設計方針

- **Outlook操作はアダプタ層に隔離する。** 業務ロジックは `adapters/base.py` の抽象インタフェースにのみ依存し、
  COM実装（`adapters/com_outlook.py`）を直接呼ばない。
  Microsoftが「新しいOutlook」への移行を進めているため、将来Graph API実装に差し替える必要が出た時に、
  上物を壊さず最下層だけ交換できるようにしておく。
- **破壊的操作は必ず人間の承認を挟む。** メールは下書き止まり、招待送信は明示的な別コマンド。
- **業務データはリポジトリに置かない。** 過去メール本文・連絡先・予定の実データはすべて `.gitignore` で除外。
  privateリポジトリであってもGitHubは社外サービスであるため。

## 構成

```
outlook-assistant/
├── src/outlook_assistant/
│   ├── adapters/
│   │   ├── base.py           # 抽象インタフェース（差し替え点）
│   │   └── com_outlook.py    # pywin32 / クラシックOutlook 実装
│   ├── calendar_hold.py      # 予定の仮抑え・招待送信
│   └── mail_draft.py         # メール下書き生成
├── skills/                   # Agent Skills（Copilot / Claude Code 共通形式）
├── docs/decisions.md         # 設計判断ログ
└── samples/                  # サンプルデータ（実データは追跡しない）
```

## セットアップ（社用PC）

```powershell
git clone <このリポジトリ>
cd outlook-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## ステータス

要件定義中。`docs/decisions.md` に確定事項と保留事項を記録している。
