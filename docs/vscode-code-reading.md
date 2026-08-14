# VS Code で Python を読む

`outlook-assistant` のコードを実際に辿りながら、
「実装クラスを探す」「呼び出し元を探す」といった操作を覚えるための手引き。

キーは Mac / Windows の両方を併記する（開発機は Mac、社用PC は Windows のため）。

---

## 0. まず設定する ── これが無いと何も動かない

このリポジトリはパッケージを `src/` の下に置いている。
そのままだと Pylance が `outlook_assistant` を解決できず、
**「定義へ移動」も「実装へ移動」も全滅する**。

`.vscode/settings.json` に設定済み（`.gitignore` 対象なのでコミットされない）。

```json
{
  "python.analysis.extraPaths": ["src", "exercises"]
}
```

### 効いているかの確かめ方

`tests/test_scheduling.py` を開き、8 行目の

```python
from outlook_assistant.scheduling import (
```

の `outlook_assistant` に**黄色い波線が出ていなければ成功**。
波線が出て `Import "outlook_assistant" could not be resolved` と言われる場合は、

1. `⇧⌘P` → `Python: Select Interpreter` で使うPythonを選び直す
2. `⇧⌘P` → `Developer: Reload Window`

の順で試す。設定を入れても波線が消えないときは、
インタプリタが別の環境（venv 未選択など）を指していることが多い。

### 必要な拡張機能

| 拡張機能 | 役割 |
|---|---|
| `ms-python.python` | 実行・テスト・デバッグ |
| `ms-python.vscode-pylance` | **補完と全ジャンプ機能の本体** |
| `ms-python.debugpy` | デバッガ |

ジャンプ系がすべて Pylance の解析結果に依存している。
「効かない」ときは、まず Pylance がそのファイルを解析できているかを疑う。

---

## 1. 基本の4つ

この 4 つだけで大半は足りる。
**この環境（Mac）は IntelliJ 寄せに割り当て直してある**ので、その列を追加してある。
設定内容は「9. IntelliJ 寄せの割り当て」を参照。

| 操作 | この環境（Mac） | VS Code 既定(Mac) | Windows 既定 | 何が起きるか |
|---|---|---|---|---|
| **定義へ移動** | `⌘`+クリック / `⌘B` | `F12` / `⌘`+クリック | `F12` / `Ctrl`+クリック | その名前が定義された場所へ飛ぶ |
| **実装へ移動** | `⌘⇧B` / `⌥⌘B` | `⌘F12` | `Ctrl+F12` | 抽象メソッドの**実装側**を一覧する |
| **参照をすべて検索** | `⌥F7` | `⇧F12` | `Shift+F12` | 使われている箇所を全部出す |
| **戻る** | `⌘←` / `⌘[` | `⌃-` | `Alt+←` | 直前にいた場所へ帰る |
| **進む** | `⌘→` / `⌘]` | `⌃⇧-` | `Alt+→` | 戻る前の場所へ帰る |

**「戻る」が一番大事。** ジャンプは飛ぶより帰る方が難しい。
`⌘←` を指に覚えさせると、深く潜っても迷子にならない。
進むは `⌘→` / `⌘]`（この環境）/ `⌃⇧-`（Mac 既定）/ `Alt+→`（Windows）。

飛ばずに覗くだけの **Peek** もある。`⌥F12`（Mac）/ `Alt+F12`（Windows）で、
現在のファイルを離れずに定義が小窓で開く。

---

## 2. 抽象 → 実装を探す（このリポジトリの本命）

`adapters/base.py` は抽象クラスの集まりで、
中身が docstring しか無い。ここで「定義へ移動」（`⌘`+クリック）を押しても意味がない。

### やってみる

1. `src/outlook_assistant/adapters/base.py` を開く
2. 78 行目 `def create_tentative(self, appointment: Appointment) -> Appointment:` の
   **`create_tentative` の上**にカーソルを置く
3. `⌘⇧B`（この環境）／ `⌘F12`（Mac 既定）／ `Ctrl+F12`（Windows）

実装が 2 つ並ぶ。

