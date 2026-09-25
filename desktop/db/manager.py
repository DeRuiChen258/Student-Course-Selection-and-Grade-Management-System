"""数据库门面：参数化查询、事务、存储过程调用与 SQL 追踪。"""

import logging
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass

import pymysql

from .errors import DbError, translate
from .pool import ConnectionPool

log = logging.getLogger(__name__)


def _quote(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("\\", "\\\\").replace("'", "''") + "'"


@dataclass
class SqlTrace:
    seq: int
    sql: str
    params: tuple = ()
    rows: int = 0
    elapsed_ms: float = 0.0
    at: str = ""
    ok: bool = True
    error: str = ""
    source: str = ""

    def rendered(self):
        text = self.sql
        for value in self.params or ():
            text = text.replace("%s", _quote(value), 1)
        return " ".join(text.split())


class Tx:
    """事务内使用的执行句柄。"""

    def __init__(self, conn, tracer):
        self._conn = conn
        self._tracer = tracer

    def execute(self, sql, params=()):
        return self._run(sql, params, fetch=False)

    def query(self, sql, params=()):
        return self._run(sql, params, fetch=True)

    def _run(self, sql, params, fetch):
        started = time.perf_counter()
        try:
            with self._conn.cursor(pymysql.cursors.DictCursor) as cur:
                if params:
                    cur.execute(sql, tuple(params))
                else:
                    cur.execute(sql)
                rows = cur.fetchall() if fetch else cur.rowcount
            self._tracer(sql, params, len(rows) if fetch else int(rows or 0),
                         (time.perf_counter() - started) * 1000, True, "")
            return rows
        except Exception as exc:
            err = translate(exc, sql)
            self._tracer(sql, params, 0, (time.perf_counter() - started) * 1000, False, str(err))
            raise err from exc


class DatabaseManager:
    def __init__(self, profile=None, pool_size=5, trace_size=200):
        self._pool = ConnectionPool(profile or {}, maxsize=pool_size)
        self._traces = deque(maxlen=trace_size)
        self._seq = 0
        self._lock = threading.Lock()
        self._listeners = []
        self.profile = dict(profile or {})
        self.last_health = {}

    def configure(self, profile):
        profile = dict(profile or {})
        self._pool.reset(profile)
        self.profile = profile
        self.last_health = {}

    def add_trace_listener(self, callback):
        if callback not in self._listeners:
            self._listeners.append(callback)

    @property
    def traces(self):
        return list(self._traces)

    def _record(self, sql, params, rows, elapsed_ms, ok, error, source):
        with self._lock:
            self._seq += 1
            seq = self._seq
        trace = SqlTrace(seq=seq, sql=sql, params=tuple(params or ()), rows=rows,
                         elapsed_ms=round(elapsed_ms, 2), at=time.strftime("%H:%M:%S"),
                         ok=ok, error=error, source=source)
        self._traces.append(trace)
        for callback in list(self._listeners):
            try:
                callback(trace)
            except Exception:
                log.debug("追踪回调失败", exc_info=True)
        return trace

    def _run(self, sql, params, fetch, source=""):
        started = time.perf_counter()
        try:
            with self._pool.connection() as conn:
                with conn.cursor(pymysql.cursors.DictCursor) as cur:
                    if params:
                        cur.execute(sql, tuple(params))
                    else:
                        cur.execute(sql)
                    result = cur.fetchall() if fetch else cur.rowcount
        except Exception as exc:
            err = translate(exc, sql)
            self._record(sql, params, 0, (time.perf_counter() - started) * 1000, False, str(err), source)
            log.warning("SQL 失败 %s | %s", err, " ".join(sql.split())[:180])
            raise err from exc
        elapsed = (time.perf_counter() - started) * 1000
        count = len(result) if fetch else int(result or 0)
        self._record(sql, params, count, elapsed, True, "", source)
        return result

    def query(self, sql, params=(), source=""):
        return self._run(sql, params, True, source)

    def query_one(self, sql, params=(), source=""):
        rows = self._run(sql, params, True, source)
        return rows[0] if rows else None

    def scalar(self, sql, params=(), source=""):
        row = self.query_one(sql, params, source)
        if not row:
            return None
        return next(iter(row.values()))

    def execute(self, sql, params=(), source=""):
        return self._run(sql, params, False, source)

    def executemany(self, sql, seq, source=""):
        started = time.perf_counter()
        seq = list(seq)
        if not seq:
            return 0
        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    total = cur.executemany(sql, seq)
        except Exception as exc:
            err = translate(exc, sql)
            self._record(sql, (f"{len(seq)} 行批量",), 0,
                         (time.perf_counter() - started) * 1000, False, str(err), source)
            raise err from exc
        elapsed = (time.perf_counter() - started) * 1000
        self._record(sql, (f"{len(seq)} 行批量",), int(total or 0), elapsed, True, "", source)
        return int(total or 0)

    def query_page(self, sql, count_sql, params=(), limit=20, offset=0, source=""):
        total = int(self.scalar(count_sql, params, source) or 0)
        rows = self.query(f"{sql} LIMIT %s OFFSET %s", tuple(params) + (int(limit), int(offset)), source)
        return rows, total

    def call_proc(self, name, in_args, out_names=("o_code", "o_msg"), source=""):
        in_args = tuple(in_args or ())
        placeholders = ", ".join(["%s"] * len(in_args))
        outs = ", ".join(f"@{n}" for n in out_names)
        call_sql = f"CALL {name}({placeholders}, {outs})"
        select_sql = "SELECT " + ", ".join(f"@{n} AS {n}" for n in out_names)
        with self._pool.connection() as conn:
            started = time.perf_counter()
            try:
                with conn.cursor(pymysql.cursors.DictCursor) as cur:
                    cur.execute(call_sql, tuple(in_args))
                    while cur.nextset():
                        pass
                    cur.execute(select_sql)
                    row = cur.fetchone() or {}
                self._record(call_sql, in_args, 1,
                             (time.perf_counter() - started) * 1000, True, "", source)
            except Exception as exc:
                err = translate(exc, call_sql)
                self._record(call_sql, in_args, 0,
                             (time.perf_counter() - started) * 1000, False, str(err), source)
                raise err from exc
        return tuple(row.get(n) for n in out_names)

    @contextmanager
    def transaction(self, source=""):
        conn = self._pool.acquire()
        try:
            conn.begin()
        except Exception:
            self._pool.discard(conn)
            raise
        tx = Tx(conn, lambda sql, params, rows, ms, ok, err: self._record(
            sql, params, rows, ms, ok, err, source))
        try:
            yield tx
            conn.commit()
        except Exception as exc:
            conn.rollback()
            raise (exc if isinstance(exc, DbError) else translate(exc)) from exc
        finally:
            self._pool.release(conn)

    def health(self):
        started = time.perf_counter()
        row = self.query_one(
            "SELECT VERSION() AS version, DATABASE() AS db_name, "
            "CURRENT_USER() AS db_user, @@sql_mode AS sql_mode", source="健康检查")
        row = row or {}
        row["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)
        row["profile"] = dict(self.profile)
        self.last_health = row
        return row

    def object_counts(self):
        return self.query_one(
            "SELECT (SELECT COUNT(*) FROM information_schema.tables "
            "        WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE') AS tables, "
            "       (SELECT COUNT(*) FROM information_schema.views "
            "        WHERE table_schema = DATABASE()) AS views, "
            "       (SELECT COUNT(*) FROM information_schema.triggers "
            "        WHERE trigger_schema = DATABASE()) AS triggers, "
            "       (SELECT COUNT(*) FROM information_schema.routines "
            "        WHERE routine_schema = DATABASE()) AS routines, "
            "       (SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics "
            "        WHERE table_schema = DATABASE() AND LEFT(index_name, 4) = 'idx_') AS named_indexes, "
            "       (SELECT COUNT(DISTINCT index_name) FROM information_schema.statistics "
            "        WHERE table_schema = DATABASE()) AS all_indexes",
            source="数据库对象自检")

    def close(self):
        self._pool.close_all()
