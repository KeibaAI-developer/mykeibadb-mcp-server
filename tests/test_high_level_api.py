"""集計API（high_level_api）のモックテスト."""

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from mykeibadb_mcp_server.high_level_api import (
    analyze_chokyo_debut_seiseki,
    analyze_kishu_seiseki,
    analyze_ninki_seiseki,
    analyze_sire_seiseki,
    analyze_waku_seiseki,
    get_uma_chokyo,
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


# 正常系: get_uma_chokyo


def test_get_uma_chokyo_returns_success(mock_manager: MockerFixture) -> None:
    """get_uma_chokyoがsuccess=Trueを返す."""
    horses_df = pd.DataFrame({
        "ketto_toroku_bango": ["2020100001"],
        "bamei": ["テスト馬"],
        "debut_date": ["20220101"],
    })
    wood_df = pd.DataFrame({
        "tracen_kubun": ["1"],
        "chokyo_nengappi": ["20211201"],
        "chokyo_jikoku": ["0700"],
        "time_gokei_6furlong": ["0820"],
        "time_gokei_5furlong": ["0680"],
        "time_gokei_4furlong": ["0540"],
        "laptime_1furlong": ["112"],
        "laptime_2furlong": ["115"],
        "laptime_3furlong": ["118"],
    })
    hanro_df = pd.DataFrame({
        "tracen_kubun": ["1"],
        "chokyo_nengappi": ["20211205"],
        "chokyo_jikoku": ["0630"],
        "time_gokei_4furlong": ["0540"],
        "lap_time_1furlong": ["125"],
        "lap_time_2furlong": ["128"],
        "lap_time_3furlong": ["130"],
        "lap_time_4furlong": ["133"],
    })
    mock_manager.fetch_dataframe.side_effect = [horses_df, wood_df, hanro_df]

    result = get_uma_chokyo(mock_manager, uma_name="テスト馬")

    assert result["success"] is True
    assert result["count"] == 1
    horse = result["results"][0]
    assert horse["bamei"] == "テスト馬"
    assert horse["debut_date"] == "20220101"
    assert horse["wood_count"] == 1
    assert horse["hanro_count"] == 1
    # 日付降順ソートのため坂路（20211205）がウッド（20211201）より先
    assert horse["chokyo"][0]["course_type"] == "坂路"
    assert horse["chokyo"][1]["time_6f"] == "82.0秒"


def test_get_uma_chokyo_horse_not_found(mock_manager: MockerFixture) -> None:
    """馬名マッチなし時にcount=0が返る."""
    mock_manager.fetch_dataframe.return_value = pd.DataFrame({
        "ketto_toroku_bango": pd.Series([], dtype=str),
        "bamei": pd.Series([], dtype=str),
        "debut_date": pd.Series([], dtype=str),
    })

    result = get_uma_chokyo(mock_manager, uma_name="存在しない馬")

    assert result["success"] is True
    assert result["count"] == 0
    assert result["results"] == []


def test_get_uma_chokyo_before_debut_filter(mock_manager: MockerFixture) -> None:
    """before_debut=Trueのときデビュー前フィルタがSQLに適用される."""
    horses_df = pd.DataFrame({
        "ketto_toroku_bango": ["2020100001"],
        "bamei": ["テスト馬"],
        "debut_date": ["20220101"],
    })
    empty_wood = pd.DataFrame({
        "tracen_kubun": pd.Series([], dtype=str),
        "chokyo_nengappi": pd.Series([], dtype=str),
        "chokyo_jikoku": pd.Series([], dtype=str),
        "time_gokei_6furlong": pd.Series([], dtype=str),
        "time_gokei_5furlong": pd.Series([], dtype=str),
        "time_gokei_4furlong": pd.Series([], dtype=str),
        "laptime_1furlong": pd.Series([], dtype=str),
        "laptime_2furlong": pd.Series([], dtype=str),
        "laptime_3furlong": pd.Series([], dtype=str),
    })
    empty_hanro = pd.DataFrame({
        "tracen_kubun": pd.Series([], dtype=str),
        "chokyo_nengappi": pd.Series([], dtype=str),
        "chokyo_jikoku": pd.Series([], dtype=str),
        "time_gokei_4furlong": pd.Series([], dtype=str),
        "lap_time_1furlong": pd.Series([], dtype=str),
        "lap_time_2furlong": pd.Series([], dtype=str),
        "lap_time_3furlong": pd.Series([], dtype=str),
        "lap_time_4furlong": pd.Series([], dtype=str),
    })
    mock_manager.fetch_dataframe.side_effect = [horses_df, empty_wood, empty_hanro]

    result = get_uma_chokyo(mock_manager, uma_name="テスト馬", before_debut=True)

    assert result["success"] is True
    wood_sql = mock_manager.fetch_dataframe.call_args_list[1][0][0]
    assert "chokyo_nengappi < %s" in wood_sql


# 準正常系: get_uma_chokyo


def test_get_uma_chokyo_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = get_uma_chokyo(mock_manager, uma_name="テスト馬")

    assert result["success"] is False
    assert "error" in result


# 正常系: analyze_chokyo_debut_seiseki


def test_analyze_chokyo_debut_seiseki_returns_success(mock_manager: MockerFixture) -> None:
    """analyze_chokyo_debut_seisekiがsuccess=Trueを返す."""
    df = pd.DataFrame({"total": [74], "winners": [37]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_chokyo_debut_seiseki(
        mock_manager,
        debut_date_from="20250607",
        debut_date_to="20260531",
        tracen_kubun="0",
        wood_time_6f_max=825,
        wood_laptime_1f_max=115,
    )

    assert result["success"] is True
    assert result["total"] == 74
    assert result["winners"] == 37
    assert result["win_rate"] == 50.0


def test_analyze_chokyo_debut_seiseki_zero_total_returns_zero_rate(
    mock_manager: MockerFixture,
) -> None:
    """条件を満たす馬が0頭のときwin_rateが0.0になる."""
    df = pd.DataFrame({"total": [0], "winners": [0]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_chokyo_debut_seiseki(
        mock_manager,
        debut_date_from="20250101",
        debut_date_to="20251231",
        wood_time_6f_max=700,
    )

    assert result["success"] is True
    assert result["win_rate"] == 0.0


def test_analyze_chokyo_debut_seiseki_with_both_conditions(mock_manager: MockerFixture) -> None:
    """ウッドと坂路の両条件指定時にINTERSECTが使われる."""
    df = pd.DataFrame({"total": [10], "winners": [5]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_chokyo_debut_seiseki(
        mock_manager,
        debut_date_from="20250101",
        debut_date_to="20251231",
        wood_time_6f_max=825,
        hanro_time_4f_max=540,
    )

    assert result["success"] is True
    sql = mock_manager.fetch_dataframe.call_args[0][0]
    assert "INTERSECT" in sql


def test_analyze_chokyo_debut_seiseki_no_conditions(mock_manager: MockerFixture) -> None:
    """調教条件なしのときdebutした馬全体が集計対象になる."""
    df = pd.DataFrame({"total": [200], "winners": [80]})
    mock_manager.fetch_dataframe.return_value = df

    result = analyze_chokyo_debut_seiseki(
        mock_manager,
        debut_date_from="20250101",
        debut_date_to="20251231",
    )

    assert result["success"] is True
    assert result["total"] == 200
    sql = mock_manager.fetch_dataframe.call_args[0][0]
    assert "debut_horses" in sql


# 準正常系: analyze_chokyo_debut_seiseki


def test_analyze_chokyo_debut_seiseki_returns_error_on_db_failure(
    mock_manager: MockerFixture,
) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = analyze_chokyo_debut_seiseki(
        mock_manager,
        debut_date_from="20250101",
        debut_date_to="20251231",
    )

    assert result["success"] is False
    assert "error" in result
