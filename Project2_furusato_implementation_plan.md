# 第2案 実装計画書

**プロジェクト名**: ふるさと納税 人気返礼品トレンド分析（Furusato Nozei Trends）
**作成日**: 2026年4月30日
**想定実装期間**: 8〜10日間（実働、1日3〜4時間）／カレンダー上2〜3週間

---

## 1. プロジェクト概要

楽天ウェブサービス（楽天ふるさと納税API）から返礼品データを取得し、総務省「ふるさと納税に関する現況調査」CSV と組み合わせて、ふるさと納税市場の人気構造・価格戦略・自治体戦略を可視化する。中江哲夫氏のEC・マーケティング・ブランドリサーチの実務経験と直結する作品として、「事業視点を持ったデータアナリスト」という差別化を打ち出す。

**最終成果物**

1. GitHub Pages で公開するインタラクティブダッシュボード（`/web/`）
2. 分析プロセスを示す Jupyter Notebook 群（`/notebooks/`）
3. 再現可能な Python コードベース（`/src/`）と README
4. ポートフォリオ用の解説記事（市場分析の発見と示唆）

**第1作との差別化**

第1作（e-Stat 人口予測）が「公的データ × 時系列予測 × ストーリーテリング」だったのに対し、第2作は「商業データ × クロスデータ分析 × ダッシュボード型UI」で対比させ、データアナリストの幅広さを示す。

---

## 2. ファイル構成

```
furusato-nozei-trends/
│
├── README.md                       # プロジェクト概要、セットアップ手順、成果物リンク
├── .gitignore                      # APIキー、生データ、キャッシュを除外
├── .env.example                    # 環境変数テンプレート（RAKUTEN_APP_ID 等）
├── requirements.txt                # 依存ライブラリ
├── pyproject.toml                  # black/ruff 設定
│
├── config/
│   ├── settings.py                 # 楽天APIキー、ジャンルID、定数
│   └── category_mapping.yml        # カテゴリ正規化ルール（手動メンテ用）
│
├── data/
│   ├── raw/
│   │   ├── rakuten_cache.sqlite    # 楽天APIレスポンスのキャッシュ
│   │   └── soumu_donations.csv     # 総務省「現況調査」CSV
│   ├── processed/
│   │   ├── products.parquet        # 商品マスター（クレンジング済み）
│   │   └── donations_by_pref.parquet
│   └── analysis/
│       ├── category_stats.parquet  # カテゴリ別集計
│       ├── price_segments.parquet  # 価格帯別集計
│       └── municipality_stats.parquet
│
├── notebooks/
│   ├── 01_data_exploration.ipynb   # EDA：取得データの全体像把握
│   ├── 02_categorization.ipynb     # カテゴリ分類・名寄せプロセス
│   ├── 03_price_strategy.ipynb     # 価格帯・還元率分析
│   └── 04_municipality_analysis.ipynb  # 自治体戦略の類型化
│
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── rakuten_client.py       # 楽天市場API ラッパー
│   │   ├── soumu_loader.py         # 総務省CSV ローダー
│   │   └── data_fetcher.py         # 取得タスクのオーケストレーション
│   ├── preprocessing/
│   │   ├── __init__.py
│   │   ├── cleaner.py              # 欠損値処理、型変換
│   │   ├── categorizer.py          # カテゴリ正規化（YML+正規表現+簡易NLP）
│   │   └── return_rate.py          # 還元率推定（楽天市場の同等商品との比較）
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── category.py             # カテゴリ別分析
│   │   ├── price.py                # 価格帯セグメント分析
│   │   ├── municipality.py         # 自治体タイプ分類（クラスタリング）
│   │   └── insight_generator.py    # 主要指標サマリーの自動生成
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── dashboard_data.py       # フロント用JSON生成
│   │   ├── maps.py                 # 自治体ヒートマップ
│   │   └── charts.py               # 散布図・棒グラフ・ヒストグラム
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── rate_limiter.py         # 楽天APIレート制限対応（1req/sec）
│
├── web/
│   ├── index.html                  # メインダッシュボード
│   ├── about.html                  # データソース・手法・免責事項
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── responsive.css
│   │   ├── js/
│   │   │   ├── dashboard.js        # ダッシュボード状態管理
│   │   │   ├── filters.js          # カテゴリ・価格帯・自治体フィルター
│   │   │   ├── charts.js           # Plotly チャート差し替え
│   │   │   └── table.js            # Grid.js テーブル制御
│   │   └── data/
│   │       ├── products_summary.json    # 集計済み商品サマリー
│   │       ├── categories.json          # カテゴリ別統計
│   │       ├── price_segments.json      # 価格帯別統計
│   │       └── municipalities.json      # 自治体別統計＋座標
│   └── assets/
│       └── images/                 # OG画像、サイトロゴ
│
├── tests/
│   ├── test_api.py
│   ├── test_preprocessing.py
│   ├── test_categorizer.py
│   └── test_analysis.py
│
└── scripts/
    ├── fetch_data.py               # CLI: 楽天APIからデータ一括取得
    ├── run_analysis.py             # CLI: 分析パイプライン実行
    └── build_site.py               # CLI: フロント用JSON生成・ビルド
```

