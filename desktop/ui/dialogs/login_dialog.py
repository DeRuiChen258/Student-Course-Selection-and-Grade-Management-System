"""登录对话框：校验 sys_account 并按角色裁剪功能。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout)

from ui.widgets import Notifier


class LoginDialog(QDialog):
    def __init__(self, context, parent=None, allow_skip=True):
        super().__init__(parent)
        self.context = context
        self.allow_skip = allow_skip
        self.account = None
        self.setWindowTitle("登录 · 学生选课与成绩管理系统")
        self.setMinimumWidth(430)
        root = QVBoxLayout(self)
        root.setSpacing(12)
        title = QLabel("登录")
        title.setObjectName("DialogTitle")
        subtitle = QLabel("账号存于 sys_account 表，口令按 salt$SHA-256(salt+口令) 校验；"
                          "角色决定可见页面与可用动作。")
        subtitle.setObjectName("DialogHint")
        subtitle.setWordWrap(True)
        root.addWidget(title)
        root.addWidget(subtitle)

        form = QFormLayout()
        self.profile_box = QComboBox()
        for name, profile in (context.config.get("profiles") or {}).items():
            self.profile_box.addItem(f"{profile.get('label', name)} "
                                     f"({profile.get('host')}:{profile.get('port')})", name)
        current = self.profile_box.findData(context.profile_name)
        if current >= 0:
            self.profile_box.setCurrentIndex(current)
        self.username = QLineEdit("admin")
        self.username.setPlaceholderText("admin / teacher01 / student01")
        self.password = QLineEdit("Admin@123")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("演示口令：Admin@123 / Teacher@123 / Student@123")
        form.addRow("数据库连接", self.profile_box)
        form.addRow("用户名", self.username)
        form.addRow("口令", self.password)
        root.addLayout(form)

        self.error = QLabel("")
        self.error.setObjectName("ErrorText")
        self.error.setWordWrap(True)
        self.error.setVisible(False)
        root.addWidget(self.error)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.skip_button = QPushButton("以管理员身份进入")
        self.skip_button.setObjectName("Ghost")
        self.skip_button.setVisible(allow_skip)
        self.login_button = QPushButton("登录")
        self.login_button.setObjectName("Primary")
        self.login_button.setDefault(True)
        buttons.addWidget(self.skip_button)
        buttons.addWidget(self.login_button)
        root.addLayout(buttons)

        self.login_button.clicked.connect(self.try_login)
        self.skip_button.clicked.connect(self.accept)
        self.password.returnPressed.connect(self.try_login)
        self.username.returnPressed.connect(self.try_login)

    def try_login(self):
        self.error.setVisible(False)
        name = self.profile_box.currentData()
        if name and name != self.context.profile_name:
            profile = self.context.config["profiles"][name]
            self.context.switch_profile(name, profile)
        self.login_button.setEnabled(False)
        self.login_button.setText("登录中…")
        self.context.runner.run(
            lambda: self.context.auth.login(self.username.text().strip(),
                                            self.password.text()),
            self._on_ok, self._on_err, self._on_done)

    def _on_done(self):
        self.login_button.setEnabled(True)
        self.login_button.setText("登录")

    def _on_ok(self, account):
        self.account = account
        self.context.set_account(account)
        self.accept()

    def _on_err(self, code, message):
        self.error.setText(f"登录失败：{message}")
        self.error.setVisible(True)
        Notifier.warn(self, f"登录失败：{message}")
