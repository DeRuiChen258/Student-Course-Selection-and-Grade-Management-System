"""元数据服务：对象计数、表结构、索引、外键、CHECK 约束。"""

from db.dao import MetaDao


class MetaService:
    def __init__(self, db):
        self.db = db
        self.dao = MetaDao(db)
        self._cache = {}

    def clear_cache(self):
        self._cache.clear()

    def counts(self):
        return self.db.object_counts() or {}

    def objects(self):
        return self.dao.list_objects()

    def columns(self, table):
        key = ("columns", table)
        if key not in self._cache:
            self._cache[key] = self.dao.columns(table)
        return list(self._cache[key])

    def columns_meta(self, table):
        return {row["name"]: row for row in self.columns(table)}

    def indexes(self, table):
        return self.dao.indexes(table)

    def foreign_keys(self, table):
        return self.dao.foreign_keys(table)

    def checks(self, table):
        return self.dao.checks(table)

    def primary_key(self, table):
        return self.dao.primary_key(table)

    def label(self, table, column):
        return self.dao.column_label(table, column)

    def enum_values(self, table, column):
        return self.dao.enum_values(table, column)

    def row_count(self, table):
        return self.dao.table_rows(table)

    def overview(self):
        counts = self.counts()
        counts["students"] = self.dao.table_rows("student")
        counts["courses"] = self.dao.table_rows("course")
        counts["offerings"] = self.dao.table_rows("course_offering")
        counts["enrollments"] = self.dao.table_rows("enrollment")
        counts["score_ready"] = int(self.db.scalar(
            "SELECT COUNT(*) FROM enrollment WHERE score IS NOT NULL",
            source="已出分记录") or 0)
        counts["avg_score"] = self.db.scalar(
            "SELECT ROUND(AVG(score), 2) FROM enrollment WHERE score IS NOT NULL",
            source="总体均分")
        return counts

    def structure_report(self, table):
        return {
            "columns": self.columns(table),
            "indexes": self.indexes(table),
            "foreign_keys": self.foreign_keys(table),
            "checks": self.checks(table),
        }
