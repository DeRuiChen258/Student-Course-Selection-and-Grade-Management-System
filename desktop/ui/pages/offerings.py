"""F10 开课管理页。"""

from app.specs import OFFERING
from .crud_page import EntityListPage


def make_page(context, parent=None):
    return EntityListPage(context, OFFERING, parent)
