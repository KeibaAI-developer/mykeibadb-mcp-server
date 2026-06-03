"""mykeibadb MCP Server."""

import math
import os
import sys
from collections.abc import Callable
from datetime import date
from typing import Any

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
    records = df.to_dict(orient="records")
    return [
        {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items()}
        for row in records
    ]


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
