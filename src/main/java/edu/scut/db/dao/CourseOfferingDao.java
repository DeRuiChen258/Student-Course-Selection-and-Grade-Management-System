package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.CourseOffering;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class CourseOfferingDao extends BaseDao {

    private static final String SELECT = "SELECT o.offering_id, o.course_id, o.teacher_id, o.semester, o.capacity, "
            + "o.enrolled_count, o.classroom, o.open_time, c.course_code, c.course_name, t.teacher_name "
            + "FROM course_offering o JOIN course c ON c.course_id = o.course_id "
            + "JOIN teacher t ON t.teacher_id = o.teacher_id ";

    public CourseOfferingDao(ConnectionProvider provider) {
        super(provider);
    }

    public CourseOffering findById(Integer offeringId) {
        return queryOne(SELECT + "WHERE o.offering_id = ?", this::map, offeringId);
    }

    public CourseOffering findByIdForUpdate(Connection connection, Integer offeringId) {
        return queryOne(connection, "SELECT offering_id, course_id, teacher_id, semester, capacity, "
                + "enrolled_count, classroom, open_time FROM course_offering WHERE offering_id = ? FOR UPDATE",
                this::mapBase, offeringId);
    }

    public List<CourseOffering> search(String semester, String teacherNo, String courseCode) {
        StringBuilder sql = new StringBuilder(SELECT).append("WHERE 1 = 1");
        List<Object> args = new ArrayList<>();
        if (semester != null && !semester.isBlank()) {
            sql.append(" AND o.semester = ?");
            args.add(semester);
        }
        if (teacherNo != null && !teacherNo.isBlank()) {
            sql.append(" AND t.teacher_no = ?");
            args.add(teacherNo);
        }
        if (courseCode != null && !courseCode.isBlank()) {
            sql.append(" AND c.course_code = ?");
            args.add(courseCode);
        }
        sql.append(" ORDER BY o.semester DESC, c.course_code LIMIT 200");
        return query(sql.toString(), this::map, args.toArray());
    }

    public void insert(Connection connection, CourseOffering offering) {
        update(connection, "INSERT INTO course_offering (course_id, teacher_id, semester, capacity, "
                        + "enrolled_count, classroom, open_time) VALUES (?, ?, ?, ?, 0, ?, ?)",
                offering.getCourseId(), offering.getTeacherId(), offering.getSemester(), offering.getCapacity(),
                offering.getClassroom(), offering.getOpenTime());
    }

    public int updateCapacity(Connection connection, Integer offeringId, Integer capacity) {
        return update(connection, "UPDATE course_offering SET capacity = ? WHERE offering_id = ?",
                capacity, offeringId);
    }

    public int updateEnrolledCount(Connection connection, Integer offeringId, Integer enrolledCount) {
        return update(connection, "UPDATE course_offering SET enrolled_count = ? WHERE offering_id = ?",
                enrolledCount, offeringId);
    }

    private CourseOffering map(ResultSet rs) throws SQLException {
        CourseOffering offering = mapBase(rs);
        offering.setCourseCode(rs.getString("course_code"));
        offering.setCourseName(rs.getString("course_name"));
        offering.setTeacherName(rs.getString("teacher_name"));
        return offering;
    }

    private CourseOffering mapBase(ResultSet rs) throws SQLException {
        CourseOffering offering = new CourseOffering();
        offering.setOfferingId(rs.getInt("offering_id"));
        offering.setCourseId(rs.getInt("course_id"));
        offering.setTeacherId(rs.getInt("teacher_id"));
        offering.setSemester(rs.getString("semester"));
        offering.setCapacity(rs.getInt("capacity"));
        offering.setEnrolledCount(rs.getInt("enrolled_count"));
        offering.setClassroom(rs.getString("classroom"));
        offering.setOpenTime(rs.getTimestamp("open_time").toLocalDateTime());
        return offering;
    }
}
