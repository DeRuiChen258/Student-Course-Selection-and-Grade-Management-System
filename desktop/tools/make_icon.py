"""从一张方形插画生成多尺寸应用图标（居中裁剪 + 平滑缩放）。

用法：.venv/bin/python tools/make_icon.py [源图片路径]
输出：resources/icon.png（512 主图）与 resources/icons/edu-desktop_<size>.png
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

SIZES = (16, 24, 32, 48, 64, 128, 256, 512)
ROOT_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT_DIR / "resources" / "icon-source.png"


def build(source, out_dir, master_path):
    image = QImage(str(source))
    if image.isNull():
        raise SystemExit(f"[失败] 无法读取图片：{source}")
    side = min(image.width(), image.height())
    cropped = image.copy((image.width() - side) // 2, (image.height() - side) // 2, side, side)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for size in SIZES:
        scaled = cropped.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        target = out_dir / f"edu-desktop_{size}.png"
        scaled.save(str(target), "PNG")
        written.append(target)
    master = cropped.scaled(512, 512, Qt.KeepAspectRatio, Qt.SmoothTransformation)
    master.save(str(master_path), "PNG")
    return side, written, master_path


def main(argv):
    app = QApplication(sys.argv[:1])
    source = Path(argv[1]) if len(argv) > 1 else Path(DEFAULT_SOURCE)
    if not source.exists():
        raise SystemExit(f"[失败] 源图片不存在：{source}\n"
                         f"用法：.venv/bin/python tools/make_icon.py <方形图片路径>")
    side, written, master = build(source, ROOT_DIR / "resources" / "icons",
                                  ROOT_DIR / "resources" / "icon.png")
    print(f"[图标] 源图 {source.name} 裁剪为 {side}×{side}，"
          f"生成 {len(written)} 个尺寸，主图 {master.relative_to(ROOT_DIR)}")
    app.quit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
