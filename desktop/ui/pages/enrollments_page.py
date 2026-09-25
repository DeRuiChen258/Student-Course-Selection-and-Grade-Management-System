"""F11–F15 选课与成绩页入口。"""

from .enrollments import EnrollmentListPage


def make_page(context, parent=None):
    return EnrollmentListPage(context, mode="enroll", parent=parent)
