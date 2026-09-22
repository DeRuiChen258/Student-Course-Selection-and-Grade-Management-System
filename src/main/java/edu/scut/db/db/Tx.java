package edu.scut.db.db;

import edu.scut.db.exception.DataAccessException;

import java.sql.Connection;
import java.sql.SQLException;

public class Tx {

    @FunctionalInterface
    public interface SqlFunction<C, T> {
        T apply(C connection) throws SQLException;
    }

    private final ConnectionProvider provider;

    public Tx(ConnectionProvider provider) {
        this.provider = provider;
    }

    public ConnectionProvider provider() {
        return provider;
    }

    public <T> T runInTx(SqlFunction<Connection, T> work) {
        Connection connection = provider.getConnection();
        boolean originalAutoCommit;
        try {
            originalAutoCommit = connection.getAutoCommit();
            connection.setAutoCommit(false);
        } catch (SQLException e) {
            throw new DataAccessException("开启事务失败：" + e.getMessage(), e);
        }
        try {
            T result = work.apply(connection);
            connection.commit();
            return result;
        } catch (SQLException | RuntimeException e) {
            rollback(connection);
            if (e instanceof RuntimeException) {
                throw (RuntimeException) e;
            }
            throw new DataAccessException("事务执行失败并已回滚：" + e.getMessage(), e);
        } finally {
            try {
                connection.setAutoCommit(originalAutoCommit);
            } catch (SQLException ignored) {
                // 恢复自动提交失败时连接会被下一次 getConnection 检测并重建
            }
        }
    }

    private void rollback(Connection connection) {
        try {
            connection.rollback();
        } catch (SQLException e) {
            throw new DataAccessException("回滚失败：" + e.getMessage(), e);
        }
    }
}
