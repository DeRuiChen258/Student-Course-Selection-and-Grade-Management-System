"""F13 / F14 成绩管理页，复用选课列表页并切换为成绩模式。"""

from .enrollments import EnrollmentListPage


def make_page(context, parent=None):
    return EnrollmentListPage(context, mode="grade", parent=parent)
