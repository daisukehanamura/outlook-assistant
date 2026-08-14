# Python 学習記録

このリポジトリの実コードを教材に、Pythonの文法・設計を学んだ記録。
疑問に思ったことと、その答えを追記していく。コード例はすべて本リポジトリの実物から引用する。

---

## 1. アンダースコアで囲まれた名前（dunder）

`__init__` のように **前後を2本ずつのアンダースコアで挟んだ名前** を **dunder**（double underscore）と呼ぶ。
文法ではなく **命名の予約ルール**。「この形の名前は処理系が特別扱いする」と決めることで、
利用者が普通に名前を付ける限り衝突しないようにしている。

アンダースコアの使い分けは4段階ある。

| 書き方 | 意味 | 本リポジトリの実例 |
|---|---|---|
| `_QUOTE_MARKERS` | モジュール内部用の目印。強制力なし（`import *` で読まれないだけ） | `style_profile.py:21` |
| `__init__` | 処理系が特別扱いする名前（dunder） | `tests/test_calendar_hold.py:23` |
| `__x`（クラス内、後ろに `_` なし） | 名前マングリング。継承時の衝突回避。実務では稀 | 該当なし |
| `"________________"` | **ただの文字列データ。特別な意味はゼロ** | `style_profile.py:24` |

最後の行が良い対比になる。`style_profile.py:24` のアンダースコアの羅列は、
Outlookが返信メールに挿入する区切り線そのもので、Pythonの機能とは無関係。
**「`_` があるから特別」ではなく「dunderという特定の形かつ処理系が知っている名前だから特別」**。

### `__init__.py` — ディレクトリをパッケージに昇格させる

Pythonが「このディレクトリをモジュールの入れ物として扱ってよいか」を判断する目印。

```
src/outlook_assistant/
├── __init__.py          ← これがあるので import 可能なパッケージ
├── cli.py               ← outlook_assistant.cli として import される
└── adapters/
    ├── __init__.py      ← これがあるので adapters もパッケージ
    └── base.py          ← outlook_assistant.adapters.base
```

本リポジトリの `__init__.py` は2つとも **中身が空**。これは正常な状態で、
「このディレクトリはパッケージである」以外に言いたいことが無いなら空でよい。

中身を書いた場合は **パッケージが最初に import された時に1回だけ実行** される。
よくある用途は再エクスポート:

```python
# __init__.py にこう書けば
from .scheduling import find_free_slots
# 利用側が短く書ける
from outlook_assistant import find_free_slots
```

> **紛らわしい点**: `def __init__(self, ...)` メソッド（`tests/test_calendar_hold.py:23`）は
> ファイルの `__init__.py` とは **別物**。名前が同じだけ。
> あちらはインスタンス生成直後に呼ばれる初期化メソッド（他言語のコンストラクタ相当）。

### `__main__.py` — `python -m パッケージ名` の入口

`-m` は「パッケージを指定して実行する」オプション。Pythonはパッケージ内の
`__main__.py` を探して実行する。つまり **パッケージの main 関数に相当するファイル**。

```python
# src/outlook_assistant/__main__.py の全内容
from .cli import main      # 相対import：「今いるパッケージの中の cli」

raise SystemExit(main())   # 戻り値をシェルの終了コードにしてプロセスを終える
```

- 先頭のドット（`.cli`）は **相対 import**。ドット無しだとシステム全体から探しに行き、
  意図しないものを掴む危険がある。
- `raise SystemExit(x)` は終了コードを `x` にする書き方。慣習として `0` が成功。
  `sys.exit(x)` でも同じ。

### `if __name__ == "__main__":`

`__name__` はモジュール読み込み時にPythonが自動で用意する変数で、状況で値が変わる。

| 実行のされ方 | `cli.py` の `__name__` |
|---|---|
| 他から `import` された | `"outlook_assistant.cli"` |
| `python cli.py` と直接実行された | `"__main__"` |

したがって `if __name__ == "__main__":` は **「直接実行されたときだけ動かす」** の意味。
ライブラリとしても単体実行としても使えるようにする定番イディオム。
本リポジトリでは `cli.py:204` と各テストファイル末尾に出てくる。

### `from __future__ import annotations`

