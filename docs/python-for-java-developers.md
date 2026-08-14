# Java との文法対比

Java の経験がある人向けに、Python で「同じことをどう書くか」「そもそも概念が無いもの」を並べる。
例はすべて `outlook-assistant` の実コードから採っている。

関連: [python-learning.md](python-learning.md)（本編） /
[python-execution.md](python-execution.md)（実行とコンパイル）

---

## 早見表

| Java | Python | 備考 |
|---|---|---|
| `private void foo()` | `def _foo(self):` | **強制力なし**。ただの命名慣習 |
| `public` | （既定） | 修飾子そのものが無い |
| `interface` | `class X(ABC)` + `@abstractmethod` | または `Protocol` |
| `implements` / `extends` | `class Sub(Base):` | どちらも同じ書き方 |
| `@Override` | （無し） | 名前が一致すれば上書きされる |
| `final` フィールド | `@dataclass(frozen=True)` | 変数レベルの `final` は無い |
| `static final` 定数 | `MAX_SIZE = 100` | 大文字にする慣習だけ。変更できる |
| `static` メソッド | `@staticmethod` / モジュール直下の関数 | 後者が普通 |
| `this` | `self` | **明示的に第1引数で受け取る** |
| `null` | `None` | |
| `Optional<T>` | `T \| None` | |
| `List<String>` | `list[str]` | |
| `Map<String, String>` | `dict[str, str]` | |
| `enum` | `class X(Enum)` | |
| `record` / Lombok | `@dataclass` | |
| `toString()` | `__repr__()` | dataclass が自動生成 |
| `equals()` / `hashCode()` | `__eq__()` / `__hash__()` | dataclass が自動生成 |
| `==`（参照比較） | `is` | |
| `.equals()`（値比較） | `==` | **逆になるので注意** |
| `throws IOException` | （無し） | 検査例外という概念が無い |
| `try-with-resources` | `with` 文 | |
| `switch` | `match` 文（3.10〜） | `if/elif` でも十分 |
| `getter` / `setter` | 属性を直接公開 / `@property` | |
| メソッドのオーバーロード | 既定値引数 | **多重定義は不可** |
| `package com.example;` | ディレクトリ + `__init__.py` | 宣言文が無い |
| Maven / Gradle | `pip` + `pyproject.toml` | |
| `public static void main` | `__main__.py` | |
| `javac` → `.class` | （自動）→ `__pycache__/*.pyc` | ビルド工程が無い |

---

## 1. アクセス修飾子は存在しない

Java の `private` にあたる**言語機能が無い**。あるのは命名の慣習だけ。

```python
def _parse_datetime(value: str) -> datetime:   # cli.py:25
    ...
def _cmd_slots(args) -> int:                   # cli.py:79
    ...
```

`cli.py` の関数はほぼ全部 `_` で始まっている。
これは「モジュール外から呼ばないでほしい」という**書き手の意思表示**にすぎない。

実際、外から普通に呼べてしまう。

```python
>>> s = Sample()
>>> s._single       # '慣習上のprivate'      ← 読める
>>> s._helper()     # '呼べてしまう'          ← 呼べる
```

### アンダースコア 2 つ（`__foo`）は少しだけ違う

こちらは**名前修飾（name mangling）**が働き、`_クラス名__foo` に改名される。

```python
>>> s = Sample()      # __double という属性を持つ
>>> [k for k in vars(s) if "double" in k]
['_Sample__double']
>>> s.__double        # AttributeError
>>> s._Sample__double # 'name mangling される'   ← 名前さえ知れば読める
```

**アクセス制御ではなく、サブクラスとの名前衝突を避けるための仕組み**。
`private` の代用として使うのは Python では推奨されない。実務ではほぼ `_` 一つを使う。

> **考え方の違い**
> Java は「見せないことで守る」。Python は「見えるが、触るなら自己責任」。
> ライブラリの内部にどうしても手を入れたい場面で、
> Python は塀を越えられる。その代わり越えた側が壊れる責任を負う。

