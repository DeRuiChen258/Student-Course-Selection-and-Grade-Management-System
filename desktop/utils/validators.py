"""字段校验：与数据库 CHECK / UNIQUE / 触发器形成多层校验的第二层。"""

import re

STUDENT_NO = re.compile(r"^\d{12}$")
TEACHER_NO = re.compile(r"^\d{8}$")
COURSE_CODE = re.compile(r"^[A-Z0-9]{2,16}$")
SEMESTER = re.compile(r"^\d{4}-\d{4}-[12]$")
PHONE = re.compile(r"^[0-9\-+ ]{6,20}$")
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def check_text(value, label, required=False, maxlen=None, pattern=None, hint=""):
    text = "" if value is None else str(value).strip()
    if not text:
        return f"{label}不能为空" if required else None
    if maxlen and len(text) > maxlen:
        return f"{label}长度不能超过 {maxlen} 个字符"
    if pattern and not pattern.match(text):
        return f"{label}格式不正确" + (f"（{hint}）" if hint else "")
    return None


def check_number(value, label, required=False, minimum=None, maximum=None):
    if value is None or value == "":
        return f"{label}不能为空" if required else None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return f"{label}必须是数字"
    if minimum is not None and number < minimum:
        return f"{label}不得小于 {minimum}"
    if maximum is not None and number > maximum:
        return f"{label}不得大于 {maximum}"
    return None


def check_choice(value, label, choices, required=True):
    if not value:
        return f"{label}必须选择" if required else None
    if choices and value not in choices:
        return f"{label}取值不合法"
    return None
