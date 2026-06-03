"""スキーマ情報ツールのモックテスト."""

import pandas as pd
from pytest_mock import MockerFixture

from mykeibadb_mcp_server.server import (
    get_column_examples,
    get_sql_generation_prompt,
    get_table_info,
    get_table_sample_data,
    list_tables,
)

# 正常系: list_tables


def test_list_tables_returns_63_tables() -> None:
    """list_tablesが63テーブルを返す."""
    result = list_tables()

    assert result["total"] == 63
    assert len(result["tables"]) == 63
    assert "RACE_SHOSAI" in result["tables"]
    assert "UMAGOTO_RACE_JOHO" in result["tables"]


def test_list_tables_includes_descriptions() -> None:
    """各テーブルに説明文字列が含まれる."""
    result = list_tables()

    for table_name, description in result["tables"].items():
        assert isinstance(description, str), f"{table_name} の説明が文字列でない"


# 正常系: get_table_info


def test_get_table_info_returns_column_list(mocker: MockerFixture) -> None:
    """get_table_infoがカラム一覧を返す."""
    df = pd.DataFrame({
        "column_name": ["race_code", "kaisai_nen", "grade_code"],
        "data_type": ["character", "character", "character"],
        "character_maximum_length": [12, 4, 1],
        "is_nullable": ["NO", "NO", "YES"],
    })
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.return_value = df
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = get_table_info("RACE_SHOSAI")

    assert result["success"] is True
    assert result["table_name"] == "RACE_SHOSAI"
    assert result["column_count"] == 3
    col_names = [col["name"] for col in result["columns"]]
    assert "RACE_CODE" in col_names


def test_get_table_info_includes_column_notes(mocker: MockerFixture) -> None:
    """column_notesが含まれる."""
    df = pd.DataFrame({
        "column_name": ["grade_code"],
        "data_type": ["character"],
        "character_maximum_length": [1],
        "is_nullable": ["YES"],
    })
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.return_value = df
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = get_table_info("RACE_SHOSAI")

    grade_col = next(c for c in result["columns"] if c["name"] == "GRADE_CODE")
    assert "GI" in grade_col["note"]


# 正常系: get_sql_generation_prompt


def test_get_sql_generation_prompt_contains_schema_info() -> None:
    """プロンプトにスキーマ情報が含まれる."""
    result = get_sql_generation_prompt("G1の勝率を騎手別に集計して")

    assert "query" in result
    assert "tables" in result
    assert "key_codes" in result
    assert "encoding_notes" in result
    assert len(result["tables"]) == 63


def test_get_sql_generation_prompt_contains_tracen_kubun() -> None:
    """TRACEN_KUBUNコード表が含まれる."""
    result = get_sql_generation_prompt("調教データを取得して")

    tracen = result["key_codes"]["tracen_kubun（トレセン）"]
    assert tracen["0"] == "美浦"
    assert tracen["1"] == "栗東"


# 正常系: get_table_sample_data


def test_get_table_sample_data_returns_rows(mocker: MockerFixture) -> None:
    """get_table_sample_dataがサンプル行を返す."""
    df = pd.DataFrame({
        "race_code": ["202501010101", "202501010102"],
        "grade_code": ["A", "B"],
    })
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.return_value = df
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = get_table_sample_data("RACE_SHOSAI", num_rows=2)

    assert result["success"] is True
    assert result["rows"] == 2
    assert "race_code" in result["columns"]


# 正常系: get_column_examples


def test_get_column_examples_returns_distinct_values(mocker: MockerFixture) -> None:
    """get_column_examplesがDISTINCT値を返す."""
    df = pd.DataFrame({"grade_code": ["A", "B", "C"]})
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.return_value = df
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = get_column_examples("RACE_SHOSAI", "GRADE_CODE", limit=10)

    assert result["success"] is True
    assert result["count"] == 3
    assert "A" in result["examples"]


# 準正常系: get_table_info

def test_get_table_info_returns_error_on_db_failure(mocker: MockerFixture) -> None:
    """DBエラー時にsuccessFalseが返される."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = get_table_info("RACE_SHOSAI")

    assert result["success"] is False
    assert "error" in result


# 準正常系: get_table_sample_data

def test_get_table_sample_data_returns_error_on_db_failure(mocker: MockerFixture) -> None:
    """DBエラー時にsuccessFalseが返される."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = get_table_sample_data("RACE_SHOSAI")

    assert result["success"] is False
    assert "error" in result
