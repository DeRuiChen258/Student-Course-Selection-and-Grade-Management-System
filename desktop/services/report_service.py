"""报表服务：统计图表与仪表盘的数据来源。"""

from db.dao import AuditDao, ReportDao


class ReportService:
    def __init__(self, db):
        self.db = db
        self.dao = ReportDao(db)
        self.audit = AuditDao(db)

    def course_stat(self, semester=None, dept_id=None, top=20):
        return self.dao.course_stat(semester, dept_id, top)

    def score_distribution(self, semester=None, dept_id=None):
        return self.dao.score_distribution(semester, dept_id)

    def semester_summary(self):
        return self.dao.semester_summary()

    def course_type_share(self, dept_id=None):
        return self.dao.course_type_share(dept_id)

    def gpa_ranking(self, class_id=None, top=20):
        return self.dao.gpa_ranking(class_id, top)

    def classes(self):
        return self.dao.class_options()

    def departments(self):
        return self.dao.dept_options()

    def recent_audit(self, limit=10):
        return self.audit.recent(limit)

    def audit_page(self, table_name=None, action=None, keyword=None, limit=50, offset=0):
        return self.audit.page(table_name, action, keyword, limit, offset)

    def audit_tables(self):
        return self.audit.tables()

    def explain_compare(self, offering_id):
        return self.dao.explain_index_compare(offering_id)
