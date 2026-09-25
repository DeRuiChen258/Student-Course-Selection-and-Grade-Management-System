"""值格式化：统一 Decimal / 日期 / 空值在界面上的呈现。"""

import datetime as dt
from decimal import Decimal


def fmt_value(value, kind="text"):
    if value is None:
        return "—"
    if isinstance(value, Decimal):
        return fmt_decimal(value)
    if isinstance(value, dt.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, dt.date):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, dt.timedelta):
        total = int(value.total_seconds())
        return f"{total // 3600:02d}:{total % 3600 // 60:02d}:{total % 60:02d}"
    if isinstance(value, bool):
        return "是" if value else "否"
    if kind == "number" and isinstance(value, (int, float)):
        return f"{value:,}"
    return str(value)


def fmt_decimal(value, digits=2):
    if value is None:
        return "—"
    text = f"{Decimal(value):.{digits}f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def fmt_number(value):
    if value is None:
        return "—"
    return f"{int(value):,}"


def fmt_percent(value, digits=1):
    if value is None:
        return "—"
    return f"{float(value):.{digits}f}%"


def short(text, limit=48):
    text = "" if text is None else str(text).replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"
