# 税務・法務デモアプリ

2 つのアプリを同じフルスタック基盤（FastAPI + Next.js）に載せたデモです。

1. **法人税・財務諸表 税務調整シミュレーター**（`/`）— 試算表から別表四と法人税等を試算
2. **ディベート立論アナライザー**（`/debate`）— 賛否の立論を読み込み、論点マップ・反駁候補・想定尋問・出典の欠落を抽出

- バックエンド: FastAPI + Pydantic + SQLAlchemy (SQLite)
- フロントエンド: Next.js (App Router) + Tailwind CSS + lucide-react
- インフラ: Docker / Docker Compose

## クイックスタート

```bash
docker compose up --build
```

- フロントエンド: http://localhost:3000 （税務シミュレーター）/ http://localhost:3000/debate （立論アナライザー）
- バックエンド API ドキュメント: http://localhost:8000/docs

画面上でサンプル試算表を選び、「シミュレーション実行」を押すと、
サマリーカード・比較チャート・別表四（加算/減算）ビューが表示されます。

## ディレクトリ構成

```
backend/
  app/
    api/routes.py          API ルーティングのみを担当
    services/              業務ロジック（税務計算）
      entertainment.py     交際費等の損金不算入
      depreciation.py      減価償却超過額
      tax_calc.py          法人税等の概算
      reconciliation.py    別表四シミュレーション
      trial_balance.py     試算表集計
      samples.py           サンプルデータの読み込み
      debate/              ディベート立論の解析
        parser.py          立論テキスト → 論証ブロック
        issues.py          争点辞書と論点マップの構築
        rebuttal.py        反駁パターンと想定尋問の生成
        extractor.py       .docx / .txt からの本文抽出
        materials.py       参考資料のパースと資料Nの突合
        analysis.py        解析の統合エントリポイント
      statute/             法令の自動参照（e-Gov 法令API）
        references.py      本文 → 法令参照の抽出・正規化
        egov.py            e-Gov 法令API クライアントと XML パース
        service.py         条文の取得と SQLite キャッシュ
    schemas/               Pydantic スキーマ（入出力の契約）
    db/                    SQLAlchemy エンジンとモデル
    data/                  サンプル試算表 / サンプル立論
  tests/                   pytest（税務ロジック + 立論解析 + API）
frontend/
  app/                     App Router のページ / レイアウト
  components/              表示コンポーネント
  lib/                     API クライアント・型・フォーマッタ
docker-compose.yml
```

API ルート（`api/`）・業務ロジック（`services/`）・永続化（`db/`）・
スキーマ（`schemas/`）を明確に分離しています。

## ディベート立論アナライザー（`/debate`）

賛成側・反対側の立論（.docx / .txt の読み込み、または貼り付け）を解析し、次を出力します。

| 出力 | 内容 |
| --- | --- |
| 立論の構造 | 見出し（Ⅰ. / 1. / （1））で論証ブロックへ分解し、結論文と出典【】を抽出 |
| 論点マップ | 争点ごとに賛否を対置。片側しか論じていない争点は「無応答」として検出 |
| 反駁候補 | 相手立論の文言（trigger）を起点に反駁の型を引き当て、想定尋問を付す |
| 出典チェック | 資料 / 法令 / 判例の一覧と、出典が付いていない論証ブロックの一覧 |
| 法令・参考資料の突合 | 引用された法令の現行条文（e-Gov 法令API）と、【資料N参照】と参考資料の突合 |

解析は LLM を使わない規則ベースで、生成される反駁には必ず起点となった
相手の文言が付きます（原文にない事実を作り出さない）。

- 争点辞書: `backend/app/services/debate/issues.py`
- 反駁パターン: `backend/app/services/debate/rebuttal.py`
- 立論パーサ: `backend/app/services/debate/parser.py`

### 法令の自動参照（e-Gov 法令API）

