"""主要集計API。よく使われる競馬分析クエリをラップした関数群。"""

from typing import Any

from mykeibadb.connection import ConnectionManager
from mykeibadb.exceptions import MykeibaDBError


def analyze_ninki_seiseki(
    manager: ConnectionManager,
    ninki: int = 1,
    keibajo: str | None = None,
    grade: str | None = None,
    year_from: str | None = None,
    kyori: int | None = None,
    course_kubun: str | None = None,
    week_in_course: int | None = None,
) -> dict[str, Any]:
    """指定人気順位の勝率・複勝率・出走数・勝利数を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        ninki (int): 人気順位（デフォルト1）
        keibajo (str | None): 競馬場コード（例: '05'=東京）
        grade (str | None): グレードコード（例: 'A'=GI）
        year_from (str | None): 集計開始年（4桁文字列、例: '2020'）
        kyori (int | None): 距離（メートル単位）
        course_kubun (str | None): コース区分（例: 'C'）。week_in_courseと併用。
        week_in_course (int | None): コース使用開始からの週番号。course_kubunと併用。

    Returns:
        dict: 出走数・勝利数・勝率・複勝数・複勝率を含む辞書
    """
    try:
        ninki_str = str(ninki).zfill(2)
        cte_params: list[Any] = []
        cte_sql, join_sql = "", ""
        if course_kubun is not None and week_in_course is not None:
            cte_sql, join_sql = _build_course_week_cte(
                keibajo, course_kubun, week_in_course, cte_params
            )

        where_clauses = [
            "u.tansho_ninkijun = %s",
            "u.kakutei_chakujun != '00'",
        ]
        where_params: list[Any] = [ninki_str]

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            where_params.append(keibajo)
        if grade:
            where_clauses.append("r.grade_code = %s")
            where_params.append(grade)
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            where_params.append(year_from)
        if kyori:
            where_clauses.append("r.kyori = %s")
            where_params.append(str(kyori))

        where = " AND ".join(where_clauses)
        with_clause = f"WITH {cte_sql}" if cte_sql else ""
        sql = f"""
            {with_clause}
            SELECT
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1
                    THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3
                    THEN 1 ELSE 0 END), 0) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            {join_sql}
            WHERE {where}
        """
        params = tuple(cte_params + where_params)
        df = manager.fetch_dataframe(sql, params=params)
        row = df.iloc[0]
        total = int(row["total"])
        wins = int(row["wins"])
        fukusho = int(row["fukusho"])
        return {
            "success": True,
            "ninki": ninki,
            "total": total,
            "wins": wins,
            "win_rate": round(wins / total * 100, 1) if total > 0 else 0.0,
            "fukusho": fukusho,
            "fukusho_rate": round(fukusho / total * 100, 1) if total > 0 else 0.0,
        }
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


def analyze_kishu_seiseki(
    manager: ConnectionManager,
    kishu_name: str,
    keibajo: str | None = None,
    year_from: str | None = None,
    kyori: int | None = None,
    course_kubun: str | None = None,
    week_in_course: int | None = None,
) -> dict[str, Any]:
    """騎手名（部分一致）で勝率・複勝率・騎乗数を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        kishu_name (str): 騎手名（部分一致で検索）
        keibajo (str | None): 競馬場コード
        year_from (str | None): 集計開始年
        kyori (int | None): 距離（メートル）
        course_kubun (str | None): コース区分（例: 'C'）。week_in_courseと併用。
        week_in_course (int | None): コース使用開始からの週番号。course_kubunと併用。

    Returns:
        dict: 騎手名・騎乗数・勝利数・勝率・複勝率を含む辞書
    """
    try:
        cte_params: list[Any] = []
        cte_sql, join_sql = "", ""
        if course_kubun is not None and week_in_course is not None:
            cte_sql, join_sql = _build_course_week_cte(
                keibajo, course_kubun, week_in_course, cte_params
            )

        where_clauses = [
            "km.kishumei LIKE %s",
            "u.kakutei_chakujun != '00'",
        ]
        where_params: list[Any] = [f"%{kishu_name}%"]

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            where_params.append(keibajo)
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            where_params.append(year_from)
        if kyori:
            where_clauses.append("r.kyori = %s")
            where_params.append(str(kyori))

        where = " AND ".join(where_clauses)
        with_clause = f"WITH {cte_sql}" if cte_sql else ""
        sql = f"""
            {with_clause}
            SELECT
                km.kishumei,
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1
                    THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3
                    THEN 1 ELSE 0 END), 0) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            JOIN kishu_master km ON u.kishu_code = km.kishu_code
            {join_sql}
            WHERE {where}
            GROUP BY km.kishumei
            ORDER BY wins DESC
        """
        params = tuple(cte_params + where_params)
        df = manager.fetch_dataframe(sql, params=params)
        results = []
        for _, row in df.iterrows():
            total = int(row["total"])
            wins = int(row["wins"])
            fukusho = int(row["fukusho"])
            results.append({
                "kishumei": row["kishumei"],
                "total": total,
                "wins": wins,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0.0,
                "fukusho": fukusho,
                "fukusho_rate": round(fukusho / total * 100, 1) if total > 0 else 0.0,
            })
        return {"success": True, "results": results, "count": len(results)}
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


