"""集計API（high_level_api）のモックテスト."""

import pandas as pd
import pytest
from pytest_mock import MockerFixture

from mykeibadb_mcp_server.high_level_api import (
    analyze_chokyo_debut_seiseki,
    get_uma_chokyo,
    get_uma_rekisen,
    run_analyze_chakudo,
)


@pytest.fixture
def mock_manager(mocker: MockerFixture):  # type: ignore[no-untyped-def]
    """モックConnectionManager."""
    return mocker.MagicMock()


def _make_entry_df(group_label: object = "1") -> pd.DataFrame:
    """select_entries が返す DataFrameのモック."""
    return pd.DataFrame({
        "ketto_toroku_bango": ["2020100001"],
        "race_code": ["202001050101"],
        "umaban": ["01"],
        "group_label": [group_label],
    })


def _make_tally_df(
    group_label: object = "1",
    total: int = 100,
    wins: int = 20,
    second: int = 15,
    third: int = 12,
    chakugai: int = 53,
    tansho_payout_sum: int = 8500,
    fukusho_payout_sum: int = 7800,
) -> pd.DataFrame:
    """tally_chakujun が返す DataFrameのモック."""
    return pd.DataFrame({
        "group_label": [group_label],
        "total": [total],
        "wins": [wins],
        "second": [second],
        "third": [third],
        "chakugai": [chakugai],
        "tansho_payout_sum": [tansho_payout_sum],
        "fukusho_payout_sum": [fukusho_payout_sum],
    })


# 正常系: get_uma_rekisen


def test_get_uma_rekisen_returns_success(mock_manager: MockerFixture) -> None:
    """get_uma_rekisenがsuccess=Trueを返す."""
    df = pd.DataFrame({
        "ketto_toroku_bango": ["2018100001"],
        "bamei": ["アーモンドアイ"],
        "race_date": ["20181028"],
        "keibajo_code": ["05"],
        "race_code": ["201810050611"],
        "umaban": ["06"],
        "kakutei_chakujun": ["01"],
        "kyori": [2000],
        "track_code": ["10"],
        "grade_code": ["A"],
    })
    mock_manager.fetch_dataframe.return_value = df

    result = get_uma_rekisen(mock_manager, uma_name="アーモンドアイ")

    assert result["success"] is True
    assert result["count"] == 1
    assert result["results"][0]["bamei"] == "アーモンドアイ"


def test_get_uma_rekisen_with_year_from(mock_manager: MockerFixture) -> None:
    """year_fromフィルタが指定可能."""
    df = pd.DataFrame({
        "ketto_toroku_bango": pd.Series([], dtype=str),
        "bamei": pd.Series([], dtype=str),
        "race_date": pd.Series([], dtype=str),
        "keibajo_code": pd.Series([], dtype=str),
        "race_code": pd.Series([], dtype=str),
        "umaban": pd.Series([], dtype=str),
        "kakutei_chakujun": pd.Series([], dtype=str),
        "kyori": pd.Series([], dtype=object),
        "track_code": pd.Series([], dtype=str),
        "grade_code": pd.Series([], dtype=str),
    })
    mock_manager.fetch_dataframe.return_value = df

    result = get_uma_rekisen(mock_manager, uma_name="テスト馬", year_from="2020")

    assert result["success"] is True
    assert result["count"] == 0


# 準正常系: get_uma_rekisen


def test_get_uma_rekisen_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = get_uma_rekisen(mock_manager, uma_name="テスト馬")

    assert result["success"] is False
    assert "error" in result


# 正常系: get_uma_chokyo


