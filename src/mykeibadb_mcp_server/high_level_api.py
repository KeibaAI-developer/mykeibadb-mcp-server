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
) -> dict[str, Any]:
    """指定人気順位の勝率・複勝率・出走数・勝利数を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        ninki (int): 人気順位（デフォルト1）
        keibajo (str | None): 競馬場コード（例: '05'=東京）
        grade (str | None): グレードコード（例: 'A'=GI）
        year_from (str | None): 集計開始年（4桁文字列、例: '2020'）
        kyori (int | None): 距離（メートル単位）

    Returns:
        dict: 出走数・勝利数・勝率・複勝数・複勝率を含む辞書
    """
    try:
        ninki_str = str(ninki).zfill(2)
        where_clauses = [
            "u.ninki_juni = %s",
            "u.kakutei_chakujun != '00'",
        ]
        params: list[Any] = [ninki_str]

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            params.append(keibajo)
        if grade:
            where_clauses.append("r.grade_code = %s")
            params.append(grade)
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            params.append(year_from)
        if kyori:
            where_clauses.append("r.kyori = %s")
            params.append(str(kyori))

        where = " AND ".join(where_clauses)
        sql = f"""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1 THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3 THEN 1 ELSE 0 END) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            WHERE {where}
        """
        df = manager.fetch_dataframe(sql, params=tuple(params))
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
) -> dict[str, Any]:
    """騎手名（部分一致）で勝率・複勝率・騎乗数を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        kishu_name (str): 騎手名（部分一致で検索）
        keibajo (str | None): 競馬場コード
        year_from (str | None): 集計開始年
        kyori (int | None): 距離（メートル）

    Returns:
        dict: 騎手名・騎乗数・勝利数・勝率・複勝率を含む辞書
    """
    try:
        where_clauses = [
            "km.kishu_mei LIKE %s",
            "u.kakutei_chakujun != '00'",
        ]
        params: list[Any] = [f"%{kishu_name}%"]

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            params.append(keibajo)
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            params.append(year_from)
        if kyori:
            where_clauses.append("r.kyori = %s")
            params.append(str(kyori))

        where = " AND ".join(where_clauses)
        sql = f"""
            SELECT
                km.kishu_mei,
                COUNT(*) AS total,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1 THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3 THEN 1 ELSE 0 END) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            JOIN kishu_master km ON u.kishu_code = km.kishu_code
            WHERE {where}
            GROUP BY km.kishu_mei
            ORDER BY wins DESC
        """
        df = manager.fetch_dataframe(sql, params=tuple(params))
        results = []
        for _, row in df.iterrows():
            total = int(row["total"])
            wins = int(row["wins"])
            fukusho = int(row["fukusho"])
            results.append({
                "kishu_mei": row["kishu_mei"],
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
) -> dict[str, Any]:
    """種牡馬（父馬）名で産駒の勝率・複勝率を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        sire_name (str): 種牡馬名（部分一致で検索）
        keibajo (str | None): 競馬場コード
        kyori (int | None): 距離（メートル）
        year_from (str | None): 集計開始年

    Returns:
        dict: 種牡馬名・産駒出走数・勝利数・勝率・複勝率を含む辞書
    """
    try:
        where_clauses = [
            "k.chichi_uma_bamei LIKE %s",
            "u.kakutei_chakujun != '00'",
        ]
        params: list[Any] = [f"%{sire_name}%"]

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            params.append(keibajo)
        if kyori:
            where_clauses.append("r.kyori = %s")
            params.append(str(kyori))
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            params.append(year_from)

        where = " AND ".join(where_clauses)
        sql = f"""
            SELECT
                k.chichi_uma_bamei AS sire_name,
                COUNT(*) AS total,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1 THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3 THEN 1 ELSE 0 END) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            JOIN keito_joho2 k ON u.ketto_toroku_bango = k.ketto_toroku_bango
            WHERE {where}
            GROUP BY k.chichi_uma_bamei
            ORDER BY wins DESC
        """
        df = manager.fetch_dataframe(sql, params=tuple(params))
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
) -> dict[str, Any]:
    """馬名（部分一致）で過去レース戦績一覧を取得する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        uma_name (str): 馬名（部分一致で検索）
        year_from (str | None): 集計開始年

    Returns:
        dict: 日付・競馬場・レース名・着順・タイム・騎手を含む戦績リスト
    """
    try:
        where_clauses = ["km2.bamei LIKE %s"]
        params: list[Any] = [f"%{uma_name}%"]

        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            params.append(year_from)

        where = " AND ".join(where_clauses)
        sql = f"""
            SELECT
                km2.bamei,
                r.kaisai_nen,
                r.kaisai_gappi,
                r.keibajo_code,
                r.race_name,
                r.grade_code,
                r.kyori,
                u.kakutei_chakujun,
                u.soha_time,
                u.kishu_code,
                u.ninki_juni,
                u.tansho_odds
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            JOIN kyosoba_master2 km2 ON u.ketto_toroku_bango = km2.ketto_toroku_bango
            WHERE {where}
            ORDER BY r.kaisai_nen DESC, r.kaisai_gappi DESC
        """
        df = manager.fetch_dataframe(sql, params=tuple(params))
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
                "kishu_code": row["kishu_code"],
                "ninki_juni": row["ninki_juni"],
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
) -> dict[str, Any]:
    """枠番（1〜8）別の勝率・複勝率を集計する。

    Args:
        manager (ConnectionManager): DBコネクションマネージャ
        keibajo (str | None): 競馬場コード
        kyori (int | None): 距離（メートル）
        year_from (str | None): 集計開始年

    Returns:
        dict: 枠番ごとの出走数・勝利数・勝率・複勝率を含む辞書
    """
    try:
        where_clauses = ["u.kakutei_chakujun != '00'"]
        params: list[Any] = []

        if keibajo:
            where_clauses.append("r.keibajo_code = %s")
            params.append(keibajo)
        if kyori:
            where_clauses.append("r.kyori = %s")
            params.append(str(kyori))
        if year_from:
            where_clauses.append("r.kaisai_nen >= %s")
            params.append(year_from)

        where = " AND ".join(where_clauses)
        sql = f"""
            SELECT
                u.wakuban,
                COUNT(*) AS total,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) = 1 THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN CAST(u.kakutei_chakujun AS INTEGER) <= 3 THEN 1 ELSE 0 END) AS fukusho
            FROM umagoto_race_joho u
            JOIN race_shosai r ON u.race_code = r.race_code
            WHERE {where}
            GROUP BY u.wakuban
            ORDER BY u.wakuban
        """
        df = manager.fetch_dataframe(sql, params=tuple(params) if params else None)
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