```
src/outlook_assistant/adapters/com_outlook.py:56   ComOutlookCalendar.create_tentative
tests/test_calendar_hold.py:40                     FakeCalendar.create_tentative
```

**これが第6章（依存性逆転）を目で確認する方法。**
本番用とテスト用の 2 実装が同じ抽象にぶら下がっている構造が、一覧で見える。

`MailPort` で同じことをすると 3 件出る（`ComOutlookMail` と、演習の `FakeMail` が 2 つ）。

### 複数見つかったときの Peek の操作

VS Code の既定では、実装が複数あると Peek（覗き窓）が開くだけで
**カーソルは元の場所に留まる**。だから飛ぶには一覧をダブルクリックする必要がある。
これがだるいので、この環境では設定で挙動を変えてある。

```json
"editor.gotoLocation.multipleImplementations": "gotoAndPeek"
```

`gotoAndPeek` は「**1件目へ移動したうえで Peek も開く**」。結果、

- 1件目でよければ **`⎋`（Escape）で Peek を閉じるだけ**。もう目的のファイルにいる
- 2件目を見たければ Peek の右側一覧から選ぶ

のどちらも 1アクションで済む。呼び出し元へは `⌘←`（戻る）で帰れる。

| したいこと | キー |
|---|---|
| Peek を閉じる | `⎋` / `⇧⎋`（✕ を押す必要はない） |
| 一覧へフォーカスを移す | `⇧Tab`（この環境は最初コード側にフォーカスする設定） |
| 一覧で候補を選んで飛ぶ | `↑` `↓` で選び **`Enter`**（ダブルクリック相当。シングルクリックは覗くだけ） |
| 次 / 前の候補へ | `F4` / `⇧F4` |

Peek 自体を出したくない場合は、値を `"goto"` にすると
即座に1件目へ飛び、残りは `F4` / `⇧F4` でたどる形になる。
`"peek"` が VS Code の既定（＝ダブルクリックが必要な元の挙動）。

同じキーが `multipleDefinitions` / `multipleTypeDefinitions` /
`multipleDeclarations` にもあり、この環境では 4つとも `gotoAndPeek` にしてある。

### 「定義へ移動」と「実装へ移動」の違い

| | 押した結果 |
|---|---|
| 定義へ移動（`⌘`+クリック / `⌘B`） | `base.py` の**抽象メソッド自身**に飛ぶ（中身が無いので徒労） |
| 実装へ移動（`⌘⇧B` / `⌥⌘B`） | **実際に動くコード**の一覧が出る |

抽象を挟んだコードでは「実装へ移動」を使う。これを知らないと
「定義に飛んだのに `...` しか書いていない」で止まってしまう。

IntelliJ で `⌘B` と `⌥⌘B` を使い分けるのとまったく同じ関係になっている。
この環境では、より押しやすい `⌘⇧B` でも実装へ飛べるようにしてある。

### つまずきどころ ①「`⌘B` を押したら参照の一覧が出た」

`base.py:50` の `class MailDraft:` の上で `⌘B` を押すと、
定義へ飛ぶ代わりに **`参照 (20)`** という一覧が開く。故障ではない。

**理由: すでに定義の行にカーソルがあるから。**
VS Code は「定義へ移動した結果が今いる場所と同じ」場合、
`editor.gotoLocation.alternativeDefinitionCommand`（既定値 `goToReferences`）に
自動でフォールバックする。飛ぶ先が無いので、代わりに使用箇所を出してくれる。

これは **IntelliJ の `⌘B`（Go to Declaration or Usages）とまったく同じ挙動**で、
宣言の上で押すと使用箇所が出るのも同じ。IntelliJ 寄せとしてはむしろ正しい。

- **使用箇所を見たい** → 宣言の上で `⌘B`（または `⌥F7`）
- **定義へ飛びたい** → **使っている側**の `MailDraft` の上で `⌘B`
  （例: `com_outlook.py:149` の `def create_draft(self, draft: MailDraft) -> MailDraft:`）

この折り返しが邪魔なら、`settings.json` で切れる。

```json
"editor.gotoLocation.alternativeDefinitionCommand": ""
```

### つまずきどころ ②「`⌘⇧B` を押しても何も出ない」