### 設計上の主なポイント

- **`config/category_mapping.yml`**: カテゴリ正規化ルールを YAML で外出し。表記揺れ（例: 「黒毛和牛」「和牛」「ブランド牛」を「牛肉」に統合）の運用が容易になり、ノートブックを汚さない
- **楽天APIキャッシュ必須**: レート制限（1秒1リクエスト）の制約上、開発中の再取得は避けたい。SQLite キャッシュで2回目以降は瞬時に再現
- **総務省データとの結合**: 自治体名で楽天データと総務省データを突合し、「楽天での商品掲載数 vs 全国寄付額順位」のような立体的な分析を可能にする
- **`src/analysis/` レイヤー分離**: 第1作にはなかった「分析」専用ディレクトリを新設。データ前処理と分析ロジックを明確に分ける

---

## 3. 必要ライブラリ

### 3.1 requirements.txt（推奨バージョン）

```
# === API・HTTP ===
requests>=2.31.0
python-dotenv>=1.0.0
tenacity>=8.2.0          # リトライ処理

# === データ処理 ===
pandas>=2.1.0
numpy>=1.26.0
pyarrow>=14.0.0
pyjanitor>=0.26.0
pyyaml>=6.0.1            # カテゴリマッピング YAML 読込

# === 自然言語処理（カテゴリ正規化） ===
sudachipy>=0.6.7         # 日本語形態素解析
sudachidict-core>=20240109

# === 分析・機械学習 ===
scikit-learn>=1.3.0      # クラスタリング（自治体タイプ分類）
scipy>=1.11.0            # 統計検定

# === 可視化 ===
plotly>=5.17.0
kaleido>=0.2.1
geopandas>=0.14.0        # 自治体境界データ操作
matplotlib>=3.8.0

# === 開発ツール ===
jupyter>=1.0.0
ipywidgets>=8.1.0
black>=23.10.0
ruff>=0.1.5
pytest>=7.4.0
mypy>=1.6.0

# === ロギング ===
loguru>=0.7.2
```

### 3.2 ライブラリ選定の根拠（第1作との差分中心）

| カテゴリ     | 採用ライブラリ      | 理由                                     |
| -------- | ------------ | -------------------------------------- |
| API リトライ | tenacity     | 楽天APIのレート制限・一時的エラーで自動リトライ。デコレータで簡潔に書ける |
| 日本語NLP   | sudachipy    | 商品名のカテゴリ正規化に必須。MeCab より辞書同梱で導入が楽       |
| YAML     | pyyaml       | カテゴリマッピングルールを設定ファイル化するため               |
| クラスタリング  | scikit-learn | 自治体の戦略タイプを K-means で4〜5タイプに分類          |
| 統計検定     | scipy        | 「価格帯×評価」の有意差検定で考察を強化                   |

### 3.3 別途必要なもの

