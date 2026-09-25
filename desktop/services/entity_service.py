"""通用实体服务：把 EntitySpec 翻译成参数化 SQL 与业务校验。"""

import logging

from db.dao import EntityDao
from db.errors import DbError
from utils import validators

log = logging.getLogger(__name__)

LOOKUPS = {
    "classes": "SELECT class_id AS id, class_name AS label FROM class_group ORDER BY class_id",
    "depts": "SELECT dept_id AS id, dept_name AS label FROM department ORDER BY dept_id",
    "teachers": "SELECT teacher_id AS id, CONCAT(teacher_no, ' ', teacher_name) AS label "
                "FROM teacher ORDER BY teacher_no",
    "courses": "SELECT course_id AS id, CONCAT(course_code, ' ', course_name) AS label "
               "FROM course ORDER BY course_code",
    "semesters": "SELECT DISTINCT semester AS id, semester AS label FROM course_offering "
                 "ORDER BY semester DESC",
}


class EntityService:
    def __init__(self, db):
        self.db = db
        self._specs = {}
        self._lookups = {}

    def register(self, spec):
        self._specs[spec.key] = spec

    def spec(self, key):
        if key not in self._specs:
            raise DbError(-1, f"未注册的实体: {key}")
        return self._specs[key]

    def clear_cache(self):
        self._lookups.clear()

    def dao(self, key):
        spec = self.spec(key)
        return EntityDao(self.db, spec.table, spec.pk)

    def build_where(self, spec, filters):
        clauses, params = [], []
        for item in spec.filters:
            value = (filters or {}).get(item.name)
            if value is None or value == "":
                continue
            clauses.append(item.sql)
            params.append(f"%{value}%" if item.op == "like" else value)
        return (" AND ".join(clauses) if clauses else "1 = 1"), tuple(params)

    def page(self, key, filters=None, page=1, page_size=20):
        spec = self.spec(key)
        where, params = self.build_where(spec, filters)
        base = f"{spec.list_sql} WHERE {where}"
        total = int(self.db.scalar(f"SELECT COUNT(*) FROM ({base}) AS t", params,
                                   source=f"{spec.title} 计数") or 0)
        offset = max(0, (int(page) - 1) * int(page_size))
        rows = self.db.query(f"{base} ORDER BY {spec.order_by} LIMIT %s OFFSET %s",
                             params + (int(page_size), offset),
                             source=f"{spec.title} 查询")
        return rows, total

    def lookup(self, source):
        if source not in self._lookups:
            sql = LOOKUPS.get(source)
            if not sql:
                raise DbError(-1, f"未知候选来源: {source}")
            self._lookups[source] = self.db.query(sql, source=f"候选数据 {source}")
        return list(self._lookups[source])

    def fk_options(self, spec, field_name):
        item = spec.field(field_name)
        if not item or not item.source:
            return []
        return self.lookup(item.source)

    def validate(self, key, values, mode="create", current=None):
        spec = self.spec(key)
        errors = []
        for field in spec.fields:
            if mode == "edit" and field.name == spec.pk:
                continue
            value = values.get(field.name)
            if field.kind in ("int", "decimal"):
                message = validators.check_number(value, field.label, field.required,
                                                  field.minimum, field.maximum)
            elif field.kind == "enum":
                message = validators.check_choice(value, field.label, field.choices, field.required)
            elif field.kind == "fk":
                message = f"{field.label}必须选择" if field.required and value in (None, "") else None
            elif field.kind == "date":
                message = f"{field.label}不能为空" if field.required and not value else None
            else:
                message = validators.check_text(value, field.label, field.required, field.maxlen)
            if message:
                errors.append(message)
        errors.extend(self.business_rules(spec, values, mode, current))
        return errors

    def business_rules(self, spec, values, mode, current):
        errors = []
        if spec.key == "offering":
            capacity = values.get("capacity")
            enrolled = (current or {}).get("enrolled_count") or 0
            if capacity not in (None, "") and enrolled and int(capacity) < int(enrolled):
                errors.append(f"容量不得小于已选人数 {enrolled}（数据库约束 ck_offering_enrolled）")
            message = validators.check_text(values.get("semester"), "学期", True, 11,
                                            validators.SEMESTER, "形如 2026-2027-1")
            if message:
                errors.append(message)
        if spec.key == "student":
            message = validators.check_text(values.get("student_no"), "学号", True, 12,
                                            validators.STUDENT_NO, "12 位数字")
            if message:
                errors.append(message)
        if spec.key == "teacher":
            message = validators.check_text(values.get("teacher_no"), "工号", True, 8,
                                            validators.TEACHER_NO, "8 位数字")
            if message:
                errors.append(message)
        if spec.key == "course":
            message = validators.check_text(values.get("course_code"), "课程代码", True, 16,
                                            validators.COURSE_CODE, "大写字母与数字")
            if message:
                errors.append(message)
        phone = values.get("phone")
        if phone:
            message = validators.check_text(phone, "联系电话", False, 20, validators.PHONE)
            if message:
                errors.append(message)
        email = values.get("email")
        if email:
            message = validators.check_text(email, "邮箱", False, 60, validators.EMAIL)
            if message:
                errors.append(message)
        return errors

    def unique_errors(self, key, values, mode="create", pk_value=None):
        spec = self.spec(key)
        dao = self.dao(key)
        errors = []
        candidates = [name for name in self.unique_columns(spec)
                      if name in values and (mode == "create" or name != spec.pk)]
        for name in candidates:
            value = values.get(name)
            if not value:
                continue
            if dao.exists(name, value, None if mode == "create" else pk_value):
                label = next((f.label for f in spec.fields if f.name == name), name)
                errors.append(f"{label}「{value}」已存在（UNIQUE 约束）")
        errors.extend(self.composite_rules(spec, values, mode, pk_value))
        return errors

    def unique_columns(self, spec):
        """只把单列 UNIQUE 索引当作字段级唯一校验，复合唯一键交回数据库判断。"""
        cache_key = ("unique", spec.table)
        if cache_key not in self._lookups:
            rows = self.db.query(
                "SELECT index_name AS name, COUNT(*) AS column_count, "
                "       MIN(column_name) AS column_name "
                "FROM information_schema.statistics "
                "WHERE table_schema = DATABASE() AND table_name = %s AND non_unique = 0 "
                "  AND index_name <> 'PRIMARY' "
                "GROUP BY index_name HAVING COUNT(*) = 1",
                (spec.table,), source="元数据: 单列唯一约束")
            self._lookups[cache_key] = {row["column_name"] for row in rows}
        return set(self._lookups[cache_key])

    def composite_rules(self, spec, values, mode, pk_value):
        errors = []
        if spec.key == "offering":
            course_id = values.get("course_id")
            teacher_id = values.get("teacher_id")
            semester = values.get("semester")
            if course_id and teacher_id and semester:
                sql = ("SELECT COUNT(*) FROM course_offering "
                       "WHERE course_id = %s AND teacher_id = %s AND semester = %s")
                params = [course_id, teacher_id, semester]
                if mode == "edit" and pk_value:
                    sql += " AND offering_id <> %s"
                    params.append(pk_value)
                if int(self.db.scalar(sql, tuple(params),
                                      source="唯一性检查 uk_offering") or 0) > 0:
                    errors.append("同一课程、同一教师、同一学期已存在开课记录"
                                  "（UNIQUE uk_offering）")
        return errors

    def create(self, key, values):
        errors = self.validate(key, values, "create") + self.unique_errors(key, values, "create")
        if errors:
            raise DbError(-1, "；".join(errors), hint="服务层校验未通过")
        return self.dao(key).insert(self.payload(key, values, "create"))

    def update(self, key, pk_value, values, current=None):
        errors = (self.validate(key, values, "edit", current)
                  + self.unique_errors(key, values, "edit", pk_value))
        if errors:
            raise DbError(-1, "；".join(errors), hint="服务层校验未通过")
        payload = self.payload(key, values, "edit")
        if not payload:
            raise DbError(-1, "没有需要更新的字段")
        return self.dao(key).update(pk_value, payload)

    def payload(self, key, values, mode):
        spec = self.spec(key)
        payload = {}
        for field in spec.fields:
            if field.name not in values or field.name == spec.pk:
                continue
            if mode == "edit" and field.readonly:
                continue
            value = values.get(field.name)
            if isinstance(value, str):
                value = value.strip() or None
            payload[field.name] = value
        return payload

    def delete(self, key, pk_value):
        return self.dao(key).delete(pk_value)

    def delete_many(self, key, pk_values):
        return self.dao(key).delete_many(pk_values)

    def get(self, key, pk_value):
        return self.dao(key).get(pk_value)