**実装へ移動が意味を持つのは、抽象クラスとその抽象メソッドだけ。**
このリポジトリで `ABC` を継承しているのは 2 つしかない。

```
src/outlook_assistant/adapters/base.py:74   class CalendarPort(ABC)
src/outlook_assistant/adapters/base.py:110  class MailPort(ABC)
```

`MailDraft` や `Person` は `@dataclass` で、**継承しているクラスが 1 つも無い**。
実装が存在しないので `⌘⇧B` は空振りする。

| 対象 | `⌘B` 宣言へ | `⌘⇧B` 実装へ |
|---|---|---|
| `CalendarPort` / `MailPort` とその抽象メソッド | 抽象側（中身なし） | **実装クラスが並ぶ** |
| `MailDraft` / `Person` / `Appointment`（dataclass） | 定義へ飛ぶ | 何も出ない |
| `free_gaps` などの関数 | 定義へ飛ぶ | 何も出ない |

**試すなら `base.py:78` の `create_tentative` で。**
`⌘⇧B` を押せば `ComOutlookCalendar` と `FakeCalendar` の 2 件が出る。

### つまずきどころ ③「`⌘⇧B` が反応しない」

まず**キー割り当てが効いているかどうか**を切り分ける。

`keybindings.json` の `when` は `editorTextFocus` だけにしてある。
`editorHasImplementationProvider` を条件に入れると、
言語サーバの起動状況によっては偽になり、
**既定の「ビルドタスクの実行」に素通りしてしまう**（＝無反応に見える）ためである。

条件を緩めてあるので、Python のファイル内で押せば必ず何かが起きる。

| 押した結果 | 意味 |
|---|---|
| 実装の一覧／実装へジャンプ | 成功 |
| **「'実装' は見つかりません」** と表示 | **割り当ては効いている**。その記号に実装が無いだけ |
| 何も起きない／ビルドタスクが走る | 割り当てが効いていない（下記を確認） |

割り当てが効いていない（＝無反応の）場合は、上から順に試す。

**① ウィンドウを再読み込みする ── まずこれ**

```
⇧⌘P → Developer: Reload Window
```

`keybindings.json` を **VS Code の外から**書き換えた場合、
ファイル監視が働かず新しい割り当てが読み込まれていないことがある。
「前に追加したキーは効くのに、後から足したキーだけ無反応」なら、ほぼこれ。

**② 割り当てを目で確認する**

```
⇧⌘P → 基本設定: キーボード ショートカットを開く（⌘K ⌘S）
```

`goToImplementation` で検索し、`⇧⌘B` が割り当てられているか、
競合の警告（同じキーに複数のコマンド）が出ていないかを見る。

**③ 押したキーが何に化けているかを記録する ── 決定打**

```
⇧⌘P → Developer: Toggle Keyboard Shortcuts Troubleshooting
```

有効にしてから `⇧⌘B` を押すと、出力パネルに
「どのキーとして認識され、どのコマンドに解決されたか」がそのまま出る。
`workbench.action.tasks.build` に解決されていれば割り当てが届いていない、
`editor.action.goToImplementation` に解決されていれば届いている、と切り分けられる。

> **キー表記の順序について**
> `keybindings.json` は修飾キーを順不同で解釈する（`cmd+shift+b` でも `shift+cmd+b` でも
> 同じに読まれる）が、VS Code 自身が書き出すのは `shift+cmd+b` の順。
> 余計な疑いを持たないよう、この順に揃えてある。

### 実装が出ないときの代替手段

Pylance の「実装へ移動」は Python の抽象メソッドに対して
期待どおり働かないことがある。その場合は次の 2 つで代用できる。
どちらも Pylance が確実に提供している機能。

**① 型階層（Show Type Hierarchy）** — クラス単位で見るならこれが確実。

`CalendarPort` の上で右クリック → **`型階層の表示`**。
`ComOutlookCalendar` と `FakeCalendar` がサブクラスとしてツリーに並ぶ。

**② 参照をすべて検索（`⌥F7`）** — メソッド単位ならこれ。