このリポジトリで本当に守りたいものは、修飾子ではなく**設計で守っている**。
`MailPort` に `send` メソッドを**定義しない**（`base.py:110`）ことで、
「メールを送る」を呼び出し不可能にしている。第12章のこの発想は Java でも有効だが、
`private` の無い Python ではより重要になる。

---

## 2. interface に相当するもの

Java:

```java
public interface CalendarPort {
    Appointment createTentative(Appointment appointment);
    void sendInvitation(String entryId);
}

public class ComOutlookCalendar implements CalendarPort { ... }
```

Python（`adapters/base.py:74`）:

```python
from abc import ABC, abstractmethod

class CalendarPort(ABC):
    @abstractmethod
    def create_tentative(self, appointment: Appointment) -> Appointment:
        """予定を「仮」として自分のカレンダーに作る。..."""

    @abstractmethod
    def send_invitation(self, entry_id: str) -> None:
        """既存の仮予定を、出席者への招待として送信する。..."""


class ComOutlookCalendar(CalendarPort):   # implements ではなく継承の構文
    ...
```

差分は 4 つ。

**① `interface` キーワードが無い。** `ABC` を継承したクラスで代用する。

**② メソッド本体を書かないと構文エラーになる。**
Java は `;` で終えられるが、Python はブロックが必要。
このリポジトリは **docstring を本体にしている**ので `pass` を書かずに済んでいる。
結果として「仕様が本体になっている」形になり、これは Python らしい書き方。

**③ 実装漏れの検出が実行時。**
Java はコンパイルエラー、Python は**インスタンス化した瞬間**に `TypeError`。

```python
>>> class Half(CalendarPort):
...     def create_tentative(self, a): ...
>>> Half()
TypeError: Can't instantiate abstract class Half without an implementation for
abstract methods 'busy_spans', 'find_free_slots', 'send_invitation'
```

**④ `@Override` が無い。** 名前が一致すれば黙って上書きされる。
綴りを間違えると「上書きしたつもりが別のメソッドを増やしただけ」になり、
Java の `@Override` のような防波堤が無い。
`@abstractmethod` が付いていれば ③ で気づけるので、抽象側に印を付けるのが防御になる。

### そもそも継承しない選択肢（ダックタイピング）

Java と決定的に違うのがここ。Python は**継承していなくても、
必要なメソッドさえ持っていれば渡せる**。

```python
class 何も継承していないFake:          # CalendarPort を implements していない
    def create_tentative(self, a): ...
    def send_invitation(self, i): ...
    def find_free_slots(self, s, e, d): ...
    def busy_spans(self, p, s, e): ...

hold(何も継承していないFake(), "件名", start, 60)   # 動く
```

「アヒルのように歩き鳴くならアヒル」＝ ダックタイピング。
型が合っているかは**使う瞬間に**判定される。

`typing.Protocol` を使うと、この「構造だけで合わせる」を型チェッカにも理解させられる。

```python
from typing import Protocol

class CalendarPort(Protocol):        # 継承させずに型を合わせられる
    def create_tentative(self, appointment: Appointment) -> Appointment: ...
```

Java の `interface` に近いのは `ABC`、Go の `interface` に近いのが `Protocol`、
と考えると分かりやすい。このリポジトリは `ABC` を選んでいる
（実装漏れを実行時に検出できるため）。

---

## 3. クラスとコンストラクタ

Java:

```java
public final class Person {
    private final String name;
    private final String address;

    public Person(String name, String address) {
        this.name = name;
        this.address = address;
    }
    // getter, equals, hashCode, toString ...
}
```

Python（`base.py:26`）:

```python
@dataclass(frozen=True)
class Person:
    name: str
    address: str | None = None
```

**2 行。** `@dataclass` が `__init__` / `__repr__` / `__eq__` を自動生成する。
Java 16 の `record` や Lombok の `@Value` に相当する。

`frozen=True` が `final` に相当し、生成後の代入を拒否する。

