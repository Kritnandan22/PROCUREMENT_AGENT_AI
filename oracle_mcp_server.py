"""
Oracle EBS MCP Server
Provides tools to connect, test, and query an Oracle EBS database.
Connection: apps/apps @ 161.118.185.249:1521 (thick mode — Oracle Instant Client required)
"""

import json
import os
import traceback
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import oracledb
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
load_dotenv(Path(__file__).with_name(".env"))

DB_HOST = os.getenv("DB_HOST", "161.118.185.249")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SID = os.getenv("DB_SID", "EBSDB")
DB_SERVICE_NAME = os.getenv("DB_SERVICE_NAME", "ebs_EBSDB")

APPS_USER = os.getenv("APPS_USER", "apps")
APPS_PASSWORD = os.getenv("APPS_PASSWORD", "apps")

# ---------------------------------------------------------------------------
# Thick mode — required for Oracle Native Network Encryption (EBS default)
# Set ORACLE_CLIENT_PATH in .env to the Instant Client folder, e.g.:
#   ORACLE_CLIENT_PATH=C:\oracle\instantclient_21_15
# ---------------------------------------------------------------------------
ORACLE_CLIENT_PATH = os.getenv("ORACLE_CLIENT_PATH", "")


def _init_thick_mode() -> bool:
    """Initialise thick mode. Returns True on success, False if client not found."""
    try:
        if ORACLE_CLIENT_PATH:
            oracledb.init_oracle_client(lib_dir=ORACLE_CLIENT_PATH)
        else:
            oracledb.init_oracle_client()   # rely on PATH / LD_LIBRARY_PATH
        return True
    except Exception as exc:
        print(f"[WARN] Thick mode init failed: {exc}")
        print("[WARN] Falling back to thin mode — NNE-encrypted DBs will fail.")
        return False


THICK_MODE = _init_thick_mode()

POOL_MIN = int(os.getenv("POOL_MIN", "1"))
POOL_MAX = int(os.getenv("POOL_MAX", "5"))
POOL_INCREMENT = int(os.getenv("POOL_INCREMENT", "1"))
STMT_CACHE_SIZE = int(os.getenv("STMT_CACHE_SIZE", "100"))

# ---------------------------------------------------------------------------
# DSN builder
# ---------------------------------------------------------------------------


def _build_dsn() -> str:
    """Build Oracle DSN. Prefers SID; falls back to SERVICE_NAME."""
    if DB_SID:
        return oracledb.makedsn(DB_HOST, DB_PORT, sid=DB_SID)
    if DB_SERVICE_NAME:
        return oracledb.makedsn(DB_HOST, DB_PORT, service_name=DB_SERVICE_NAME)
    raise ValueError("Set DB_SID or DB_SERVICE_NAME in .env")


DSN = _build_dsn()

# ---------------------------------------------------------------------------
# Connection pool (lazy-init, module-level singleton)
# ---------------------------------------------------------------------------
_pool: oracledb.ConnectionPool | None = None


def _get_pool() -> oracledb.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = oracledb.create_pool(
            user=APPS_USER,
            password=APPS_PASSWORD,
            dsn=DSN,
            min=POOL_MIN,
            max=POOL_MAX,
            increment=POOL_INCREMENT,
            stmtcachesize=STMT_CACHE_SIZE,
            getmode=oracledb.POOL_GETMODE_WAIT,
        )
    return _pool


@contextmanager
def _conn():
    """Yield a connection from the pool, auto-return on exit."""
    pool = _get_pool()
    conn = pool.acquire()
    try:
        yield conn
    finally:
        pool.release(conn)