`create_tentative` の上で `⌥F7` を押すと、
抽象側の定義と、それを上書きしている実装側が一覧に並ぶ。
実装へ移動より雑だが、**Python では結果的にこちらの方が速いことが多い**。

### クラスの継承関係を見る

`CalendarPort` の上で右クリック → **`型階層の表示`（Show Type Hierarchy）**。
サブクラスとスーパークラスをツリーで辿れる。既定のキー割り当ては無いので、
右クリックか `⇧⌘P` → `Show Type Hierarchy` で呼ぶ。

---

## 3. 呼び出し元を探す

### 参照をすべて検索（`⌥F7` / 既定は `⇧F12`）

`scheduling.py:35` の `free_gaps` の上で `⌥F7`（IntelliJ の Find Usages と同じキー）。9 箇所出る。

```
src/outlook_assistant/scheduling.py:35          定義
src/outlook_assistant/calendar_hold.py:21       import
src/outlook_assistant/calendar_hold.py:122      呼び出し
src/outlook_assistant/adapters/com_outlook.py:17    import
src/outlook_assistant/adapters/com_outlook.py:120   呼び出し
tests/test_scheduling.py:9, 39, 44, 49          テスト
```

import 文も混ざるのが難点だが、**一覧の広さで影響範囲が掴める**。
「この関数を直したら何が壊れるか」を見るのに使う。

### 呼び出し階層（`⌃⌥H` / 既定は `⇧⌥H`）

「呼び出し元の、さらに呼び出し元」まで辿りたいときはこちら。
`free_gaps` の上で `⌃⌥H`（IntelliJ の Call Hierarchy と同じキー）を押し、パネル上部で
**`呼び出し元を表示`（Show Incoming Calls）** を選ぶ。

```
free_gaps
├── find_common_slots        (calendar_hold.py:122)
│   └── _cmd_slots           (cli.py:93)
│       └── args.func(args)  ← ここで追跡が切れる（後述）
└── ComOutlookCalendar.find_free_slots  (com_outlook.py:120)
```

逆向き（**`呼び出し先を表示`／Show Outgoing Calls**）に切り替えると、
「この関数は何を呼んでいるか」をツリーで展開できる。
`_cmd_slots` から始めれば、CLI から純粋ロジックまで降りていく道筋がそのまま出る。

**使い分け**

| 知りたいこと | 使う機能 |
|---|---|
| どこで使われているか（1階層） | `⌥F7` 参照をすべて検索 |
| どこから呼ばれてくるか（多階層） | `⌃⌥H` 呼び出し階層 |
| 何を呼んでいるか | `⌃⌥H` → Outgoing Calls |

---

## 4. Python では追跡が切れることがある

ここが Python 特有の落とし穴。

`cli.py:198` のこの行で `func` に `⌘`+クリックしても、どこへも飛べない。

```python
return args.func(args)
```

理由は第11章のとおりで、`func` は `set_defaults(func=_cmd_slots)` によって
**実行時に**動的に付けられた属性だから。静的解析では追えない。

### 追えないときの手段

**① 素朴に全文検索する（`⇧⌘F` / `Ctrl+Shift+F`）**

```
func=
```

で検索すれば `set_defaults(func=_cmd_hold)` 等が並び、対応表が一望できる。
**動的な結びつきは、意味ではなく文字列で探す。**

**② デバッガで実際の値を見る**（次章）

`args.func` にブレークポイントを置いて止め、変数パネルで中身を見れば
`<function _cmd_slots ...>` と書いてある。**動かして確かめるのが一番速い。**

追跡が切れやすい書き方は他にもある。覚えておくと諦めが早くなる。

| 書き方 | このリポジトリでの例 |
|---|---|
| `set_defaults` で属性を後付け | `cli.py:160` ほか |
| `getattr(obj, "名前")` | `cli.py:81`, `com_outlook.py:177` |
| COM オブジェクト（`win32com`） | `com_outlook.py` 全体。型情報が無いので補完も効かない |
| 関数内 import | `cli.py:36` — 先頭に無いので import 一覧から漏れる |

---

## 5. 読むためのデバッガ

