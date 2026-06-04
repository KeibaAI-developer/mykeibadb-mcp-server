"""主要集計API。よく使われる競馬分析クエリをラップした関数群。"""

from typing import Any

import pandas as pd
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
        before_debut (bool): Trueの場合はデビュー前の調教のみ取得
        year_from (str | None): 集計開始年（4桁文字列）
        limit (int): ウッドチップ・坂路を合算した最大取得件数（デフォルト30）

    Returns:
        dict: 馬名・デビュー日・ウッドチップ/坂路調教レコード一覧を含む辞書
    """
    try:
        limit = max(1, limit)
        horse_sql = """
            SELECT km2.ketto_toroku_bango, km2.bamei,
                   MIN(u.kaisai_nen || u.kaisai_gappi) AS debut_date
            FROM kyosoba_master2 km2
            LEFT JOIN umagoto_race_joho u
                ON km2.ketto_toroku_bango = u.ketto_toroku_bango
                AND u.kakutei_chakujun != '00'
            WHERE km2.bamei LIKE %s
            GROUP BY km2.ketto_toroku_bango, km2.bamei
        """
        horses_df = manager.fetch_dataframe(horse_sql, params=(f"%{uma_name}%",))
        if horses_df.empty:
            return {"success": True, "count": 0, "results": []}

        results = []
        for _, horse in horses_df.iterrows():
            ketto = str(horse["ketto_toroku_bango"])
            bamei = str(horse["bamei"])
            raw_debut = horse["debut_date"]
            debut_date_str = str(raw_debut) if pd.notna(raw_debut) else None

            date_filter_parts: list[str] = []
            date_extra_params: list[Any] = []
            if before_debut and debut_date_str:
                date_filter_parts.append("AND chokyo_nengappi < %s")
                date_extra_params.append(debut_date_str)
            if year_from:
                date_filter_parts.append("AND chokyo_nengappi >= %s")
                date_extra_params.append(f"{year_from}0101")
            date_filter = " ".join(date_filter_parts)

            wood_sql = f"""
                SELECT tracen_kubun, chokyo_nengappi, chokyo_jikoku,
                       time_gokei_6furlong, time_gokei_5furlong,
                       time_gokei_4furlong,
                       laptime_1furlong, laptime_2furlong, laptime_3furlong
                FROM woodchip_chokyo
                WHERE ketto_toroku_bango = %s
                  AND time_gokei_6furlong NOT IN ('0000', '9999')
                  {date_filter}
                ORDER BY chokyo_nengappi DESC, chokyo_jikoku DESC
                LIMIT %s
            """
            wood_df = manager.fetch_dataframe(
                wood_sql, params=tuple([ketto] + date_extra_params + [limit])
            )

            hanro_sql = f"""
                SELECT tracen_kubun, chokyo_nengappi, chokyo_jikoku,
                       time_gokei_4furlong,
                       lap_time_1furlong, lap_time_2furlong,
                       lap_time_3furlong, lap_time_4furlong
                FROM hanro_chokyo
                WHERE ketto_toroku_bango = %s
                  AND time_gokei_4furlong NOT IN ('0000', '9999')
                  {date_filter}
                ORDER BY chokyo_nengappi DESC, chokyo_jikoku DESC
                LIMIT %s
            """
            hanro_df = manager.fetch_dataframe(
                hanro_sql, params=tuple([ketto] + date_extra_params + [limit])
            )

            wood_records = []
            for _, r in wood_df.iterrows():
                tracen = "美浦" if str(r["tracen_kubun"]) == "0" else "栗東"
                wood_records.append({
                    "course_type": "ウッドチップ",
                    "tracen": tracen,
                    "date": str(r["chokyo_nengappi"]),
                    "jikoku": str(r["chokyo_jikoku"]),
                    "time_6f": _fmt_time4(str(r["time_gokei_6furlong"])),
                    "time_5f": _fmt_time4(str(r["time_gokei_5furlong"])),
                    "time_4f": _fmt_time4(str(r["time_gokei_4furlong"])),
                    "lap_1f": _fmt_lap3(str(r["laptime_1furlong"])),
                    "lap_2f": _fmt_lap3(str(r["laptime_2furlong"])),
                    "lap_3f": _fmt_lap3(str(r["laptime_3furlong"])),
                })

            hanro_records = []
            for _, r in hanro_df.iterrows():
                tracen = "美浦" if str(r["tracen_kubun"]) == "0" else "栗東"
                hanro_records.append({
                    "course_type": "坂路",
                    "tracen": tracen,
                    "date": str(r["chokyo_nengappi"]),
                    "jikoku": str(r["chokyo_jikoku"]),
                    "time_4f": _fmt_time4(str(r["time_gokei_4furlong"])),
                    "lap_1f": _fmt_lap3(str(r["lap_time_1furlong"])),
                    "lap_2f": _fmt_lap3(str(r["lap_time_2furlong"])),
                    "lap_3f": _fmt_lap3(str(r["lap_time_3furlong"])),
                    "lap_4f": _fmt_lap3(str(r["lap_time_4furlong"])),
                })

            all_records = sorted(
                wood_records + hanro_records,
                key=lambda x: (x["date"], x["jikoku"]),
                reverse=True,
            )[:limit]

            results.append({
                "bamei": bamei,
                "debut_date": debut_date_str,
                "wood_count": len(wood_records),
                "hanro_count": len(hanro_records),
                "chokyo": all_records,
            })

        return {"success": True, "count": len(results), "results": results}
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


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
    try:
        use_wood = wood_time_6f_max is not None or wood_laptime_1f_max is not None
        use_hanro = hanro_time_4f_max is not None or hanro_laptime_1f_max is not None
        cte_parts: list[str] = []
        sql_params: list[Any] = []

        cte_parts.append("""
    debut_horses AS (
        SELECT ketto_toroku_bango,
               MIN(kaisai_nen || kaisai_gappi) AS debut_date
        FROM umagoto_race_joho
        WHERE kakutei_chakujun != '00'
        GROUP BY ketto_toroku_bango
        HAVING MIN(kaisai_nen || kaisai_gappi) BETWEEN %s AND %s
    )""")
        sql_params.extend([debut_date_from, debut_date_to])

        if use_wood:
            wood_conds = ["w.time_gokei_6furlong NOT IN ('0000', '9999')"]
            if tracen_kubun:
                wood_conds.append("w.tracen_kubun = %s")
                sql_params.append(tracen_kubun)
            if wood_time_6f_max is not None:
                wood_conds.append("CAST(w.time_gokei_6furlong AS INTEGER) <= %s")
                sql_params.append(wood_time_6f_max)
            if wood_laptime_1f_max is not None:
                wood_conds.append("w.laptime_1furlong NOT IN ('000', '999')")
                wood_conds.append("CAST(w.laptime_1furlong AS INTEGER) <= %s")
                sql_params.append(wood_laptime_1f_max)
            wood_where = " AND ".join(wood_conds)
            cte_parts.append(f"""
    wood_qualified AS (
        SELECT DISTINCT w.ketto_toroku_bango
        FROM woodchip_chokyo w
        JOIN debut_horses d ON w.ketto_toroku_bango = d.ketto_toroku_bango
        WHERE w.chokyo_nengappi < d.debut_date
          AND {wood_where}
    )""")

        if use_hanro:
            hanro_conds = ["h.time_gokei_4furlong NOT IN ('0000', '9999')"]
            if tracen_kubun:
                hanro_conds.append("h.tracen_kubun = %s")
                sql_params.append(tracen_kubun)
            if hanro_time_4f_max is not None:
                hanro_conds.append("CAST(h.time_gokei_4furlong AS INTEGER) <= %s")
                sql_params.append(hanro_time_4f_max)
            if hanro_laptime_1f_max is not None:
                hanro_conds.append("h.lap_time_1furlong NOT IN ('000', '999')")
                hanro_conds.append("CAST(h.lap_time_1furlong AS INTEGER) <= %s")
                sql_params.append(hanro_laptime_1f_max)
            hanro_where = " AND ".join(hanro_conds)
            cte_parts.append(f"""
    hanro_qualified AS (
        SELECT DISTINCT h.ketto_toroku_bango
        FROM hanro_chokyo h
        JOIN debut_horses d ON h.ketto_toroku_bango = d.ketto_toroku_bango
        WHERE h.chokyo_nengappi < d.debut_date
          AND {hanro_where}
    )""")

        cte_parts.append("""
    winners AS (
        SELECT DISTINCT ketto_toroku_bango
        FROM umagoto_race_joho
        WHERE kakutei_chakujun = '01'
          AND kaisai_nen || kaisai_gappi BETWEEN %s AND %s
    )""")
        sql_params.extend([debut_date_from, debut_date_to])

        if use_wood and use_hanro:
            qualified_from = (
                "(SELECT ketto_toroku_bango FROM wood_qualified "
                "INTERSECT "
                "SELECT ketto_toroku_bango FROM hanro_qualified) qualified"
            )
        elif use_wood:
            qualified_from = "wood_qualified qualified"
        elif use_hanro:
            qualified_from = "hanro_qualified qualified"
        else:
            qualified_from = "debut_horses qualified"

        cte_sql = ",".join(cte_parts)
        sql = f"""
    WITH {cte_sql}
    SELECT
        COUNT(DISTINCT qualified.ketto_toroku_bango) AS total,
        COUNT(DISTINCT CASE WHEN winners.ketto_toroku_bango IS NOT NULL
            THEN qualified.ketto_toroku_bango END) AS winners
    FROM {qualified_from}
    LEFT JOIN winners ON qualified.ketto_toroku_bango = winners.ketto_toroku_bango
        """

        df = manager.fetch_dataframe(sql, params=tuple(sql_params))
        row = df.iloc[0]
        total = int(row["total"])
        win_count = int(row["winners"])
        return {
            "success": True,
            "debut_date_from": debut_date_from,
            "debut_date_to": debut_date_to,
            "total": total,
            "winners": win_count,
            "win_rate": round(win_count / total * 100, 1) if total > 0 else 0.0,
        }
    except MykeibaDBError as e:
        return {"success": False, "error": str(e)}


def analyze_race_chakudo(
    manager: ConnectionManager,
    group_expr: str,
    sort_expr: str,
    race_name: str | None = None,
    keibajo: str | None = None,
    kyori: int | None = None,
    year_from: str | None = None,
    year_to: str | None = None,
    grade: str | None = None,
    course_kubun: str | None = None,
    week_in_course: int | None = None,
) -> dict[str, Any]:
    """レース結果を指定グループ別に着度数・勝率・複勝率・回収率で集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        group_expr (str): グループ化SQL式（SELECT句に埋め込む）
        sort_expr (str): ソートSQL式（ORDER BY句に埋め込む）
        race_name (str | None): レース名（部分一致）
        keibajo (str | None): 競馬場コード
        kyori (int | None): 距離（メートル）
        year_from (str | None): 集計開始年（4桁文字列）
        year_to (str | None): 集計終了年（4桁文字列）
        grade (str | None): グレードコード
        course_kubun (str | None): コース区分（week_in_courseと共に指定）
        week_in_course (int | None): コース使用開始からの週番号（course_kubunと共に指定）

    Returns:
        dict: 集計結果を含む辞書
    """
    try:
        params: list[Any] = []
        cte_parts: list[str] = []
        join_sql = ""

        using_cw = course_kubun is not None and week_in_course is not None
        if using_cw:
            cte_sql, join_sql = _build_course_week_cte(
                keibajo, course_kubun, week_in_course, params  # type: ignore[arg-type]
            )
            cte_parts.append(cte_sql)

        cte_parts.append(
            """fukusho_payouts AS (
            SELECT race_code, fukusho1_umaban AS umaban,
                   CAST(TRIM(fukusho1_haraimodoshikin) AS INTEGER) AS payout
            FROM haraimodoshi
            WHERE TRIM(fukusho1_haraimodoshikin) ~ '^[0-9]+'
              AND TRIM(fukusho1_haraimodoshikin)::INTEGER > 0
            UNION ALL
            SELECT race_code, fukusho2_umaban,
                   CAST(TRIM(fukusho2_haraimodoshikin) AS INTEGER)
            FROM haraimodoshi WHERE TRIM(fukusho2_haraimodoshikin) ~ '^[0-9]+'
              AND TRIM(fukusho2_haraimodoshikin)::INTEGER > 0
            UNION ALL
            SELECT race_code, fukusho3_umaban,
                   CAST(TRIM(fukusho3_haraimodoshikin) AS INTEGER)
            FROM haraimodoshi WHERE TRIM(fukusho3_haraimodoshikin) ~ '^[0-9]+'
              AND TRIM(fukusho3_haraimodoshikin)::INTEGER > 0
        )"""
        )
        cte_parts.append(
            """tansho_payouts AS (
            SELECT race_code, tansho1_umaban AS umaban,
                   CAST(TRIM(tansho1_haraimodoshikin) AS INTEGER) AS payout
            FROM haraimodoshi WHERE TRIM(tansho1_haraimodoshikin) ~ '^[0-9]+'
              AND TRIM(tansho1_haraimodoshikin)::INTEGER > 0
        )"""
        )

        where_parts: list[str] = [
            "u.kakutei_chakujun != '00'",
            "u.kakutei_chakujun ~ '^[0-9]+'",
        ]
        if race_name:
            where_parts.append("r.race_name LIKE %s")
            params.append(f"%{race_name}%")
        if keibajo and not using_cw:
            where_parts.append("r.keibajo_code = %s")
            params.append(keibajo)
        if kyori:
            where_parts.append("r.kyori = %s")
            params.append(kyori)
        if year_from:
            where_parts.append("r.kaisai_nen >= %s")
            params.append(year_from)
        if year_to:
            where_parts.append("r.kaisai_nen <= %s")
            params.append(year_to)
        if grade:
            where_parts.append("r.grade_code = %s")
            params.append(grade)

        where_clause = "\n              AND ".join(where_parts)
        cte_parts.append(
            f"""base AS (
            SELECT
                {group_expr} AS grp,
                {sort_expr} AS sort_key,
                u.kakutei_chakujun,
                u.umaban,
                u.race_code
            FROM umagoto_race_joho u
            JOIN race_joho r ON u.race_code = r.race_code
            {join_sql}
            WHERE {where_clause}
        )"""
        )

        sql = f"""
            WITH {", ".join(cte_parts)}
            SELECT
                grp,
                sort_key,
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE kakutei_chakujun = '01') AS wins,
                COUNT(*) FILTER (WHERE kakutei_chakujun = '02') AS second,
                COUNT(*) FILTER (WHERE kakutei_chakujun = '03') AS third,
                COUNT(*) FILTER (
                    WHERE kakutei_chakujun NOT IN ('01', '02', '03')
                ) AS chakugai,
                ROUND(
                    COUNT(*) FILTER (WHERE kakutei_chakujun = '01')
                    * 100.0 / NULLIF(COUNT(*), 0), 1
                ) AS win_rate,
                ROUND(
                    COUNT(*) FILTER (WHERE kakutei_chakujun IN ('01', '02', '03'))
                    * 100.0 / NULLIF(COUNT(*), 0), 1
                ) AS fukusho_rate,
                ROUND(
                    COALESCE(SUM(tp.payout), 0) * 1.0 / NULLIF(COUNT(*), 0), 1
                ) AS tansho_kaishuu,
                ROUND(
                    COALESCE(SUM(fp.payout), 0) * 1.0 / NULLIF(COUNT(*), 0), 1
                ) AS fukusho_kaishuu
            FROM base
            LEFT JOIN tansho_payouts tp
                ON base.race_code = tp.race_code AND base.umaban = tp.umaban
            LEFT JOIN fukusho_payouts fp
                ON base.race_code = fp.race_code AND base.umaban = fp.umaban
            GROUP BY grp, sort_key
            ORDER BY sort_key
        """

        df = manager.fetch_dataframe(sql, params=tuple(params))
        results = []
        for _, row in df.iterrows():
            results.append({
                "group": str(row["grp"]),
                "total": int(row["total"]),
                "wins": int(row["wins"]),
                "second": int(row["second"]),
                "third": int(row["third"]),
                "chakugai": int(row["chakugai"]),
                "win_rate": float(row["win_rate"]) if pd.notna(row["win_rate"]) else 0.0,
                "fukusho_rate": (
                    float(row["fukusho_rate"]) if pd.notna(row["fukusho_rate"]) else 0.0
                ),
                "tansho_kaishuu": (
                    float(row["tansho_kaishuu"]) if pd.notna(row["tansho_kaishuu"]) else 0.0
                ),
                "fukusho_kaishuu": (
                    float(row["fukusho_kaishuu"]) if pd.notna(row["fukusho_kaishuu"]) else 0.0
                ),
            })
        return {"success": True, "count": len(results), "results": results}
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


def _fmt_time4(val: str) -> str | None:
    """4桁タイム文字列（0.1秒単位）を秒表記に変換する。センチネル値はNoneを返す。"""
    if not val or val in ("0000", "9999"):
        return None
    return f"{int(val) / 10:.1f}秒"


def _fmt_lap3(val: str) -> str | None:
    """3桁ラップタイム文字列（0.1秒単位）を秒表記に変換する。センチネル値はNoneを返す。"""
    if not val or val in ("000", "999"):
        return None
    return f"{int(val) / 10:.1f}秒"
