"""实体规格：字段、筛选、列表列与业务校验的声明式描述。"""

from dataclasses import dataclass, field

from .table_model import Column


@dataclass
class FieldSpec:
    name: str
    label: str
    kind: str = "text"
    required: bool = False
    readonly: bool = False
    maxlen: int = 0
    hint: str = ""
    minimum: float = None
    maximum: float = None
    decimals: int = 1
    choices: tuple = ()
    source: str = ""
    default: object = None
    comment: str = ""


@dataclass
class FilterSpec:
    name: str
    label: str
    sql: str
    op: str = "like"
    kind: str = "text"
    source: str = ""
    choices: tuple = ()
    width: int = 150


@dataclass
class EntitySpec:
    key: str
    title: str
    funcs: tuple
    table: str
    pk: str
    biz_key: str
    list_sql: str
    columns: list
    fields: list = field(default_factory=list)
    filters: list = field(default_factory=list)
    order_by: str = "1"
    subtitle: str = ""
    delete_note: str = ""

    def field(self, name):
        for item in self.fields:
            if item.name == name:
                return item
        return None

    def filter(self, name):
        for item in self.filters:
            if item.name == name:
                return item
        return None
