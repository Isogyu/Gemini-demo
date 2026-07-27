# 法人税・財務諸表 税務調整シミュレーター (MVP)

試算表（Trial Balance）を取り込み、交際費等・減価償却の税務調整を行って
課税所得と法人税等（法人税・地方法人税・法人住民税・法人事業税）を試算する
フルスタック MVP アプリケーションです。

- バックエンド: FastAPI + Pydantic + SQLAlchemy (SQLite)
- フロントエンド: Next.js (App Router) + Tailwind CSS + lucide-react
- インフラ: Docker / Docker Compose

## クイックスタート

```bash
docker compose up --build
```

- フロントエンド: http://localhost:3000
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
    schemas/tax.py         Pydantic スキーマ（入出力の契約）
    db/                    SQLAlchemy エンジンとモデル
    data/samples.json      サンプル試算表データセット
  tests/                   pytest（税務ロジック + API）
frontend/
  app/                     App Router のページ / レイアウト
  components/              表示コンポーネント
  lib/                     API クライアント・型・フォーマッタ
docker-compose.yml
```

API ルート（`api/`）・業務ロジック（`services/`）・永続化（`db/`）・
スキーマ（`schemas/`）を明確に分離しています。

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

## 免責

本アプリは学習・デモ用の簡略モデルであり、実際の申告実務に用いることはできません。
