"""集計API（high_level_api）のモックテスト."""

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from mykeibadb_mcp_server.high_level_api import (
    analyze_kishu_seiseki,
    analyze_ninki_seiseki,
    analyze_sire_seiseki,
    analyze_waku_seiseki,
    get_uma_rekisen,
)


@pytest.fixture
def mock_manager(mocker: MockerFixture):  # type: ignore[no-untyped-def]
    """モックConnectionManager."""
    return mocker.MagicMock()


# 正常系: analyze_ninki_seiseki


def test_analyze_ninki_seiseki_returns_success(mock_manager: MockerFixture) -> None:
    """analyze_ninki_seisekiがsuccess=Trueを返す."""
    df = pd.DataFrame({"total": [100], "wins": [20], "fukusho": [45]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_ninki_seiseki(mock_manager, ninki=1)

    assert result["success"] is True
    assert result["total"] == 100
    assert result["wins"] == 20
    assert result["win_rate"] == 20.0
    assert result["fukusho"] == 45
    assert result["fukusho_rate"] == 45.0
    assert result["ninki"] == 1


def test_analyze_ninki_seiseki_with_filters(mock_manager: MockerFixture) -> None:
    """フィルタパラメータが指定可能."""
    df = pd.DataFrame({"total": [50], "wins": [10], "fukusho": [20]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_ninki_seiseki(
        mock_manager, ninki=2, keibajo="05", grade="A", year_from="2020", kyori=2000
    )

    assert result["success"] is True
    assert result["total"] == 50


def test_analyze_ninki_seiseki_zero_total_returns_zero_rate(mock_manager: MockerFixture) -> None:
    """出走数0のときに勝率0.0が返る."""
    df = pd.DataFrame({"total": [0], "wins": [0], "fukusho": [0]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_ninki_seiseki(mock_manager)

    assert result["win_rate"] == 0.0
    assert result["fukusho_rate"] == 0.0


# 正常系: analyze_kishu_seiseki


def test_analyze_kishu_seiseki_returns_success(mock_manager: MockerFixture) -> None:
    """analyze_kishu_seisekiがsuccess=Trueを返す."""
    df = pd.DataFrame({
        "kishumei": ["武豊"],
        "total": [500],
        "wins": [100],
        "fukusho": [200],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_kishu_seiseki(mock_manager, kishu_name="武豊")

    assert result["success"] is True
    assert result["count"] == 1
    row = result["results"][0]
    assert row["kishumei"] == "武豊"
    assert row["win_rate"] == 20.0


def test_analyze_kishu_seiseki_empty_result(mock_manager: MockerFixture) -> None:
    """マッチなし時にcountが0."""
    df = pd.DataFrame({"kishu_mei": [], "total": [], "wins": [], "fukusho": []})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_kishu_seiseki(mock_manager, kishu_name="存在しない騎手")

    assert result["success"] is True
    assert result["count"] == 0


# 正常系: analyze_sire_seiseki


def test_analyze_sire_seiseki_returns_success(mock_manager: MockerFixture) -> None:
    """analyze_sire_seisekiがsuccess=Trueを返す."""
    df = pd.DataFrame({
        "sire_name": ["ディープインパクト"],
        "total": [1000],
        "wins": [200],
        "fukusho": [400],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_sire_seiseki(mock_manager, sire_name="ディープインパクト")

    assert result["success"] is True
    assert result["count"] == 1
    row = result["results"][0]
    assert row["sire_name"] == "ディープインパクト"
    assert row["win_rate"] == 20.0


# 正常系: get_uma_rekisen


def test_get_uma_rekisen_returns_success(mock_manager: MockerFixture) -> None:
    """get_uma_rekisenがsuccess=Trueを返す."""
    df = pd.DataFrame({
        "bamei": ["アーモンドアイ"],
        "kaisai_nen": ["2018"],
        "kaisai_gappi": ["1028"],
        "keibajo_code": ["05"],
        "race_name": ["天皇賞秋"],
        "grade_code": ["A"],
        "kyori": [2000],
        "kakutei_chakujun": ["01"],
        "soha_time": ["1576"],
        "kishumei_ryakusho": ["ルメール"],
        "tansho_ninkijun": ["01"],
        "tansho_odds": ["15"],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = get_uma_rekisen(mock_manager, uma_name="アーモンドアイ")

    assert result["success"] is True
    assert result["count"] == 1
    assert result["results"][0]["bamei"] == "アーモンドアイ"


def test_get_uma_rekisen_with_year_from(mock_manager: MockerFixture) -> None:
    """year_fromフィルタが指定可能."""
    df = pd.DataFrame({
        "bamei": [],
        "kaisai_nen": [],
        "kaisai_gappi": [],
        "keibajo_code": [],
        "race_name": [],
        "grade_code": [],
        "kyori": [],
        "kakutei_chakujun": [],
        "soha_time": [],
        "kishumei_ryakusho": [],
        "tansho_ninkijun": [],
        "tansho_odds": [],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = get_uma_rekisen(mock_manager, uma_name="テスト馬", year_from="2020")

    assert result["success"] is True
    assert result["count"] == 0


# 正常系: analyze_waku_seiseki


def test_analyze_waku_seiseki_returns_success(mock_manager: MockerFixture) -> None:
    """analyze_waku_seisekiがsuccess=Trueを返す."""
    df = pd.DataFrame({
        "wakuban": ["1", "2", "3"],
        "total": [100, 120, 110],
        "wins": [10, 15, 12],
        "fukusho": [25, 30, 28],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_waku_seiseki(mock_manager)

    assert result["success"] is True
    assert result["count"] == 3


def test_analyze_waku_seiseki_with_filters(mock_manager: MockerFixture) -> None:
    """フィルタパラメータが指定可能."""
    df = pd.DataFrame({
        "wakuban": ["1"],
        "total": [50],
        "wins": [8],
        "fukusho": [18],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_waku_seiseki(mock_manager, keibajo="05", kyori=2000, year_from="2020")

    assert result["success"] is True
    assert result["results"][0]["win_rate"] == 16.0


# 正常系: course_kubun / week_in_course フィルタ


def test_analyze_waku_seiseki_with_course_week_filter(mock_manager: MockerFixture) -> None:
    """course_kubunとweek_in_courseを指定するとCTEフィルタが適用される."""
    df = pd.DataFrame({
        "wakuban": ["1"],
        "total": [30],
        "wins": [6],
        "fukusho": [12],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_waku_seiseki(
        mock_manager, keibajo="05", kyori=1600, year_from="2021",
        course_kubun="C", week_in_course=2,
    )

    assert result["success"] is True
    assert result["count"] == 1
    assert result["results"][0]["win_rate"] == 20.0

    call_args = mock_manager.fetch_dataframe.call_args
    sql = call_args[0][0]
    params = call_args[1]["params"]
    assert "cw_target" in sql
    assert "C" in params
    assert 2 in params


def test_analyze_ninki_seiseki_with_course_week_filter(mock_manager: MockerFixture) -> None:
    """course_kubunとweek_in_courseを指定するとCTEフィルタが適用される."""
    df = pd.DataFrame({"total": [80], "wins": [16], "fukusho": [32]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_ninki_seiseki(
        mock_manager, ninki=1, keibajo="05", course_kubun="C", week_in_course=2
    )

    assert result["success"] is True
    assert result["total"] == 80
    assert result["win_rate"] == 20.0

    call_args = mock_manager.fetch_dataframe.call_args
    sql = call_args[0][0]
    params = call_args[1]["params"]
    assert "cw_target" in sql
    assert "C" in params
    assert 2 in params


# 準正常系: DBエラー


def test_analyze_ninki_seiseki_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = analyze_ninki_seiseki(mock_manager)

    assert result["success"] is False
    assert "error" in result


def test_analyze_kishu_seiseki_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = analyze_kishu_seiseki(mock_manager, kishu_name="武豊")

    assert result["success"] is False
    assert "error" in result


def test_get_uma_rekisen_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = get_uma_rekisen(mock_manager, uma_name="テスト馬")

    assert result["success"] is False
    assert "error" in result


def test_analyze_sire_seiseki_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = analyze_sire_seiseki(mock_manager, sire_name="ディープインパクト")

    assert result["success"] is False
    assert "error" in result


def test_analyze_waku_seiseki_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = analyze_waku_seiseki(mock_manager)

    assert result["success"] is False
    assert "error" in result