本リポジトリの **全 `.py` ファイルの先頭** にある。dunderだが毛色が違い、
「将来の標準になる挙動を今から先取りする」という宣言。
型ヒントの解釈を実行時ではなく文字列として遅延させる。
御利益は「まだ定義されていないクラス名を型ヒントに書ける」「起動が少し速い」。
当面は先頭に置くおまじないとして扱ってよい。

---

## 2. 関数の呼び出しと受け渡し

### 実行するだけなら `関数名(引数)`

宣言も型登録も不要。`f(a, b)` と書けばその場で実行される。

### 「渡す」と「実行する」は別物

| 書き方 | 意味 |
|---|---|
| `free_gaps` | **関数そのもの**（オブジェクト）。実行されない。変数に入れたり引数として渡せる |
| `free_gaps(...)` | **実行**される。カッコが「今ここで動かせ」の合図 |

他言語の **関数ポインタ / デリゲート / コールバック** と同じ概念。
Pythonでは関数が第一級オブジェクトなので、数値や文字列と同様に代入・受け渡しができる。

### 実例：`cli.py` のディスパッチテーブル

本リポジトリに、貼り付けと実行が両方書かれている。

```python
# cli.py:160  カッコ無し ＝ 「_cmd_hold という関数を func という名前で保管しておけ」
p_hold.set_defaults(func=_cmd_hold)

# cli.py:198  カッコ有り ＝ 「保管した関数を、今 args を渡して実行しろ」
return args.func(args)
```

`build_parser()` では「`hold` が来たら `_cmd_hold`」と関数を貼り付けておくだけにして、
実行は `main()` の一箇所に集約している。
もし `cli.py:160` を `func=_cmd_hold(...)` と書くと
**パーサ組み立て中にOutlookを操作しに行ってしまい破綻する**。カッコ1組で挙動が根本から変わる。

### 引数の渡し方は4通り（`free_gaps()` で実行確認済み）

```python
free_gaps(busy, day_start, day_end, 60)                        # ① 位置引数：定義順に並べる
free_gaps(duration_minutes=60, busy=busy, start=s, end=e)      # ② キーワード引数：名前指定、順不同
f = free_gaps;  f(busy, day_start, day_end, 60)                # ③ 変数に入れた関数を呼ぶ
free_gaps(**params)                                            # ④ 辞書を展開して渡す
```

4通りとも同じ結果を返す。カッコを外すと `<function free_gaps at 0x...>` と表示され、
**実行されずに関数オブジェクトそのものが出てくる**。

### 引数が3つを超えたらキーワード引数

本リポジトリも `cli.py:49-57` でそうしている。

```python
appointment = hold(
    _calendar(),              # 第1引数だけ位置引数
    subject=args.subject,     # 以降は全部キーワード
    duration_minutes=args.duration,
    ...
)
```

`hold(cal, "打ち合わせ", start, 60, [], "", "")` でも動くが、
最後の3つが何なのか読んで分からない。**名前を書くコストより半年後に読む時の利益が上回る**。

### デフォルト引数

```python
# cli.py:195
def main(argv: list[str] | None = None) -> int:
```

`= None` は「渡さなければ `None` を使う」の宣言。呼び出し側は `main()` と引数ゼロで呼べる
（`__main__.py` が実際そうしている）。`None` のとき argparse は自動的に `sys.argv` を読み、
テストからは `main(["hold", "--subject", "テスト"])` と明示的なリストを渡して検証できる。
デフォルト引数ひとつで **本番とテストの両立** を実現している。

---

## 動作確認の手引き（Mac開発機）

Outlook連携（COM）はWindows専用だが、`scheduling.py` は
「Outlookに依存しない純粋なロジック」として切り出されているため **Macでも実行できる**。
文法を試したいときはここを使うのが手軽。

```bash
PYTHONPATH=src python3 -c "
from datetime import datetime
from outlook_assistant.scheduling import free_gaps
busy = [(datetime(2026,8,19,10,0), datetime(2026,8,19,11,0))]
print(free_gaps(busy, datetime(2026,8,19,9,0), datetime(2026,8,19,15,0), 60))
"
```

`PYTHONPATH=src` は「`src/` の下をパッケージの探索先に加える」指定。
これが無いと `outlook_assistant` が見つからない。
