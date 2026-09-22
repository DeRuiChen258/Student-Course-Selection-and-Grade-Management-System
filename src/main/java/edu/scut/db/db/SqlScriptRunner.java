package edu.scut.db.db;

import edu.scut.db.exception.DataAccessException;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.sql.Connection;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Stream;

public class SqlScriptRunner {

    private final ConnectionProvider provider;

    public SqlScriptRunner(ConnectionProvider provider) {
        this.provider = provider;
    }

    public int runFile(Path file) {
        List<String> statements = split(file);
        Connection connection = provider.getConnection();
        int executed = 0;
        for (String sql : statements) {
            try (Statement statement = connection.createStatement()) {
                statement.execute(sql);
                executed++;
            } catch (SQLException e) {
                throw new DataAccessException("执行 " + file.getFileName() + " 第 " + executed + " 条语句失败："
                        + e.getMessage() + " SQL=" + summarize(sql), e);
            }
        }
        return executed;
    }

    public int runDirectory(Path directory, List<String> fileNames) {
        int total = 0;
        for (String name : fileNames) {
            total += runFile(directory.resolve(name));
        }
        return total;
    }

    public List<String[]> query(String sql) {
        if (!sql.stripLeading().toUpperCase().startsWith("SELECT")) {
            throw new DataAccessException("维护菜单只允许执行 SELECT 查询");
        }
        List<String[]> rows = new ArrayList<>();
        try (Statement statement = provider.getConnection().createStatement();
             ResultSet rs = statement.executeQuery(sql)) {
            ResultSetMetaData meta = rs.getMetaData();
            String[] header = new String[meta.getColumnCount()];
            for (int i = 0; i < header.length; i++) {
                header[i] = meta.getColumnLabel(i + 1);
            }
            rows.add(header);
            while (rs.next()) {
                String[] row = new String[header.length];
                for (int i = 0; i < header.length; i++) {
                    Object value = rs.getObject(i + 1);
                    row[i] = value == null ? "" : String.valueOf(value);
                }
                rows.add(row);
            }
            return rows;
        } catch (SQLException e) {
            throw new DataAccessException("查询失败：" + e.getMessage(), e);
        }
    }

    List<String> split(Path file) {
        List<String> statements = new ArrayList<>();
        StringBuilder current = new StringBuilder();
        String delimiter = ";";
        try {
            for (String raw : Files.readAllLines(file, StandardCharsets.UTF_8)) {
                String line = raw.strip();
                if (line.isEmpty() || line.startsWith("--")) {
                    continue;
                }
                if (line.toUpperCase().startsWith("DELIMITER ")) {
                    delimiter = line.substring("DELIMITER ".length()).trim();
                    continue;
                }
                current.append(raw).append('\n');
                if (line.endsWith(delimiter)) {
                    String sql = current.toString().trim();
                    sql = sql.substring(0, sql.length() - delimiter.length()).trim();
                    if (!sql.isEmpty()) {
                        statements.add(sql);
                    }
                    current.setLength(0);
                }
            }
        } catch (IOException e) {
            throw new DataAccessException("读取脚本失败：" + file, e);
        }
        if (!current.toString().isBlank()) {
            statements.add(current.toString().trim());
        }
        return statements;
    }

    private String summarize(String sql) {
        String flat = sql.replaceAll("\\s+", " ");
        return flat.length() > 60 ? flat.substring(0, 60) + "..." : flat;
    }
}
