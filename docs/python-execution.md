# 実行とコンパイルの仕組み

`python -m outlook_assistant slots ...` と打ったとき、Python が何をしているか。
コマンドがどう解決され、どこでコンパイルされ、どう終了コードが返るかまでを追う。

教材は [outlook-assistant](../README.md) の実コード。
文中の「第N章」は [python-learning.md](python-learning.md) の章を指す。

---

README に載っているこのコマンドを、左から順に分解する。

```powershell
python -m outlook_assistant slots --from "2026-08-18 09:00" --to "2026-08-22 18:00" `
    --duration 60 --attendee "山田太郎" --attendee "佐藤花子"
```

| 部分 | 誰が解釈するか |
|---|---|
| `python` | シェル。PATH から実行ファイルを探す |
| `-m outlook_assistant` | **Python 本体**。モジュールを探して実行する |
| `slots --from ... --attendee ...` | **アプリ側**。`argparse` が読む（第11章） |
| 行末の `` ` `` | PowerShell の行継続。Python とは無関係 |

行末の `` ` `` は PowerShell の記法で、Mac/Linux のシェルでは `\` を使う。
Python のコードではないので、対話モードに貼り付けても動かない。

### `-m` は何を探すのか

`-m 名前` は「`名前` というモジュール／パッケージを import して実行する」という指示。
探し方は `import` と**まったく同じ**で、`sys.path` を上から順に見る。

`sys.path` の中身は 3 つの層でできている。

```bash
$ PYTHONPATH=src python3 -c "import sys; print(sys.path[0]); print(sys.path[1])"
''                                          ← カレントディレクトリ（-m のとき先頭に入る）
/Users/hanamaru/Git/outlook-assistant/src   ← 環境変数 PYTHONPATH
                                            ← （以下）標準ライブラリと site-packages
```

つまり `python -m outlook_assistant` は、

1. カレントディレクトリに `outlook_assistant/` があるか
2. `PYTHONPATH` の各ディレクトリにあるか
3. インストール済みパッケージ（`site-packages`）にあるか

を順に探す。**見つかった時点で確定**なので、上の層が下の層を隠す。

### 実際に確かめる

このリポジトリはパッケージを `src/` の下に置いている（src レイアウト）。
だからリポジトリ直下でそのまま叩くと**見つからない**。

```bash
$ python3 -m outlook_assistant slots --from "..." --to "..." --duration 60
/usr/local/opt/python@3.13/bin/python3.13: No module named outlook_assistant
```

`src` を `sys.path` に入れると、今度は先へ進む。

```bash
$ PYTHONPATH=src python3 -m outlook_assistant slots --from "..." --to "..." --duration 60
エラー: No module named 'win32com'
```

エラーが変わったことに意味がある。

- 1 回目は **outlook_assistant が見つからない**（入口にも立てていない）
- 2 回目は **見つかって、引数も解釈できて、Outlook に接続しようとして落ちた**

2 回目は `cli.py:36` の遅延 import（第8章）まで到達している。
Mac には `win32com` が無いのでここで止まる ── **想定どおりの止まり方**である。

引数の解釈までなら Mac でも完走する。

```bash
$ PYTHONPATH=src python3 -m outlook_assistant --help
usage: outlook_assistant [-h] {hold,invite,style,slots} ...
```

### ⚠ 社用PC の手順は、このままでは動かない

README のセットアップは

```powershell
pip install -r requirements.txt
```

だけで、`python -m outlook_assistant` を叩くことになっている。
しかし `requirements.txt` が入れるのは **pywin32 と python-dateutil という依存ライブラリだけ**で、
`outlook_assistant` 自身はどこにもインストールされない。
このリポジトリには `pyproject.toml` も `setup.py` も無いためである。

```bash
$ ls pyproject.toml setup.py setup.cfg
ls: pyproject.toml: No such file or directory   （3つとも無い）
```

したがって社用PC でも `No module named outlook_assistant` になる。直し方は 3 つ。

**案1: `pyproject.toml` を置いて editable install する（推奨）**

```toml
[project]
name = "outlook-assistant"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["pywin32>=306; sys_platform == 'win32'", "python-dateutil>=2.9.0"]

