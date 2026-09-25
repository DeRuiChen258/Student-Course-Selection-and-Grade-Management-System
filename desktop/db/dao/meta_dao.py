"""元数据访问：表结构、索引、外键、CHECK 约束、对象计数。"""

import re

from .base import DaoBase

_ENUM = re.compile(r"^enum\((.*)\)$")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def ident(name):
    if not _IDENT.match(str(name)):
        raise ValueError(f"非法标识符: {name}")
    return str(name)


class MetaDao(DaoBase):
    def list_objects(self):
        return self.db.query(
            "SELECT table_name AS name, table_type AS kind, "
            "       IFNULL(table_comment, '') AS comment, "
            "       IFNULL(table_rows, 0) AS est_rows "
            "FROM information_schema.tables "
            "WHERE table_schema = DATABASE() "
            "ORDER BY table_type DESC, table_name",
            source="元数据: 对象清单")

    def columns(self, table):
        return self.db.query(
            "SELECT column_name AS name, column_type AS type, data_type AS data_type, "
            "       is_nullable AS nullable, column_key AS key_type, "
            "       IFNULL(column_default, '') AS default_value, "
            "       IFNULL(column_comment, '') AS comment, "
            "       IFNULL(extra, '') AS extra, "
            "       IFNULL(character_maximum_length, 0) AS max_length, "
            "       IFNULL(numeric_precision, 0) AS num_precision, "
            "       IFNULL(numeric_scale, 0) AS num_scale "
            "FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s "
            "ORDER BY ordinal_position",
            (ident(table),), source="元数据: 表结构")

    def indexes(self, table):
        return self.db.query(
            "SELECT index_name AS name, "
            "       GROUP_CONCAT(column_name ORDER BY seq_in_index) AS columns, "
            "       IF(MIN(non_unique) = 0, '唯一', '普通') AS kind, "
            "       IFNULL(MAX(cardinality), 0) AS cardinality, "
            "       IF(index_name = 'PRIMARY', '主键', '') AS note "
            "FROM information_schema.statistics "
            "WHERE table_schema = DATABASE() AND table_name = %s "
            "GROUP BY index_name ORDER BY index_name = 'PRIMARY' DESC, index_name",
            (ident(table),), source="元数据: 索引")

    def foreign_keys(self, table):
        return self.db.query(
            "SELECT k.constraint_name AS name, k.column_name AS column_name, "
            "       k.referenced_table_name AS ref_table, k.referenced_column_name AS ref_column, "
            "       r.delete_rule AS delete_rule, r.update_rule AS update_rule "
            "FROM information_schema.key_column_usage k "
            "JOIN information_schema.referential_constraints r "
            "  ON r.constraint_schema = k.constraint_schema "
            " AND r.constraint_name = k.constraint_name "
            "WHERE k.table_schema = DATABASE() AND k.table_name = %s "
            "  AND k.referenced_table_name IS NOT NULL "
            "ORDER BY k.constraint_name",
            (ident(table),), source="元数据: 外键")

    def checks(self, table):
        return self.db.query(
            "SELECT t.constraint_name AS name, c.check_clause AS clause "
            "FROM information_schema.table_constraints t "
            "JOIN information_schema.check_constraints c "
            "  ON c.constraint_schema = t.constraint_schema "
            " AND c.constraint_name = t.constraint_name "
            "WHERE t.table_schema = DATABASE() AND t.table_name = %s "
            "  AND t.constraint_type = 'CHECK' "
            "ORDER BY t.constraint_name",
            (ident(table),), source="元数据: CHECK 约束")

    def primary_key(self, table):
        return self.db.scalar(
            "SELECT column_name FROM information_schema.key_column_usage "
            "WHERE table_schema = DATABASE() AND table_name = %s AND constraint_name = 'PRIMARY' "
            "ORDER BY ordinal_position LIMIT 1",
            (ident(table),), source="元数据: 主键")

    def columns_meta(self, table):
        return {row["name"]: row for row in self.columns(table)}

    def enum_values(self, table, column):
        row = self.db.query_one(
            "SELECT column_type AS column_type FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
            (ident(table), ident(column)), source="元数据: 枚举取值")
        matched = _ENUM.match((row or {}).get("column_type", "") or "")
        if not matched:
            return []
        return [part.strip().strip("'") for part in matched.group(1).split(",")]

    def column_label(self, table, column):
        row = self.db.query_one(
            "SELECT column_comment AS column_comment FROM information_schema.columns "
            "WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s",
            (ident(table), ident(column)), source="元数据: 字段注释")
        comment = (row or {}).get("column_comment", "") or ""
        return comment.split("，")[0].strip() or column

    def table_rows(self, table):
        return int(self.db.scalar(f"SELECT COUNT(*) FROM {ident(table)}",
                                  source="元数据: 行数") or 0)
