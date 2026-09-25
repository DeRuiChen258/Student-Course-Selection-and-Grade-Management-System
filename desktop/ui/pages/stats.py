"""F16 统计分析：五类图表 + GPA 排名 + EXPLAIN 索引对比，全部由真实聚合驱动。"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
                               QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from models.table_model import Column
from ui.widgets import DataTable, Notifier, PageBase
from ui.widgets.charts import bar_chart, line_chart, pie_chart


class ChartTab(QWidget):
    def __init__(self, columns, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 0)
        self.chart_area = QVBoxLayout()
        layout.addLayout(self.chart_area)
        self.table = DataTable(columns)
        layout.addWidget(self.table, 1)

    def set_chart(self, view):
        while self.chart_area.count():
            item = self.chart_area.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        if view is not None:
            self.chart_area.addWidget(view)

    def set_rows(self, rows, empty_hint="调整筛选条件后重试"):
        self.table.set_rows(rows, "该维度暂无数据", empty_hint)


class StatsPage(PageBase):
    def __init__(self, context, parent=None):
        super().__init__(context, "统计分析", ("F16",),
                         "图表数据来自 v_course_stat、f_gpa 与 GROUP BY 聚合；"
                         "切换筛选条件会重跑聚合 SQL，图形不是静态图片。", page_key="stats",
                         parent=parent)
        self.semester_box = QComboBox()
        self.semester_box.addItem("全部学期", None)
        for semester in context.enrollment.semesters():
            self.semester_box.addItem(semester, semester)
        self.dept_box = QComboBox()
        self.dept_box.addItem("全部院系", None)
        for row in context.report.departments():
            self.dept_box.addItem(row["name"], row["id"])
        self.class_box = QComboBox()
        self.class_box.addItem("全部班级", None)
        for row in context.report.classes():
            self.class_box.addItem(row["name"], row["id"])
        self.top_box = QSpinBox()
        self.top_box.setRange(5, 50)
        self.top_box.setValue(15)
        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("Primary")
        self.add_action(QLabel("学期"))
        self.add_action(self.semester_box)
        self.add_action(QLabel("院系"))
        self.add_action(self.dept_box)
        self.add_action(QLabel("班级"))
        self.add_action(self.class_box)
        self.add_action(QLabel("条数"))
        self.add_action(self.top_box)
        self.add_stretch()
        self.add_action(self.refresh_button)
        self.refresh_button.clicked.connect(self.reload)
        self.semester_box.currentIndexChanged.connect(lambda: self.reload())
        self.dept_box.currentIndexChanged.connect(lambda: self.reload())
        self.class_box.currentIndexChanged.connect(lambda: self.reload())

        self.tabs = QTabWidget()
        self.course_tab = ChartTab([
            Column("code", "课程代码", 100), Column("name", "课程名", 180),
            Column("semester", "学期", 105, "center"),
            Column("students", "选课人数", 90, "right", "number"),
            Column("avg_score", "平均分", 80, "right", "decimal"),
            Column("max_score", "最高分", 80, "right", "decimal"),
            Column("min_score", "最低分", 80, "right", "decimal"),
            Column("fail_count", "不及格", 80, "right", "number"),
            Column("fail_rate", "不及格率%", 90, "right", "decimal"),
        ])
        self.tabs.addTab(self.course_tab, "课程选课人数")
        self.dist_tab = ChartTab([
            Column("bucket", "分数区间", 120), Column("cnt", "人数", 90, "right", "number"),
        ])
        self.tabs.addTab(self.dist_tab, "成绩分布")
        self.semester_tab = ChartTab([
            Column("semester", "学期", 120, "center"),
            Column("offerings", "开课数", 90, "right", "number"),
            Column("courses", "课程数", 90, "right", "number"),
            Column("capacity", "总容量", 90, "right", "number"),
            Column("enrolled", "已选人次", 100, "right", "number"),
            Column("avg_score", "均分", 80, "right", "decimal"),
        ])
        self.tabs.addTab(self.semester_tab, "学期趋势")
        self.type_tab = ChartTab([
            Column("course_type", "课程类型", 120),
            Column("cnt", "课程门数", 100, "right", "number"),
            Column("credits", "学分合计", 100, "right", "decimal"),
        ])
        self.tabs.addTab(self.type_tab, "课程类型占比")
        self.gpa_tab = ChartTab([
            Column("student_no", "学号", 130), Column("student_name", "姓名", 90),
            Column("class_name", "班级", 200), Column("status", "学籍", 70, "center"),
            Column("gpa", "GPA", 80, "right", "decimal"),
            Column("credits", "已修学分", 90, "right", "decimal"),
            Column("failed", "不及格门数", 100, "right", "number"),
        ])
        self.tabs.addTab(self.gpa_tab, "GPA 排名")
        self.tabs.addTab(self._index_tab(), "索引效果对比")
        self.root.addWidget(self.tabs, 1)

    def _index_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        line = QHBoxLayout()
        line.addWidget(QLabel("开课号"))
        self.offering_box = QSpinBox()
        self.offering_box.setRange(1, 99999)
        self.offering_box.setValue(2)
        self.explain_button = QPushButton("执行 EXPLAIN 对比")
        self.explain_button.setObjectName("Primary")
        self.explain_hint = QLabel("对比 idx_enroll_offering 命中前后的执行计划（type / key / rows / Extra）")
        self.explain_hint.setObjectName("HintLabel")
        line.addWidget(self.offering_box)
        line.addWidget(self.explain_button)
        line.addWidget(self.explain_hint)
        line.addStretch(1)
        layout.addLayout(line)
        self.explain_with = DataTable()
        self.explain_without = DataTable()
        layout.addWidget(QLabel("① 使用 idx_enroll_offering"))
        layout.addWidget(self.explain_with, 1)
        layout.addWidget(QLabel("② IGNORE INDEX (idx_enroll_offering)"))
        layout.addWidget(self.explain_without, 1)
        self.explain_button.clicked.connect(self.run_explain)
        return widget

    def on_enter(self, **_):
        if not self.tabs.currentIndex():
            self.reload()

    def reload(self):
        params = {
            "semester": self.semester_box.currentData(),
            "dept_id": self.dept_box.currentData(),
            "class_id": self.class_box.currentData(),
            "top": self.top_box.value(),
        }
        self.set_busy(True, "正在执行聚合查询…")
        self.context.runner.run(lambda: self._collect(params), self._apply,
                                lambda code, message: Notifier.error(self, f"[{code}] {message}"),
                                lambda: self.set_busy(False))

    def _collect(self, params):
        semester = params["semester"]
        dept_id = params["dept_id"]
        return {
            "course": self.context.report.course_stat(semester, dept_id, params["top"]),
            "dist": self.context.report.score_distribution(semester, dept_id),
            "semester": self.context.report.semester_summary(),
            "type": self.context.report.course_type_share(dept_id),
            "gpa": self.context.report.gpa_ranking(params["class_id"], params["top"]),
        }

    def _apply(self, data):
        course_rows = data["course"]
        self.course_tab.set_rows(course_rows)
        self.course_tab.set_chart(bar_chart(
            "课程选课人数（Top N）",
            [row["code"] for row in course_rows],
            [row["students"] for row in course_rows]))

        dist_rows = data["dist"]
        self.dist_tab.set_rows(dist_rows)
        self.dist_tab.set_chart(bar_chart(
            "成绩分布（CASE 分箱）",
            [row["bucket"] for row in dist_rows],
            [row["cnt"] for row in dist_rows], "#0F766E"))

        semester_rows = data["semester"]
        self.semester_tab.set_rows(semester_rows)
        self.semester_tab.set_chart(line_chart(
            "各学期选课人次与均分趋势",
            [row["semester"] for row in semester_rows],
            [row["enrolled"] for row in semester_rows], "#D97706"))

        type_rows = data["type"]
        self.type_tab.set_rows(type_rows)
        self.type_tab.set_chart(pie_chart(
            "课程类型占比（按门数）",
            [row["course_type"] for row in type_rows],
            [row["cnt"] for row in type_rows]))

        gpa_rows = data["gpa"]
        self.gpa_tab.set_rows(gpa_rows)
        top = [row for row in gpa_rows if row["gpa"] is not None][:10]
        self.gpa_tab.set_chart(bar_chart(
            "GPA 排名（前 10 名，f_gpa 标量函数）",
            [row["student_name"] for row in top],
            [row["gpa"] for row in top], "#7C3AED"))
        self.emit_status(f"统计刷新完成：课程 {len(course_rows)} 条 · "
                         f"成绩分布 {len(dist_rows)} 段 · GPA 排名 {len(gpa_rows)} 条")

    def run_explain(self):
        offering_id = self.offering_box.value()
        self.explain_button.setEnabled(False)
        self.context.runner.run(
            lambda: self.context.report.explain_compare(offering_id),
            self._apply_explain, lambda code, message: Notifier.error(self, f"[{code}] {message}"),
            lambda: self.explain_button.setEnabled(True))

    def _apply_explain(self, payload):
        with_index, without_index = payload
        for table, rows in ((self.explain_with, with_index),
                            (self.explain_without, without_index)):
            if rows:
                table.set_columns([Column(key, key, 140 if key.endswith("keys") or key == "Extra"
                                          else 110) for key in rows[0]])
            table.set_rows(rows, "没有执行计划", "确认开课号存在")
        Notifier.info(self, "EXPLAIN 对比完成，见下方两张执行计划表")