- **楽天アプリケーション ID**: [https://webservice.rakuten.co.jp/](https://webservice.rakuten.co.jp/) で無料登録、即時発行
- **総務省「ふるさと納税に関する現況調査結果」**: [総務省ふるさと納税ポータル](https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/) から最新年度のCSVをダウンロード
- **市区町村境界 GeoJSON**: [国土数値情報](https://nlftp.mlit.go.jp/ksj/) または [japan-topojson](https://github.com/dataofjapan/land) などの公開リポジトリ
- **Python バージョン**: 3.11 以上を推奨

### 3.4 楽天API利用上の留意事項

- レート制限: 1リクエスト/秒、30,000リクエスト/日
- 1リクエストで取得できる商品は最大30件、ページネーション必須
- **規約上、取得した商品データの再配布は不可**。サイトでは集計結果と統計値のみを表示する設計が必須
- 商品ページ・画像へのリンクは可（楽天アフィリエイト推奨だが必須ではない）

---

## 4. 週次マイルストーン

実働9日（中央値）を 2〜3週間に分割。1日3〜4時間想定。

### Week 1（Day 1〜4）: データ取得・前処理基盤の構築

**ゴール**: 楽天APIから返礼品データを安定的に取得し、カテゴリ正規化されたマスターデータが手元にある状態

| Day | 主タスク                                                                                                                                              | 成果物                               |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| 1   | プロジェクト初期化／楽天アプリID取得／GitHubリポジトリ作成／ディレクトリ構造構築／`.gitignore`・`requirements.txt`・`pyproject.toml` 整備／仮想環境セットアップ                                       | リポジトリの初期コミット                      |
| 2   | 楽天APIクライアント（`src/api/rakuten_client.py`）の実装／レート制限対応（`utils/rate_limiter.py`、tenacity）／1ジャンル・1ページ分の取得テスト／総務省CSVローダー実装                              | API クライアント＋ユニットテスト                |
| 3   | 「ふるさと納税」ジャンル全カテゴリのデータ一括取得（数千〜数万件想定）／SQLite キャッシュへの保存／`scripts/fetch_data.py` 完成                                                                   | `data/raw/rakuten_cache.sqlite`   |
| 4   | EDA ノートブック（`01_data_exploration.ipynb`）／カテゴリ正規化ルール（`category_mapping.yml`）の初版作成／sudachipy で商品名トークナイズ／カテゴリ正規化器（`src/preprocessing/categorizer.py`） | `data/processed/products.parquet` |

**Week 1 の完了判定**:

- 楽天から取得した全商品データが SQLite に保存されている
- 商品が10〜15程度の主要カテゴリに正規化されている
- 同じスクリプトを再実行しても結果が再現される

---

### Week 2（Day 5〜7）: 分析・指標設計

**ゴール**: 4本の分析切り口がそれぞれノートブックで完結し、フロント用JSONが生成されている状態

| Day | 主タスク                                                                                                              | 成果物                                    |
| --- | ----------------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| 5   | カテゴリ別人気構造の分析（`src/analysis/category.py`、`03_price_strategy.ipynb`の前半）／価格帯セグメント分析／レビュー数・評価との相関                     | `data/analysis/category_stats.parquet` |
| 6   | 還元率の推定（`src/preprocessing/return_rate.py`）／楽天市場の同等商品との価格突合ロジック／コスパランキング作成                                         | 還元率推定ロジック＋検証ノートブック                     |
| 7   | 自治体タイプ分類（`04_municipality_analysis.ipynb`）／K-means で4〜5タイプにクラスタリング／総務省データと突合／フロント用JSON生成（`scripts/build_site.py`） | `web/static/data/*.json`               |

**Week 2 の完了判定**:

- カテゴリ・価格・還元率・自治体の4切り口で分析ノートブックが完成
- フロント用JSONがブラウザから fetch できる形式で書き出されている
- 主要な発見が3〜5個、文章化されている

---

### Week 3（Day 8〜10）: ダッシュボード実装・公開

**ゴール**: 一般の閲覧者がフィルター操作で自由にデータを探索できるダッシュボードが公開されている状態

| Day | 主タスク                                                                                       | 成果物              |
| --- | ------------------------------------------------------------------------------------------ | ---------------- |
| 8   | ダッシュボードのHTML骨組み（`web/index.html`）／KPIカード・フィルター・チャート領域のレイアウト／Plotly散布図（価格×レビュー数）／カテゴリ別棒グラフ  | 動作するダッシュボード（基本版） |
| 9   | 自治体ヒートマップ（GeoJSON + Plotly）／Grid.js による詳細テーブル／フィルター連動（`filters.js`）／インタラクション（クリックでドリルダウン）  | フィルター連動版ダッシュボード  |
| 10  | スタイリング／スマホ対応／`about.html`（データソース・手法・免責事項）／README整備／GitHub Pages 公開／LinkedIn・ポートフォリオへのリンク追加 | 公開URL            |

**Week 3 の完了判定**:

- 公開URLにアクセスでき、フィルター操作でチャートが即座に更新される
- スマホで閲覧できる
- About ページで「楽天規約に基づき集計値のみ表示」を明記

---

## 5. リスクと対策

| リスク            | 影響度 | 対策                                                      |
| -------------- | --- | ------------------------------------------------------- |
| 楽天APIのレート制限・障害 | 中   | tenacity で自動リトライ、SQLite キャッシュで再取得を回避、取得処理は夜間バッチ的に分散     |
| カテゴリ正規化の精度不足   | 高   | YAML マッピング＋目視チェックを反復。完璧を狙わず「主要15カテゴリで80%カバー」を目標に        |
| 総務省CSVの形式変動    | 中   | スキーマを `src/api/soumu_loader.py` で吸収。年度違いのCSVが混在する想定で柔軟に |
| 還元率推定の信頼性      | 高   | 「あくまで推定値」と注記、ロジックを About ページで完全公開、断定的表現を避ける             |
| 楽天規約違反リスク      | 高   | 商品個別データは表示せず集計値のみに徹する。About ページで規約遵守を明記                 |
| 9日で終わらない       | 中   | Week 3 の Day 10（公開準備）から圧縮可能。分析切り口を4→3本に減らす逃げ道も用意        |

---

## 6. 完成の定義（Definition of Done）

公開時点で次の全項目が満たされていること。

- 公開URL（GitHub Pages）が存在し、リンクをクリックして閲覧できる
- ダッシュボード上で最低3種類のフィルター（カテゴリ／価格帯／自治体）が動作する
- フィルター変更で、KPIカード・散布図・ヒートマップ・テーブルが2秒以内に更新される
- About ページにデータソース（楽天API・総務省）、手法、免責事項、楽天規約遵守の明記がある
- README に「セットアップ手順・データ取得コマンド・楽天APIの規約上の注意」が書かれている
- リポジトリが Public で、`.env`（APIキー）はコミットされていない
- LinkedIn または個人ポートフォリオから当サイトへのリンクが設置されている

---

## 7. 第1作との関係・流用ポイント

第1作（e-Stat 人口予測）から流用できる資産。

- **API クライアントの設計パターン**: requests + tenacity + SQLite キャッシュ
- **環境変数管理**: `.env`、`config/settings.py` の構造
- **可視化基盤**: Plotly のラッパー関数、CSS の基本テーマ
- **GitHub Pages デプロイ手順**: そのまま再利用
- **README テンプレート**: 構成を踏襲

これにより第2作の実装は **第1作より2〜3割短縮** できる見込み。

---

## 8. 次のアクション

着手にあたっての最初の3ステップ。

1. **楽天アプリケーション ID の取得**（[https://webservice.rakuten.co.jp/](https://webservice.rakuten.co.jp/)、所要10分）
2. **総務省「現況調査結果」CSV のダウンロード**（最新年度版）
3. **GitHub リポジトリの作成**（推奨名: `furusato-nozei-trends`、Public）

---

*本計画書は実装の進捗に応じて随時更新する。*
