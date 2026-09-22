package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.Enrollment;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

public class EnrollmentDao extends BaseDao {

    private static final String SELECT = "SELECT e.enrollment_id, e.student_id, e.offering_id, e.enroll_time, "
            + "e.score, e.score_time, e.status, s.student_no, s.student_name, c.course_code, c.course_name, "
            + "o.semester, t.teacher_name FROM enrollment e "
            + "JOIN student s ON s.student_id = e.student_id "
            + "JOIN course_offering o ON o.offering_id = e.offering_id "
            + "JOIN course c ON c.course_id = o.course_id "
            + "JOIN teacher t ON t.teacher_id = o.teacher_id ";

    public EnrollmentDao(ConnectionProvider provider) {
        super(provider);
    }

    public List<Enrollment> findByStudent(String studentNo) {
        return query(SELECT + "WHERE s.student_no = ? AND e.status = '已选' ORDER BY o.semester DESC, c.course_code",
                this::map, studentNo);
    }

    public List<Enrollment> findByOffering(Integer offeringId) {
        return query(SELECT + "WHERE e.offering_id = ? AND e.status = '已选' "
                + "ORDER BY e.score IS NULL, e.score DESC", this::map, offeringId);
    }

    public List<String[]> scoreDistribution(Integer offeringId) {
        return query("SELECT CASE WHEN score IS NULL THEN '未出分' WHEN score >= 90 THEN '90-100' "
                        + "WHEN score >= 80 THEN '80-89' WHEN score >= 70 THEN '70-79' "
                        + "WHEN score >= 60 THEN '60-69' ELSE '60 以下' END AS band, COUNT(*) AS cnt "
                        + "FROM enrollment WHERE offering_id = ? AND status = '已选' GROUP BY band ORDER BY MIN(score)",
                rs -> new String[]{rs.getString("band"), String.valueOf(rs.getInt("cnt"))}, offeringId);
    }

    public Enrollment findByStudentAndOffering(Connection connection, Integer studentId, Integer offeringId) {
        return queryOne(connection, "SELECT enrollment_id, student_id, offering_id, enroll_time, score, score_time, "
                + "status FROM enrollment WHERE student_id = ? AND offering_id = ? FOR UPDATE",
                this::mapBase, studentId, offeringId);
    }

    public void insert(Connection connection, Integer studentId, Integer offeringId) {
        update(connection, "INSERT INTO enrollment (student_id, offering_id, status) VALUES (?, ?, '已选')",
                studentId, offeringId);
    }

    public int markDropped(Connection connection, Integer enrollmentId) {
        return update(connection, "UPDATE enrollment SET status = '已退' WHERE enrollment_id = ? AND status = '已选'",
                enrollmentId);
    }

    public int markSelected(Connection connection, Integer enrollmentId) {
        return update(connection, "UPDATE enrollment SET status = '已选' WHERE enrollment_id = ? AND status = '已退'",
                enrollmentId);
    }

    public int delete(Connection connection, Integer enrollmentId) {
        return update(connection, "DELETE FROM enrollment WHERE enrollment_id = ?", enrollmentId);
    }

    public int updateScore(Connection connection, Integer enrollmentId, BigDecimal score) {
        return update(connection, "UPDATE enrollment SET score = ? WHERE enrollment_id = ?", score, enrollmentId);
    }

    public int countActive(Connection connection, Integer studentId) {
        return count(connection, "SELECT COUNT(*) FROM enrollment WHERE student_id = ? AND status = '已选'", studentId);
    }

    public BigDecimal gpa(Integer studentId) {
        return decimal(provider.getConnection(), "SELECT f_gpa(?)", studentId);
    }

    private Enrollment mapBase(ResultSet rs) throws SQLException {
        Enrollment enrollment = new Enrollment();
        enrollment.setEnrollmentId(rs.getInt("enrollment_id"));
        enrollment.setStudentId(rs.getInt("student_id"));
        enrollment.setOfferingId(rs.getInt("offering_id"));
        enrollment.setEnrollTime(rs.getTimestamp("enroll_time").toLocalDateTime());
        enrollment.setScore(rs.getBigDecimal("score"));
        if (rs.getTimestamp("score_time") != null) {
            enrollment.setScoreTime(rs.getTimestamp("score_time").toLocalDateTime());
        }
        enrollment.setStatus(rs.getString("status"));
        return enrollment;
    }

    private Enrollment map(ResultSet rs) throws SQLException {
        Enrollment enrollment = mapBase(rs);
        enrollment.setStudentNo(rs.getString("student_no"));
        enrollment.setStudentName(rs.getString("student_name"));
        enrollment.setCourseCode(rs.getString("course_code"));
        enrollment.setCourseName(rs.getString("course_name"));
        enrollment.setSemester(rs.getString("semester"));
        enrollment.setTeacherName(rs.getString("teacher_name"));
        return enrollment;
    }
}
