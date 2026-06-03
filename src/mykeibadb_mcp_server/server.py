"""mykeibadb MCP Server."""

import json
import os
import re
import sys
from collections.abc import Callable
from datetime import date
from typing import Any, cast

import pandas as pd
from mcp.server.fastmcp import FastMCP
from mykeibadb.code_converter import (
    convert_babajotai_code,
    convert_grade_code,
    convert_hinshu_code,
    convert_keibajo_code,
    convert_kyakushitsu_hantei_code,
    convert_seibetsu_code,
    convert_tenko_code,
    convert_track_code,
)
from mykeibadb.config import ConfigManager
from mykeibadb.connection import ConnectionManager
from mykeibadb.exceptions import MykeibaDBConnectionError, MykeibaDBError
from mykeibadb.tables import TableAccessor

from mykeibadb_mcp_server.guard import validate_select_only
from mykeibadb_mcp_server.schema.code_descriptions import (
    BABAJOTAI_CODE,
    GRADE_CODE,
    KEIBAJO_CODE,
    SEIBETSU_CODE,
    TENKO_CODE,
    TRACEN_KUBUN,
    TRACK_CODE,
)
from mykeibadb_mcp_server.schema.table_descriptions import TABLE_DESCRIPTIONS

mcp = FastMCP("mykeibadb MCP Server")

_conn_manager: ConnectionManager | None = None

_CODE_CONVERTERS: dict[str, Callable[[str], str]] = {
    "keibajo_code": convert_keibajo_code,
    "grade_code": convert_grade_code,
    "track_code": convert_track_code,
    "babajotai_code": convert_babajotai_code,
    "tenko_code": convert_tenko_code,
    "hinshu_code": convert_hinshu_code,
    "seibetsu_code": convert_seibetsu_code,
    "kyakushitsu_hantei_code": convert_kyakushitsu_hantei_code,
}

_MAX_QUERY_ROWS = 200


@mcp.tool()
def execute_query(sql_query: str) -> dict[str, Any]:
    """任意の SELECT 文を実行してデータを取得する。

    Args:
        sql_query (str): 実行するSELECT文

    Returns:
        dict: 実行結果。success=True時はrows/columns/data/noteを含む。
              success=False時はerrorを含む。
    """
    try:
        validate_select_only(sql_query)
        manager = _get_connection_manager()
        df = manager.fetch_dataframe(sql_query)

        note = None
        if len(df) > _MAX_QUERY_ROWS:
            note = f"結果が {len(df)} 行あるため、先頭 {_MAX_QUERY_ROWS} 行のみ返しています"
            df = df.head(_MAX_QUERY_ROWS)

        return {
            "success": True,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": _df_to_records(df),
            "note": note,
        }
    except (ValueError, MykeibaDBError) as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_table_data(
    table_name: str,
    filters: dict[str, str | int | list[str | int]] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    convert_codes: bool = True,
) -> dict[str, Any]:
    """テーブル名・フィルタ・期間を指定してデータを取得する。

    Args:
        table_name (str): テーブル名（例: "RACE_SHOSAI"）
        filters (dict | None): フィルタ条件。値がリストの場合はIN句として処理
        start_date (str | None): 開始日（ISO形式: "YYYY-MM-DD"）
        end_date (str | None): 終了日（ISO形式: "YYYY-MM-DD"）
        convert_codes (bool): コード値を名称に変換するかどうか

    Returns:
        dict: rows/columns/dataを含む取得結果
    """
    try:
        manager = _get_connection_manager()
        accessor = TableAccessor(manager)

        start = date.fromisoformat(start_date) if start_date else None
        end = date.fromisoformat(end_date) if end_date else None

        if start or end:
            df = accessor.get_table_data_with_period(table_name, filters, start, end)
        else:
            df = accessor.get_table_data(table_name, filters)

        if convert_codes:
            df = _apply_code_conversion(df)

        return {
            "success": True,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": _df_to_records(df),
        }
    except (ValueError, MykeibaDBError) as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_tables() -> dict[str, Any]:
    """利用可能な63テーブルの一覧と日本語説明を返す。

    Returns:
        dict: tables（テーブル名→説明の辞書）とtotal（テーブル数）を含む辞書
    """
    tables = {
        name: info.get("description", "")
        for name, info in TABLE_DESCRIPTIONS.items()
    }
    return {"tables": tables, "total": len(tables)}