**Mac では `slots` コマンドを完走できない**（`win32com` が無い）。
代わりに**テストをデバッグ実行する**のが、このリポジトリでの主力の読み方になる。

`.vscode/launch.json` に構成を用意してある。

### 手順

1. `src/outlook_assistant/scheduling.py:46` あたり、`free_gaps` のループ内に
   ブレークポイントを置く（行番号の左をクリック → 赤丸）
2. 左サイドバーの**フラスコのアイコン（テスト）**を開く
3. `FreeGapsTest` → `test_必要な長さに満たない隙間は返さない` の
   **再生ボタンを右クリック → デバッグ**

止まったら、

- **変数パネル**で `busy` `cursor` `need` の中身を見る
- **ステップオーバー `F10`** で 1 行ずつ進め、`cursor` が動くのを追う
- **デバッグコンソール**に式を打つと、その場の変数を使って評価できる

```
> merge_spans(busy)
> busy_start - cursor >= need
```

**第3章のループを目で追うより、止めて値を見る方が圧倒的に速い。**
「読んで分からなかったら止める」を基本にするとよい。

### 実行だけしたいとき

`⇧⌘D`（実行とデバッグ）→ 上部のドロップダウンから選ぶ。

| 構成名 | 用途 |
|---|---|
| テスト: 全部 | 38 件をまとめて |
| テスト: 演習 | `exercises/` の課題 |
| CLI: --help | argparse の動きを見る（Mac でも完走する） |
| CLI: slots | 社用PC 用。Mac では `win32com` で止まる |

`justMyCode: false` にしてあるので、標準ライブラリの中まで踏み込める。
`argparse` が実際にどう引数を解釈しているかを追いたいときに効く。

---

## 6. 移動と検索の小技

### ファイル内のシンボル一覧（`⌘⇧O` / `Ctrl+Shift+O`）

IntelliJ の File Structure に相当する。この環境では `⌘F12` でも開けるようにしてある。

**一番使う。** ファイルを開いて `⌘⇧O` を押すと関数・クラスの一覧が出る。
そのまま名前を打ち込めば絞り込める。

`:` を続けて打つと**種類ごとにグループ化**される。
`cli.py` でやると `_cmd_hold` `_cmd_invite` `_cmd_slots` `_cmd_style` が並び、
サブコマンドの全体像が一目で分かる。

### プロジェクト全体からシンボルを探す（`⌘T` / `Ctrl+T`）

ファイル名を知らなくてもクラス名・関数名で飛べる。
`CalendarPort` と打てば `base.py` へ、`FakeCalendar` と打てばテストへ。

### ファイルを開く（`⌘P` / `Ctrl+P`）

`sched` くらい打てば `scheduling.py` が出る。
`⌘P` の中で `@関数名` と続けると、ファイル内のシンボルまで一気に指定できる。

```
scheduling@free_gaps
```

### 全文検索の絞り込み（`⇧⌘F` / `Ctrl+Shift+F`）

検索欄の下にある **`含めるファイル`** が効く。

| 入れる値 | 意味 |
|---|---|
| `src/**` | 本体だけ（テストと演習を除く） |
| `!tests/**` | テストを除く |
| `*.py` | Python ファイルだけ |

`.*` アイコンで正規表現も使える。
`def _cmd_\w+` で CLI のハンドラだけを列挙する、といった探し方ができる。

### そのほか

