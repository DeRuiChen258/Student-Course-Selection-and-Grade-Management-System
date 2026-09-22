package edu.scut.db.dao;

import edu.scut.db.db.ConnectionProvider;
import edu.scut.db.db.RowMapper;
import edu.scut.db.exception.DataAccessException;
import edu.scut.db.util.Logger;

import java.math.BigDecimal;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.sql.Types;
import java.util.ArrayList;
import java.util.List;

public abstract class BaseDao {

    protected final ConnectionProvider provider;

    protected BaseDao(ConnectionProvider provider) {
        this.provider = provider;
    }

    protected <T> List<T> query(String sql, RowMapper<T> mapper, Object... args) {
        return query(provider.getConnection(), sql, mapper, args);
    }

    protected <T> List<T> query(Connection connection, String sql, RowMapper<T> mapper, Object... args) {
        Logger.debug("SQL: " + sql);
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            bind(statement, args);
            try (ResultSet rs = statement.executeQuery()) {
                return RowMapper.mapList(rs, mapper);
            }
        } catch (SQLException e) {
            throw new DataAccessException("查询失败：" + e.getMessage() + " SQL=" + sql, e);
        }
    }

    protected <T> T queryOne(String sql, RowMapper<T> mapper, Object... args) {
        List<T> list = query(sql, mapper, args);
        return list.isEmpty() ? null : list.get(0);
    }

    protected <T> T queryOne(Connection connection, String sql, RowMapper<T> mapper, Object... args) {
        List<T> list = query(connection, sql, mapper, args);
        return list.isEmpty() ? null : list.get(0);
    }

    protected int update(Connection connection, String sql, Object... args) {
        Logger.debug("SQL: " + sql);
        try (PreparedStatement statement = connection.prepareStatement(sql, Statement.RETURN_GENERATED_KEYS)) {
            bind(statement, args);
            int affected = statement.executeUpdate();
            try (ResultSet keys = statement.getGeneratedKeys()) {
                if (keys.next()) {
                    lastGeneratedKey = keys.getInt(1);
                }
            }
            return affected;
        } catch (SQLException e) {
            throw new DataAccessException("写入失败：" + e.getMessage() + " SQL=" + sql, e);
        }
    }

    protected int update(String sql, Object... args) {
        return update(provider.getConnection(), sql, args);
    }

    protected int count(String sql, Object... args) {
        Number value = queryOne(sql, rs -> rs.getInt(1), args);
        return value == null ? 0 : value.intValue();
    }

    protected int count(Connection connection, String sql, Object... args) {
        Number value = queryOne(connection, sql, rs -> rs.getInt(1), args);
        return value == null ? 0 : value.intValue();
    }

    protected BigDecimal decimal(Connection connection, String sql, Object... args) {
        return queryOne(connection, sql, rs -> rs.getBigDecimal(1), args);
    }

    protected int[] batch(Connection connection, String sql, List<Object[]> rows) {
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            for (Object[] row : rows) {
                bind(statement, row);
                statement.addBatch();
            }
            return statement.executeBatch();
        } catch (SQLException e) {
            throw new DataAccessException("批量写入失败：" + e.getMessage() + " SQL=" + sql, e);
        }
    }

    private volatile int lastGeneratedKey;

    protected int lastGeneratedKey() {
        return lastGeneratedKey;
    }

    protected static void bind(PreparedStatement statement, Object... args) throws SQLException {
        for (int i = 0; i < args.length; i++) {
            Object arg = args[i];
            int index = i + 1;
            if (arg == null) {
                statement.setNull(index, Types.NULL);
            } else if (arg instanceof Integer) {
                statement.setInt(index, (Integer) arg);
            } else if (arg instanceof Long) {
                statement.setLong(index, (Long) arg);
            } else if (arg instanceof BigDecimal) {
                statement.setBigDecimal(index, (BigDecimal) arg);
            } else if (arg instanceof java.time.LocalDate) {
                statement.setDate(index, java.sql.Date.valueOf((java.time.LocalDate) arg));
            } else if (arg instanceof java.time.LocalDateTime) {
                statement.setTimestamp(index, java.sql.Timestamp.valueOf((java.time.LocalDateTime) arg));
            } else {
                statement.setString(index, String.valueOf(arg));
            }
        }
    }

    protected static List<String> columns(String... names) {
        return new ArrayList<>(List.of(names));
    }
}
