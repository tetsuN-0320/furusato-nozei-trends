"""総務省「ふるさと納税に関する現況調査結果」CSVローダー。

CSVの構造:
- 行0: 空行
- 行1: 団体名, NaN, 平成20年度, NaN, 平成21年度, ... 令和４年度, NaN
- 行2: 空行
- 行3: NaN, NaN, 金額, 件数, 金額, 件数, ...（各年度の列ヘッダー）
- 行4以降: 都道府県名, 市区町村名, 金額, 件数, ...（データ行）

列構成（0始まり）:
- col 0: 都道府県名
- col 1: 市区町村名
- col 2,3: 平成20年度 金額・件数
- col 4,5: 平成21年度 金額・件数
- ...
- col 30,31: 令和４年度 金額・件数（最新年度）
"""

from pathlib import Path

import pandas as pd

from src.utils.logger import logger

# 最新年度（令和４年度）の列インデックス
# col2=H20金額, col3=H20件数, ... col30=R4金額, col31=R4件数
LATEST_YEAR_LABEL = "令和４年度"
LATEST_AMOUNT_COL = 30   # 金額（千円）
LATEST_COUNT_COL = 31    # 件数


def load_soumu_csv(csv_path: Path) -> pd.DataFrame:
    """総務省の現況調査CSVを読み込んでDataFrameを返す。

    Args:
        csv_path: CSVファイルのパス（`data/raw/soumu_donations.csv`）。

    Returns:
        以下の列を持つ DataFrame:
            - 都道府県名: str
            - 市区町村名: str
            - 受入額_合計: int（千円単位、令和４年度）
            - 受入件数: int（令和４年度）

    Raises:
        FileNotFoundError: CSVファイルが存在しない場合。
    """
    if not csv_path.exists():
        raise FileNotFoundError(
            f"総務省CSVが見つかりません: {csv_path}\n"
            "https://www.soumu.go.jp/main_sosiki/jichi_zeisei/czaisei/czaisei_seido/furusato/archive/"
            " からダウンロードしてください。"
        )

    df_raw = pd.read_csv(csv_path, encoding="utf-8", header=None)
    logger.info(f"CSVロード: {len(df_raw)} 行 × {len(df_raw.columns)} 列")

    # データ行はrow4以降（row0-3はヘッダー）
    df = df_raw.iloc[4:].copy()
    df = df.reset_index(drop=True)

    # 必要な列だけ取り出してリネーム
    df = df[[0, 1, LATEST_AMOUNT_COL, LATEST_COUNT_COL]].copy()
    df.columns = ["都道府県名", "市区町村名", "受入額_合計", "受入件数"]

    # 空行・不要行を除去
    df = df.dropna(subset=["都道府県名"])
    df = df[df["都道府県名"].astype(str).str.strip() != ""]

    # 都道府県合計行（市区町村名がNaN）を除去
    df = df.dropna(subset=["市区町村名"])
    df = df[df["市区町村名"].astype(str).str.strip() != ""]

    # 数値変換（カンマ区切り・ハイフン対応）
    for col in ["受入額_合計", "受入件数"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", "")
            .str.replace("－", "0")
            .str.replace("-", "0")
            .str.strip()
            .pipe(pd.to_numeric, errors="coerce")
            .fillna(0)
            .astype(int)
        )

    df = df.reset_index(drop=True)
    logger.info(
        f"総務省データ読み込み完了 ({LATEST_YEAR_LABEL}): {len(df):,} 自治体"
    )
    return df