[build-system]
requires = ["setuptools>=64"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]
```

```powershell
pip install -e .
```

`-e`（editable）は「コピーせず、この場所を見に行くリンクを作る」インストール。
ソースを編集した結果が即座に反映されるので開発中はこれを使う。
これを一度やれば、**どのディレクトリからでも** `python -m outlook_assistant` が動く。

**案2: 環境変数で通す**

```powershell
$env:PYTHONPATH = "src"
python -m outlook_assistant --help
```

インストール不要だが、シェルを開き直すたびに設定が要る。

**案3: `src/` に入ってから叩く**

```powershell
cd src
python -m outlook_assistant --help
```

カレントディレクトリが `sys.path[0]` に入る性質を使う。手軽だが出力ファイルの相対パス
（`data/style_profile.md`）の基準位置がずれるので、常用には向かない。

> なぜ `src/` に置くのか。パッケージを直下に置くと、
> **インストールし忘れていてもカレントディレクトリ経由で動いてしまう**。
> 「自分の環境では動くのに配布先で動かない」を防ぐため、
> わざと `src/` に隔離して「インストールしないと動かない」状態を作るのが src レイアウトの狙い。
> 今回の「動かない」は、その仕掛けが正しく働いた結果でもある。

### `__init__.py` と `__main__.py`

見つかった後の流れはこう。

```
src/outlook_assistant/
├── __init__.py     ① まずこれが実行される（中身は空でよい）
└── __main__.py     ② -m のときはこれが実行される
```

`__init__.py` の中身を見ると**完全に空**である。
「このディレクトリはパッケージだ」という印であって、何かを書く義務は無い。

`__main__.py` はたった 3 行。

```python
from .cli import main

raise SystemExit(main())
```

`-m パッケージ名` は「そのパッケージの `__main__.py` を `__main__` という名前で実行する」
という規則になっている。だから `python -m outlook_assistant` でこの 3 行が走る。

### `from .cli import main` ── 1行目

同じパッケージの `cli.py` から、`main` という**関数そのもの**を取り込んでいる。
先頭の `.` は「このパッケージの中の」という意味の相対 import（第8章）。

`main` は `cli.py:195` で定義されている関数で、実体はこれだけ。

```python
def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:
        print(f"エラー: {exc}", file=sys.stderr)
        return 1
```

**`__main__.py` に処理を書かず、`cli.py` の関数を呼ぶだけにしている**のがポイント。
こうしておくと `main()` はテストからも呼べる（第11章）。
`__main__.py` に直接書いてしまうと、import した瞬間に実行されてしまい手が出せない。

### `raise SystemExit(main())` ── 3行目

これは 3 つの動作が 1 行に畳まれている。

```python
raise SystemExit(main())
#                ^^^^^^  ① main() を呼ぶ。戻り値は int（終了コード）
#     ^^^^^^^^^^^^^^^^^^  ② その値を持った SystemExit を作る
# ^^^^^^^^^^^^^^^^^^^^^^  ③ 投げる
```

**`SystemExit` は例外である。** ただし「エラー」ではなく、
Python インタプリタが特別扱いする「終了してくれ」という合図として使われる。
どこにも捕まえられずにインタプリタまで届くと、
インタプリタは**トレースバックを出さずに、持っていた値を終了コードにしてプロセスを終える**。

例外であることは、捕まえてみれば分かる。

```python
>>> try:
...     raise SystemExit(3)
... except SystemExit as exc:
...     print(exc.code)
3
```

よく使う `sys.exit(3)` も、中身はこれとまったく同じ。

```python
>>> import sys
>>> try:
...     sys.exit(7)
... except SystemExit as exc:
...     print(exc.code)
7
```

`sys.exit()` は `raise SystemExit()` の別名にすぎない。どちらで書いても同じ。

### なぜ `main()` を呼ぶだけでは駄目か

```python
main()                      # ← これだと戻り値が捨てられる
raise SystemExit(main())    # ← 戻り値が終了コードになる
```

`main()` だけだと、`main` が `1`（失敗）を返しても**プロセスは成功（0）で終わる**。
シェルから成否を判定できなくなる。

実際の終了コードを確かめるとこうなっている（`$?` が直前のコマンドの終了コード）。

```bash
$ PYTHONPATH=src python3 -m outlook_assistant --help > /dev/null; echo $?
0     # 成功

$ PYTHONPATH=src python3 -m outlook_assistant slots --from ... > /dev/null 2>&1; echo $?
1     # main() が返した 1（Outlook に繋げず失敗）

$ PYTHONPATH=src python3 -m outlook_assistant slots --from "おととい" ... > /dev/null 2>&1; echo $?
2     # argparse が使い方の誤りとして終了させた
```

`0` = 成功、`1` = アプリの失敗、`2` = 引数の誤り、という Unix の慣習に沿っている。
おかげでシェルからこう書ける。

```bash
if python -m outlook_assistant slots --from ... ; then
    echo "候補が見つかった"
