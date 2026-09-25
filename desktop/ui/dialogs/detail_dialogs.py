"""F15 选课信息查询：学生课表与开课名单，以及通用 SQL 文本窗口。"""

from PySide6.QtWidgets import (QComboBox, QDialog, QHBoxLayout, QLabel, QPlainTextEdit,
                               QPushButton, QVBoxLayout)

from models.table_model import Column
from ui.widgets import DataTable, Notifier


class TranscriptDialog(QDialog):
    def __init__(self, context, parent=None, student_no=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle("F15 学生课表与成绩单")
        self.resize(940, 620)
        root = QVBoxLayout(self)
        root.setSpacing(10)
        head = QLabel("F15 按学生查课表（v_student_transcript + f_gpa）")
        head.setObjectName("DialogTitle")
        root.addWidget(head)
        bar = QHBoxLayout()
        self.student_box = QComboBox()
        self.student_box.setMinimumWidth(320)
        for row in context.enrollment.student_options():
            self.student_box.addItem(f"{row['student_no']} {row['student_name']}", row["student_no"])
        self.semester_box = QComboBox()
        self.semester_box.addItem("全部学期", None)
        for semester in context.enrollment.semesters():
            self.semester_box.addItem(semester, semester)
        self.export_button = QPushButton("导出 CSV")
        self.export_button.setObjectName("Ghost")
        bar.addWidget(QLabel("学生"))
        bar.addWidget(self.student_box)
        bar.addWidget(QLabel("学期"))
        bar.addWidget(self.semester_box)
        bar.addStretch(1)
        bar.addWidget(self.export_button)
        root.addLayout(bar)
        self.summary = QLabel("—")
        self.summary.setObjectName("InfoPanel")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        self.table = DataTable([
            Column("semester", "学期", 110, "center"),
            Column("course_code", "课程代码", 100),
            Column("course_name", "课程名", 190),
            Column("credit", "学分", 70, "right", "decimal"),
            Column("score", "成绩", 80, "right", "decimal"),
            Column("grade", "等级", 60, "center"),
            Column("gpa", "绩点", 70, "right", "decimal"),
            Column("teacher", "教师", 90),
        ])
        root.addWidget(self.table, 1)
        self.student_box.currentIndexChanged.connect(self.reload)
        self.semester_box.currentIndexChanged.connect(self.reload)
        self.export_button.clicked.connect(self.export)
        if student_no:
            index = self.student_box.findData(student_no)
            if index >= 0:
                self.student_box.setCurrentIndex(index)
        self.reload()

    def reload(self):
        student_no = self.student_box.currentData()
        semester = self.semester_box.currentData()
        if not student_no:
            return
        rows = self.context.enrollment.transcript(student_no, semester)
        summary = self.context.enrollment.student_summary(student_no)
        self.table.set_rows(rows, "该学生暂无选课记录", "可在 F11 选课界面为其选课")
        self.summary.setText(
            f"{summary.get('student_name', '')}（{summary.get('student_no', '')}）· "
            f"{summary.get('class_name', '')} · {summary.get('dept_name', '')} · "
            f"学籍 {summary.get('status', '')} | 选课 {summary.get('course_count', 0)} 门 · "
            f"已修学分 {summary.get('credits', 0)} · GPA {summary.get('gpa') or '—'} · "
            f"不及格 {summary.get('failed', 0)} 门")

    def export(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "导出成绩单", "transcript.csv",
                                              "CSV 文件 (*.csv)")
        if not path:
            return
        columns = [(column.label, column.key) for column in self.table.model.columns]
        count = self.context.io.export(path, columns, self.table.rows(), "csv",
                                       "v_student_transcript")
        Notifier.success(self, f"已导出 {count} 行到 {path}")


class RosterDialog(QDialog):
    def __init__(self, context, parent=None, offering_id=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle("F15 开课名单与成绩")
        self.resize(900, 600)
        root = QVBoxLayout(self)
        root.setSpacing(10)
        head = QLabel("F15 按开课查名单（enrollment ⋈ student ⋈ class_group）")
        head.setObjectName("DialogTitle")
        root.addWidget(head)
        bar = QHBoxLayout()
        self.offering_box = QComboBox()
        self.offering_box.setMinimumWidth(430)
        for row in context.enrollment.offering_options(only_open=False):
            self.offering_box.addItem(f"[{row['id']}] {row['code']} {row['name']} · "
                                      f"{row['semester']} · {row['enrolled']}/{row['capacity']}",
                                      row["id"])
        self.export_button = QPushButton("导出 CSV")
        self.export_button.setObjectName("Ghost")
        bar.addWidget(QLabel("开课"))
        bar.addWidget(self.offering_box)
        bar.addStretch(1)
        bar.addWidget(self.export_button)
        root.addLayout(bar)
        self.summary = QLabel("—")
        self.summary.setObjectName("InfoPanel")
        self.summary.setWordWrap(True)
        root.addWidget(self.summary)
        self.table = DataTable([
            Column("student_no", "学号", 130), Column("student_name", "姓名", 90),
            Column("class_name", "班级", 210), Column("status", "状态", 70, "center"),
            Column("score", "成绩", 80, "right", "decimal"),
            Column("score_time", "录入时间", 150),
        ])
        root.addWidget(self.table, 1)
        self.offering_box.currentIndexChanged.connect(self.reload)
        self.export_button.clicked.connect(self.export)
        if offering_id:
            index = self.offering_box.findData(offering_id)
            if index >= 0:
                self.offering_box.setCurrentIndex(index)
        self.reload()

    def reload(self):
        offering_id = self.offering_box.currentData()
        if not offering_id:
            return
        rows = self.context.enrollment.roster(offering_id)
        stats = self.context.enrollment.roster_stats(offering_id)
        self.table.set_rows(rows, "该开课暂无选课记录", "可在 F11 选课界面添加")
        self.summary.setText(
            f"名单 {stats.get('total', 0)} 人 · 已出分 {stats.get('scored', 0)} · "
            f"均分 {stats.get('avg_score') or '—'} · 最高 {stats.get('max_score') or '—'} · "
            f"最低 {stats.get('min_score') or '—'} · 不及格 {stats.get('failed') or 0} 人")

    def export(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(self, "导出名单", "roster.csv", "CSV 文件 (*.csv)")
        if not path:
            return
        columns = [(column.label, column.key) for column in self.table.model.columns]
        count = self.context.io.export(path, columns, self.table.rows(), "csv", "roster")
        Notifier.success(self, f"已导出 {count} 行到 {path}")


class SqlTextDialog(QDialog):
    def __init__(self, title, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 480)
        layout = QVBoxLayout(self)
        head = QLabel(title)
        head.setObjectName("DialogTitle")
        layout.addWidget(head)
        editor = QPlainTextEdit(text)
        editor.setReadOnly(True)
        layout.addWidget(editor)
        close = QPushButton("关闭")
        close.setObjectName("Ghost")
        close.clicked.connect(self.accept)
        line = QHBoxLayout()
        line.addStretch(1)
        line.addWidget(close)
        layout.addLayout(line)
