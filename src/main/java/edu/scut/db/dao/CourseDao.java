package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.Course;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class CourseDao extends BaseDao {

    private static final String SELECT = "SELECT c.course_id, c.course_code, c.course_name, c.credit, c.hours, "
            + "c.course_type, c.dept_id, d.dept_name FROM course c "
            + "JOIN department d ON d.dept_id = c.dept_id ";

    public CourseDao(ConnectionProvider provider) {
        super(provider);
    }

    public Course findByCode(String courseCode) {
        return queryOne(SELECT + "WHERE c.course_code = ?", this::map, courseCode);
    }

    public Course findById(Connection connection, Integer courseId) {
        return queryOne(connection, SELECT + "WHERE c.course_id = ?", this::map, courseId);
    }

    public List<Course> search(String keyword, String deptCode, String courseType) {
        StringBuilder sql = new StringBuilder(SELECT).append("WHERE 1 = 1");
        List<Object> args = new ArrayList<>();
        if (keyword != null && !keyword.isBlank()) {
            sql.append(" AND (c.course_code LIKE ? OR c.course_name LIKE ?)");
            args.add("%" + keyword + "%");
            args.add("%" + keyword + "%");
        }
        if (deptCode != null && !deptCode.isBlank()) {
            sql.append(" AND d.dept_code = ?");
            args.add(deptCode);
        }
        if (courseType != null && !courseType.isBlank()) {
            sql.append(" AND c.course_type = ?");
            args.add(courseType);
        }
        sql.append(" ORDER BY c.course_code");
        return query(sql.toString(), this::map, args.toArray());
    }

    public void insert(Connection connection, Course course) {
        update(connection, "INSERT INTO course (course_code, course_name, credit, hours, course_type, dept_id) "
                        + "VALUES (?, ?, ?, ?, ?, ?)",
                course.getCourseCode(), course.getCourseName(), course.getCredit(), course.getHours(),
                course.getCourseType(), course.getDeptId());
    }

    public int update(Connection connection, Course course) {
        return update(connection, "UPDATE course SET course_name = ?, credit = ?, hours = ?, course_type = ?, "
                        + "dept_id = ? WHERE course_code = ?",
                course.getCourseName(), course.getCredit(), course.getHours(), course.getCourseType(),
                course.getDeptId(), course.getCourseCode());
    }

    public int deleteByCode(Connection connection, String courseCode) {
        return update(connection, "DELETE FROM course WHERE course_code = ?", courseCode);
    }

    public int countOfferings(Connection connection, Integer courseId) {
        return count(connection, "SELECT COUNT(*) FROM course_offering WHERE course_id = ?", courseId);
    }

    private Course map(ResultSet rs) throws SQLException {
        Course course = new Course();
        course.setCourseId(rs.getInt("course_id"));
        course.setCourseCode(rs.getString("course_code"));
        course.setCourseName(rs.getString("course_name"));
        course.setCredit(rs.getBigDecimal("credit"));
        course.setHours(rs.getInt("hours"));
        course.setCourseType(rs.getString("course_type"));
        course.setDeptId(rs.getInt("dept_id"));
        course.setDeptName(rs.getString("dept_name"));
        return course;
    }
}