| 操作 | Mac | Windows | 用途 |
|---|---|---|---|
| コマンドパレット | `⇧⌘P` | `Ctrl+Shift+P` | 迷ったらここ。機能名を日本語で打てる |
| 名前の変更 | `⇧F6`（既定 `F2`） | `F2` | 参照を全部まとめて改名（grep 置換より安全） |
| 次のエラーへ | `F8` | `F8` | 型エラーを順に潰す |
| 折りたたむ／展開 | `⌘K ⌘0` / `⌘K ⌘J` | `Ctrl+K Ctrl+0` | 全体構造だけ眺めたいとき |
| 選択範囲を広げる | `⌃⇧⌘→` | `Shift+Alt+→` | 式 → 行 → ブロックと段階的に選択 |
| 分割表示 | `⌘\` | `Ctrl+\` | 抽象と実装を左右に並べて読む |

---

## 7. 表示まわりの設定

`.vscode/settings.json` に入れてある。読みやすさに直結する。

**スティッキースクロール** — 長い関数を読んでいるとき、
今どのクラス・どの関数の中にいるかが画面上部に固定表示される。

```json
"editor.stickyScroll.enabled": true
```

**インレイヒント** — 型注釈を省略した変数や戻り値に、
推論された型を薄く重ねて表示する。

```json
"python.analysis.inlayHints.functionReturnTypes": true,
"python.analysis.inlayHints.variableTypes": true
```

**型チェックを厳しめに** — Python は実行時に型を見ないので、
編集中に指摘させると気づける（第9章）。

```json
"python.analysis.typeCheckingMode": "standard"
```

**Peek ウィンドウの境界を見えるようにする** — `⌘⇧B`（実装へ移動）で複数の実装が
見つかると、エディタの中に**覗き窓（Peek）**が開く。

```
┌─ base.py（本体のエディタ）──────────────────────────┐
│  93  def find_free_slots(                          │
├─ com_outlook.py  …/adapters - 実装 (2) ────────────┤ ← ここが Peek の始まり
│ 100    def find_free_slots(     │ com_outlook.py 1 │
│ 101      self, start: datetime, │ test_calendar…  1│
└────────────────────────────────┴─────────────────┘
```

**既定では Peek の中も外も背景色が同じ**なので、この境界線が事実上見えない。
「今どっちのファイルを見ているのか」が分からなくなる原因はこれ。

`.vscode/settings.json` で、**Peek だけを白基調に反転**させてある。
本体エディタ（ダーク）の中に白い窓が開くので、境界を見落としようがない。

```json
"workbench.colorCustomizations": {
  "peekView.border": "#c8c4b8",
  "peekViewTitle.background": "#e8e6df",
  "peekViewTitleLabel.foreground": "#1f1f1f",
  "peekViewResult.background": "#ffffff",
  "peekViewResult.fileForeground": "#1f1f1f",
  "peekViewResult.selectionBackground": "#cfe3f7",
  "peekViewEditor.background": "#fbfaf7",
  "peekViewEditorGutter.background": "#f0eee8"
}
```

`peekView*` が Peek 専用の色キーで、`peekViewEditor.*` がコード面、
`peekViewResult.*` が右側の一覧、`peekViewTitle.*` が上のタイトルバーに対応する。

### 白基調にするときの制約 ── コード面の文字色は変えられない

**VS Code には Peek の中だけ構文色を差し替える手段が無い。**
`peekViewEditor.background`（背景）は指定できるが、
`peekViewEditor.foreground` に相当するキーは存在せず、
コードの文字色は**テーマのトークン色がそのまま使われる**。

つまり白地にしても、文字はダークテーマ用の淡い色のまま出る。
Dark Modern の場合、白地に対するコントラスト比はこうなる。

| 対象 | 色 | 白地（`#fbfaf7`）でのコントラスト |
|---|---|---|
| 既定の文字 | `#CCCCCC` | 1.5 : 1 |
| 関数名 | `#DCDCAA` | 1.4 : 1 |
| 変数名 | `#9CDCFE` | 1.4 : 1 |
| 文字列 | `#CE9178` | 2.5 : 1 |
| キーワード | `#569CD6` | 2.8 : 1 |

読める最低ラインが 3:1 なので、**すべて下回る**。
実際に開いてみて文字が飛んで見えるなら、次のどちらかを選ぶ。

**① コード面だけダークに戻す**（枠と一覧の白は残る）

```json
"peekViewEditor.background": "#22201b",
"peekViewEditorGutter.background": "#22201b",
"peekViewEditorStickyScroll.background": "#22201b"
```

白い帯がタイトルバーと右の一覧に出るので、境界はこれでも十分に分かる。
**構文色が一切壊れないのが利点**で、迷ったらこれでよい。

**② VS Code 全体をライトテーマにして、Peek を濃色にする**

明暗を丸ごと反転させる案。`⇧⌘P` → `基本設定: 配色テーマ` で
`Light Modern` などを選び、`peekView*` を暗い値に置き換える。
構文色が白地用に最適化されたものになるので破綻しないが、
普段の編集画面ごと明るくなる。

あわせて、開いた直後のフォーカスをコード側に置くようにしてある。

```json
"editor.peekWidgetDefaultFocus": "editor"
```

右側の一覧へ移りたいときは `⇧Tab`、Peek を閉じるのは `Esc`。
枠の上端をドラッグすれば覗き窓自体を広げられる。

**ダブルクリックしないと飛べない問題を消す** — 既定の Peek は
「一覧を見せるだけで、カーソルは元の場所に留まる」挙動なので、
実際に飛ぶには一覧をダブルクリックする必要がある。
この環境では 1件目へ先に移動する設定にしてある（第2章に操作表）。

```json
"editor.gotoLocation.multipleImplementations": "gotoAndPeek",
"editor.gotoLocation.multipleDefinitions": "gotoAndPeek",
"editor.gotoLocation.multipleTypeDefinitions": "gotoAndPeek",
"editor.gotoLocation.multipleDeclarations": "gotoAndPeek"
```

取りうる値は 3 つ。

| 値 | どうなるか |
|---|---|
| `"peek"` | VS Code の既定。Peek だけ開いて留まる（＝ダブルクリックが要る） |
| `"gotoAndPeek"` | **この環境の設定。** 1件目へ移動しつつ Peek も開く。1件目でよければ `⎋` で閉じるだけ |
| `"goto"` | Peek を出さず 1件目へ飛ぶ。次の候補へは `F4` / `⇧F4`。IntelliJ の `⌥⌘B` に近い |

**そもそも Peek を使わない選択もある**

色を付けても「エディタの中に別のファイルが挟まる」構造自体が読みにくい、
という場合は、出し先を変えてしまうのが早い。

| やり方 | 設定 | どうなるか |
|---|---|---|
| **直接ジャンプする** | 上の表の `"goto"` | 覗き窓を出さず 1 件目へ飛ぶ |
| **サイドパネルに出す** | `"references.preferredLocation": "view"` | エディタを一切侵食せず、左サイドバーの「参照」ビューに一覧が並ぶ。行を選ぶと本体エディタで開く |
| **左右に並べる** | 設定不要（`⌘\`） | 抽象と実装を別ペインで開いて見比べる。第2章の「本番用とテスト用の 2 実装」を確認するときはこれが一番分かりやすい |

なお `⌥F7`（参照をすべて検索）は `references-view.findReferences` に割り当ててあるので、
はじめからサイドパネルに出る。Peek にはならない。

**ホバー** — 名前の上にマウスを置くと、型と docstring が出る。
このリポジトリは docstring に設計意図を書いてあるので、
`busy_spans` にホバーするだけで
「相手が公開していない場合は空リストが返り、終日空きと区別できない」まで読める。
**`base.py` を開きに行かずに仕様が読める**のが効く。

---

## 8. 読む順番の型

初見のコードを追うときの手順として。

1. `⌘P` でファイルを開き、`⌘⇧O` で**全体の見出しを眺める**（細部は読まない）
2. 入口を決める。CLI なら `cli.py` の `main`、テストからなら失敗しているテスト
3. `⌘`+クリックで降りていく。抽象に当たったら `⌘⇧B` で実装へ
4. 分からなくなったら `⌘←` で戻る
5. それでも分からなければ**ブレークポイントを置いて止める**
6. 直したくなったら、`⌥F7` で影響範囲を確認してから触る

このリポジトリなら、こう辿るのが分かりやすい。

```
cli.py:_cmd_slots  →  calendar_hold.py:find_common_slots  →  scheduling.py:free_gaps
   （文字列を受け取る）      （抽象に依存する業務ロジック）      （純粋関数）
```

外から内へ、型がだんだん厳密になっていく。第12章で読んだ設計が、
ジャンプの体験としてそのまま出てくる。

---

## 9. IntelliJ 寄せの割り当て

キー割り当てを IntelliJ に寄せてある。設定場所は 2 つ。

| ファイル | 範囲 |
|---|---|
| `~/Library/Application Support/Code/User/keybindings.json` | **VS Code 全体**（他プロジェクトにも効く） |
| `.vscode/settings.json` | このリポジトリだけ |

### 割り当て一覧

| 操作 | IntelliJ (Mac) | 設定後の VS Code | VS Code 既定 |
|---|---|---|---|
| 宣言へ移動 | `⌘`+クリック / `⌘B` | **`⌘`+クリック / `⌘B`** | `⌘`+クリック / `F12` |
| 実装へ移動 | `⌥⌘B` | **`⌘⇧B` / `⌥⌘B`** | `⌘F12` |
| 戻る | `⌘[` | **`⌘←` / `⌘[`** | `⌃-` |
| 進む | `⌘]` | **`⌘→` / `⌘]`** | `⌃⇧-` |
| 使用箇所検索 | `⌥F7` | **`⌥F7`** | `⇧F12` |
| 呼び出し階層 | `⌃⌥H` | **`⌃⌥H`** | `⇧⌥H` |
| ファイル構造 | `⌘F12` | **`⌘F12`** | （`⌘⇧O`） |
| 名前の変更 | `⇧F6` | **`⇧F6`** | `F2` |

既定のキーも消していないので、`F12` や `⇧F12` はそのまま併用できる。

### `⌘`+クリックは設定不要だった

**VS Code の既定でもう「定義へ移動」になっている。** IntelliJ と同じ挙動。

これを保証するために、`.vscode/settings.json` に 1 行だけ入れてある。

```json
"editor.multiCursorModifier": "alt"
```

この設定が `ctrlCmd` になっていると `⌘`+クリックがマルチカーソル追加に化け、
ジャンプできなくなる。既定値と同じ内容だが、明示しておくと事故らない。
**マルチカーソルは `⌥`+クリック**で使う。

### `⌘⇧`+クリックは割り当てられない

**VS Code はマウス操作へのキー割り当てに対応していない。**
`keybindings.json` に書けるのはキーボードのキーだけで、
`cmd+shift+click` のような指定は受け付けない。

そのため「実装へ移動」はキーボードに割り当てた。
**`⌘⇧B`**（`⌘⇧`+クリックに一番近い形）と、IntelliJ 本来の **`⌥⌘B`** の両方が使える。
クリックで飛べるのは「宣言へ移動」だけ、と割り切ることになる。

読む流れとしてはこうなる。

1. `⌘`+クリックで宣言へ飛ぶ
2. 抽象メソッドだったら（`base.py` に着いたら）そこで `⌘⇧B`
3. `⌘←` で戻る

### 副作用として失うもの

上書きした 3 つのキーには、もともと別の役割がある。

| キー | 失う機能 | 代替 |
|---|---|---|
| `⌘←` | 行頭へ移動 | **`fn+←`**（Home）で同じことができる |
| `⌘→` | 行末へ移動 | **`fn+→`**（End）で同じことができる |
| `⌘B` | サイドバーの表示切替 | `⌘⇧E`（エクスプローラ）。エディタ外では `⌘B` のまま効く |
| `⌘[` / `⌘]` | インデントの増減 | `Tab` / `⇧Tab` |
| `⌘⇧B` | ビルドタスクの実行 | `⇧⌘P` → `Tasks: Run Build Task`（このプロジェクトでは未使用） |

いずれも `keybindings.json` の該当ブロックを消せば元に戻る。
特に `⌘←` / `⌘→`（行頭・行末）は編集中によく使うので、
**戻る・進むは `⌘[` / `⌘]` だけにする**という選択もある。
その場合は `cmd+left` と `cmd+right` の 2 件を削除する。

### まとめて寄せたい場合

個別に割り当てるのではなく、キーマップ全体を IntelliJ にしたいなら拡張機能がある。

```
⇧⌘P → Extensions: Install Extensions → "IntelliJ IDEA Keybindings"
（拡張ID: k--kato.intellij-idea-keybindings）
```

ほぼすべてのキーが IntelliJ 準拠になる代わりに、
**VS Code 側の既定を広範囲に置き換える**ので、
VS Code の流儀も併用したい場合は今の個別設定の方が扱いやすい。
