"""数据库连接配置：profile 管理 + 真实连通性测试。"""

from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit,
                               QPushButton, QSpinBox, QSplitter, QVBoxLayout, QWidget)
from PySide6.QtCore import Qt

from ui.widgets import Notifier


class ConnectionDialog(QDialog):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle("数据库连接配置")
        self.resize(880, 520)
        root = QVBoxLayout(self)
        title = QLabel("数据库连接配置")
        title.setObjectName("DialogTitle")
        hint = QLabel("连接参数保存在 config/connection.json（权限 600，已被 .gitignore 忽略）；"
                      "口令不写入任何源码，符合提交物红线 §11(2)。")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(hint)

        splitter = QSplitter(Qt.Horizontal)
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("连接档案"))
        self.list = QListWidget()
        left_layout.addWidget(self.list)
        left_buttons = QHBoxLayout()
        self.add_button = QPushButton("新建")
        self.add_button.setObjectName("Ghost")
        self.remove_button = QPushButton("删除")
        self.remove_button.setObjectName("Ghost")
        left_buttons.addWidget(self.add_button)
        left_buttons.addWidget(self.remove_button)
        left_layout.addLayout(left_buttons)
        splitter.addWidget(left)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        form = QFormLayout()
        self.label = QLineEdit()
        self.host = QLineEdit()
        self.port = QSpinBox()
        self.port.setRange(1, 65535)
        self.database = QLineEdit()
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.charset = QComboBox()
        self.charset.addItems(["utf8mb4", "utf8", "gbk"])
        self.timeout = QSpinBox()
        self.timeout.setRange(1, 60)
        form.addRow("显示名称", self.label)
        form.addRow("主机", self.host)
        form.addRow("端口", self.port)
        form.addRow("数据库", self.database)
        form.addRow("账号", self.user)
        form.addRow("口令", self.password)
        form.addRow("字符集", self.charset)
        form.addRow("连接超时（秒）", self.timeout)
        right_layout.addLayout(form)
        self.result = QPlainTextEdit()
        self.result.setReadOnly(True)
        self.result.setPlaceholderText("点击「测试连接」后显示 SELECT VERSION(), DATABASE(), "
                                       "CURRENT_USER() 的真实返回")
        self.result.setFixedHeight(130)
        right_layout.addWidget(self.result)
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.test_button = QPushButton("测试连接")
        self.save_button = QPushButton("保存并切换")
        self.save_button.setObjectName("Primary")
        self.close_button = QPushButton("关闭")
        self.close_button.setObjectName("Ghost")
        buttons.addWidget(self.test_button)
        buttons.addWidget(self.save_button)
        buttons.addWidget(self.close_button)
        right_layout.addLayout(buttons)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        root.addWidget(splitter, 1)

        self.list.currentItemChanged.connect(self._on_select)
        self.add_button.clicked.connect(self._add_profile)
        self.remove_button.clicked.connect(self._remove_profile)
        self.test_button.clicked.connect(self._test)
        self.save_button.clicked.connect(self._save)
        self.close_button.clicked.connect(self.accept)
        self._reload()

    def _reload(self, select=None):
        self.list.clear()
        profiles = self.context.config.get("profiles") or {}
        for name, profile in profiles.items():
            item = QListWidgetItem(f"{profile.get('label', name)}\n"
                                   f"{profile.get('host')}:{profile.get('port')}/"
                                   f"{profile.get('database')}")
            item.setData(Qt.UserRole, name)
            self.list.addItem(item)
        target = select or self.context.profile_name
        for index in range(self.list.count()):
            if self.list.item(index).data(Qt.UserRole) == target:
                self.list.setCurrentRow(index)
                break
        if self.list.count() and self.list.currentRow() < 0:
            self.list.setCurrentRow(0)

    def _current_name(self):
        item = self.list.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _on_select(self, *_):
        name = self._current_name()
        if not name:
            return
        profile = self.context.config["profiles"][name]
        self.label.setText(profile.get("label", name))
        self.host.setText(profile.get("host", ""))
        self.port.setValue(int(profile.get("port", 3306)))
        self.database.setText(profile.get("database", ""))
        self.user.setText(profile.get("user", ""))
        self.password.setText(profile.get("password", ""))
        self.charset.setCurrentText(profile.get("charset", "utf8mb4"))
        self.timeout.setValue(int(profile.get("connect_timeout", 5)))

    def _collect(self):
        return {
            "label": self.label.text().strip() or self._current_name(),
            "host": self.host.text().strip(),
            "port": self.port.value(),
            "database": self.database.text().strip(),
            "user": self.user.text().strip(),
            "password": self.password.text(),
            "charset": self.charset.currentText(),
            "connect_timeout": self.timeout.value(),
        }

    def _add_profile(self):
        name = f"profile{len(self.context.config.get('profiles') or {}) + 1}"
        self.context.config.setdefault("profiles", {})[name] = {
            "label": "新建连接", "host": "127.0.0.1", "port": 3306, "database": "edu_system",
            "user": "edu_app", "password": "", "charset": "utf8mb4", "connect_timeout": 5,
        }
        self._reload(select=name)

    def _remove_profile(self):
        name = self._current_name()
        if not name:
            return
        if name == self.context.profile_name:
            Notifier.warn(self, "当前正在使用的连接不能删除")
            return
        if Notifier.confirm(self, "删除连接档案", f"确认删除连接档案「{name}」？", danger=True):
            self.context.config["profiles"].pop(name, None)
            self._reload()

    def _test(self):
        profile = self._collect()
        self.result.setPlainText("正在连接…")
        self.context.runner.run(lambda: self._probe(profile), self._on_test_ok,
                                self._on_test_err)

    def _probe(self, profile):
        from db import DatabaseManager
        probe = DatabaseManager(profile)
        try:
            return probe.health()
        finally:
            probe.close()

    def _on_test_ok(self, health):
        self.result.setPlainText(
            f"连接成功\n"
            f"服务端版本 : {health.get('version')}\n"
            f"当前数据库 : {health.get('db_name')}\n"
            f"认证身份   : {health.get('db_user')}\n"
            f"往返耗时   : {health.get('elapsed_ms')} ms\n"
            f"sql_mode   : {health.get('sql_mode')}")
        Notifier.success(self, "连接成功")

    def _on_test_err(self, code, message):
        self.result.setPlainText(f"连接失败\n错误码: {code}\n原因  : {message}")
        Notifier.error(self, f"连接失败：{message}")

    def _save(self):
        name = self._current_name() or "default"
        profile = self._collect()
        self.context.switch_profile(name, profile)
        Notifier.success(self, f"已切换到「{profile['label']}」")
        self.accept()
