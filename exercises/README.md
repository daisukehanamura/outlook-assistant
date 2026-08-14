# 演習

[`docs/python-learning.md`](../docs/python-learning.md) の章に対応した、手を動かす課題。
**最初は全部赤（失敗）**。緑にしていくのが課題。

このディレクトリは学習用で、`outlook_assistant` 本体からは参照されていない。
消してもアプリケーションは動く。

## 走らせる

```bash
cd ~/Git/outlook-assistant

# 答え合わせ（最初はすべて失敗する）
PYTHONPATH=src:exercises python3 -m unittest discover -s exercises -t exercises

# 1問だけ
PYTHONPATH=src:exercises python3 -m unittest test_exercises.Ex01IntersectSpansTest -v

# 解答例で走らせて「緑になる状態」を確認する
EX_SOLUTIONS=1 PYTHONPATH=src:exercises python3 -m unittest discover -s exercises -t exercises
```

毎回打つのが面倒なら、シェルに登録しておく。

```bash
alias extest='PYTHONPATH=src:exercises python3 -m unittest discover -s exercises -t exercises'
```

## 課題一覧

| ファイル | 対応する章 | 題材 |
|---|---|---|
| `ex01_spans.py` | 🌱 第1〜3章 | リスト・タプル・ループ。時間帯の積集合 |
| `ex02_errors.py` | 🌿 第4・7章 | 例外の設計と正規表現。所要時間のパース |
| `ex03_dataclass.py` | 🌿 第5章 | dataclass と Enum。型を自分で定義する |
| `ex04_port.py` | 🌳 第6章 | 抽象インタフェースとテストダブル |
| `ex05_text.py` | 🌿 第7章 | 文字列処理と Counter |

`solutions/` に解答例がある。**詰まってから見ること。**
解答例には「なぜそう書くか」のコメントを付けてあるので、
自力で解けた場合も後で読み比べる価値がある。

## 進め方

1. `exNN_*.py` の docstring を読む（何を作るかが書いてある）
2. テストを走らせて、落ちるメッセージを読む
3. 実装する
4. 緑になったら `solutions/` と読み比べる

テストの失敗メッセージは学習の主要な情報源である。
`AssertionError: [(...)] != [(...)]` の左右が「実際 / 期待」であることを覚えておくと、
何がずれているかがすぐ分かる。

## 卒業課題

`docs/python-learning.md` の末尾にある `mail_draft.py` の実装。
ここまでの 5 問はその部品になっている。
