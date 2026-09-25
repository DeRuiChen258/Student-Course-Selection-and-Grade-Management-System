"""F01–F04 学生管理页。"""

from app.specs import STUDENT
from .crud_page import EntityListPage


def make_page(context, parent=None):
    return EntityListPage(context, STUDENT, parent)