def _rows_to_dicts(cursor: oracledb.Cursor) -> list[dict[str, Any]]:
    """Convert cursor rows to list of dicts using column names."""
    if cursor.description is None:
        return []
    cols = [d[0].lower() for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def _ok(data: Any, **extra) -> str:
    return json.dumps({"status": "ok", **extra, "data": data}, default=str)


def _err(msg: str, detail: str = "") -> str:
    return json.dumps({"status": "error", "message": msg, "detail": detail})


# ---------------------------------------------------------------------------
# MCP server
# ---------------------------------------------------------------------------
_host = os.getenv("MCP_HOST", "0.0.0.0")
_port = int(os.getenv("MCP_PORT", "8100"))

mcp = FastMCP(
    "oracle-ebs",
    instructions="Oracle EBS database MCP server for connect, test, and query operations.",
    host=_host,
    port=_port,
)


# ---------------------------------------------------------------------------
# Tool: test_connection
# ---------------------------------------------------------------------------
@mcp.tool()
def test_connection() -> str:
    """
    Test the Oracle DB connection.
    Returns server version, current user, and timestamp from the DB.
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT VERSION, USER, SYSDATE FROM V$INSTANCE, DUAL"
                )
                row = cur.fetchone()
                if row:
                    version, user, sysdate = row
                    return _ok(
                        {
                            "db_version": version,
                            "connected_user": user,
                            "db_sysdate": str(sysdate),
                            "host": DB_HOST,
                            "port": DB_PORT,
                            "sid": DB_SID or "(service_name used)",
                        },
                        message="Connection successful",
                    )
                return _err("Query returned no rows — unexpected.")
    except oracledb.DatabaseError as exc:
        (error,) = exc.args
        return _err(
            f"ORA-{error.code}: {error.message.strip()}",
            detail=f"DSN={DSN}  USER={APPS_USER}",
        )
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Tool: get_db_info
# ---------------------------------------------------------------------------
@mcp.tool()
def get_db_info() -> str:
    """
    Return key Oracle instance/database metadata:
    DB name, host, version, NLS settings, open mode, pool stats.
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        d.NAME          AS db_name,
                        d.DB_UNIQUE_NAME,
                        d.OPEN_MODE,
                        i.HOST_NAME,
                        i.VERSION,
                        i.INSTANCE_NAME,
                        i.STATUS,
                        i.STARTUP_TIME
                    FROM V$DATABASE d, V$INSTANCE i
                    """
                )
                info = _rows_to_dicts(cur)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT PARAMETER, VALUE
                    FROM NLS_DATABASE_PARAMETERS
                    WHERE PARAMETER IN (
                        'NLS_CHARACTERSET','NLS_LANGUAGE',
                        'NLS_TERRITORY','NLS_DATE_FORMAT'
                    )
                    """
                )
                nls = {r[0]: r[1] for r in cur.fetchall()}

        pool = _get_pool()
        pool_stats = {
            "open_count": pool.opened,
            "busy_count": pool.busy,
            "max": pool.max,
        }

        return _ok(
            {"instance": info[0] if info else {},
                "nls": nls, "pool": pool_stats}
        )
    except oracledb.DatabaseError as exc:
        (error,) = exc.args
        return _err(f"ORA-{error.code}: {error.message.strip()}")
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Tool: list_tables
# ---------------------------------------------------------------------------
@mcp.tool()
def list_tables(schema: str = "APPS", name_filter: str = "") -> str:
    """
    List tables in a schema.

    Args:
        schema: Oracle schema name (default: APPS).
        name_filter: Optional substring filter on table name (case-insensitive).
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                sql = """
                    SELECT OWNER, TABLE_NAME, NUM_ROWS, LAST_ANALYZED
                    FROM ALL_TABLES
                    WHERE OWNER = :owner
                """
                params: dict[str, Any] = {"owner": schema.upper()}
                if name_filter:
                    sql += " AND TABLE_NAME LIKE :filter"
                    params["filter"] = f"%{name_filter.upper()}%"
                sql += " ORDER BY TABLE_NAME"
                cur.execute(sql, params)
                rows = _rows_to_dicts(cur)
        return _ok(rows, count=len(rows), schema=schema.upper())
    except oracledb.DatabaseError as exc:
        (error,) = exc.args
        return _err(f"ORA-{error.code}: {error.message.strip()}")
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Tool: execute_query
# ---------------------------------------------------------------------------
@mcp.tool()
def execute_query(sql: str, max_rows: int = 100) -> str:
    """
    Execute a read-only SELECT query and return results as JSON.

    Args:
        sql: A SELECT statement (DML/DDL is rejected).
        max_rows: Maximum rows to return (default 100, max 1000).
    """
    sql_clean = sql.strip().upper()
    if not sql_clean.startswith("SELECT") and not sql_clean.startswith("WITH"):
        return _err("Only SELECT (or WITH ... SELECT) queries are allowed.")

    max_rows = min(max_rows, 1000)

    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql.strip())
                cur.rowfactory = None   # use default
                rows = _rows_to_dicts(cur)
                truncated = len(rows) > max_rows
                rows = rows[:max_rows]
        return _ok(rows, count=len(rows), truncated=truncated)
    except oracledb.DatabaseError as exc:
        (error,) = exc.args
        return _err(f"ORA-{error.code}: {error.message.strip()}")
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Tool: describe_table
# ---------------------------------------------------------------------------
@mcp.tool()
def describe_table(table_name: str, schema: str = "APPS") -> str:
    """
    Describe columns of a table (name, type, nullable, comments).

    Args:
        table_name: Table name (case-insensitive).
        schema: Schema/owner (default: APPS).
    """
    try:
        with _conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        c.COLUMN_NAME,
                        c.DATA_TYPE,
                        c.DATA_LENGTH,
                        c.DATA_PRECISION,
                        c.DATA_SCALE,
                        c.NULLABLE,
                        c.COLUMN_ID,
                        cc.COMMENTS
                    FROM ALL_TAB_COLUMNS c
                    LEFT JOIN ALL_COL_COMMENTS cc
                        ON  cc.OWNER       = c.OWNER
                        AND cc.TABLE_NAME  = c.TABLE_NAME
                        AND cc.COLUMN_NAME = c.COLUMN_NAME
                    WHERE c.OWNER      = :owner
                      AND c.TABLE_NAME = :tname
                    ORDER BY c.COLUMN_ID
                    """,
                    {"owner": schema.upper(), "tname": table_name.upper()},
                )
                cols = _rows_to_dicts(cur)

        if not cols:
            return _err(
                f"Table {schema.upper()}.{table_name.upper()} not found "
                "or no SELECT privilege."
            )
        return _ok(cols, table=f"{schema.upper()}.{table_name.upper()}", column_count=len(cols))
    except oracledb.DatabaseError as exc:
        (error,) = exc.args
        return _err(f"ORA-{error.code}: {error.message.strip()}")
    except Exception as exc:
        return _err(str(exc), detail=traceback.format_exc())


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    transport = "sse" if "--sse" in sys.argv else "stdio"
    if transport == "sse":
        print(
            f"Starting Oracle EBS MCP server (SSE) on http://{_host}:{_port}/sse")
    else:
        print("Starting Oracle EBS MCP server (stdio)", file=sys.stderr)
    print(f"  DSN  : {DSN}", file=sys.stderr)
    print(f"  User : {APPS_USER}", file=sys.stderr)
    mcp.run(transport=transport)
