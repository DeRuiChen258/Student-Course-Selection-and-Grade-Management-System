package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.ClassGroup;

import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

public class ClassGroupDao extends BaseDao {

    private static final String SELECT = "SELECT c.class_id, c.class_code, c.class_name, c.dept_id, c.grade_year, "
            + "c.advisor_teacher_id, d.dept_name, t.teacher_name AS advisor_name FROM class_group c "
            + "JOIN department d ON d.dept_id = c.dept_id "
            + "LEFT JOIN teacher t ON t.teacher_id = c.advisor_teacher_id ";

    public ClassGroupDao(ConnectionProvider provider) {
        super(provider);
    }

    public List<ClassGroup> findAll() {
        return query(SELECT + "ORDER BY c.class_code", this::map);
    }

    public List<ClassGroup> findByDept(String deptCode) {
        return query(SELECT + "WHERE d.dept_code = ? ORDER BY c.class_code", this::map, deptCode);
    }

    public ClassGroup findByCode(String classCode) {
        return queryOne(SELECT + "WHERE c.class_code = ?", this::map, classCode);
    }

    public ClassGroup findById(java.sql.Connection connection, Integer classId) {
        return queryOne(connection, SELECT + "WHERE c.class_id = ?", this::map, classId);
    }

    public boolean existsCode(String classCode) {
        return count("SELECT COUNT(*) FROM class_group WHERE class_code = ?", classCode) > 0;
    }

    private ClassGroup map(ResultSet rs) throws SQLException {
        ClassGroup group = new ClassGroup();
        group.setClassId(rs.getInt("class_id"));
        group.setClassCode(rs.getString("class_code"));
        group.setClassName(rs.getString("class_name"));
        group.setDeptId(rs.getInt("dept_id"));
        group.setGradeYear(rs.getInt("grade_year"));
        int advisor = rs.getInt("advisor_teacher_id");
        group.setAdvisorTeacherId(rs.wasNull() ? null : advisor);
        group.setDeptName(rs.getString("dept_name"));
        group.setAdvisorName(rs.getString("advisor_name"));
        return group;
    }
}
