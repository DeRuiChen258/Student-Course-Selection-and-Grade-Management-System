"""成绩录入与修改（F13 / F14）：调用 p_save_score，展示触发器保护。"""

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout,
                               QLabel, QPushButton, QVBoxLayout)

from models.table_model import Column
from ui.widgets import DataTable, Notifier


class ScoreDialog(QDialog):
    dataChanged = Signal()

    def __init__(self, context, parent=None, preset_offering=None, preset_student=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle("F13 / F14 成绩录入与修改")
        self.resize(900, 620)
        self._rows = []
        root = QVBoxLayout(self)
        root.setSpacing(10)
        head = QLabel("F13 成绩录入 · F14 成绩修改")
        head.setObjectName("DialogTitle")
        hint = QLabel("分数区间由存储过程（40008）与触发器 trg_enrollment_bu（E007）双重校验；"
                      "写分同时刷新 score_time。")
        hint.setObjectName("DialogHint")
        hint.setWordWrap(True)
        root.addWidget(head)
        root.addWidget(hint)

        form = QFormLayout()
        self.semester_box = QComboBox()
        self.semester_box.addItem("全部学期", None)
        for semester in context.enrollment.semesters():
            self.semester_box.addItem(semester, semester)
        self.offering_box = QComboBox()
        self.offering_box.setMinimumWidth(430)
        form.addRow("学期", self.semester_box)
        form.addRow("开课", self.offering_box)
        root.addLayout(form)

        self.table = DataTable([
            Column("student_no", "学号", 130), Column("student_name", "姓名", 90),
            Column("class_name", "班级", 200), Column("status", "状态", 70, "center"),
            Column("score", "成绩", 80, "right", "decimal"),
            Column("score_time", "录入 / 修改时间", 160),
        ])
        self.table.rowActivated.connect(self._pick_row)
        self.table.selectionChanged.connect(self._on_selection)
        root.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        self.stats = QLabel("—")
        self.stats.setObjectName("InfoPanel")
        self.student_label = QLabel("未选择学生")
        self.score_box = QDoubleSpinBox()
        self.score_box.setRange(0, 100)
        self.score_box.setDecimals(2)
        self.score_box.setValue(80)
        self.score_box.setFixedWidth(110)
        self.save_button = QPushButton("保存成绩")
        self.save_button.setObjectName("Primary")
        self.save_button.setEnabled(False)
        self.close_button = QPushButton("关闭")
        self.close_button.setObjectName("Ghost")
        bottom.addWidget(self.stats, 1)
        bottom.addWidget(self.student_label)
        bottom.addWidget(self.score_box)
        bottom.addWidget(self.save_button)
        bottom.addWidget(self.close_button)
        root.addLayout(bottom)

        self.semester_box.currentIndexChanged.connect(self.reload_offerings)
        self.offering_box.currentIndexChanged.connect(self.reload_roster)
        self.save_button.clicked.connect(self.submit)
        self.close_button.clicked.connect(self.accept)
        self.reload_offerings()
        if preset_offering:
            index = self.offering_box.findData(preset_offering)
            if index >= 0:
                self.offering_box.setCurrentIndex(index)
        if preset_student:
            self._preset_student = preset_student

    def reload_offerings(self):
        semester = self.semester_box.currentData()
        options = self.context.enrollment.offering_options(semester, only_open=False)
        self.offering_box.blockSignals(True)
        self.offering_box.clear()
        for row in options:
            self.offering_box.addItem(f"[{row['id']}] {row['code']} {row['name']} · "
                                      f"{row['teacher']} · {row['semester']} · "
                                      f"{row['enrolled']}/{row['capacity']}", row["id"])
        self.offering_box.blockSignals(False)
        self.reload_roster()

    def reload_roster(self):
        offering_id = self.offering_box.currentData()
        if not offering_id:
            self.table.set_rows([])
            self.stats.setText("—")
            return
        self._rows = self.context.enrollment.roster(offering_id)
        self.table.set_rows(self._rows, "该开课暂无选课记录",
                            "先在 F11 选课界面为学生选课")
        stats = self.context.enrollment.roster_stats(offering_id)
        self.stats.setText(
            f"名单 {stats.get('total', 0)} 人 · 已出分 {stats.get('scored', 0)} · "
            f"均分 {stats.get('avg_score') or '—'} · 最高 {stats.get('max_score') or '—'} · "
            f"最低 {stats.get('min_score') or '—'} · 不及格 {stats.get('failed') or 0} 人")
        preset = getattr(self, "_preset_student", None)
        if preset:
            for index, row in enumerate(self._rows):
                if row["student_no"] == preset:
                    self.table.view.selectRow(index)
                    break

    def _on_selection(self, row):
        if not row:
            return
        self.student_label.setText(f"{row['student_no']} {row['student_name']}")
        if row.get("score") is not None:
            self.score_box.setValue(float(row["score"]))
        self.save_button.setEnabled(True)

    def _pick_row(self, row):
        self.student_label.setText(f"{row['student_no']} {row['student_name']}")
        self.score_box.setFocus()

    def submit(self):
        row = self.table.selected_row()
        if not row:
            Notifier.warn(self, "请先在名单中选择一名学生")
            return
        offering_id = self.offering_box.currentData()
        self.save_button.setEnabled(False)
        self.context.runner.run(
            lambda: self.context.enrollment.save_score(row["student_no"], offering_id,
                                                       self.score_box.value()),
            self._ok, self._err, lambda: self.save_button.setEnabled(True))

    def _ok(self, message):
        Notifier.success(self, message)
        self.dataChanged.emit()
        self.reload_roster()

    def _err(self, code, message):
        Notifier.error(self, f"[{code}] {message}")
