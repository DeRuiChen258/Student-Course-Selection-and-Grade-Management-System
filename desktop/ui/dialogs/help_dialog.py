"""帮助与功能对照：F01–F16 到页面、入口与数据库对象的映射。"""

from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton,
                               QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout,
                               QWidget)

from app.labels import FUNCTIONS

FUNCTION_MAP = {
    "F01": ("学生管理", "工具栏「新增」", "student + UNIQUE uk_student_no"),
    "F02": ("学生管理", "选中行「编辑」", "student UPDATE + 触发器审计"),
    "F03": ("学生管理", "选中行「删除」", "student ← enrollment ON DELETE CASCADE、trg_student_ad"),
    "F04": ("学生管理", "筛选条 + 分页", "student ⋈ class_group ⋈ department"),
    "F05": ("课程管理", "工具栏「新增」", "course + ck_course_credit / ck_course_hours"),
    "F06": ("课程管理", "选中行「编辑」", "course UNIQUE uk_course_code"),
    "F07": ("课程管理", "选中行「删除」", "course ← course_offering ON DELETE RESTRICT"),
    "F08": ("课程管理", "筛选条", "course ⋈ department"),
    "F09": ("教师管理", "全部操作", "teacher + uk_teacher_no + fk_teacher_dept"),
    "F10": ("开课管理", "新增 / 编辑容量", "course_offering + uk_offering + ck_offering_enrolled"),
    "F11": ("选课与成绩", "「学生选课」", "p_enroll_student + trg_enrollment_bi / ai"),
    "F12": ("选课与成绩", "「学生退课」", "p_drop_course + trg_enrollment_au"),
    "F13": ("成绩管理", "「保存成绩」", "p_save_score + trg_enrollment_bu"),
    "F14": ("成绩管理", "选中已出分学生改分", "p_save_score + score_time 刷新"),
    "F15": ("选课与成绩", "「学生课表」「开课名单」", "v_student_transcript、v_offering_detail"),
    "F16": ("统计分析", "五个页签", "v_course_stat、f_gpa、GROUP BY 聚合"),
}

ERROR_TABLE = [
    ("40001", "p_enroll_student / p_drop_course", "学生不存在"),
    ("40002", "p_enroll_student", "学籍状态不允许选课（休学 / 退学）"),
    ("40004", "p_enroll_student", "重复选课"),
    ("40005", "p_enroll_student", "名额已满"),
    ("40006", "p_drop_course / p_save_score", "未选该课"),
    ("40007", "p_drop_course", "已有成绩，不能退课"),
    ("40008", "p_save_score", "成绩必须在 0 到 100 之间"),
    ("E004", "trg_enrollment_bi", "重复选课（触发器 SIGNAL）"),
    ("E005", "trg_enrollment_bi", "名额已满（触发器 SIGNAL）"),
    ("E007", "trg_enrollment_bu", "成绩越界（触发器 SIGNAL）"),
    ("1062", "MySQL 引擎", "唯一性约束冲突"),
    ("1451", "MySQL 引擎", "存在引用记录，禁止删除（外键 RESTRICT）"),
    ("1452", "MySQL 引擎", "外键引用不存在"),
    ("3819", "MySQL 引擎", "CHECK 约束不满足"),
    ("1142", "MySQL 引擎", "权限不足（数据库账号越权）"),
]

DEMO_SCRIPT = """现场演示顺序（10 分钟）

1. 登录：admin / Admin@123 —— 账号存于 sys_account，口令按 salt$SHA-256(salt+口令) 校验。
2. 仪表盘：对象自检卡片显示「基础表 9 / 视图 4 / 触发器 5 / 例程 5 / 显式索引 8」。
3. F04 学生管理：姓名输入「林」+ 状态「在读」，命中 1 条，观察 SQL 面板中的参数化 LIMIT/OFFSET。
4. F01 新生入学：新增 202301019999 / 演示同学 / 班级 1 号 / 2023-09-01，提交后回查。
5. F05 + F10：新增课程 ZZ901 → 为其新建开课（容量 2）。
6. F11 选课：为该生选上 ZZ901，观察已选 0/2 → 1/2 与触发器 trg_enrollment_ai。
7. F12 退课：退回 0/2；重新选上后进入 F13 录入 88.5 分。
8. F14 与错误演示：改分为 101 → 回显 [40008]；尝试退课 → 回显 [40007]。
9. F15：查看该生课表（v_student_transcript）与开课名单（含均分）。
10. F16：五类图表（课程选课人数、成绩分布、学期趋势、类型占比、GPA 排名）。
11. 权限页：切换 edu_teacher 账号执行越权 UPDATE，回显真实 ERROR 1142。
12. 数据表浏览：查看 student 表的结构 / 索引 / 外键 / CHECK，并用 EXPLAIN 对比索引效果。
"""


class HelpDialog(QDialog):
    def __init__(self, context, parent=None):
        super().__init__(parent)
        self.context = context
        self.setWindowTitle("帮助 · 功能对照与演示脚本")
        self.resize(980, 640)
        layout = QVBoxLayout(self)
        head = QLabel("帮助说明")
        head.setObjectName("DialogTitle")
        layout.addWidget(head)
        tabs = QTabWidget()
        tabs.addTab(self._function_tab(), "F01–F16 功能对照")
        tabs.addTab(self._object_tab(), "数据库对象")
        tabs.addTab(self._error_tab(), "错误码对照")
        tabs.addTab(self._script_tab(), "演示脚本")
        layout.addWidget(tabs, 1)
        close = QPushButton("关闭")
        close.setObjectName("Ghost")
        close.clicked.connect(self.accept)
        line = QHBoxLayout()
        line.addStretch(1)
        line.addWidget(close)
        layout.addLayout(line)

    def _table(self, headers, rows):
        table = QTableWidget(len(rows), len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                table.setItem(r, c, QTableWidgetItem(str(value)))
        table.resizeColumnsToContents()
        return table

    def _function_tab(self):
        rows = []
        for code in sorted(FUNCTIONS):
            page, entry, objects = FUNCTION_MAP.get(code, ("—", "—", "—"))
            rows.append((code, FUNCTIONS[code], page, entry, objects))
        return self._table(["编号", "功能", "所在页面", "界面入口", "对应数据库对象"], rows)

    def _object_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        counts = self.context.meta.counts()
        summary = QLabel(
            f"基础表 {counts.get('tables', 0)} · 视图 {counts.get('views', 0)} · "
            f"触发器 {counts.get('triggers', 0)} · 例程 {counts.get('routines', 0)} · "
            f"显式索引 {counts.get('named_indexes', 0)} · 全部索引 {counts.get('all_indexes', 0)}")
        summary.setObjectName("InfoPanel")
        layout.addWidget(summary)
        rows = [(row["name"], row["kind"], row["comment"]) for row in self.context.meta.objects()]
        layout.addWidget(self._table(["对象名", "类型", "注释"], rows), 1)
        return widget

    def _error_tab(self):
        return self._table(["错误码", "来源", "含义"], ERROR_TABLE)

    def _script_tab(self):
        editor = QPlainTextEdit(DEMO_SCRIPT)
        editor.setReadOnly(True)
        return editor