立論・参考資料の本文から法令の引用（`所得税法56条` / `法37条1項` / `日本国憲法14条1項` /
`第五十六条` などの漢数字表記）を抽出し、[e-Gov 法令API](https://laws.e-gov.go.jp/) から
現行条文を取得して並べて表示します。

- 法令名 → 法令番号の解決に API v2、条単位の取得に API v1 を使用し、SQLite に 30 日キャッシュ
- 省略された「法」は論題の中心となる法令（既定値: 所得税法）として正規化
- 取得結果には常に e-Gov の出典 URL を付し、未発見・API 停止は状態（`found` / `not_found` /
  `unavailable`）として表示する（解析全体は失敗させない）
- 参考資料に貼られた条文と現行条文を突合し、差異を検出（`consistent` / `differs` /
  `unverified`）
- 参考資料の「Ⅰ. 関連法令 / Ⅱ. 資料N」をパースし、立論の【資料N参照】と紐付けて
  欠番（参考資料にない引用）と未使用資料を警告

- e-Gov API クライアント: `backend/app/services/statute/egov.py`
- 法令参照の抽出・正規化: `backend/app/services/statute/references.py`
- キャッシュと取得の統合: `backend/app/services/statute/service.py`
- 参考資料のパースと突合: `backend/app/services/debate/materials.py`

## 税務ロジックの前提（MVP 簡略モデル）

### 交際費等の損金不算入（`services/entertainment.py`）

| 資本金 | 損金算入できる額 |
| --- | --- |
| 1 億円以下 | 年 800 万円の定額控除 と 接待飲食費 × 50% の有利な方 |
| 1 億円超 100 億円以下 | 接待飲食費 × 50% |
| 100 億円超 | なし（全額損金不算入） |

損金不算入額 = 交際費等の総額 − 損金算入額（別表四の加算項目）。

### 減価償却超過額（`services/depreciation.py`）

資産ごとに `会計上の減価償却費 − 税務上の償却限度額` を計算し、
プラス分を償却超過額（加算）として集計します。マイナス分は償却不足額として
情報保持のみ行います（繰越超過額の認容は MVP では対象外）。

### 法人税等（`services/tax_calc.py`）

課税所得に実効税率（既定 29.74%）を乗じて総額を求め、法定税率
（法人税 23.2%、地方法人税 = 法人税額 × 10.3%、住民税法人税割 = 法人税額 × 7%、
事業税 = 所得 × 7%）の比率で各税目に按分します。課税所得が 0 以下の場合は税額 0 です。

## 開発

### バックエンド

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest                       # 全テスト（税務ロジック + API）
uvicorn app.main:app --reload
```

### フロントエンド

```bash
cd frontend
npm install
npm run dev        # http://localhost:3000
npm run lint
npm run typecheck
```

`NEXT_PUBLIC_API_BASE_URL`（既定 `http://localhost:8000`）でバックエンドの URL を指定します。

## 主な API

| メソッド | パス | 説明 |
| --- | --- | --- |
| GET | `/api/health` | ヘルスチェック |
| GET | `/api/samples` | サンプル試算表の一覧 |
| GET | `/api/samples/{id}` | サンプル試算表の取得 |
| POST | `/api/reconciliation` | 税務調整シミュレーションの実行（結果を SQLite に保存） |
| GET | `/api/reconciliation/history` | 過去の実行結果 |
| GET | `/api/debate/samples` | サンプル立論（賛成/反対）の一覧 |
| POST | `/api/debate/extract` | .docx / .txt から本文と立場を抽出 |
| POST | `/api/debate/analyze` | 立論の解析（論点マップ・反駁候補の生成） |
| GET | `/api/debate/history` | 過去の解析結果 |
| GET | `/api/statutes/article` | 法令名・条・項を指定して現行条文を取得（キャッシュ優先） |
| POST | `/api/statutes/resolve` | 本文中の法令引用を抽出してまとめて取得 |

## 免責

本アプリは学習・デモ用の簡略モデルであり、実際の申告実務に用いることはできません。
