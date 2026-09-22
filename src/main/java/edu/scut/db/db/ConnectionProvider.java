package edu.scut.db.db;

import edu.scut.db.config.AppConfig;
import edu.scut.db.exception.DataAccessException;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class ConnectionProvider implements AutoCloseable {

    private static ConnectionProvider instance;

    private final AppConfig config;
    private Connection shared;

    private ConnectionProvider(AppConfig config) {
        this.config = config;
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            throw new DataAccessException("未找到 JDBC 驱动，请确认 lib/mysql-connector-j-9.1.0.jar 已放入 lib/", e);
        }
        Runtime.getRuntime().addShutdownHook(new Thread(this::close));
    }

    public static synchronized ConnectionProvider of(AppConfig config) {
        if (instance == null) {
            instance = new ConnectionProvider(config);
        }
        return instance;
    }

    public synchronized Connection getConnection() {
        try {
            if (shared == null || shared.isClosed()) {
                shared = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(), config.getPassword());
            }
        } catch (SQLException e) {
            throw new DataAccessException("连接数据库失败 " + describeTarget() + "：" + e.getMessage(), e);
        }
        return shared;
    }

    public String describeTarget() {
        return config.getUser() + "@" + config.getHost() + ":" + config.getPort() + "/" + config.getDatabase();
    }

    @Override
    public synchronized void close() {
        if (shared == null) {
            return;
        }
        try {
            if (!shared.isClosed()) {
                shared.close();
            }
        } catch (SQLException ignored) {
            // 关闭钩子内不再抛异常
        } finally {
            shared = null;
        }
    }
}
