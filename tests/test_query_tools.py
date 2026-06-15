"""execute_query / get_table_data ツールのモックテスト."""

import pandas as pd
from mykeibadb.exceptions import QueryExecutionError
from pytest_mock import MockerFixture

from mykeibadb_mcp_server.server import execute_query, get_table_data, tool_analyze_chakudo

# 正常系: execute_query


def test_execute_query_returns_success(mocker: MockerFixture) -> None:
    """有効なSELECT文でsuccessレスポンスが返される."""
    df = pd.DataFrame({"race_code": ["202501010101"], "race_name": ["テストレース"]})
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.return_value = df
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = execute_query("SELECT * FROM race_shosai")

    assert result["success"] is True
    assert result["rows"] == 1
    assert result["columns"] == ["race_code", "race_name"]
    assert result["data"] == [{"race_code": "202501010101", "race_name": "テストレース"}]
    assert result["note"] is None


def test_execute_query_truncates_at_200_rows(mocker: MockerFixture) -> None:
    """200行超の場合は先頭200行のみ返してnoteを設定する."""
    df = pd.DataFrame({"id": range(250)})
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.return_value = df
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = execute_query("SELECT id FROM some_table")

    assert result["success"] is True
    assert result["rows"] == 200
    assert result["note"] is not None


def test_execute_query_no_truncation_at_200_rows(mocker: MockerFixture) -> None:
    """ちょうど200行の場合はnoteがNoneになる."""
    df = pd.DataFrame({"id": range(200)})
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.return_value = df
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = execute_query("SELECT id FROM some_table")

    assert result["success"] is True
    assert result["rows"] == 200
    assert result["note"] is None


# 準正常系: execute_query

def test_execute_query_returns_error_for_dangerous_sql() -> None:
    """危険なSQLでsuccessFalseが返される."""
    result = execute_query("DROP TABLE race_shosai")

    assert result["success"] is False
    assert "error" in result


def test_execute_query_returns_error_for_db_error(mocker: MockerFixture) -> None:
    """DB実行エラーでsuccessFalseが返される."""
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = execute_query("SELECT * FROM race_shosai")

    assert result["success"] is False
    assert "error" in result


# 正常系: get_table_data

def test_get_table_data_returns_success(mocker: MockerFixture) -> None:
    """有効なテーブル名でデータが返される."""
    df = pd.DataFrame({"race_code": ["202501010101"], "grade_code": ["A"]})
    mock_manager = mocker.MagicMock()
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)
    mock_accessor = mocker.MagicMock()
    mock_accessor.get_table_data.return_value = df
    mocker.patch("mykeibadb_mcp_server.server.TableAccessor", return_value=mock_accessor)

    result = get_table_data("RACE_SHOSAI", convert_codes=False)

    assert result["success"] is True
    assert result["rows"] == 1
    assert "race_code" in result["columns"]
    mock_accessor.get_table_data.assert_called_once_with("RACE_SHOSAI", None)


def test_get_table_data_with_filters(mocker: MockerFixture) -> None:
    """フィルタ条件がTableAccessorに渡される."""
    df = pd.DataFrame({"race_code": ["202501010101"]})
    mock_manager = mocker.MagicMock()
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)
    mock_accessor = mocker.MagicMock()
    mock_accessor.get_table_data.return_value = df
    mocker.patch("mykeibadb_mcp_server.server.TableAccessor", return_value=mock_accessor)

    filters = {"GRADE_CODE": "A"}
    result = get_table_data("RACE_SHOSAI", filters=filters, convert_codes=False)

    assert result["success"] is True
    mock_accessor.get_table_data.assert_called_once_with("RACE_SHOSAI", filters)


def test_get_table_data_with_date_range_uses_period_method(mocker: MockerFixture) -> None:
    """期間指定時はget_table_data_with_periodが呼ばれる."""
    df = pd.DataFrame({"race_code": ["202501010101"]})
    mock_manager = mocker.MagicMock()
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)
    mock_accessor = mocker.MagicMock()
    mock_accessor.get_table_data_with_period.return_value = df
    mocker.patch("mykeibadb_mcp_server.server.TableAccessor", return_value=mock_accessor)

    result = get_table_data("RACE_SHOSAI", start_date="2025-01-01", convert_codes=False)

    assert result["success"] is True
    mock_accessor.get_table_data_with_period.assert_called_once()


# 正常系: tool_analyze_chakudo


def test_tool_analyze_chakudo_returns_success(mocker: MockerFixture) -> None:
    """filters/condition/group_byのJSONからグループ別着度数集計が返される."""
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.side_effect = [
        pd.DataFrame({
            "ketto_toroku_bango": ["2020100001"],
            "race_code": ["202001050101"],
            "umaban": ["01"],
            "group_label": ["1"],
        }),
        pd.DataFrame({
            "group_label": ["1"],
            "total": [100],
            "wins": [20],
            "second": [15],
            "third": [12],
            "chakugai": [53],
            "tansho_payout_sum": [8500],
            "fukusho_payout_sum": [7800],
        }),
    ]
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = tool_analyze_chakudo(
        filters=[{"type": "subject", "subject": "kishu", "name": "武豊"}],
        condition={"keibajo_codes": ["05"], "year_from": "2020"},
        group_by={"kind": "race_col", "column": "u.wakuban"},
    )

    assert result["success"] is True
    assert result["count"] == 1
    row = result["results"][0]
    assert row["total"] == 100
    assert row["wins"] == 20
    assert row["win_rate"] == 20.0


# 準正常系: tool_analyze_chakudo


def test_tool_analyze_chakudo_returns_error_on_db_failure(mocker: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    mock_manager = mocker.MagicMock()
    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")
    mocker.patch("mykeibadb_mcp_server.server._get_connection_manager", return_value=mock_manager)

    result = tool_analyze_chakudo()

    assert result["success"] is False
    assert "error" in result