```python
>>> p = Person(name="山田太郎")
>>> p.name = "別人"
dataclasses.FrozenInstanceError: cannot assign to field 'name'
```

### `self` は明示的に書く

```python
def to_markdown(self) -> str:      # style_profile.py:60
    ...
```

Java の `this` は暗黙だが、Python は**第1引数として自分で受け取る**。
呼ぶときは `profile.to_markdown()` で `self` を渡す必要はない（自動で入る）。

定義に書き忘れると実行時に引数の数が合わずエラーになる。慣れるまで一番よく踏む。

### getter / setter は書かない

Java は「フィールドを private にして getter を生やす」が定石だが、
Python は**属性をそのまま公開する**。

```python
appointment.subject          # getSubject() ではない
```

後から計算やバリデーションを挟みたくなったら、`@property` で
**呼び出し側のコードを変えずに**メソッド化できる。

```python
@property
def subject(self) -> str:
    return self._subject.strip()
```

`appointment.subject` という書き方が変わらないので、
Java のように「将来に備えて最初から getter を書く」必要が無い。

---

## 4. メソッドのオーバーロードが無い

Java:

```java
Appointment hold(String subject, LocalDateTime start, int minutes) { ... }
Appointment hold(String subject, LocalDateTime start, int minutes, List<Person> attendees) { ... }
```

Python では**同名の定義は後勝ちで上書きされる**。

```python
class Over:
    def f(self, a): return "1引数版"
    def f(self, a, b): return "2引数版"     # 前のを消してしまう

>>> Over().f(1)
TypeError: Over.f() missing 1 required positional argument: 'b'
```

代わりに**既定値引数**で表現する（`calendar_hold.py:24`）。

```python
def hold(
    calendar: CalendarPort,
    subject: str,
    start: datetime,
    duration_minutes: int,
    attendees: list[Person] | None = None,   # ここから省略可能
    location: str = "",
    body: str = "",
) -> Appointment:
```

呼ぶ側は**キーワード引数**で必要なものだけ指定できる。

```python
hold(cal, "打ち合わせ", start, 60)
hold(cal, "打ち合わせ", start, 60, location="会議室A")
```

引数が増えたときに Java のようなオーバーロードの列や
Builder パターンが要らなくなるのは、Python の実用上の利点。

> **注意**: 既定値に `[]` や `{}` を書いてはいけない。
> 定義時に一度だけ評価され、全呼び出しで共有される（本編 第2章）。
> Java 感覚で `List<Person> attendees = new ArrayList<>()` のつもりで書くと事故る。

---

## 5. 例外 ── 検査例外が無い

Java の `throws IOException` にあたるものが**存在しない**。
すべて実行時例外（Java でいう `RuntimeException`）と同じ扱い。

```python
def risky():
    raise ValueError("throws 宣言は要らない")

risky()      # 呼び出し側に try が無くてもコンパイルは通る。実行時に落ちるだけ
```

つまり「この関数が何を投げるか」はコンパイラが教えてくれない。
**docstring に書くのが唯一の伝達手段**になる。`base.py:86` がその例。

```python
@abstractmethod
def send_invitation(self, entry_id: str) -> None:
    """既存の仮予定を、出席者への招待として送信する。

    破壊的かつ取り消せない操作。呼び出し側で必ず人間の承認を挟むこと。
    """
```

### 継承関係の違い

| Java | Python |
|---|---|
| `Throwable` | `BaseException` |
| `Error` | （`SystemExit`, `KeyboardInterrupt` など） |
| `Exception`（検査） | ── 対応物なし ── |
| `RuntimeException` | `Exception` |

**Python で `except Exception:` と書くのは、Java の `catch (RuntimeException e)` に近い。**
`except BaseException:` は `catch (Throwable t)` に相当し、
`Ctrl+C` やプロセス終了指示まで飲み込むので通常は書かない
（[python-execution.md](python-execution.md) の `SystemExit` の項）。

### `finally` と `try-with-resources`

`finally` は同じ。`try-with-resources` に相当するのが `with` 文。

