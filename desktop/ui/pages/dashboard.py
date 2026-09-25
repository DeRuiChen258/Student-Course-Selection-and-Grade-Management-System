"""主仪表盘：数据库对象自检 + 业务规模指标 + 最近审计。"""

from PySide6.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.labels import OBJECT_LABELS
from models.table_model import Column
from ui.widgets import DataTable, MetricCard, Notifier, PageBase


class DashboardPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "数据仪表盘", ("F16",),
                         "对象计数来自 information_schema，业务指标来自真实聚合查询；"
                         "所有数字可用 MySQL 客户端二次核对。", page_key="dashboard",
                         parent=parent)
        self.check_button = QPushButton("一键数据库自检")
        self.check_button.setObjectName("Primary")
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("Ghost")
        self.add_action(self.check_button)
        self.add_stretch()
        self.add_action(self.refresh_button)
        self.check_button.clicked.connect(self.reload)
        self.refresh_button.clicked.connect(self.reload)

        self.cards = {}
        grid = QGridLayout()
        grid.setSpacing(12)
        specs = [
            ("tables", "基础表", "#2563EB"), ("views", "视图", "#0F766E"),
            ("triggers", "触发器", "#D97706"), ("routines", "例程（过程 + 函数）", "#7C3AED"),
            ("named_indexes", "显式索引 idx_*", "#0891B2"),
            ("students", "学生总数", "#2563EB"), ("courses", "课程总数", "#0F766E"),
            ("offerings", "开课总数", "#D97706"), ("enrollments", "选课记录", "#7C3AED"),
            ("score_ready", "已出分记录", "#0891B2"),
        ]
        for index, (key, title, accent) in enumerate(specs):
            card = MetricCard(title, "—", OBJECT_LABELS.get(key, ""), accent)
            self.cards[key] = card
            grid.addWidget(card, index // 5, index % 5)
        self.root.addLayout(grid)

        summary_row = QHBoxLayout()
        self.summary = QLabel("—")
        self.summary.setObjectName("InfoPanel")
        self.summary.setWordWrap(True)
        summary_row.addWidget(self.summary, 1)
        self.root.addLayout(summary_row)

        self.root.addWidget(QLabel("最近操作（audit_log，由触发器写入）"))
        self.audit = DataTable([
            Column("action_time", "时间", 130, "center"),
            Column("table_name", "表", 120),
            Column("action", "操作", 80, "center"),
            Column("record_id", "记录标识", 140),
            Column("operator", "操作者", 120),
            Column("detail", "明细", 320),
        ])
        self.root.addWidget(self.audit, 1)

    def on_enter(self, **_):
        self.reload()

    def reload(self):
        self.set_busy(True, "正在执行数据库对象自检…")
        self.context.runner.run(self._collect, self._apply, self._on_error,
                                lambda: self.set_busy(False))

    def _collect(self):
        overview = self.context.meta.overview()
        audit = self.context.report.recent_audit(12)
        health = self.context.db.health()
        return overview, audit, health

    def _apply(self, payload):
        overview, audit, health = payload
        for key, card in self.cards.items():
            card.set_value(overview.get(key, 0))
        self.cards["tables"].set_value(overview.get("tables", 0),
                                       f"视图 {overview.get('views', 0)} · "
                                       f"全部索引 {overview.get('all_indexes', 0)}")
        self.summary.setText(
            f"连接 {health.get('db_user')} @ {health.get('db_name')} · "
            f"服务端 {health.get('version')} · 往返 {health.get('elapsed_ms')} ms | "
            f"总体均分 {overview.get('avg_score') or '—'} 分 · "
            f"已出分 {overview.get('score_ready', 0)} / {overview.get('enrollments', 0)} 条")
        self.audit.set_rows(audit, "暂无审计记录",
                            "删除学生或修改成绩后，触发器会写入 audit_log")
        self.emit_status(f"自检完成：表 {overview.get('tables', 0)} · "
                         f"视图 {overview.get('views', 0)} · "
                         f"触发器 {overview.get('triggers', 0)} · "
                         f"例程 {overview.get('routines', 0)}")

    def _on_error(self, code, message):
        Notifier.error(self, f"自检失败 [{code}] {message}")