@mcp.tool()
def get_table_info(table_name: str) -> dict[str, Any]:
    """指定テーブルのカラム定義・日本語説明・エンコーディング情報を返す。

    Args:
        table_name (str): テーブル名（例: "RACE_SHOSAI"）

    Returns:
        dict: テーブル説明・主キー・カラム一覧・column_notesを含む辞書
    """
    try:
        upper_name = table_name.upper()
        if upper_name not in TABLE_DESCRIPTIONS:
            return {"success": False, "error": f"テーブル '{upper_name}' はサポートされていません"}
        manager = _get_connection_manager()
        sql = """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position
        """
        df = manager.fetch_dataframe(sql, params=(upper_name.lower(),))

        desc_entry = TABLE_DESCRIPTIONS.get(upper_name, {})
        column_notes: dict[str, str] = desc_entry.get("column_notes", {})

        columns = []
        for _, row in df.iterrows():
            col_name = str(row["column_name"]).upper()
            columns.append({
                "name": col_name,
                "type": row["data_type"],
                "nullable": row["is_nullable"] == "YES",
                "note": column_notes.get(col_name, ""),
            })

        return {
            "success": True,
            "table_name": upper_name,
            "description": desc_entry.get("description", ""),
            "primary_key": desc_entry.get("primary_key", ""),
            "columns": columns,
            "column_count": len(columns),
        }
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_sql_generation_prompt(query_text: str) -> dict[str, Any]:
    """自然言語クエリをSQLに変換するためのプロンプト情報を返す。

    Args:
        query_text (str): 分析したい内容の自然言語クエリ

    Returns:
        dict: スキーマ情報・コード表・エンコーディング注意事項を含む辞書
    """
    table_summary = {
        name: info.get("description", "")
        for name, info in TABLE_DESCRIPTIONS.items()
    }

    encoding_notes = (
        "## エンコーディング共通パターン\n"
        "- タイム系カラム（TIME_GOKEI_*, LAPTIME_*, KOHAN_3F等）: "
        "整数文字列、単位は0.1秒。0000/9999はセンチネル値（無効）。"
        "比較時は CAST(col AS INTEGER) <= 825 のように整数キャストして×10の閾値で比較。\n"
        "- 走破タイム（SOHA_TIME等）: MSSS形式（例: '2315'=2分31秒5）。0000=未計測。\n"
        "- 単勝オッズ（TANSHO_ODDS）: 整数文字列、単位は0.1倍（例: '152'=15.2倍）。\n"
        "- 着順（KAKUTEI_CHAKUJUN）: 2桁ゼロ埋め文字列（例: '01'=1着）。0=取消等。\n"
        "- 開催年（KAISAI_NEN）: 4桁文字列。開催月日（KAISAI_GAPPI）: mmdd形式。\n"
        "- 血統登録番号（KETTO_TOROKU_BANGO）: 10桁文字列、先頭4桁が生年。\n"
        "- TRACEN_KUBUN: '0'=美浦、'1'=栗東。\n"
        "- GRADE_CODEが空白の場合は'_'として格納（一般競走）。\n"
    )

    return {
        "query": query_text,
        "tables": table_summary,
        "key_codes": {
            "keibajo_code（競馬場）": KEIBAJO_CODE,
            "grade_code（グレード）": GRADE_CODE,
            "track_code（トラック）": TRACK_CODE,
            "tenko_code（天候）": TENKO_CODE,
            "babajotai_code（馬場状態）": BABAJOTAI_CODE,
            "seibetsu_code（性別）": SEIBETSU_CODE,
            "tracen_kubun（トレセン）": TRACEN_KUBUN,
        },
        "encoding_notes": encoding_notes,
        "main_tables": {
            "RACE_SHOSAI": "レース詳細（グレード・距離・馬場・天候）",
            "UMAGOTO_RACE_JOHO": "馬毎レース情報（着順・タイム・騎手・人気・体重）",
            "WOODCHIP_CHOKYO": "ウッドチップ調教データ",
            "HANRO_CHOKYO": "坂路調教データ",
            "KYOSOBA_MASTER2": "競走馬マスタ（馬名・性別・血統番号）",
            "KISHU_MASTER": "騎手マスタ",
        },
    }