```java
try (var reader = new BufferedReader(...)) { ... }   // Java
```

```python
with open("file.txt", encoding="utf-8") as f:        # Python
    ...
```

Java の `AutoCloseable` にあたるのが `__enter__` / `__exit__` を持つクラス。

### 例外の連鎖

Java の `new RuntimeException(msg, cause)` に相当するのが `raise ... from exc`
（`cli.py:29`）。

```python
except ValueError as exc:
    raise argparse.ArgumentTypeError(f"...: {value!r}") from exc
```

---

## 6. `==` と `is` ── 意味が Java と逆

**ここは事故りやすい。**

| やりたいこと | Java | Python |
|---|---|---|
| 値が等しいか | `a.equals(b)` | `a == b` |
| 同じインスタンスか | `a == b` | `a is b` |

```python
>>> a, b = [1, 2], [1, 2]
>>> a == b     # True   ← 中身の比較
>>> a is b     # False  ← 別オブジェクト
```

Java で文字列を `==` で比較して痛い目を見た経験があると身構えるが、
**Python では `==` が正解**。`is` を使うのは `None` の判定くらいでよい。

```python
if value is None:      # 慣用句。== None とは書かない
```

`@dataclass` が `__eq__` を自動生成するので、`Person(name="山田太郎") == Person(name="山田太郎")`
は `True` になる。`equals()` を手で書かなくてよい。

---

## 7. 型 ── 書けるが、実行時には効かない

**最大の落とし穴。** Python の型注釈は**注釈でしかない**。

```python
def hold(calendar: CalendarPort, subject: str, start: datetime, ...) -> Appointment:
```

これだけ書いても、実行時には一切チェックされない。

```python
>>> hold("これはCalendarPortではない", "件名", "日時でもない", 60)
TypeError: can only concatenate str (not "datetime.timedelta") to str
```

関数呼び出し自体は成功し、`start + timedelta(...)` まで進んでから
**まったく関係ない理由で**落ちている。Java なら `javac` が門前払いする種類の誤り。

### だから別のものが要る

| Java | Python |
|---|---|
| `javac` の型検査 | `mypy` / Pylance（別途実行する静的解析） |
| コンパイル時の保証 | **テスト**（本編 第10章） |

```bash
python3 -m pip install mypy
PYTHONPATH=src python3 -m mypy src/outlook_assistant
```

VS Code なら `"python.analysis.typeCheckingMode": "standard"` で
編集中に指摘される（[vscode-code-reading.md](vscode-code-reading.md)）。

「型を書いたから安心」ではなく、**型は道具として自分で回す**。
このリポジトリが全ファイルに型注釈を付けつつテストも厚いのは、その両輪が要るため。

### ジェネリクス

```java
List<Person> attendees;
Map<String, String> metadata;
```

```python
attendees: list[Person]
metadata: dict[str, str]
```

`<>` が `[]` になるだけで発想は同じ。ワイルドカード（`? extends T`）に相当するものもあるが、
日常的にはまず使わない。

型に名前を付けたいときは Java の型エイリアス相当を 1 行で書ける（`scheduling.py:12`）。

```python
Span = tuple[datetime, datetime]
```

---

## 8. `static` と定数

### static メソッド

Java の `static` メソッドに対応するものは 2 つある。

```python
class Foo:
    @staticmethod
    def bar(x): ...        # クラスに属する。self を取らない

    @classmethod
    def baz(cls, x): ...   # クラス自体を第1引数で受け取る。ファクトリメソッド向き
```

ただし **Python では「クラスに入れずモジュール直下の関数にする」のが普通**。
Java のように「関数を置くためだけのユーティリティクラス」を作らない。

`scheduling.py` の `merge_spans` / `free_gaps` は、Java なら
`SchedulingUtils` という `static` メソッドの入れ物になるところを、
**そのままモジュールの関数として置いている**。これが Python らしい形。

### 定数

`final` に相当するものが無いので、**大文字の命名で「変えるな」と伝える**だけ。

