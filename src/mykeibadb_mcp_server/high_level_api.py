"""主要集計API。よく使われる競馬分析クエリをラップした関数群。"""

from dataclasses import asdict
from typing import Any

from mykeibadb.analytics import (
    ChokyoCondition,
    ChokyoThreshold,
    GroupBy,
    RaceCondition,
    analyze_chakudo,
)
from mykeibadb.analytics import analyze_chokyo_debut_seiseki as _analyze_chokyo_debut_seiseki
from mykeibadb.analytics import (
    build_entry_filter,
)
from mykeibadb.analytics import get_uma_chokyo as _get_uma_chokyo
from mykeibadb.analytics import get_uma_rekisen as _get_uma_rekisen
from mykeibadb.connection import ConnectionManager


def run_analyze_chakudo(
    manager: ConnectionManager,
    filters: list[dict[str, Any]] | None = None,
    condition: dict[str, Any] | None = None,
    group_by: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """JSON引数をdataclassに変換しanalyze_chakudoを実行する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        filters (list[dict[str, Any]] | None): EntryFilter相当のdictリスト
        condition (dict[str, Any] | None): RaceCondition相当のdict
        group_by (dict[str, Any] | None): GroupBy相当のdict

    Returns:
        dict: success / count / results（ChakudoRowのasdictリスト）。
              失敗時はsuccess=False / error。
    """
    try:
        entry_filters = [build_entry_filter(f) for f in (filters or [])]
        race_condition = RaceCondition.from_dict(condition) if condition else None
        group = GroupBy.from_dict(group_by) if group_by else None
    except (KeyError, TypeError, ValueError) as e:
        return {"success": False, "error": f"invalid argument: {e}"}
    result = analyze_chakudo(manager, entry_filters, race_condition, group)
    if not result.success:
        return {"success": False, "error": result.error}
    return {
        "success": True,
        "count": len(result.rows),
        "results": [asdict(row) for row in result.rows],
    }


def get_uma_rekisen(
    manager: ConnectionManager,
    uma_name: str,
    year_from: str | None = None,
    course_kubun: str | None = None,
    week_in_course: int | None = None,
) -> dict[str, Any]:
    """馬名（部分一致）で過去レース戦績一覧を取得する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        uma_name (str): 馬名（部分一致で検索）
        year_from (str | None): 集計開始年
        course_kubun (str | None): コース区分（例: 'C'）。week_in_courseと併用。
        week_in_course (int | None): コース使用開始からの週番号。course_kubunと併用。

    Returns:
        dict: 競走成績リストを含む辞書
    """
    condition = RaceCondition(
        year_from=year_from,
        course_kubun=course_kubun,
        week_in_course=week_in_course,
    )
    return _get_uma_rekisen(manager, uma_name=uma_name, condition=condition)


def get_uma_chokyo(
    manager: ConnectionManager,
    uma_name: str,
    before_debut: bool = False,
    year_from: str | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    """馬名（部分一致）でウッドチップ・坂路調教データを取得する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        uma_name (str): 馬名（部分一致）
        before_debut (bool): Trueの場合はデビュー日以前の調教のみ取得
        year_from (str | None): 取得開始年（4桁文字列）
        limit (int): ウッドチップ・坂路それぞれの最大取得件数（デフォルト30）

    Returns:
        dict: 馬名・デビュー日・ウッドチップ/坂路調教レコード一覧を含む辞書
    """
    rekisen_result = _get_uma_rekisen(manager, uma_name=uma_name)
    if not rekisen_result["success"]:
        return rekisen_result

    horses: dict[str, dict[str, Any]] = {}
    for r in rekisen_result["results"]:
        ketto = r["ketto_toroku_bango"]
        if ketto not in horses:
            horses[ketto] = {"bamei": r["bamei"], "debut_date": r["race_date"]}
        else:
            if r["race_date"] < horses[ketto]["debut_date"]:
                horses[ketto]["debut_date"] = r["race_date"]

    if not horses:
        return {"success": True, "count": 0, "results": []}

    results = []
    for ketto, info in horses.items():
        date_from = f"{year_from}0101" if year_from else None
        date_to = info["debut_date"] if before_debut else None

        chokyo_result = _get_uma_chokyo(
            manager, ketto_toroku_bango=ketto, date_from=date_from, date_to=date_to
        )
        if not chokyo_result["success"]:
            return chokyo_result

        results.append({
            "bamei": info["bamei"],
            "ketto_toroku_bango": ketto,
            "debut_date": info["debut_date"],
            "wood_records": chokyo_result["wood_records"][:limit],
            "hanro_records": chokyo_result["hanro_records"][:limit],
        })

    return {"success": True, "count": len(results), "results": results}


def analyze_chokyo_debut_seiseki(
    manager: ConnectionManager,
    debut_date_from: str,
    debut_date_to: str,
    tracen_kubun: str | None = None,
    wood_time_6f_max: int | None = None,
    wood_laptime_1f_max: int | None = None,
    hanro_time_4f_max: int | None = None,
    hanro_laptime_1f_max: int | None = None,
) -> dict[str, Any]:
    """デビュー前の調教条件を満たした馬のデビュー後勝利率を集計する。

    指定期間にデビューした馬のうち、デビュー前の調教データが条件を
    満たす馬を抽出し、同期間内の勝利率を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        debut_date_from (str): デビュー期間開始日（yyyymmdd形式）
        debut_date_to (str): デビュー期間終了日（yyyymmdd形式）
        tracen_kubun (str | None): トレセン区分。'0'=美浦, '1'=栗東
        wood_time_6f_max (int | None): ウッド6F合計タイム上限（0.1秒単位）
        wood_laptime_1f_max (int | None): ウッドラスト1Fタイム上限（0.1秒単位）
        hanro_time_4f_max (int | None): 坂路4F合計タイム上限（0.1秒単位）
        hanro_laptime_1f_max (int | None): 坂路ラスト1Fタイム上限（0.1秒単位）

    Returns:
        dict: 条件を満たす馬の頭数・勝利馬数・勝利率を含む辞書
    """
    condition: ChokyoCondition = []
    if wood_time_6f_max is not None:
        condition.append(ChokyoThreshold(
            course="wood", metric="gokei", furlong=6,
            max_value=wood_time_6f_max, tracen_kubun=tracen_kubun,
        ))
    if wood_laptime_1f_max is not None:
        condition.append(ChokyoThreshold(
            course="wood", metric="lap", furlong=1,
            max_value=wood_laptime_1f_max, tracen_kubun=tracen_kubun,
        ))
    if hanro_time_4f_max is not None:
        condition.append(ChokyoThreshold(
            course="hanro", metric="gokei", furlong=4,
            max_value=hanro_time_4f_max, tracen_kubun=tracen_kubun,
        ))
    if hanro_laptime_1f_max is not None:
        condition.append(ChokyoThreshold(
            course="hanro", metric="lap", furlong=1,
            max_value=hanro_laptime_1f_max, tracen_kubun=tracen_kubun,
        ))
    return _analyze_chokyo_debut_seiseki(
        manager, debut_date_from, debut_date_to, condition=condition
    )