def analyze_sire_seiseki(
    manager: ConnectionManager,
    sire_name: str,
    keibajo: str | None = None,
    kyori: int | None = None,
    year_from: str | None = None,
    course_kubun: str | None = None,
    week_in_course: int | None = None,
) -> dict[str, Any]:
    """種牡馬（父馬）名で産駒の勝率・複勝率を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        sire_name (str): 種牡馬名（部分一致で検索）
        keibajo (str | None): 競馬場コード
        kyori (int | None): 距離（メートル）
        year_from (str | None): 集計開始年
        course_kubun (str | None): コース区分（例: 'C'）。week_in_courseと併用。
        week_in_course (int | None): コース使用開始からの週番号。course_kubunと併用。

    Returns:
        dict: 種牡馬名・産駒出走数・勝利数・勝率・複勝率を含む辞書
    """
    try:
        cte_params: list[Any] = []
        cte_sql, join_sql = "", ""
        if course_kubun is not None and week_in_course is not None:
            cte_sql, join_sql = _build_course_week_cte(
                keibajo, course_kubun, week_in_course, cte_params
            )

        where_clauses = [
            "km2.ketto1_bamei LIKE %s",
            "u.kakutei_chakujun != '00'",
        ]
        where_params: list[Any] = [f"%{sire_name}%"]

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            where_params.append(keibajo)
        if kyori:
            where_clauses.append("r.kyori = %s")
            where_params.append(str(kyori))
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            where_params.append(year_from)

        where = " AND ".join(where_clauses)
        with_clause = f"WITH {cte_sql}" if cte_sql else ""
        sql = f"""
            {with_clause}
            SELECT
                km2.ketto1_bamei AS sire_name,
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1
                    THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3
                    THEN 1 ELSE 0 END), 0) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            JOIN kyosoba_master2 km2 ON u.ketto_toroku_bango = km2.ketto_toroku_bango
            {join_sql}
            WHERE {where}
            GROUP BY km2.ketto1_bamei
            ORDER BY wins DESC
        """
        params = tuple(cte_params + where_params)
        df = manager.fetch_dataframe(sql, params=params)
        results = []
        for _, row in df.iterrows():
            total = int(row["total"])
            wins = int(row["wins"])
            fukusho = int(row["fukusho"])
            results.append({
                "sire_name": row["sire_name"],
                "total": total,
                "wins": wins,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0.0,
                "fukusho": fukusho,
                "fukusho_rate": round(fukusho / total * 100, 1) if total > 0 else 0.0,
            })
        return {"success": True, "results": results, "count": len(results)}
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


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
        dict: 日付・競馬場・レース名・着順・タイム・騎手を含む戦績リスト
    """
    try:
        cte_params: list[Any] = []
        cte_sql, join_sql = "", ""
        if course_kubun is not None and week_in_course is not None:
            cte_sql, join_sql = _build_course_week_cte(
                None, course_kubun, week_in_course, cte_params
            )

        where_clauses = ["km2.bamei LIKE %s"]
        where_params: list[Any] = [f"%{uma_name}%"]

        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            where_params.append(year_from)

        where = " AND ".join(where_clauses)
        with_clause = f"WITH {cte_sql}" if cte_sql else ""
        sql = f"""
            {with_clause}
            SELECT
                km2.bamei,
                r.kaisai_nen,
                r.kaisai_gappi,
                r.keibajo_code,
                r.kyosomei_hondai AS race_name,
                r.grade_code,
                r.kyori,
                u.kakutei_chakujun,
                u.soha_time,
                u.kishumei_ryakusho,
                u.tansho_ninkijun,
                u.tansho_odds
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            JOIN kyosoba_master2 km2 ON u.ketto_toroku_bango = km2.ketto_toroku_bango
            {join_sql}
            WHERE {where}
            ORDER BY r.kaisai_nen DESC, r.kaisai_gappi DESC
        """
        params = tuple(cte_params + where_params)
        df = manager.fetch_dataframe(sql, params=params)
        records = []
        for _, row in df.iterrows():
            records.append({
                "bamei": row["bamei"],
                "kaisai_nen": row["kaisai_nen"],
                "kaisai_gappi": row["kaisai_gappi"],
                "keibajo_code": row["keibajo_code"],
                "race_name": row["race_name"],
                "grade_code": row["grade_code"],
                "kyori": row["kyori"],
                "kakutei_chakujun": row["kakutei_chakujun"],
                "soha_time": row["soha_time"],
                "kishumei_ryakusho": row["kishumei_ryakusho"],
                "tansho_ninkijun": row["tansho_ninkijun"],
                "tansho_odds": row["tansho_odds"],
            })
        return {"success": True, "results": records, "count": len(records)}
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


def analyze_waku_seiseki(
    manager: ConnectionManager,
    keibajo: str | None = None,
    kyori: int | None = None,
    year_from: str | None = None,
    course_kubun: str | None = None,
    week_in_course: int | None = None,
) -> dict[str, Any]:
    """枠番（1〜8）別の勝率・複勝率を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        keibajo (str | None): 競馬場コード
        kyori (int | None): 距離（メートル）
        year_from (str | None): 集計開始年
        course_kubun (str | None): コース区分（例: 'C'）。week_in_courseと併用。
        week_in_course (int | None): コース使用開始からの週番号。course_kubunと併用。

    Returns:
        dict: 枠番ごとの出走数・勝利数・勝率・複勝率を含む辞書
    """
    try:
        cte_params: list[Any] = []
        cte_sql, join_sql = "", ""
        if course_kubun is not None and week_in_course is not None:
            cte_sql, join_sql = _build_course_week_cte(
                keibajo, course_kubun, week_in_course, cte_params
            )

        where_clauses = ["u.kakutei_chakujun != '00'"]
        where_params: list[Any] = []

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            where_params.append(keibajo)
        if kyori:
            where_clauses.append("r.kyori = %s")
            where_params.append(str(kyori))
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            where_params.append(year_from)

        where = " AND ".join(where_clauses)
        with_clause = f"WITH {cte_sql}" if cte_sql else ""
        sql = f"""
            {with_clause}
            SELECT
                u.wakuban,
                COUNT(*) AS total,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1
                    THEN 1 ELSE 0 END), 0) AS wins,
                COALESCE(SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3
                    THEN 1 ELSE 0 END), 0) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            {join_sql}
            WHERE {where}
            GROUP BY u.wakuban
            ORDER BY u.wakuban
        """
        params = tuple(cte_params + where_params)
        df = manager.fetch_dataframe(sql, params=params if params else None)
        results = []
        for _, row in df.iterrows():
            total = int(row["total"])
            wins = int(row["wins"])
            fukusho = int(row["fukusho"])
            results.append({
                "wakuban": row["wakuban"],
                "total": total,
                "wins": wins,
                "win_rate": round(wins / total * 100, 1) if total > 0 else 0.0,
                "fukusho": fukusho,
                "fukusho_rate": round(fukusho / total * 100, 1) if total > 0 else 0.0,
            })
        return {"success": True, "results": results, "count": len(results)}
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


def _build_course_week_cte(
    keibajo: str | None,
    course_kubun: str,
    week_in_course: int,
    cte_params: list[Any],
) -> tuple[str, str]:
    """コースn週目フィルタ用のCTE SQLとJOIN句を生成する。

    同一コース区分の使用開始から2日間を1週として週番号を計算し、
    指定コース・週番号の開催日のみに絞り込むCTEを生成する。

    Args:
        keibajo (str | None): 競馬場コード。Noneの場合は全競馬場が対象。
        course_kubun (str): コース区分（例: 'C'）。
        week_in_course (int): コース使用開始からの週番号（1始まり）。
        cte_params (list[Any]): SQLパラメータリスト（末尾に追加される）。

    Returns:
        tuple[str, str]: (CTE SQL（WITHキーワードなし）, JOIN句)
    """
    keibajo_filter = "AND keibajo_code = %s" if keibajo else ""
    if keibajo:
        cte_params.append(keibajo)
    cte_params.extend([course_kubun, week_in_course])

    cte_sql = f"""
        cw_daily AS (
            SELECT DISTINCT keibajo_code, kaisai_nen, kaisai_kai, kaisai_nichime, course_kubun
            FROM race_shosai
            WHERE course_kubun != '' {keibajo_filter}
        ),
        cw_with_prev AS (
            SELECT *,
                LAG(course_kubun) OVER (
                    PARTITION BY keibajo_code, kaisai_nen ORDER BY kaisai_kai, kaisai_nichime
                ) AS prev_course
            FROM cw_daily
        ),
        cw_with_group AS (
            SELECT *,
                SUM(CASE WHEN course_kubun != COALESCE(prev_course, '_') THEN 1 ELSE 0 END)
                    OVER (PARTITION BY keibajo_code, kaisai_nen ORDER BY kaisai_kai, kaisai_nichime)
                    AS cw_group_id
            FROM cw_with_prev
        ),
        cw_weeks AS (
            SELECT *,
                CEIL(
                    ROW_NUMBER() OVER (
                        PARTITION BY keibajo_code, kaisai_nen, cw_group_id
                        ORDER BY kaisai_kai, kaisai_nichime
                    ) / 2.0
                )::INT AS week_in_course
            FROM cw_with_group
        ),
        cw_target AS (
            SELECT keibajo_code, kaisai_nen, kaisai_kai, kaisai_nichime
            FROM cw_weeks
            WHERE course_kubun = %s AND week_in_course = %s
        )"""

    join_sql = """JOIN cw_target ON r.keibajo_code = cw_target.keibajo_code
            AND r.kaisai_nen = cw_target.kaisai_nen
            AND r.kaisai_kai = cw_target.kaisai_kai
            AND r.kaisai_nichime = cw_target.kaisai_nichime"""

    return cte_sql, join_sql
