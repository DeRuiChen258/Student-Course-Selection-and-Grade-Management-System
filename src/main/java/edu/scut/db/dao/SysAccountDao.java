package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.SysAccount;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;

public class SysAccountDao extends BaseDao {

    public SysAccountDao(ConnectionProvider provider) {
        super(provider);
    }

    public SysAccount findByUsername(String username) {
        return queryOne("SELECT account_id, username, password_hash, role, student_id, teacher_id, last_login "
                + "FROM sys_account WHERE username = ?", this::map, username);
    }

    public int updateLastLogin(Connection connection, String username) {
        return update(connection, "UPDATE sys_account SET last_login = NOW() WHERE username = ?", username);
    }

    public void insert(Connection connection, SysAccount account) {
        update(connection, "INSERT INTO sys_account (username, password_hash, role, student_id, teacher_id) "
                        + "VALUES (?, ?, ?, ?, ?)",
                account.getUsername(), account.getPasswordHash(), account.getRole(),
                account.getStudentId(), account.getTeacherId());
    }

    private SysAccount map(ResultSet rs) throws SQLException {
        SysAccount account = new SysAccount();
        account.setAccountId(rs.getInt("account_id"));
        account.setUsername(rs.getString("username"));
        account.setPasswordHash(rs.getString("password_hash"));
        account.setRole(rs.getString("role"));
        int studentId = rs.getInt("student_id");
        account.setStudentId(rs.wasNull() ? null : studentId);
        int teacherId = rs.getInt("teacher_id");
        account.setTeacherId(rs.wasNull() ? null : teacherId);
        if (rs.getTimestamp("last_login") != null) {
            account.setLastLogin(rs.getTimestamp("last_login").toLocalDateTime());
        }
        return account;
    }
}
