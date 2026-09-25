"""后台任务执行器：所有数据库调用经此进入线程池，主线程只处理界面。"""

import logging
import traceback

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal, Slot

from db.errors import DbError

log = logging.getLogger(__name__)


class WorkerSignals(QObject):
    succeeded = Signal(object)
    failed = Signal(str, str)
    finished = Signal()


class Job(QRunnable):
    def __init__(self, fn, args, kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()
        self.setAutoDelete(True)

    @Slot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except DbError as exc:
            self.signals.failed.emit(str(exc.code), str(exc.message))
        except Exception as exc:
            log.error("后台任务失败: %s\n%s", exc, traceback.format_exc())
            self.signals.failed.emit("TASK", str(exc))
        else:
            self.signals.succeeded.emit(result)
        finally:
            self.signals.finished.emit()


class AsyncRunner(QObject):
    def __init__(self, parent=None, max_threads=4):
        super().__init__(parent)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(max(2, max_threads))
        self._jobs = []

    def run(self, fn, on_ok=None, on_err=None, on_done=None, *args, **kwargs):
        job = Job(fn, args, kwargs)
        if on_ok:
            job.signals.succeeded.connect(on_ok)
        if on_err:
            job.signals.failed.connect(on_err)
        if on_done:
            job.signals.finished.connect(on_done)
        self._jobs.append(job)
        job.signals.finished.connect(lambda: self._forget(job))
        self._pool.start(job)
        return job

    def _forget(self, job):
        try:
            self._jobs.remove(job)
        except ValueError:
            pass

    def wait(self, timeout_ms=3000):
        return self._pool.waitForDone(timeout_ms)
