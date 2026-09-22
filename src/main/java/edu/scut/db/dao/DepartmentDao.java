package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.Department;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

public class DepartmentDao extends BaseDao {

    public DepartmentDao(ConnectionProvider provider) {
        super(provider);
    }

    public List<Department> findAll() {
        return query("SELECT dept_id, dept_code, dept_name, office, phone FROM department ORDER BY dept_code", this::map);
    }

    public Department findByCode(String deptCode) {
        return queryOne("SELECT dept_id, dept_code, dept_name, office, phone FROM department WHERE dept_code = ?",
                this::map, deptCode);
    }

    public boolean existsName(Connection connection, String deptName, String excludeCode) {
        return count(connection, "SELECT COUNT(*) FROM department WHERE dept_name = ? AND dept_code <> ?",
                deptName, excludeCode == null ? "" : excludeCode) > 0;
    }

    public void insert(Connection connection, Department department) {
        update(connection, "INSERT INTO department (dept_code, dept_name, office, phone) VALUES (?, ?, ?, ?)",
                department.getDeptCode(), department.getDeptName(), department.getOffice(), department.getPhone());
    }

    public int update(Connection connection, Department department) {
        return update(connection, "UPDATE department SET dept_name = ?, office = ?, phone = ? WHERE dept_code = ?",
                department.getDeptName(), department.getOffice(), department.getPhone(), department.getDeptCode());
    }

    public int deleteByCode(Connection connection, String deptCode) {
        return update(connection, "DELETE FROM department WHERE dept_code = ?", deptCode);
    }

    private Department map(ResultSet rs) throws SQLException {
        Department department = new Department();
        department.setDeptId(rs.getInt("dept_id"));
        department.setDeptCode(rs.getString("dept_code"));
        department.setDeptName(rs.getString("dept_name"));
        department.setOffice(rs.getString("office"));
        department.setPhone(rs.getString("phone"));
        return department;
    }
}
