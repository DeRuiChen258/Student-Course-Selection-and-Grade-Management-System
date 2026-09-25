"""轻量连接池：每个工作线程独占一条连接，避免 PyMySQL 跨线程复用。"""

import logging
import queue
import threading
from contextlib import contextmanager

import pymysql

from .errors import translate

log = logging.getLogger(__name__)


class ConnectionPool:
    def __init__(self, profile, maxsize=5):
        self._profile = dict(profile)
        self._max = max(2, int(maxsize))
        self._idle = queue.LifoQueue(self._max)
        self._lock = threading.Lock()
        self._created = 0
        self._closed = False

    @property
    def profile(self):
        return dict(self._profile)

    def _connect(self):
        p = self._profile
        return pymysql.connect(
            host=p.get("host", "127.0.0.1"),
            port=int(p.get("port", 3306)),
            user=p.get("user", "edu_app"),
            password=p.get("password", ""),
            database=p.get("database", "edu_system"),
            charset=p.get("charset", "utf8mb4"),
            connect_timeout=int(p.get("connect_timeout", 5)),
            read_timeout=int(p.get("read_timeout", 30)),
            autocommit=True,
        )

    def acquire(self, timeout=8.0):
        if self._closed:
            raise translate(RuntimeError("连接池已关闭"))
        conn = None
        try:
            conn = self._idle.get_nowait()
        except queue.Empty:
            with self._lock:
                if self._created < self._max:
                    self._created += 1
                    try:
                        return self._connect()
                    except Exception:
                        self._created -= 1
                        raise
            conn = self._idle.get(timeout=timeout)
        try:
            conn.ping(reconnect=True)
            return conn
        except Exception:
            self.discard(conn)
            return self.acquire(timeout)

    def release(self, conn):
        if conn is None:
            return
        if self._closed:
            self.discard(conn)
            return
        try:
            self._idle.put_nowait(conn)
        except queue.Full:
            self.discard(conn)

    def discard(self, conn):
        if conn is None:
            return
        try:
            conn.close()
        except Exception:
            pass
        with self._lock:
            self._created = max(0, self._created - 1)

    @contextmanager
    def connection(self):
        conn = self.acquire()
        ok = True
        try:
            yield conn
        except Exception:
            ok = False
            raise
        finally:
            if ok:
                self.release(conn)
            else:
                self.discard(conn)

    def close_all(self):
        self._closed = True
        while True:
            try:
                conn = self._idle.get_nowait()
            except queue.Empty:
                break
            try:
                conn.close()
            except Exception:
                pass
        with self._lock:
            self._created = 0

    def reset(self, profile=None):
        self.close_all()
        if profile:
            self._profile = dict(profile)
        self._closed = False
        self._idle = queue.LifoQueue(self._max)