@mcp.tool()
def get_table_sample_data(table_name: str, num_rows: int = 5) -> dict[str, Any]:
    """指定テーブルのサンプルデータを返す。

    Args:
        table_name (str): テーブル名（例: "RACE_SHOSAI"）
        num_rows (int): 取得行数（デフォルト5）

    Returns:
        dict: サンプルデータのrows/columns/dataを含む辞書
    """
    try:
        upper_name = table_name.upper()
        if upper_name not in TABLE_DESCRIPTIONS:
            return {"success": False, "error": f"テーブル '{upper_name}' はサポートされていません"}
        clamped_rows = max(1, min(num_rows, _MAX_QUERY_ROWS))
        manager = _get_connection_manager()
        df = manager.fetch_dataframe(
            f"SELECT * FROM {upper_name.lower()} LIMIT %s",
            params=(clamped_rows,),
        )
        return {
            "success": True,
            "table_name": upper_name,
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": _df_to_records(df),
        }
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_column_examples(table_name: str, column_name: str, limit: int = 10) -> dict[str, Any]:
    """指定カラムの実際の値例（DISTINCT）を返す。

    Args:
        table_name (str): テーブル名（例: "RACE_SHOSAI"）
        column_name (str): カラム名（例: "GRADE_CODE"）
        limit (int): 取得件数（デフォルト10）

    Returns:
        dict: カラムの値例リストを含む辞書
    """
    try:
        upper_name = table_name.upper()
        if upper_name not in TABLE_DESCRIPTIONS:
            return {"success": False, "error": f"テーブル '{upper_name}' はサポートされていません"}
        if not re.fullmatch(r"[A-Za-z0-9_]+", column_name):
            return {"success": False, "error": "column_name は英数字とアンダースコアのみ使用可能です"}
        clamped_limit = max(1, min(limit, _MAX_QUERY_ROWS))
        col_lower = column_name.lower()
        tbl_lower = upper_name.lower()
        sql = f"SELECT DISTINCT {col_lower} FROM {tbl_lower} ORDER BY {col_lower} LIMIT %s"
        manager = _get_connection_manager()
        df = manager.fetch_dataframe(sql, params=(clamped_limit,))
        values = df[col_lower].tolist() if col_lower in df.columns else []
        return {
            "success": True,
            "table_name": upper_name,
            "column_name": column_name.upper(),
            "examples": values,
            "count": len(values),
        }
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


@mcp.resource("schema://tables")
def schema_tables_resource() -> str:
    """63テーブル一覧と説明（接続時に自動ロード）。"""
    tables = [
        {"table_name": name, "description": info.get("description", "")}
        for name, info in TABLE_DESCRIPTIONS.items()
    ]
    return json.dumps({"tables": tables, "total": len(tables)}, ensure_ascii=False)


@mcp.resource("schema://table/{table_name}")
def schema_table_detail_resource(table_name: str) -> str:
    """個別テーブルの説明・主キー・column_notes。

    Args:
        table_name: テーブル名

    Returns:
        テーブル詳細情報のJSON文字列
    """
    upper = table_name.upper()
    if upper not in TABLE_DESCRIPTIONS:
        return json.dumps({"success": False, "error": f"テーブル '{upper}' はサポートされていません"})
    info = TABLE_DESCRIPTIONS[upper]
    return json.dumps(
        {
            "success": True,
            "table_name": upper,
            "description": info.get("description", ""),
            "primary_key": info.get("primary_key", ""),
            "date_column": info.get("date_column", {}),
            "column_notes": info.get("column_notes", {}),
        },
        ensure_ascii=False,
    )


