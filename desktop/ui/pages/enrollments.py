"""F11–F15 选课与成绩页：选课 / 退课 / 课表 / 名单（含成绩管理模式的复用）。"""

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLineEdit, QPushButton

from models.table_model import Column
from ui.dialogs import DropDialog, EnrollDialog, RosterDialog, ScoreDialog, TranscriptDialog
from ui.widgets import DataTable, Notifier, PageBase, Pager


class EnrollmentListPage(PageBase):
    def __init__(self, context, mode="enroll", parent=None):
        self.mode = mode
        if mode == "grade":
            title, funcs = "成绩管理", ("F13", "F14")
            subtitle = ("分数写入走 p_save_score（40008 区间校验）与触发器 trg_enrollment_bu"
                        "（E007 / score_time 刷新）。")
            page_key = "grades"
        else:
            title, funcs = "选课与成绩", ("F11", "F12", "F15")
            subtitle = ("选课 / 退课调用 p_enroll_student、p_drop_course，名额计数由触发器联动；"
                        "课表与名单读视图 v_student_transcript / v_offering_detail。")
            page_key = "enrollments"
        super().__init__(context, title, funcs, subtitle, page_key=page_key, parent=parent)
        self._rows = []

        if mode == "enroll":
            self.enroll_button = QPushButton("学生选课")
            self.enroll_button.setObjectName("Primary")
            self.drop_button = QPushButton("学生退课")
            self.transcript_button = QPushButton("学生课表")
            self.roster_button = QPushButton("开课名单")
            self.add_action(self.enroll_button)
            self.add_action(self.drop_button)
            self.add_action(self.transcript_button)
            self.add_action(self.roster_button)
            self.enroll_button.clicked.connect(self.open_enroll)
            self.drop_button.clicked.connect(self.open_drop)
            self.transcript_button.clicked.connect(self.open_transcript)
            self.roster_button.clicked.connect(self.open_roster)
            self.enroll_button.setEnabled(context.can_do("enroll"))
            self.drop_button.setEnabled(context.can_do("drop"))
        else:
            self.score_button = QPushButton("录入 / 修改成绩")
            self.score_button.setObjectName("Primary")
            self.add_action(self.score_button)
            self.score_button.clicked.connect(self.open_score)
            self.score_button.setEnabled(context.can_do("score"))

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.setObjectName("Ghost")
        self.count_label = QLabel("")
        self.count_label.setObjectName("HintLabel")
        self.add_stretch()
        self.add_action(self.count_label)
        self.add_action(self.refresh_button)
        self.refresh_button.clicked.connect(self.reload)

        filters = QHBoxLayout()
        self.semester_box = QComboBox()
        self.semester_box.addItem("全部学期", None)
        for semester in context.enrollment.semesters():
            self.semester_box.addItem(semester, semester)
        self.keyword_box = QLineEdit()
        self.keyword_box.setPlaceholderText("学号 / 姓名 / 课程代码 / 课程名")
        self.keyword_box.setMinimumWidth(260)
        self.status_box = QComboBox()
        self.status_box.addItem("全部状态", None)
        self.status_box.addItem("已选", "已选")
        self.status_box.addItem("已退", "已退")
        self.score_box = QComboBox()
        self.score_box.addItem("全部成绩状态", None)
        self.score_box.addItem("未出分", "未出分")
        self.score_box.addItem("已出分", "已出分")
        self.apply_button = QPushButton("查询")
        self.apply_button.setObjectName("Primary")
        filters.addWidget(QLabel("学期"))
        filters.addWidget(self.semester_box)
        filters.addWidget(QLabel("关键字"))
        filters.addWidget(self.keyword_box)
        filters.addWidget(self.status_box)
        filters.addWidget(self.score_box)
        filters.addStretch(1)
        filters.addWidget(self.apply_button)
        self.root.insertLayout(2, filters)

        columns = [
            Column("student_no", "学号", 125), Column("student_name", "姓名", 85),
            Column("class_name", "班级", 190), Column("course_code", "课程代码", 95),
            Column("course_name", "课程名", 175), Column("teacher_name", "教师", 80),
            Column("semester", "学期", 105, "center"),
            Column("score", "成绩", 70, "right", "decimal"),
            Column("status", "状态", 65, "center"),
            Column("score_time", "录入 / 修改时间", 150),
        ]
        self.table = DataTable(columns)
        self.pager = Pager(page_size=int(context.profile.get("page_size", 20)))
        self.root.addWidget(self.table, 1)
        self.root.addWidget(self.pager)
        self.table.rowActivated.connect(self._open_detail_for_row)
        self.apply_button.clicked.connect(lambda: self.reload(reset_page=True))
        self.semester_box.currentIndexChanged.connect(lambda: self.reload(reset_page=True))
        self.status_box.currentIndexChanged.connect(lambda: self.reload(reset_page=True))
        self.score_box.currentIndexChanged.connect(lambda: self.reload(reset_page=True))
        self.keyword_box.returnPressed.connect(lambda: self.reload(reset_page=True))
        self.pager.pageChanged.connect(self.load)

    def on_enter(self, **kwargs):
        self.reload(reset_page=kwargs.get("reset", False))

    def reload(self, reset_page=False):
        if reset_page:
            self.pager.reset()
        self.load(self.pager.page, self.pager.page_size)

    def load(self, page=1, page_size=None):
        page_size = int(page_size or self.pager.page_size)
        params = {
            "semester": self.semester_box.currentData(),
            "keyword": self.keyword_box.text().strip() or None,
            "status": self.status_box.currentData(),
            "score_state": self.score_box.currentData(),
        }
        self.set_busy(True, "正在查询选课记录…")
        self.context.runner.run(
            lambda: self.context.enrollment.page(page=page, page_size=page_size, **params),
            self._apply, lambda code, message: Notifier.error(self, f"[{code}] {message}"),
            lambda: self.set_busy(False))

    def _apply(self, payload):
        rows, total = payload
        self._rows = rows
        self.table.set_rows(rows, "没有匹配的选课记录", "调整筛选条件或先执行 F11 选课")
        self.pager.update_state(total, self.pager.page, self.pager.page_size)
        self.count_label.setText(f"命中 {total} 条 · 当前页 {len(rows)} 条")
        self.emit_status(f"选课记录：命中 {total} 条")

    def _selected(self):
        row = self.table.selected_row()
        if not row:
            Notifier.warn(self, "请先在列表中选择一条记录")
        return row

    def _open_detail_for_row(self, row):
        if self.mode == "enroll":
            TranscriptDialog(self.context, self, row["student_no"]).exec()
        else:
            ScoreDialog(self.context, self, preset_offering=row["offering_id"],
                        preset_student=row["student_no"]).exec()
            self.reload()

    def open_enroll(self):
        dialog = EnrollDialog(self.context, self)
        dialog.dataChanged.connect(self.reload)
        dialog.exec()

    def open_drop(self):
        dialog = DropDialog(self.context, self)
        dialog.dataChanged.connect(self.reload)
        dialog.exec()

    def open_transcript(self):
        row = self.table.selected_row()
        dialog = TranscriptDialog(self.context, self, row["student_no"] if row else None)
        dialog.exec()

    def open_roster(self):
        row = self.table.selected_row()
        dialog = RosterDialog(self.context, self, row["offering_id"] if row else None)
        dialog.exec()

    def open_score(self):
        row = self.table.selected_row()
        dialog = ScoreDialog(self.context, self,
                             preset_offering=row["offering_id"] if row else None,
                             preset_student=row["student_no"] if row else None)
        dialog.dataChanged.connect(self.reload)
        dialog.exec()
