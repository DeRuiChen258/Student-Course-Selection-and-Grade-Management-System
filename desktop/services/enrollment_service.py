"""选课 / 退课 / 成绩：统一走存储过程并翻译错误码。"""

import logging

from db.dao import EnrollmentDao
from db.errors import PROC_CODES, DbError

log = logging.getLogger(__name__)


class EnrollmentService:
    def __init__(self, db):
        self.db = db
        self.dao = EnrollmentDao(db)

    def _ensure_ok(self, code, message):
        if code is None:
            raise DbError(-1, "存储过程未返回错误码")
        if int(code) != 0:
            text = message or PROC_CODES.get(int(code), "未知错误")
            raise DbError(int(code), text, hint=PROC_CODES.get(int(code), ""))
        return message or "OK"

    def enroll(self, student_no, offering_id):
        code, message = self.dao.enroll(student_no, offering_id)
        self._ensure_ok(code, message)
        detail = self.dao.offering_detail(offering_id) or {}
        return (f"选课成功：{student_no} → {detail.get('course_code', '')} "
                f"{detail.get('course_name', '')}（已选 {detail.get('enrolled', '?')}/"
                f"{detail.get('capacity', '?')}，触发器 trg_enrollment_ai 已联动计数）")

    def drop(self, student_no, offering_id):
        code, message = self.dao.drop(student_no, offering_id)
        self._ensure_ok(code, message)
        detail = self.dao.offering_detail(offering_id) or {}
        return (f"退课成功：{student_no} ← {detail.get('course_code', '')} "
                f"（已选 {detail.get('enrolled', '?')}/{detail.get('capacity', '?')}，"
                f"触发器 trg_enrollment_au 已回补计数）")

    def save_score(self, student_no, offering_id, score):
        code, message = self.dao.save_score(student_no, offering_id, score)
        self._ensure_ok(code, message)
        return f"成绩保存成功：{student_no} / {score} 分（触发器 trg_enrollment_bu 已刷新时间戳）"

    def transcript(self, student_no, semester=None):
        return self.dao.transcript(student_no, semester)

    def roster(self, offering_id):
        return self.dao.roster(offering_id)

    def offering_detail(self, offering_id):
        return self.dao.offering_detail(offering_id)

    def offering_options(self, semester=None, keyword=None, only_open=True):
        return self.dao.offering_options(semester, keyword, only_open)

    def student_options(self, keyword=None, limit=300):
        return self.dao.student_options(keyword, limit)

    def semesters(self):
        return self.dao.semester_options()

    def student_records(self, student_no):
        return self.dao.by_student(student_no)

    def student_summary(self, student_no):
        return self.dao.student_summary(student_no) or {}

    def roster_stats(self, offering_id):
        return self.dao.roster_stats(offering_id) or {}

    def page(self, semester=None, keyword=None, status=None, score_state=None,
             page=1, page_size=20):
        offset = max(0, (int(page) - 1) * int(page_size))
        return self.dao.page(semester, keyword, status, score_state,
                             int(page_size), offset)