@mcp.resource("codes://keibajo")
def codes_keibajo_resource() -> str:
    """競馬場コード表。"""
    return json.dumps(KEIBAJO_CODE, ensure_ascii=False)


@mcp.resource("codes://grade")
def codes_grade_resource() -> str:
    """グレードコード表（GI/GII/GIII等）。"""
    return json.dumps(GRADE_CODE, ensure_ascii=False)


@mcp.resource("codes://track")
def codes_track_resource() -> str:
    """トラックコード表（芝/ダート等）。"""
    return json.dumps(TRACK_CODE, ensure_ascii=False)


@mcp.resource("codes://tracen")
def codes_tracen_resource() -> str:
    """トレセン区分コード表（0=美浦/1=栗東）。"""
    return json.dumps(TRACEN_KUBUN, ensure_ascii=False)


@mcp.resource("examples://queries")
def query_examples_resource() -> str:
    """代表的なSQLクエリ例集。"""
    examples = [
        {
            "title": "G1レース一覧（2025年）",
            "sql": (
                "SELECT race_code, race_name, kaisai_nen, kaisai_gappi, keibajo_code "
                "FROM race_shosai "
                "WHERE kaisai_nen = '2025' AND grade_code = 'A' "
                "ORDER BY kaisai_gappi"
            ),
        },
        {
            "title": "武豊騎手の直近成績",
            "sql": (
                "SELECT u.race_code, u.kakutei_chakujun, u.kishu_code, r.race_name "
                "FROM umagoto_race_joho u "
                "JOIN race_shosai r ON u.race_code = r.race_code "
                "WHERE u.kishu_code = '00666' "
                "ORDER BY r.kaisai_nen DESC, r.kaisai_gappi DESC LIMIT 20"
            ),
        },
        {
            "title": "単勝人気1番の複勝率集計",
            "sql": (
                "SELECT COUNT(*) AS total,"
                " SUM(CASE WHEN CAST(kakutei_chakujun AS INTEGER) <= 3 THEN 1 ELSE 0 END)"
                " AS fukusho,"
                " ROUND(100.0 * SUM(CASE WHEN CAST(kakutei_chakujun AS INTEGER) <= 3"
                " THEN 1 ELSE 0 END) / COUNT(*), 1) AS fukusho_rate"
                " FROM umagoto_race_joho"
                " WHERE ninki_juni = '01' AND kakutei_chakujun != '00'"
            ),
        },
        {
            "title": "ウッドチップ好時計馬の抽出（6F 82秒台以下）",
            "sql": (
                "SELECT ketto_toroku_bango, chokyo_nengappi, time_gokei_6furlong "
                "FROM woodchip_chokyo "
                "WHERE time_gokei_6furlong NOT IN ('0000', '9999') "
                "AND CAST(time_gokei_6furlong AS INTEGER) <= 825 "
                "ORDER BY CAST(time_gokei_6furlong AS INTEGER) LIMIT 20"
            ),
        },
    ]
    return json.dumps({"examples": examples}, ensure_ascii=False)


def _get_connection_manager() -> ConnectionManager:
    global _conn_manager
    if _conn_manager is None:
        config = ConfigManager.from_env()
        _conn_manager = ConnectionManager(config)
    return _conn_manager


def _apply_code_conversion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col, converter in _CODE_CONVERTERS.items():
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v, c=converter: c(str(v).strip()) if pd.notna(v) else v
            )
    return df


def _df_to_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    records = cast(list[dict[str, Any]], df.to_dict(orient="records"))
    return [{k: (None if pd.isna(v) else v) for k, v in row.items()} for row in records]


def _check_db_connection() -> None:
    try:
        manager = _get_connection_manager()
        manager.execute_query("SELECT 1")
    except MykeibaDBConnectionError as e:
        raise RuntimeError(f"DB接続に失敗しました: {e}") from e


if __name__ == "__main__":
    _check_db_connection()
    if "--sse" in sys.argv:
        import uvicorn

        port = int(os.getenv("MCP_PORT", "8000"))
        host = os.getenv("MCP_HOST", "127.0.0.1")
        uvicorn.run(mcp.sse_app(), host=host, port=port)
    else:
        mcp.run()
