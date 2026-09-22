package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.Student;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

public class StudentDao extends BaseDao {

    private static final String SELECT = "SELECT s.student_id, s.student_no, s.student_name, s.gender, s.birth_date, "
            + "s.class_id, s.enroll_date, s.phone, s.email, s.status, c.class_name, d.dept_name "
            + "FROM student s JOIN class_group c ON c.class_id = s.class_id "
            + "JOIN department d ON d.dept_id = c.dept_id ";

    public StudentDao(ConnectionProvider provider) {
        super(provider);
    }

    public Student findByNo(String studentNo) {
        return queryOne(SELECT + "WHERE s.student_no = ?", this::map, studentNo);
    }

    public Student findById(Connection connection, Integer studentId) {
        return queryOne(connection, SELECT + "WHERE s.student_id = ?", this::map, studentId);
    }

    public List<Student> search(String studentNo, String nameKeyword, String classCode, String status,
                                int page, int size) {
        StringBuilder sql = new StringBuilder(SELECT).append("WHERE 1 = 1");
        List<Object> args = new ArrayList<>();
        if (studentNo != null && !studentNo.isBlank()) {
            sql.append(" AND s.student_no = ?");
            args.add(studentNo);
        }
        if (nameKeyword != null && !nameKeyword.isBlank()) {
            sql.append(" AND s.student_name LIKE ?");
            args.add("%" + nameKeyword + "%");
        }
        if (classCode != null && !classCode.isBlank()) {
            sql.append(" AND c.class_code = ?");
            args.add(classCode);
        }
        if (status != null && !status.isBlank()) {
            sql.append(" AND s.status = ?");
            args.add(status);
        }
        sql.append(" ORDER BY s.student_no LIMIT ? OFFSET ?");
        args.add(size);
        args.add(Math.max(0, (page - 1) * size));
        return query(sql.toString(), this::map, args.toArray());
    }

    public int count(String studentNo, String nameKeyword, String classCode, String status) {
        StringBuilder sql = new StringBuilder("SELECT COUNT(*) FROM student s "
                + "JOIN class_group c ON c.class_id = s.class_id WHERE 1 = 1");
        List<Object> args = new ArrayList<>();
        if (studentNo != null && !studentNo.isBlank()) {
            sql.append(" AND s.student_no = ?");
            args.add(studentNo);
        }
        if (nameKeyword != null && !nameKeyword.isBlank()) {
            sql.append(" AND s.student_name LIKE ?");
            args.add("%" + nameKeyword + "%");
        }
        if (classCode != null && !classCode.isBlank()) {
            sql.append(" AND c.class_code = ?");
            args.add(classCode);
        }
        if (status != null && !status.isBlank()) {
            sql.append(" AND s.status = ?");
            args.add(status);
        }
        Number value = queryOne(sql.toString(), rs -> rs.getInt(1), args.toArray());
        return value == null ? 0 : value.intValue();
    }

    public void insert(Connection connection, Student student) {
        update(connection, "INSERT INTO student (student_no, student_name, gender, birth_date, class_id, "
                        + "enroll_date, phone, email, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                student.getStudentNo(), student.getStudentName(), student.getGender(), student.getBirthDate(),
                student.getClassId(), student.getEnrollDate(), student.getPhone(), student.getEmail(),
                student.getStatus());
    }

    public int update(Connection connection, Student student) {
        return update(connection, "UPDATE student SET student_name = ?, gender = ?, birth_date = ?, class_id = ?, "
                        + "enroll_date = ?, phone = ?, email = ?, status = ? WHERE student_no = ?",
                student.getStudentName(), student.getGender(), student.getBirthDate(), student.getClassId(),
                student.getEnrollDate(), student.getPhone(), student.getEmail(), student.getStatus(),
                student.getStudentNo());
    }

    public int deleteByNo(Connection connection, String studentNo) {
        return update(connection, "DELETE FROM student WHERE student_no = ?", studentNo);
    }

    public int countEnrollments(Connection connection, Integer studentId) {
        return count(connection, "SELECT COUNT(*) FROM enrollment WHERE student_id = ? AND status = '已选'", studentId);
    }

    private Student map(ResultSet rs) throws SQLException {
        Student student = new Student();
        student.setStudentId(rs.getInt("student_id"));
        student.setStudentNo(rs.getString("student_no"));
        student.setStudentName(rs.getString("student_name"));
        student.setGender(rs.getString("gender"));
        if (rs.getDate("birth_date") != null) {
            student.setBirthDate(rs.getDate("birth_date").toLocalDate());
        }
        student.setClassId(rs.getInt("class_id"));
        student.setEnrollDate(rs.getDate("enroll_date").toLocalDate());
        student.setPhone(rs.getString("phone"));
        student.setEmail(rs.getString("email"));
        student.setStatus(rs.getString("status"));
        student.setClassName(rs.getString("class_name"));
        student.setDeptName(rs.getString("dept_name"));
        return student;
    }
}
