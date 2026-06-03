"""validate_select_only のユニットテスト."""

import pytest

from mykeibadb_mcp_server.guard import validate_select_only

# 正常系


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM race_shosai",
        "SELECT race_code, race_name FROM race_shosai WHERE grade_code = 'A'",
        "SELECT COUNT(*) FROM umagoto_race_joho",
        "select * from race_shosai",
        "SELECT * FROM race_shosai;",
    ],
)
def test_validate_select_only_valid_queries(sql: str) -> None:
    """有効なSELECT文で例外が発生しない."""
    validate_select_only(sql)


# 準正常系

@pytest.mark.parametrize(
    "sql",
    [
        "DROP TABLE race_shosai",
        "DELETE FROM race_shosai WHERE 1=1",
        "UPDATE race_shosai SET grade_code = 'A'",
        "INSERT INTO race_shosai VALUES (1)",
        "CREATE TABLE tmp AS SELECT 1",
        "ALTER TABLE race_shosai ADD COLUMN foo TEXT",
        "TRUNCATE TABLE race_shosai",
        "REPLACE INTO race_shosai SELECT * FROM tmp",
        "GRANT ALL ON race_shosai TO user1",
        "REVOKE ALL ON race_shosai FROM user1",
    ],
)
def test_validate_select_only_raises_for_dangerous_keywords(sql: str) -> None:
    """危険なキーワードを含むSQLでValueErrorが発生する."""
    with pytest.raises(ValueError):
        validate_select_only(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT 1; DROP TABLE race_shosai",
        "SELECT * FROM foo; SELECT * FROM bar",
        "SELECT 1; DELETE FROM foo",
    ],
)
def test_validate_select_only_raises_for_multiple_statements(sql: str) -> None:
    """複文でValueErrorが発生する."""
    with pytest.raises(ValueError):
        validate_select_only(sql)


def test_validate_select_only_raises_for_no_select() -> None:
    """SELECT文を含まないSQLでValueErrorが発生する."""
    with pytest.raises(ValueError):
        validate_select_only("SHOW TABLES")


def test_validate_select_only_raises_error_message_for_dangerous_keyword() -> None:
    """危険なキーワードのエラーメッセージにキーワード名が含まれる."""
    with pytest.raises(ValueError, match="DROP"):
        validate_select_only("DROP TABLE race_shosai")