```python
FREE_BUSY_INTERVAL_MINUTES = 30      # com_outlook.py:44
OL_APPOINTMENT_ITEM = 1              # com_outlook.py:30
_DATETIME_HINT = "YYYY-MM-DD HH:MM"  # cli.py:22
```

代入し直すことは技術的に可能。ここでも「慣習で守る」文化が出る。

---

## 9. enum

Java:

```java
public enum Busy { FREE, TENTATIVE, BUSY }
```

Python（`base.py:18`）:

```python
class Busy(str, Enum):
    FREE = "free"
    TENTATIVE = "tentative"
    BUSY = "busy"
```

値を明示的に書く点が違う。`str` も継承しているので**文字列としても比較できる**。

```python
>>> Busy.FREE == "free"
True
```

Java の enum のようにメソッドやフィールドを持たせることもできるが、
Python では**辞書で対応表を作る**方が軽い（`com_outlook.py:37`）。

```python
_BUSY_STATUS = {Busy.FREE: 0, Busy.TENTATIVE: 1, Busy.BUSY: 2}
```

Java なら enum のコンストラクタに数値を持たせるところ。
どちらが良いかは場合によるが、「外部システムの都合の値」は
enum 本体から切り離しておくと、システムが増えたときに対応表を足すだけで済む。

---

## 10. パッケージと import

### 宣言文が無い

Java は `package com.example.foo;` をファイル先頭に書くが、
Python は**ディレクトリ構造がそのままパッケージ**になる。

```
src/outlook_assistant/
├── __init__.py          ← このディレクトリはパッケージだ、という印（中身は空）
├── scheduling.py
└── adapters/
    ├── __init__.py
    └── base.py
```

`__init__.py` は Java に対応物が無い。**中身が空でも置く**。

### import は「名前を取り込む」

```java
import com.example.Person;           // 型を1つ取り込む
import static java.util.Arrays.*;
```

```python
from .adapters.base import Person          # 名前を1つ取り込む
from . import scheduling                   # モジュールごと取り込む
import argparse                            # 標準ライブラリ
```

Java の `import` はコンパイラへの指示にすぎないが、
**Python の `import` は実行される文**。書いた場所でモジュールが読み込まれ、
トップレベルのコードが走る。だからこんな書き方が成立する（`cli.py:34`）。

```python
def _calendar():
    from .adapters.com_outlook import ComOutlookCalendar   # 関数の中で import
    return ComOutlookCalendar()
```

Windows 専用モジュールを Mac では読み込ませない、という制御ができる。
Java ではまず出てこない発想。

`.` は相対 import で「このパッケージの中の」、`..` は「ひとつ上の」の意味。

### ワイルドカード

`from module import *` は書けるが**強く避けられる**。
どの名前が入ってきたか分からなくなるため、Java の `import java.util.*;` ほど気軽には使わない。

---

## 11. ビルドと実行

| | Java | Python |
|---|---|---|
| ビルド定義 | `pom.xml` / `build.gradle` | `pyproject.toml` |
| 依存解決 | Maven Central | PyPI（`pip`） |
| コンパイル | `javac` → `.class` | **自動** → `__pycache__/*.pyc` |
| 成果物 | `.jar` | `.whl` / ソースそのまま |
| 実行 | `java -jar app.jar` | `python -m パッケージ名` |
| エントリポイント | `public static void main(String[])` | `__main__.py` |

**ビルド工程が無い**のが一番大きな違い。`.py` を保存すればそれが動く。
バイトコードへのコンパイルは実行時に自動で行われ、`__pycache__` に載る。
`javac` を打つ相当の操作は要らないし、キャッシュを消しても勝手に作り直される。

詳しくは [python-execution.md](python-execution.md)。

### エントリポイント

Java:

```java
public class Main {
    public static void main(String[] args) {
        System.exit(run(args));
    }
}
```

Python（`__main__.py`）:

```python
from .cli import main

raise SystemExit(main())
```

