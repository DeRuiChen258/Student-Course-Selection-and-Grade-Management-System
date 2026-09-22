package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.Teacher;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class TeacherDao extends BaseDao {

    private static final String SELECT = "SELECT t.teacher_id, t.teacher_no, t.teacher_name, t.gender, t.title, "
            + "t.dept_id, t.hire_date, t.phone, t.email, d.dept_name FROM teacher t "
            + "JOIN department d ON d.dept_id = t.dept_id ";

    public TeacherDao(ConnectionProvider provider) {
        super(provider);
    }

    public Teacher findByNo(String teacherNo) {
        return queryOne(SELECT + "WHERE t.teacher_no = ?", this::map, teacherNo);
    }

    public Teacher findById(Integer teacherId) {
        return queryOne(SELECT + "WHERE t.teacher_id = ?", this::map, teacherId);
    }

    public List<Teacher> findAll() {
        return query(SELECT + "ORDER BY t.teacher_no", this::map);
    }

    public List<Teacher> search(String keyword, String deptCode, String title) {
        StringBuilder sql = new StringBuilder(SELECT).append("WHERE 1 = 1");
        List<Object> args = new ArrayList<>();
        if (keyword != null && !keyword.isBlank()) {
            sql.append(" AND (t.teacher_no LIKE ? OR t.teacher_name LIKE ?)");
            args.add("%" + keyword + "%");
            args.add("%" + keyword + "%");
        }
        if (deptCode != null && !deptCode.isBlank()) {
            sql.append(" AND d.dept_code = ?");
            args.add(deptCode);
        }
        if (title != null && !title.isBlank()) {
            sql.append(" AND t.title = ?");
            args.add(title);
        }
        sql.append(" ORDER BY t.teacher_no");
        return query(sql.toString(), this::map, args.toArray());
    }

    public void insert(Connection connection, Teacher teacher) {
        update(connection, "INSERT INTO teacher (teacher_no, teacher_name, gender, title, dept_id, hire_date, "
                        + "phone, email) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                teacher.getTeacherNo(), teacher.getTeacherName(), teacher.getGender(), teacher.getTitle(),
                teacher.getDeptId(), teacher.getHireDate(), teacher.getPhone(), teacher.getEmail());
    }

    public int update(Connection connection, Teacher teacher) {
        return update(connection, "UPDATE teacher SET teacher_name = ?, gender = ?, title = ?, dept_id = ?, "
                        + "hire_date = ?, phone = ?, email = ? WHERE teacher_no = ?",
                teacher.getTeacherName(), teacher.getGender(), teacher.getTitle(), teacher.getDeptId(),
                teacher.getHireDate(), teacher.getPhone(), teacher.getEmail(), teacher.getTeacherNo());
    }

    public int deleteByNo(Connection connection, String teacherNo) {
        return update(connection, "DELETE FROM teacher WHERE teacher_no = ?", teacherNo);
    }

    public int countOfferings(Connection connection, Integer teacherId) {
        return count(connection, "SELECT COUNT(*) FROM course_offering WHERE teacher_id = ?", teacherId);
    }

    private Teacher map(ResultSet rs) throws SQLException {
        Teacher teacher = new Teacher();
        teacher.setTeacherId(rs.getInt("teacher_id"));
        teacher.setTeacherNo(rs.getString("teacher_no"));
        teacher.setTeacherName(rs.getString("teacher_name"));
        teacher.setGender(rs.getString("gender"));
        teacher.setTitle(rs.getString("title"));
        teacher.setDeptId(rs.getInt("dept_id"));
        teacher.setHireDate(rs.getDate("hire_date").toLocalDate());
        teacher.setPhone(rs.getString("phone"));
        teacher.setEmail(rs.getString("email"));
        teacher.setDeptName(rs.getString("dept_name"));
        return teacher;
    }
}
