"""SELECT-only ガードモジュール."""

import re

_DANGEROUS_KEYWORDS: list[str] = [
    "DROP",
    "DELETE",
    "UPDATE",
    "INSERT",
    "CREATE",
    "ALTER",
    "TRUNCATE",
    "REPLACE",
    "MERGE",
    "GRANT",
    "REVOKE",
]


def validate_select_only(sql: str) -> None:
    """SELECT 文以外を拒否する。

    Args:
        sql (str): 検証するSQL文字列

    Raises:
        ValueError: 危険キーワード検出・複文・SELECT なし の場合
    """
    stripped = sql.rstrip().rstrip(";")
    if ";" in stripped:
        raise ValueError("複文は許可されていません")

    sql_upper = sql.upper()
    for kw in _DANGEROUS_KEYWORDS:
        if re.search(r"\b" + kw + r"\b", sql_upper):
            raise ValueError(f"危険なキーワードが検出されました: {kw}")

    if not re.search(r"\bSELECT\b", sql_upper):
        raise ValueError("SELECT文のみ許可されています")
