"""日志：轮转文件 + 控制台，并接管未捕获异常。"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_FORMAT = "%(asctime)s | %(levelname)-7s | %(name)-24s | %(message)s"


def setup_logging(log_dir, level="INFO", console=True):
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    root.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    for handler in list(root.handlers):
        root.removeHandler(handler)
    file_handler = RotatingFileHandler(log_dir / "desktop.log", maxBytes=1_000_000,
                                       backupCount=5, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter(_FORMAT))
    root.addHandler(file_handler)
    if console:
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(logging.Formatter(_FORMAT))
        root.addHandler(stream)
    return root


def install_excepthook(callback=None):
    def handle(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.getLogger("未捕获异常").error("未处理异常", exc_info=(exc_type, exc_value, exc_tb))
        if callback:
            try:
                callback(exc_type, exc_value, exc_tb)
            except Exception:
                logging.getLogger("未捕获异常").exception("异常回调失败")

    sys.excepthook = handle
