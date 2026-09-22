package edu.scut.db.service;

import edu.scut.db.dao.AuditLogDao;
import edu.scut.db.dao.BaseDao;
import edu.scut.db.dao.EnrollmentDao;
import edu.scut.db.db.Tx;
import edu.scut.db.model.AuditLog;
import edu.scut.db.service.dto.CourseStat;
import edu.scut.db.service.dto.GpaRow;
import edu.scut.db.service.dto.StudentTranscript;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

public class ReportService extends BaseDao {

    private final EnrollmentDao enrollmentDao;
    private final AuditLogDao auditLogDao;

    public ReportService(Tx tx) {
        super(tx.provider());
        this.enrollmentDao = new EnrollmentDao(tx.provider());
        this.auditLogDao = new AuditLogDao(tx.provider());
    }

    public List<CourseStat> courseStats(int limit) {
        return query("SELECT `课程代码`, `课程名`, `学期`, `选课人数`, `平均分`, `最高分`, `最低分`, `不及格人数` "
                + "FROM v_course_stat ORDER BY `平均分` IS NULL, `平均分` DESC LIMIT ?", this::mapCourseStat, limit);
    }

    public List<GpaRow> gpaRanking(int limit) {
        String sql = "SELECT ROW_NUMBER() OVER (ORDER BY t.gpa DESC, t.student_no) AS rk, t.student_no, "
                + "t.student_name, t.gpa, t.credits, t.fails FROM ("
                + "SELECT s.student_no, s.student_name, ROUND(SUM(x.gp * x.credit) / SUM(x.credit), 2) AS gpa, "
                + "SUM(x.credit) AS credits, SUM(CASE WHEN x.score < 60 THEN 1 ELSE 0 END) AS fails "
                + "FROM (SELECT e.student_id, c.credit, e.score, CASE WHEN e.score >= 90 THEN 4.0 "
                + "WHEN e.score >= 80 THEN 3.0 WHEN e.score >= 70 THEN 2.0 WHEN e.score >= 60 THEN 1.0 "
                + "ELSE 0.0 END AS gp FROM enrollment e JOIN course_offering o ON o.offering_id = e.offering_id "
                + "JOIN course c ON c.course_id = o.course_id WHERE e.status = '已选' AND e.score IS NOT NULL) x "
                + "JOIN student s ON s.student_id = x.student_id "
                + "GROUP BY s.student_id, s.student_no, s.student_name) t ORDER BY t.gpa DESC, t.student_no LIMIT ?";
        return query(sql, this::mapGpa, limit);
    }

    public List<String[]> semesterSummary() {
        return query("SELECT semester, COUNT(*) AS offerings, COUNT(DISTINCT course_id) AS courses, "
                + "SUM(capacity) AS capacity, SUM(enrolled_count) AS enrolled FROM course_offering "
                + "GROUP BY semester ORDER BY semester DESC LIMIT 12",
                rs -> new String[]{rs.getString("semester"), String.valueOf(rs.getInt("offerings")),
                        String.valueOf(rs.getInt("courses")), String.valueOf(rs.getInt("capacity")),
                        String.valueOf(rs.getInt("enrolled"))});
    }

    public List<StudentTranscript> transcript(String studentNo) {
        return query("SELECT `学号`, `姓名`, `学期`, `课程代码`, `课程名`, `学分`, `成绩`, `等级`, `绩点`, `教师` "
                + "FROM v_student_transcript WHERE `学号` = ? ORDER BY `学期` DESC, `课程代码`",
                this::mapTranscript, studentNo);
    }

    public List<String[]> scoreDistribution(Integer offeringId) {
        return enrollmentDao.scoreDistribution(offeringId);
    }

    public List<AuditLog> recentAudit(int limit) {
        return auditLogDao.findRecent(limit);
    }

    private CourseStat mapCourseStat(ResultSet rs) throws SQLException {
        CourseStat stat = new CourseStat();
        stat.setCourseCode(rs.getString(1));
        stat.setCourseName(rs.getString(2));
        stat.setSemester(rs.getString(3));
        stat.setEnrolledCount(rs.getInt(4));
        stat.setAvgScore(rs.getBigDecimal(5));
        stat.setMaxScore(rs.getBigDecimal(6));
        stat.setMinScore(rs.getBigDecimal(7));
        stat.setFailCount(rs.getInt(8));
        return stat;
    }

    private GpaRow mapGpa(ResultSet rs) throws SQLException {
        GpaRow row = new GpaRow();
        row.setRank(rs.getInt("rk"));
        row.setStudentNo(rs.getString("student_no"));
        row.setStudentName(rs.getString("student_name"));
        row.setGpa(rs.getBigDecimal("gpa"));
        row.setTotalCredit(rs.getBigDecimal("credits"));
        row.setFailCount(rs.getInt("fails"));
        return row;
    }

    private StudentTranscript mapTranscript(ResultSet rs) throws SQLException {
        StudentTranscript row = new StudentTranscript();
        row.setStudentNo(rs.getString(1));
        row.setStudentName(rs.getString(2));
        row.setSemester(rs.getString(3));
        row.setCourseCode(rs.getString(4));
        row.setCourseName(rs.getString(5));
        row.setCredit(rs.getBigDecimal(6));
        row.setScore(rs.getBigDecimal(7));
        row.setLevel(rs.getString(8));
        row.setGradePoint(rs.getBigDecimal(9));
        row.setTeacherName(rs.getString(10));
        return row;
    }
}
