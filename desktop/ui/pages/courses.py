"""F05–F08 课程管理页。"""

from app.specs import COURSE
from .crud_page import EntityListPage


def make_page(context, parent=None):
    return EntityListPage(context, COURSE, parent)