def test_get_uma_chokyo_returns_success(mock_manager: MockerFixture) -> None:
    """get_uma_chokyoがsuccess=Trueを返す."""
    rekisen_df = pd.DataFrame({
        "ketto_toroku_bango": ["2020100001"],
        "bamei": ["テスト馬"],
        "race_date": ["20220101"],
        "keibajo_code": ["05"],
        "race_code": ["202201050101"],
        "umaban": ["01"],
        "kakutei_chakujun": ["01"],
        "kyori": [2000],
        "track_code": ["10"],
        "grade_code": ["F"],
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
    mock_manager.fetch_dataframe.side_effect = [rekisen_df, wood_df, hanro_df]

    result = get_uma_chokyo(mock_manager, uma_name="テスト馬")

    assert result["success"] is True
    assert result["count"] == 1
    horse = result["results"][0]
    assert horse["bamei"] == "テスト馬"
    assert horse["debut_date"] == "20220101"
    assert len(horse["wood_records"]) == 1
    assert len(horse["hanro_records"]) == 1
    assert horse["wood_records"][0]["time_6f"] == "0820"
    assert horse["hanro_records"][0]["course_type"] == "坂路"


def test_get_uma_chokyo_horse_not_found(mock_manager: MockerFixture) -> None:
    """馬名マッチなし時にcount=0が返る."""
    mock_manager.fetch_dataframe.return_value = pd.DataFrame({
        "ketto_toroku_bango": pd.Series([], dtype=str),
        "bamei": pd.Series([], dtype=str),
        "race_date": pd.Series([], dtype=str),
        "keibajo_code": pd.Series([], dtype=str),
        "race_code": pd.Series([], dtype=str),
        "umaban": pd.Series([], dtype=str),
        "kakutei_chakujun": pd.Series([], dtype=str),
        "kyori": pd.Series([], dtype=object),
        "track_code": pd.Series([], dtype=str),
        "grade_code": pd.Series([], dtype=str),
    })

    result = get_uma_chokyo(mock_manager, uma_name="存在しない馬")

    assert result["success"] is True
    assert result["count"] == 0
    assert result["results"] == []


def test_get_uma_chokyo_before_debut_filter(mock_manager: MockerFixture) -> None:
    """before_debut=TrueのときデビューデートのフィルタがSQLに適用される."""
    rekisen_df = pd.DataFrame({
        "ketto_toroku_bango": ["2020100001"],
        "bamei": ["テスト馬"],
        "race_date": ["20220101"],
        "keibajo_code": ["05"],
        "race_code": ["202201050101"],
        "umaban": ["01"],
        "kakutei_chakujun": ["01"],
        "kyori": [2000],
        "track_code": ["10"],
        "grade_code": ["F"],
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
    mock_manager.fetch_dataframe.side_effect = [rekisen_df, empty_wood, empty_hanro]

    result = get_uma_chokyo(mock_manager, uma_name="テスト馬", before_debut=True)

    assert result["success"] is True
    wood_call_args = mock_manager.fetch_dataframe.call_args_list[1]
    wood_sql = wood_call_args[0][0]
    assert "chokyo_nengappi <= %s" in wood_sql


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


# 正常系: run_analyze_chakudo


def test_run_analyze_chakudo_returns_success(mock_manager: MockerFixture) -> None:
    """filters/condition/group_byなしでもsuccess=Trueを返す."""
    mock_manager.fetch_dataframe.side_effect = [
        _make_entry_df(group_label="1"),
        _make_tally_df(group_label="1", total=100, wins=20),
    ]

    result = run_analyze_chakudo(mock_manager)

    assert result["success"] is True
    assert result["count"] == 1
    row = result["results"][0]
    assert row["total"] == 100
    assert row["wins"] == 20
    assert row["win_rate"] == 20.0


def test_run_analyze_chakudo_with_multiple_filters(mock_manager: MockerFixture) -> None:
    """複数filters指定時にAND（INTERSECT）でエントリが絞り込まれる."""
    mock_manager.fetch_dataframe.side_effect = [
        _make_entry_df(group_label="1"),
        _make_tally_df(group_label="1", total=50, wins=10),
    ]

    result = run_analyze_chakudo(
        mock_manager,
        filters=[
            {"type": "race_col", "column": "u.wakuban", "values": ["1"]},
            {"type": "subject", "subject": "kishu", "name": "武豊"},
        ],
        condition={"keibajo_codes": ["05"], "year_from": "2020"},
        group_by={"kind": "race_col", "column": "u.tansho_ninkijun"},
    )

    assert result["success"] is True
    assert result["count"] == 1

    entry_call = mock_manager.fetch_dataframe.call_args_list[0]
    sql = entry_call[0][0]
    assert "INTERSECT" in sql


def test_run_analyze_chakudo_history_group_by(mock_manager: MockerFixture) -> None:
    """history group_byでAttrSource由来のグループ別集計が行われる."""
    mock_manager.fetch_dataframe.side_effect = [
        _make_entry_df(group_label="東京"),
        _make_tally_df(group_label="東京", total=30, wins=5),
    ]

    result = run_analyze_chakudo(
        mock_manager,
        group_by={"kind": "history", "source": {"type": "debut_venue"}},
    )

    assert result["success"] is True
    assert result["count"] == 1
    assert result["results"][0]["group"] == "東京"


def test_run_analyze_chakudo_fixed_group_by(mock_manager: MockerFixture) -> None:
    """fixed group_byでrowsに定義したラベル別の集計が行われる."""
    mock_manager.fetch_dataframe.side_effect = [
        _make_entry_df(group_label="初出走"),
        _make_tally_df(group_label="初出走", total=10, wins=1),
    ]

    result = run_analyze_chakudo(
        mock_manager,
        group_by={
            "kind": "fixed",
            "source": {"type": "career_count"},
            "rows": {"初出走": 0, "経験馬": [1, 9999]},
        },
    )

    assert result["success"] is True
    assert result["count"] == 1
    assert result["results"][0]["group"] == "初出走"


# 準正常系: run_analyze_chakudo


def test_run_analyze_chakudo_returns_error_on_db_failure(mock_manager: MockerFixture) -> None:
    """DBエラー時にsuccess=Falseが返る."""
    from mykeibadb.exceptions import QueryExecutionError

    mock_manager.fetch_dataframe.side_effect = QueryExecutionError("接続失敗")

    result = run_analyze_chakudo(mock_manager)

    assert result["success"] is False
    assert "error" in result


def test_run_analyze_chakudo_returns_error_for_unknown_filter_type(
    mock_manager: MockerFixture,
) -> None:
    """filtersのtypeが未知の場合にsuccess=Falseが返る."""
    result = run_analyze_chakudo(mock_manager, filters=[{"type": "unknown"}])

    assert result["success"] is False
    assert "error" in result


def test_run_analyze_chakudo_returns_error_for_unknown_group_by_kind(
    mock_manager: MockerFixture,
) -> None:
    """group_byのkindが未知の場合にsuccess=Falseが返る."""
    result = run_analyze_chakudo(mock_manager, group_by={"kind": "unknown"})

    assert result["success"] is False
    assert "error" in result