fi
```

`slots` が候補ゼロなら `1` を返す（`cli.py:121` の `return 0 if slots else 1`）ので、
**AI エージェントやスクリプトが結果を機械的に判定できる。**

### `SystemExit` が `Exception` の仲間ではない理由

`main()` の中には `except Exception:` がある（`cli.py:199`）。
ここで `SystemExit` まで捕まってしまうと、終了の合図が握りつぶされて困る。
そうならないよう、継承関係が分けてある。

```python
>>> [c.__name__ for c in SystemExit.__mro__]
['SystemExit', 'BaseException', 'object']
>>> [c.__name__ for c in Exception.__mro__]
['Exception', 'BaseException', 'object']
>>> issubclass(SystemExit, Exception)
False
```

`SystemExit` は `Exception` を経由せず、直接 `BaseException` を継承している。
だから `except Exception:` には引っかからない。`KeyboardInterrupt`（Ctrl+C）も同じ仲間である。

**これが「`except Exception:` と書き、`except BaseException:` とは書かない」理由。**
前者は「プログラムの異常」だけを捕まえ、後者は「終了しろという指示」まで捕まえてしまう。
第4章で `except Exception:` の是非を扱ったが、そこで `BaseException` が
選択肢に上がらなかったのはこのためである。

### `if __name__ == "__main__":` は要らないのか

`cli.py` の末尾（`cli.py:204-205`）には見張りが付いている。

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

`__main__.py` には付いていない。この差には理由がある。

- `cli.py` は**他のモジュールから import される**。
  見張りが無いと、`from .cli import main` した瞬間に `main()` が走ってしまう
- `__main__.py` は**実行される以外の使い道が無い**。
  `-m` で起動されたときにしか読まれないので、見張っても意味がない

`__name__` は「そのモジュールが今どう呼ばれているか」が入る変数で、
import されたときはモジュール名（`"outlook_assistant.cli"`）、
直接実行されたときは `"__main__"` になる。

### `python cli.py` ではなぜ駄目か

「ファイルを直接指定すればいいのでは」と思うところだが、壊れる。

```bash
$ PYTHONPATH=src python3 src/outlook_assistant/cli.py --help
  File ".../cli.py", line 18, in <module>
    from .adapters.base import Person
ImportError: attempted relative import with no known parent package
```

ファイルを直接指定すると、Python はそれを**パッケージの一部ではなく単独のスクリプト**として扱う。
`__package__` が空になるので、`.adapters`（第8章の相対 import）の `.` が指す先が無い。

**`-m` を使う本当の理由がこれ。** パッケージとして読み込ませることで、
相対 import と `__init__.py` が正しく働く。

### 呼び出しの連鎖

`python -m outlook_assistant slots ...` が最終的に何を呼ぶか。

```
__main__.py         raise SystemExit(main())
  └─ cli.main()           build_parser().parse_args(argv)  ← 文字列を解釈
       └─ args.func(args)  = _cmd_slots   ← set_defaults で結び付けた関数（第11章）
            └─ _calendar()          ← ここで初めて win32com を import（第8章）
            └─ find_common_slots()  ← 業務ロジック（Outlook を知らない）
                 └─ free_gaps() / within_business_hours()  ← 純粋関数（第3章）
```

`--from "2026-08-18 09:00"` という**文字列**が `datetime` になるのは、
`parse_args()` の中で `type=_parse_datetime` が呼ばれる瞬間（`cli.py:180`）。
それより内側の関数は、もう文字列を見ることがない。

`--attendee "山田太郎" --attendee "佐藤花子"` が
`["山田太郎", "佐藤花子"]` というリストになるのは `action="append"` の働き（`cli.py:183-188`）。
それを `cli.py:96` が `[Person(name=name) for name in args.attendee]` で `Person` に変える。

**外側ほど文字列を扱い、内側ほど型のある値を扱う。** この境界が `cli.py` にある。

---

### コンパイルは要るのか

**要らない。ただし「コンパイルしていない」わけではない。**

C や Java のような「ビルドしてから実行」の工程は無い。
`python xxx.py` と打った瞬間に、内部でこれだけのことが起きている。

```
ソースコード (.py)
    ↓ 字句解析・構文解析
抽象構文木 (AST)
    ↓ コンパイル          ← ここでコンパイルしている
バイトコード (.pyc の中身)
    ↓ 実行