`System.exit(n)` に相当するのが `raise SystemExit(n)`（= `sys.exit(n)`）。
Python では**終了指示が例外として実装されている**のが違い。

### 実行時の引数

Java の `String[] args` は `sys.argv` に相当するが、
Python では `argparse` で宣言的に定義するのが標準（`cli.py:146`）。
Java でいう picocli や Commons CLI が標準ライブラリに入っていると思えばよい。

---

## 12. 文法の細かい差

### ブロックはインデント

`{}` が無い。**インデントが構文**。

```python
if duration_minutes <= 0:
    raise ValueError("所要時間は1分以上で指定してください")
```

`;` も不要（書いてもよいが誰も書かない）。
インデントの混在（タブとスペース）は構文エラーになるので、エディタ設定を統一しておく。

### コレクション操作は Stream ではなく内包表記

```java
attendees.stream().map(Person::getName).collect(Collectors.joining(", "));
```

```python
", ".join(p.name for p in appointment.attendees)      # cli.py:65
```

```java
list.stream().filter(x -> x.isValid()).collect(Collectors.toList());
```

```python
[x for x in items if x.is_valid()]
```

`map` / `filter` 関数も存在するが、**内包表記の方が読みやすいとされ**、こちらが主流。

### 三項演算子は語順が違う

```java
String s = flag ? "はい" : "いいえ";
```

```python
s = "はい" if flag else "いいえ"
```

条件が真ん中に来る。慣れるまで読みにくい（`style_profile.py:69`）。

### 文字列連結

`StringBuilder` は要らない。ループで `+=` するより `join` を使う。

```python
"\n".join(lines) + "\n"          # style_profile.py:85
```

書式付き文字列は `String.format` ではなく **f-string**。

```java
String.format("%s: %d通", name, count);
```

```python
f"{name}: {count}通"
f"{appointment.start:%Y-%m-%d %H:%M}"     # cli.py:61  日付書式もそのまま書ける
```

### `switch`

Python 3.10 から `match` 文があるが、`if/elif` で書くことも多い。
このリポジトリでは、そもそも分岐を**辞書と関数で消している**（`cli.py:190`）。

```python
p_slots.set_defaults(func=_cmd_slots)
...
return args.func(args)         # if/elif の代わりに関数を持ち回る
```

関数を値として扱えるので、Java 8 以前の「分岐を書くしかない」制約が無い。
Java の `Map<String, Function<...>>` でディスパッチするのと同じ発想。

### null 安全

`Optional<T>` に相当するのは `T | None`。ただし
`orElse` / `map` のようなメソッドチェーンは無く、素直に `if` で書く。

```python
address = person.address or person.name      # null なら別の値、を1行で
```

`or` が**値そのものを返す**性質を使った慣用句（本編 第2章）。
Java の `Objects.requireNonNullElse(a, b)` に近い。

---

## 13. まとめ ── 考え方の違い

| | Java | Python |
|---|---|---|
| 誤りを見つける場所 | コンパイル時 | **実行時**（＋静的解析ツール） |
| 守り方 | 言語機能で強制（`private`, `final`, 検査例外） | **慣習と設計で示す**（`_`, docstring, そもそも作らない） |
| 冗長さ | 明示的に書く | 定型は自動生成（`@dataclass`）に寄せる |
| 型 | 必須 | 任意。書くなら別途チェックを回す |

Java の安全性は言語が保証してくれるが、Python は**書き手が仕組みを用意する**必要がある。
このリポジトリがやっているのは、まさにその肩代わりである。

- 型注釈を全ファイルに付ける → コンパイラの代わりに `mypy` / Pylance に見せる
- テストを厚く書く（38件）→ 「壊れたら困ること」を実行して守る
- `MailPort` に `send` を定義しない → `private` の代わりに**存在させないことで守る**
- docstring に契約を書く → `throws` や javadoc の代わり

Java から来た人が最初に不安になるのは「こんなに緩くて大丈夫なのか」だが、
**緩い分を何で埋めるかが設計の腕になる**、と考えると読み方が変わる。
