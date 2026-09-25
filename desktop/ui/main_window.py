"""主窗口：工具栏、左侧导航、工作区、详情抽屉、SQL 抽屉与状态栏。"""

import logging

from PySide6.QtCore import QSettings, Qt
from PySide6.QtWidgets import (QComboBox, QDockWidget, QHBoxLayout, QLabel, QListWidget,
                               QListWidgetItem, QMainWindow, QPushButton, QSizePolicy,
                               QStackedWidget, QStatusBar, QTabWidget, QToolBar, QVBoxLayout,
                               QWidget)

from models.table_model import Column
from ui.dialogs import ConnectionDialog, HelpDialog, LoginDialog
from ui.pages.dashboard import DashboardPage
from ui.pages.enrollments_page import make_page as make_enrollments_page
from ui.pages.grades import make_page as make_grades_page
from ui.pages.io_page import ImportExportPage
from ui.pages.logs import LogsPage
from ui.pages.permissions import PermissionsPage
from ui.pages.courses import make_page as make_courses_page
from ui.pages.offerings import make_page as make_offerings_page
from ui.pages.query import QueryPage
from ui.pages.settings import SettingsPage
from ui.pages.stats import StatsPage
from ui.pages.students import make_page as make_students_page
from ui.pages.table_browser import TableBrowserPage
from ui.pages.teachers import make_page as make_teachers_page
from ui.widgets import DataTable, Notifier, SqlPreview

log = logging.getLogger(__name__)

PAGE_DEFS = [
    ("dashboard", "数据仪表盘", "F16", lambda ctx: DashboardPage(ctx)),
    ("tables", "数据表浏览", "结构/索引", lambda ctx: TableBrowserPage(ctx)),
    ("query", "查询与筛选", "F04/F08", lambda ctx: QueryPage(ctx)),
    ("students", "学生管理", "F01–F04", make_students_page),
    ("teachers", "教师管理", "F09", make_teachers_page),
    ("courses", "课程管理", "F05–F08", make_courses_page),
    ("offerings", "开课管理", "F10", make_offerings_page),
    ("enrollments", "选课与成绩", "F11/F12/F15", make_enrollments_page),
    ("grades", "成绩管理", "F13/F14", make_grades_page),
    ("stats", "统计分析", "F16", lambda ctx: StatsPage(ctx)),
    ("logs", "操作日志", "审计", lambda ctx: LogsPage(ctx)),
    ("permissions", "权限管理", "账号/授权", lambda ctx: PermissionsPage(ctx)),
    ("io", "导入导出", "数据迁移", lambda ctx: ImportExportPage(ctx)),
    ("settings", "系统设置", "主题/分页", lambda ctx: SettingsPage(ctx)),
]


class DetailPanel(QWidget):
    """右侧详情抽屉：选中行的字段值 + 该表的外键 / CHECK / 索引。"""

    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        self.title = QLabel("在列表中选中一行查看详情")
        self.title.setObjectName("SectionTitle")
        layout.addWidget(self.title)
        self.fields = DataTable([Column("field", "字段", 130), Column("value", "值", 200)])
        self.meta = DataTable([Column("kind", "类型", 90), Column("content", "内容", 260)])
        tabs = QTabWidget()
        tabs.addTab(self.fields, "字段值")
        tabs.addTab(self.meta, "外键 / 约束 / 索引")
        layout.addWidget(tabs, 1)

    def clear(self):
        self.title.setText("在列表中选中一行查看详情")
        self.fields.set_rows([], "尚未选择记录", "在左侧表格中单击任意一行即可查看字段值")
        self.meta.set_rows([], "尚未选择记录", "选中行后会显示该表的外键、CHECK 约束与索引")

    def show_row(self, row, meta):
        if not row:
            return
        table = meta.get("table", "")
        self.title.setText(f"{meta.get('title', table)} · {table}")
        self.fields.set_rows([{"field": key, "value": "" if value is None else str(value)}
                              for key, value in row.items()])
        self.context.runner.run(lambda: self._load_meta(table),
                                lambda rows: self.meta.set_rows(rows, "该表没有外键或约束", ""),
                                lambda code, message: log.debug("详情元数据失败 %s", message))

    def _load_meta(self, table):
        rows = []
        for fk in self.context.meta.foreign_keys(table):
            rows.append({"kind": "外键",
                         "content": f"{fk['column_name']} → {fk['ref_table']}."
                                    f"{fk['ref_column']}（DELETE {fk['delete_rule']}）"})
        for check in self.context.meta.checks(table):
            rows.append({"kind": "CHECK", "content": f"{check['name']}: {check['clause']}"})
        for index in self.context.meta.indexes(table):
            rows.append({"kind": "索引",
                         "content": f"{index['name']}（{index['kind']}）: {index['columns']}"})
        return rows


