"""桌面端入口：初始化日志、主题、连接与主窗口。"""

import argparse
import logging
import sys
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app import specs, theme
from app.context import AppContext
from ui.dialogs import LoginDialog
from ui.main_window import MainWindow
from utils import config as config_util
from utils.logging_setup import install_excepthook, setup_logging

log = logging.getLogger(__name__)


def parse_args(argv):
    parser = argparse.ArgumentParser(description="学生选课与成绩管理系统 桌面端")
    parser.add_argument("--profile", help="启动时使用的连接档案名")
    parser.add_argument("--skip-login", action="store_true", help="跳过登录直接进入")
    parser.add_argument("--role", choices=["ADMIN", "TEACHER", "STUDENT"],
                        help="跳过登录时使用的角色")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    app = QApplication(sys.argv[:1])
    app.setApplicationName("EduDesktop")
    app.setOrganizationName("SCUT_DB")
    app.setDesktopFileName("edu-desktop")
    root = config_util.app_root()
    setup_logging(root / "logs", level="INFO")
    icon_path = config_util.resource_path("resources/icon.png")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    settings = QSettings("SCUT_DB", "EduDesktop")
    theme.apply_theme(app, str(settings.value("theme", theme.LIGHT)))

    context = AppContext()
    specs.register(context.entities)
    if args.profile and args.profile in context.config.get("profiles", {}):
        context.switch_profile(args.profile, context.config["profiles"][args.profile])

    def report_exception(exc_type, exc_value, exc_tb):
        QMessageBox.critical(
            None, "未处理的异常",
            f"{exc_type.__name__}: {exc_value}\n\n详细信息已写入 logs/desktop.log")

    install_excepthook(report_exception)
    log.info("启动桌面端：连接 %s，配置文件 %s", context.profile_name, config_util.config_file())

    window = MainWindow(context)
    window.show()
    if not args.skip_login:
        dialog = LoginDialog(context, window)
        dialog.exec()
    elif args.role:
        context.set_account({"username": f"console-{args.role.lower()}", "role": args.role})
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
