package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.model.AuditLog;

import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

public class AuditLogDao extends BaseDao {

    public AuditLogDao(ConnectionProvider provider) {
        super(provider);
    }

    public void insert(Connection connection, AuditLog log) {
        update(connection, "INSERT INTO audit_log (table_name, action, record_id, operator, detail) "
                        + "VALUES (?, ?, ?, ?, ?)",
                log.getTableName(), log.getAction(), log.getRecordId(), log.getOperator(), log.getDetail());
    }

    public List<AuditLog> findRecent(int limit) {
        return query("SELECT log_id, table_name, action, record_id, operator, action_time, detail "
                + "FROM audit_log ORDER BY action_time DESC, log_id DESC LIMIT ?", this::map, limit);
    }

    public List<AuditLog> findByTable(String tableName) {
        return query("SELECT log_id, table_name, action, record_id, operator, action_time, detail "
                + "FROM audit_log WHERE table_name = ? ORDER BY action_time DESC, log_id DESC LIMIT 50",
                this::map, tableName);
    }

    private AuditLog map(ResultSet rs) throws SQLException {
        AuditLog log = new AuditLog();
        log.setLogId(rs.getLong("log_id"));
        log.setTableName(rs.getString("table_name"));
        log.setAction(rs.getString("action"));
        log.setRecordId(rs.getString("record_id"));
        log.setOperator(rs.getString("operator"));
        log.setActionTime(rs.getTimestamp("action_time").toLocalDateTime());
        log.setDetail(rs.getString("detail"));
        return log;
    }
}