class MainWindow(QMainWindow):
    def __init__(self, context):
        super().__init__()
        self.context = context
        self.settings = QSettings("SCUT_DB", "EduDesktop")
        self.pages = {}
        self.setWindowTitle("学生选课与成绩管理系统 · 桌面端（Python + Qt）")
        self.resize(1500, 900)
        self._build_toolbar()
        self._build_central()
        self._build_docks()
        self._build_statusbar()
        self.context.tracesUpdated.connect(self._on_trace)
        self.context.roleChanged.connect(self._on_role_changed)
        self.context.connectionChanged.connect(lambda _: self.refresh_connection_label())
        self._rebuild_nav()
        self.navigate("dashboard")
        self.refresh_connection_label()

    def _build_toolbar(self):
        bar = QToolBar("主工具栏")
        bar.setMovable(False)
        bar.setObjectName("MainToolBar")
        self.addToolBar(bar)
        self.status_dot = QLabel("●")
        self.status_dot.setObjectName("StatusDot")
        self.connection_label = QLabel("未连接")
        self.connection_label.setObjectName("ToolbarLabel")
        bar.addWidget(self.status_dot)
        bar.addWidget(self.connection_label)
        bar.addSeparator()
        bar.addWidget(QLabel("角色"))
        self.role_box = QComboBox()
        self.role_box.addItem("管理员（ADMIN）", "ADMIN")
        self.role_box.addItem("教师（TEACHER）", "TEACHER")
        self.role_box.addItem("学生（STUDENT）", "STUDENT")
        self.role_box.currentIndexChanged.connect(
            lambda: self.context.roleChanged.emit(self.role_box.currentData())
            or self._apply_role(self.role_box.currentData()))
        bar.addWidget(self.role_box)
        self.user_label = QLabel("未登录")
        self.user_label.setObjectName("ToolbarLabel")
        bar.addWidget(self.user_label)
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        bar.addWidget(spacer)
        self.login_button = QPushButton("登录")
        self.login_button.setObjectName("Ghost")
        self.connection_button = QPushButton("连接配置")
        self.connection_button.setObjectName("Ghost")
        self.help_button = QPushButton("帮助 / 演示脚本")
        self.help_button.setObjectName("Ghost")
        for button in (self.login_button, self.connection_button, self.help_button):
            bar.addWidget(button)
        self.login_button.clicked.connect(self.open_login)
        self.connection_button.clicked.connect(self.open_connection)
        self.help_button.clicked.connect(lambda: HelpDialog(self.context, self).exec())

    def _build_central(self):
        self.nav = QListWidget()
        self.nav.setObjectName("NavList")
        self.nav.setFixedWidth(228)
        self.stack = QStackedWidget()
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.nav)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(container)
        self.nav.currentRowChanged.connect(self._on_nav_changed)

    def _build_docks(self):
        self.detail_panel = DetailPanel(self.context, self)
        self.detail_dock = QDockWidget("详情", self)
        self.detail_dock.setObjectName("DetailDock")
        self.detail_dock.setWidget(self.detail_panel)
        self.detail_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.detail_dock)
        self.sql_panel = SqlPreview(self)
        self.sql_dock = QDockWidget("SQL 预览（真实执行记录）", self)
        self.sql_dock.setObjectName("SqlDock")
        self.sql_dock.setWidget(self.sql_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.sql_dock)
        self.detail_dock.setMinimumWidth(320)
        self.sql_dock.setMinimumHeight(190)

    def _build_statusbar(self):
        bar = QStatusBar()
        self.setStatusBar(bar)
        self.status_label = QLabel("就绪")
        self.stats_label = QLabel("")
        self.stats_label.setObjectName("StatusValue")
        bar.addWidget(self.status_label, 1)
        bar.addPermanentWidget(self.stats_label)

    def _rebuild_nav(self):
        self.nav.blockSignals(True)
        self.nav.clear()
        self._nav_keys = []
        for key, title, tag, _factory in PAGE_DEFS:
            if not self.context.can_view(key):
                continue
            item = QListWidgetItem(f"{title}    {tag}")
            item.setData(Qt.UserRole, key)
            item.setToolTip(self._tooltip_for(key))
            self.nav.addItem(item)
            self._nav_keys.append(key)
        self.nav.blockSignals(False)
        if self._nav_keys:
            self.nav.setCurrentRow(0)

    def _tooltip_for(self, key):
        for item_key, title, tag, _factory in PAGE_DEFS:
            if item_key == key:
                return f"{title}（{tag}）"
        return key

    def _on_nav_changed(self, row):
        if 0 <= row < len(self._nav_keys):
            self.navigate(self._nav_keys[row])

    def navigate(self, key, **kwargs):
        if not self.context.can_view(key):
            Notifier.warn(self, f"当前角色 {self.context.role_label} 无权访问该页面")
            return
        page = self.pages.get(key)
        if page is None:
            factory = next((entry[3] for entry in PAGE_DEFS if entry[0] == key), None)
            if factory is None:
                return
            page = factory(self.context)
            page.statusMessage.connect(self._on_status)
            page.rowSelected.connect(self.detail_panel.show_row)
            self.pages[key] = page
            self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        self.detail_panel.clear()
        index = self._nav_keys.index(key) if key in getattr(self, "_nav_keys", []) else -1
        if index >= 0 and self.nav.currentRow() != index:
            self.nav.blockSignals(True)
            self.nav.setCurrentRow(index)
            self.nav.blockSignals(False)
        if hasattr(page, "on_enter"):
            page.on_enter(**kwargs)

    def _on_status(self, text):
        self.status_label.setText(text)
        traces = self.context.db.traces
        if traces:
            last = traces[-1]
            self.stats_label.setText(f"最近 SQL {last.elapsed_ms} ms · 返回 {last.rows} 行 · "
                                     f"共执行 {len(traces)} 条")

    def _on_trace(self, trace):
        self.sql_panel.add_trace(trace)
        state = "成功" if trace.ok else "失败"
        self.stats_label.setText(f"最近 SQL {trace.elapsed_ms} ms · 返回 {trace.rows} 行 · {state}")

    def _on_role_changed(self, role):
        self.role_box.blockSignals(True)
        index = self.role_box.findData(role)
        if index >= 0:
            self.role_box.setCurrentIndex(index)
        self.role_box.blockSignals(False)
        self._apply_role(role)

    def _apply_role(self, role):
        self.user_label.setText(f"{self.context.username} · {self.context.role_label}")
        self._rebuild_nav()
        available = set(self._nav_keys)
        for key in list(self.pages):
            if key not in available:
                widget = self.pages.pop(key)
                self.stack.removeWidget(widget)
                widget.deleteLater()
        if self._nav_keys:
            self.navigate(self._nav_keys[0])
        log.info("角色切换为 %s，可见页面 %d 个", role, len(self._nav_keys))

    def refresh_connection_label(self):
        self._probe_health()

    def _probe_health(self):
        def done(health):
            self.status_dot.setStyleSheet("color: #16A34A;")
            self.connection_label.setText(
                f"{health.get('db_user')} @ {health.get('profile', {}).get('host')}:"
                f"{health.get('profile', {}).get('port')}/{health.get('db_name')} · "
                f"{health.get('elapsed_ms')} ms")
        self.context.runner.run(self.context.db.health, done, self._health_failed)

    def _health_failed(self, code, message):
        self.status_dot.setStyleSheet("color: #DC2626;")
        self.connection_label.setText(f"连接失败 [{code}] {message}")
        Notifier.error(self, f"数据库连接失败：[{code}] {message}")

    def open_login(self):
        dialog = LoginDialog(self.context, self)
        if dialog.exec():
            self._on_role_changed(self.context.role)
            Notifier.success(self, f"登录成功：{self.context.username}"
                                   f"（{self.context.role_label}）")

    def open_connection(self):
        if ConnectionDialog(self.context, self).exec():
            self.refresh_connection_label()
            self.navigate("dashboard")

    def apply_settings(self):
        show_sql = str(self.settings.value("show_sql", "true")) == "true"
        self.sql_dock.setVisible(show_sql)

    def showEvent(self, event):
        super().showEvent(event)
        self.apply_settings()

    def closeEvent(self, event):
        log.info("窗口关闭，释放连接")
        self.context.shutdown()
        super().closeEvent(event)
