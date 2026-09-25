"""功能编号与对象中文名：界面显式标注 F01–F16。"""

FUNCTIONS = {
    "F01": "学生信息新增（新生入学）",
    "F02": "学生信息修改",
    "F03": "学生信息删除",
    "F04": "学生信息查询",
    "F05": "课程录入",
    "F06": "课程信息修改",
    "F07": "课程信息删除",
    "F08": "课程信息查询",
    "F09": "教师信息管理",
    "F10": "开课管理（容量调整）",
    "F11": "学生选课",
    "F12": "学生退课",
    "F13": "成绩录入",
    "F14": "成绩修改",
    "F15": "选课信息查询（课表 / 名单）",
    "F16": "统计报表",
}

TABLE_LABELS = {
    "department": "院系",
    "teacher": "教师",
    "class_group": "班级",
    "student": "学生",
    "course": "课程",
    "course_offering": "开课",
    "enrollment": "选课与成绩",
    "sys_account": "账号与角色",
    "audit_log": "审计日志",
    "v_student_profile": "视图: 学生档案",
    "v_offering_detail": "视图: 开课详情",
    "v_student_transcript": "视图: 学生成绩单",
    "v_course_stat": "视图: 课程统计",
}

OBJECT_LABELS = {
    "tables": "基础表",
    "views": "视图",
    "triggers": "触发器",
    "routines": "例程（过程 + 函数）",
    "named_indexes": "显式索引 idx_*",
    "all_indexes": "全部索引",
}

ROLE_HINT = {
    "ADMIN": "完整权限",
    "TEACHER": "教学与成绩",
    "STUDENT": "学生自助",
}


def func_text(code):
    return f"{code} {FUNCTIONS.get(code, '')}".strip()


def func_labels(codes):
    return " · ".join(func_text(code) for code in codes)


def table_label(name):
    return TABLE_LABELS.get(name, name)
