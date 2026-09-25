"""离屏截图：为答辩与实验报告生成 14 张页面 PNG。

用法：QT_QPA_PLATFORM=offscreen .venv/bin/python tools/capture_pages.py
"""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from app import specs, theme
from app.context import AppContext
from ui.main_window import MainWindow, PAGE_DEFS


def pump(app, seconds=1.2):
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)


def main():
    app = QApplication(sys.argv[:1])
    theme_name = sys.argv[1] if len(sys.argv) > 1 else "light"
    settings = QSettings("SCUT_DB", "EduDesktop")
    settings.setValue("theme", theme_name)
    settings.setValue("show_sql", "true")
    settings.sync()
    theme.apply_theme(app, theme_name)
    context = AppContext()
    specs.register(context.entities)
    window = MainWindow(context)
    window.resize(1600, 980)
    window.show()
    pump(app, 1.5)

    out_dir = Path(__file__).resolve().parent.parent / "out" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for index, (key, title, _tag, _factory) in enumerate(PAGE_DEFS, start=1):
        window.navigate(key)
        pump(app, 1.4)
        page = window.pages.get(key)
        if page is not None and hasattr(page, "table"):
            try:
                page.table.select_first()
            except Exception:
                pass
        pump(app, 0.4)
        path = out_dir / f"{index:02d}_{key}.png"
        window.grab().save(str(path))
        saved.append(path)
        print(f"[截图] {key} → {path.name}", flush=True)
    context.shutdown()
    print(f"\n共生成 {len(saved)} 张截图，目录：{out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
