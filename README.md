# ふるさと納税 人気返礼品トレンド分析

楽天ウェブサービス（楽天ふるさと納税API）と総務省「ふるさと納税に関する現況調査」を組み合わせた、返礼品市場のインタラクティブ分析ダッシュボード。

**公開URL**: （GitHub Pages 公開後に記載）

---

## 分析の4つの切り口

1. **カテゴリ別の人気構造** — 食品（肉/魚/果物）、家電、旅行券、日用品の構成比とレビュー評価
2. **価格帯戦略の解析** — 1万円・3万円・5万円・10万円の価格帯別の売れ筋ゾーン
3. **還元率の推定** — 寄付額÷市場相場価格でコスパランキング作成
4. **自治体タイプ別の成功パターン** — 特産品依存型 vs 家電・汎用品型を K-means で分類

---

## セットアップ

### 前提条件

- Python 3.11 以上
- 楽天ウェブサービス アプリケーションID（[無料登録](https://webservice.rakuten.co.jp/)）

### インストール

```bash
# 仮想環境を作成・有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存ライブラリをインストール
pip install -r requirements.txt

# 環境変数を設定
cp .env.example .env
# .env を開き RAKUTEN_APP_ID に取得したIDを記入
```

### データ取得

```bash
# 楽天APIからデータ一括取得（初回は30〜60分かかる場合あり）
python scripts/fetch_data.py

# テスト用（各キーワード最大3ページのみ）
python scripts/fetch_data.py --max-pages 3
```

### 総務省データの準備

1. [総務省ふるさと納税ポータル](https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/) から最新年度の「現況調査結果」CSVをダウンロード
2. `data/raw/soumu_donations.csv` として保存

### 分析パイプライン実行

```bash
# カテゴリ別・価格帯別・自治体タイプ別の集計データを生成
python scripts/run_analysis.py
```

### ダッシュボード用 JSON 生成

```bash
# web/static/data/ にフロントエンド用JSONを書き出す
python scripts/build_site.py
```

### ローカル確認

```bash
cd docs && python -m http.server 8765
# → http://localhost:8765/ をブラウザで開く
```

---

## ディレクトリ構成

```
furusato-nozei-trends/
├── config/          # 設定ファイル、カテゴリマッピングYAML
├── data/            # データファイル（.gitignore 対象）
├── notebooks/       # 分析Jupyter Notebook
├── src/             # Pythonソースコード
├── web/             # ダッシュボード（HTML/CSS/JS）
├── tests/           # テストコード
└── scripts/         # CLIスクリプト
```

---

## データについての注意事項

- 楽天ウェブサービスの利用規約に基づき、**取得した商品データは集計・統計値のみに使用**しています
- 個別商品データの再配布・個別表示は行っていません
- 詳細は `web/about.html` をご参照ください

---

## テスト実行

```bash
# 通常テスト（API モック使用）
pytest

# 統合テスト（実際のAPIアクセスあり）
pytest -m integration
```

---

## ライセンス

MIT License

データソース:
- 楽天ウェブサービス（楽天株式会社）— 楽天ウェブサービス規約に準拠
- 総務省「ふるさと納税に関する現況調査結果」— CC BY 4.0