Python 仮想マシン (CPython)
```

つまり Python は**インタプリタ言語であると同時にコンパイルされている**。
違いは、コンパイルが**別工程ではなく実行の一部**として自動で走ること。

### 証拠 ── `__pycache__`

一度でも import されたモジュールは、コンパイル結果がディスクに保存される。

```bash
$ ls src/outlook_assistant/__pycache__/
__init__.cpython-313.pyc
__main__.cpython-313.pyc
calendar_hold.cpython-313.pyc
cli.cpython-313.pyc
scheduling.cpython-313.pyc
```

`cpython-313` は「CPython 3.13 用」という印。
**バイトコードは Python のバージョン間で互換性が無い**ので、名前で分けてある。

読み込み元は実行時にも確認できる。

```bash
$ PYTHONPATH=src python3 -c "import outlook_assistant.cli as c; print(c.__cached__)"
.../src/outlook_assistant/__pycache__/cli.cpython-313.pyc
```

このキャッシュは、

- **消しても問題ない。** 次の実行で自動的に作り直される
- **コミットしない。** `.gitignore` に `__pycache__/` がある
- **配布物ではない。** 別のマシンに `.pyc` だけ持っていく用途は基本的に無い
- **`.py` が新しければ無視される。** ソースの更新時刻とサイズを見て自動で再コンパイルする

だから「ソースを直したのに古い挙動のまま」ということは起きない。
**手動でビルドし直す必要はない。**

なお `python3 script.py` のように**直接指定したファイルは `.pyc` を作らない**。
キャッシュされるのは `import`（および `-m`）で読み込まれたモジュールだけ。
1 回しか読まないものをキャッシュしても得が無いためである。

### バイトコードを覗く

`dis` モジュールで、コンパイル結果を人間が読める形で見られる。

```bash
$ PYTHONPATH=src python3 -c "
import dis
from outlook_assistant.scheduling import merge_spans
dis.dis(merge_spans)
"
```

```
 21    LOAD_GLOBAL      1 (sorted + NULL)
       LOAD_CONST       1 (<code object <genexpr> ...>)
       MAKE_FUNCTION
       LOAD_FAST        0 (spans)
       GET_ITER
       CALL             0
       CALL             1
       STORE_FAST       1 (ordered)

 22    LOAD_FAST        1 (ordered)
       TO_BOOL
       POP_JUMP_IF_TRUE 2 (to L1)

 23    BUILD_LIST       0
       RETURN_VALUE
```

左の数字が `scheduling.py` の行番号。第3章で読んだ

```python
ordered = sorted(span for span in spans if span[0] < span[1])   # 21行目
if not ordered:                                                  # 22行目
    return []                                                    # 23行目
```

がそのまま対応している。`MAKE_FUNCTION` があるのは、
ジェネレータ式が**その場で作られる無名の関数**としてコンパイルされているから。
第3章の「リストを作らず 1 個ずつ取り出す」が、機械語のレベルでも確認できる。

普段この出力を読む必要はまったく無いが、
「Python にもコンパイル結果がある」ことは一度見ておくと納得が早い。

### 構文エラーは実行前に出る

コンパイル工程がある証拠がもうひとつある。

```python
print("この行は実行される？")
if True          # ← コロンが無い
    pass
```

```bash
$ python3 broken.py
  File "broken.py", line 2
    if True
           ^
SyntaxError: expected ':'
```

**1 行目の `print` が実行されていない。**
ファイル全体をコンパイルしてから実行を始めるので、
構文エラーは 1 行も動かないうちに検出される。

ただし**型の誤りや存在しない属性は検出されない**（第9章）。
コンパイル時に見るのは文法だけで、意味は実行時まで分からない。
そこを埋めるのがテスト（第10章）と `mypy` の役割になる。

### まとめ

| 疑問 | 答え |
|---|---|
| なぜ `python -m outlook_assistant` で呼べる？ | `sys.path` からパッケージが見つかり、その `__main__.py` が実行されるから |
| このリポジトリではなぜ見つからない？ | パッケージが `src/` の下にあり、インストールもされていないから |
| どうすれば動く？ | `pip install -e .`（要 `pyproject.toml`）／`PYTHONPATH=src`／`cd src` |
| コンパイルは要る？ | 不要。実行時に自動でバイトコード化され `__pycache__` に載る |
| `__pycache__` は消していい？ | よい。自動で作り直される。コミットもしない |
| ビルドし直す必要は？ | 無い。ソースの更新は自動で検出される |

### 試す

```bash
# 1. 引数の解釈だけなら Mac でも完走する
PYTHONPATH=src python3 -m outlook_assistant --help
PYTHONPATH=src python3 -m outlook_assistant slots --help

# 2. わざと止める。エラーメッセージがどこで出るかを見る
PYTHONPATH=src python3 -m outlook_assistant slots --from "おととい" --to "..." --duration 60
#    -> _parse_datetime のエラー。argparse が使い方として整形して出す（第4章）

# 3. キャッシュを消して、作り直されることを確認する
find src -name "__pycache__" -exec rm -rf {} +
PYTHONPATH=src python3 -m outlook_assistant --help >/dev/null && ls src/outlook_assistant/__pycache__

# 4. -m を使わずにファイルを直接指定して、壊れ方を見る
PYTHONPATH=src python3 src/outlook_assistant/cli.py --help
```
