"""选课（F11）与退课（F12）：调用存储过程，展示触发器联动结果。"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
                               QLineEdit, QPushButton, QVBoxLayout)

from ui.widgets import Notifier


def fill_offering_combo(combo, options):
    combo.clear()
    for row in options:
        text = (f"[{row['id']}] {row['code']} {row['name']} · {row['teacher']} · "
                f"{row['semester']} · {row['enrolled']}/{row['capacity']}")
        combo.addItem(text, row["id"])


def fill_student_combo(combo, options):
    combo.clear()
    for row in options:
        combo.addItem(f"{row['student_no']} {row['student_name']}（{row['class_name']}）"
                      f" {row['status']}", row["student_no"])


class EnrollmentDialogBase(QDialog):
    dataChanged = Signal()

    def __init__(self, context, title, func_key, parent=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle(title)
        self.setMinimumWidth(660)
        self.root = QVBoxLayout(self)
        self.root.setSpacing(10)
        head = QLabel(title)
        head.setObjectName("DialogTitle")
        hint = QLabel("选课 / 退课全部走存储过程（p_enroll_student / p_drop_course），"
                      "名额计数由触发器维护；错误码 40001–40099 原样回显。")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        self.root.addWidget(head)
        self.root.addWidget(hint)
        self.form = QFormLayout()
        self.root.addLayout(self.form)
        self.detail = QLabel("")
        self.detail.setObjectName("InfoPanel")
        self.detail.setWordWrap(True)
        self.root.addWidget(self.detail)
        self.error = QLabel("")
        self.error.setObjectName("ErrorText")
        self.error.setWordWrap(True)
        self.error.setVisible(False)
        self.root.addWidget(self.error)

    def add_buttons(self, primary_text, primary_handler):
        buttons = QHBoxLayout()
        buttons.addStretch(1)
        close = QPushButton("关闭")
        close.setObjectName("Ghost")
        close.clicked.connect(self.accept)
        self.primary = QPushButton(primary_text)
        self.primary.setObjectName("Primary")
        self.primary.clicked.connect(primary_handler)
        buttons.addWidget(close)
        buttons.addWidget(self.primary)
        self.root.addLayout(buttons)


class EnrollDialog(EnrollmentDialogBase):
    def __init__(self, context, parent=None, preset_student=None, preset_offering=None):
        super().__init__(context, "F11 学生选课", "F11", parent)
        self.semester_box = QComboBox()
        self.semester_box.addItem("全部学期", None)
        for semester in context.enrollment.semesters():
            self.semester_box.addItem(semester, semester)
        self.student_search = QLineEdit()
        self.student_search.setPlaceholderText("按学号或姓名过滤")
        self.student_box = QComboBox()
        self.student_box.setMinimumWidth(320)
        self.offering_box = QComboBox()
        self.offering_box.setMinimumWidth(420)
        self.form.addRow("学期", self.semester_box)
        self.form.addRow("学生", self.student_search)
        self.form.addRow("", self.student_box)
        self.form.addRow("开课", self.offering_box)
        self.add_buttons("选课", self.submit)
        self.semester_box.currentIndexChanged.connect(self.reload)
        self.offering_box.currentIndexChanged.connect(self.show_detail)
        self.student_search.textChanged.connect(self._filter_students)
        self.reload()
        if preset_student:
            index = self.student_box.findData(preset_student)
            if index >= 0:
                self.student_box.setCurrentIndex(index)
        if preset_offering:
            index = self.offering_box.findData(preset_offering)
            if index >= 0:
                self.offering_box.setCurrentIndex(index)

    def _filter_students(self, text):
        self._student_rows = self.context.enrollment.student_options(text or None)
        fill_student_combo(self.student_box, self._student_rows)

    def reload(self):
        semester = self.semester_box.currentData()
        self._student_rows = self.context.enrollment.student_options()
        fill_student_combo(self.student_box, self._student_rows)
        fill_offering_combo(self.offering_box,
                            self.context.enrollment.offering_options(semester, only_open=True))
        self.show_detail()

    def show_detail(self):
        offering_id = self.offering_box.currentData()
        if not offering_id:
            self.detail.setText("当前学期没有余量大于 0 的开课")
            return
        row = self.context.enrollment.offering_detail(offering_id) or {}
        self.detail.setText(
            f"开课详情（v_offering_detail）：{row.get('course_code')} {row.get('course_name')} · "
            f"教师 {row.get('teacher')} · 学分 {row.get('credit')} · "
            f"容量 {row.get('capacity')} · 已选 {row.get('enrolled')} · 余量 {row.get('remain')}\n"
            f"当前均分 {row.get('avg_score')}（f_offering_avg 口径为已出分记录）")

    def submit(self):
        student_no = self.student_box.currentData()
        offering_id = self.offering_box.currentData()
        if not student_no or not offering_id:
            Notifier.warn(self, "请先选择学生与开课")
            return
        self.error.setVisible(False)
        self.primary.setEnabled(False)
        self.context.runner.run(
            lambda: self.context.enrollment.enroll(student_no, offering_id),
            self._ok, self._err, self._done)

    def _done(self):
        self.primary.setEnabled(True)

    def _ok(self, message):
        Notifier.success(self, message)
        self.dataChanged.emit()
        self.reload()

    def _err(self, code, message):
        self.error.setText(f"[{code}] {message}")
        self.error.setVisible(True)
        Notifier.error(self, f"[{code}] {message}")


class DropDialog(EnrollmentDialogBase):
    def __init__(self, context, parent=None, preset_student=None):
        super().__init__(context, "F12 学生退课", "F12", parent)
        self.student_search = QLineEdit(preset_student or "")
        self.student_search.setPlaceholderText("按学号或姓名过滤")
        self.student_box = QComboBox()
        self.student_box.setMinimumWidth(340)
        self.course_box = QComboBox()
        self.course_box.setMinimumWidth(420)
        self.form.addRow("学生", self.student_search)
        self.form.addRow("", self.student_box)
        self.form.addRow("已选课程", self.course_box)
        self.add_buttons("退课", self.submit)
        self.student_search.textChanged.connect(self._reload_students)
        self.student_box.currentIndexChanged.connect(self.reload_courses)
        self.course_box.currentIndexChanged.connect(self.show_detail)
        self._reload_students()

    def _reload_students(self):
        rows = self.context.enrollment.student_options(self.student_search.text().strip() or None)
        fill_student_combo(self.student_box, rows)
        self.reload_courses()

    def reload_courses(self):
        student_no = self.student_box.currentData()
        self._records = self.context.enrollment.student_records(student_no) if student_no else []
        self.course_box.clear()
        for row in self._records:
            score = "未出分" if row["score"] is None else f"{row['score']} 分"
            self.course_box.addItem(f"[{row['offering_id']}] {row['course_code']} "
                                    f"{row['course_name']} · {row['semester']} · {score} · "
                                    f"{row['status']}", row["offering_id"])
        self.show_detail()

    def show_detail(self):
        record = next((row for row in getattr(self, "_records", [])
                       if row["offering_id"] == self.course_box.currentData()), None)
        if not record:
            self.detail.setText("该学生没有可选记录")
            return
        self.detail.setText(
            f"记录：{record['course_code']} {record['course_name']} · 状态 {record['status']} · "
            f"成绩 {record['score'] if record['score'] is not None else '未出分'}\n"
            "退课规则：已出分的记录会被存储过程以 40007 拒绝（p_drop_course）")

    def submit(self):
        student_no = self.student_box.currentData()
        offering_id = self.course_box.currentData()
        if not student_no or not offering_id:
            Notifier.warn(self, "请先选择学生与课程")
            return
        self.error.setVisible(False)
        self.primary.setEnabled(False)
        self.context.runner.run(
            lambda: self.context.enrollment.drop(student_no, offering_id),
            self._ok, self._err, self._done)

    def _done(self):
        self.primary.setEnabled(True)

    def _ok(self, message):
        Notifier.success(self, message)
        self.dataChanged.emit()
        self.reload_courses()

    def _err(self, code, message):
        self.error.setText(f"[{code}] {message}")
        self.error.setVisible(True)
        Notifier.error(self, f"[{code}] {message}")
