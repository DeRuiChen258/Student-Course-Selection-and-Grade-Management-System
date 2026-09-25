"""系统设置：主题、分页、日志与连接信息。"""

import logging

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (QApplication, QComboBox, QFormLayout, QHBoxLayout, QLabel,
                               QPushButton, QSpinBox, QVBoxLayout, QWidget)

from app import theme
from utils.config import config_file, mask_password
from ui.widgets import Notifier, PageBase


class SettingsPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "系统设置", (),
                         "主题、分页大小与日志级别通过 QSettings 持久化；连接参数保存在 "
                         "config/connection.json（口令打码显示）。", page_key="settings",
                         parent=parent)
        self.settings = QSettings("SCUT_DB", "EduDesktop")
        body = QWidget()
        form = QFormLayout(body)
        self.theme_box = QComboBox()
        self.theme_box.addItem("浅色（答辩推荐）", theme.LIGHT)
        self.theme_box.addItem("深色", theme.DARK)
        current = self.settings.value("theme", theme.LIGHT)
        self.theme_box.setCurrentIndex(1 if current == theme.DARK else 0)
        self.page_size_box = QSpinBox()
        self.page_size_box.setRange(10, 200)
        self.page_size_box.setValue(int(self.settings.value("page_size", 20)))
        self.log_box = QComboBox()
        self.log_box.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_box.setCurrentText(str(self.settings.value("log_level", "INFO")))
        form.addRow("界面主题", self.theme_box)
        form.addRow("每页条数", self.page_size_box)
        form.addRow("日志级别", self.log_box)
        buttons = QHBoxLayout()
        self.save_button = QPushButton("保存并应用")
        self.save_button.setObjectName("Primary")
        self.reload_button = QPushButton("重新读取设置")
        self.reload_button.setObjectName("Ghost")
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.reload_button)
        buttons.addStretch(1)
        holder = QWidget()
        holder_layout = QVBoxLayout(holder)
        holder_layout.addWidget(body)
        holder_layout.addLayout(buttons)
        holder_layout.addWidget(self._info_panel())
        holder_layout.addStretch(1)
        self.root.addWidget(holder, 1)
        self.save_button.clicked.connect(self.apply_settings)
        self.reload_button.clicked.connect(self.reload)
        self.theme_box.currentIndexChanged.connect(lambda: self.apply_settings(quiet=True))

    def _info_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 12, 0, 0)
        title = QLabel("当前连接")
        title.setObjectName("SectionTitle")
        layout.addWidget(title)
        info = dict(self.context.profile)
        info["profile"] = self.context.profile_name
        text = QLabel(mask_password(info))
        text.setObjectName("HintLabel")
        text.setWordWrap(True)
        layout.addWidget(text)
        path = QLabel(f"配置文件：{config_file()}")
        path.setObjectName("HintLabel")
        path.setWordWrap(True)
        layout.addWidget(path)
        role = QLabel(f"当前账号：{self.context.username} · 角色 {self.context.role_label}")
        role.setObjectName("HintLabel")
        layout.addWidget(role)
        return panel

    def on_enter(self, **_):
        pass

    def reload(self):
        self.settings.sync()
        self.page_size_box.setValue(int(self.settings.value("page_size", 20)))
        self.log_box.setCurrentText(str(self.settings.value("log_level", "INFO")))
        Notifier.info(self, "已重新读取设置")

    def apply_settings(self, quiet=False):
        self.settings.setValue("theme", self.theme_box.currentData())
        self.settings.setValue("page_size", self.page_size_box.value())
        self.settings.setValue("log_level", self.log_box.currentText())
        self.settings.sync()
        app = QApplication.instance()
        if app is not None:
            theme.apply_theme(app, self.theme_box.currentData())
        logging.getLogger().setLevel(
            getattr(logging, self.log_box.currentText(), logging.INFO))
        if not quiet:
            Notifier.success(self, "设置已保存并应用")
