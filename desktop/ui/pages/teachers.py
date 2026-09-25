"""F09 教师管理页。"""

from app.specs import TEACHER
from .crud_page import EntityListPage


def make_page(context, parent=None):
    return EntityListPage(context, TEACHER, parent)
