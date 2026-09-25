"""主题：浅色 / 深色 QSS 切换。"""

import logging
from pathlib import Path

from utils.config import resource_path

log = logging.getLogger(__name__)

LIGHT = "light"
DARK = "dark"


def load_qss(name):
    path = resource_path(Path("resources") / f"{name}.qss")
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        log.warning("样式文件缺失: %s", path)
        return ""


def apply_theme(app, name=LIGHT):
    app.setStyleSheet(load_qss(name if name in (LIGHT, DARK) else LIGHT))
