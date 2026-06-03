"""mykeibadb MCP Server."""

import os
import sys

from mcp.server.fastmcp import FastMCP
from mykeibadb.config import ConfigManager
from mykeibadb.connection import ConnectionManager
from mykeibadb.exceptions import MykeibaDBConnectionError

mcp = FastMCP("mykeibadb MCP Server")

_conn_manager: ConnectionManager | None = None


def _get_connection_manager() -> ConnectionManager:
    global _conn_manager
    if _conn_manager is None:
        config = ConfigManager.from_env()
        _conn_manager = ConnectionManager(config)
    return _conn_manager


def _check_db_connection() -> None:
    try:
        manager = _get_connection_manager()
        manager.execute_query("SELECT 1")
    except MykeibaDBConnectionError as e:
        raise RuntimeError(f"DB接続に失敗しました: {e}") from e


if __name__ == "__main__":
    _check_db_connection()
    if "--sse" in sys.argv:
        import uvicorn

        port = int(os.getenv("MCP_PORT", "8000"))
        host = os.getenv("MCP_HOST", "127.0.0.1")
        uvicorn.run(mcp.sse_app(), host=host, port=port)
    else:
        mcp.run()
