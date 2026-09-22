package edu.scut.db.config;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;

public class AppConfig {

    private static final String DEFAULT_PATH = "config/db.properties";

    private final Map<String, String> values = new HashMap<>();

    private AppConfig(Path path) throws IOException {
        Properties properties = new Properties();
        try (InputStream in = Files.newInputStream(path)) {
            properties.load(new java.io.InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8));
        }
        for (String key : properties.stringPropertyNames()) {
            values.put(key, properties.getProperty(key).trim());
        }
        overrideFromEnv("DB_HOST", "db.host");
        overrideFromEnv("DB_PORT", "db.port");
        overrideFromEnv("DB_NAME", "db.name");
        overrideFromEnv("DB_USER", "db.user");
        overrideFromEnv("DB_PASSWORD", "db.password");
        require("db.host");
        require("db.port");
        require("db.name");
        require("db.user");
        require("db.password");
    }

    public static AppConfig load(String pathText) throws IOException {
        Path path = Paths.get(pathText == null ? DEFAULT_PATH : pathText);
        if (!Files.exists(path)) {
            throw new IOException("找不到配置文件 " + path.toAbsolutePath()
                    + "，请复制 config/db.properties.example 为 config/db.properties 并填写连接信息");
        }
        return new AppConfig(path);
    }

    private void overrideFromEnv(String envName, String key) {
        String value = System.getenv(envName);
        if (value != null && !value.isBlank()) {
            values.put(key, value.trim());
        }
    }

    private void require(String key) throws IOException {
        String value = values.get(key);
        if (value == null || value.isBlank()) {
            throw new IOException("配置缺少必填项 " + key + "，请检查 config/db.properties");
        }
    }

    private String get(String key, String fallback) {
        String value = values.get(key);
        return value == null || value.isBlank() ? fallback : value;
    }

    public String getJdbcUrl() {
        String params = get("db.params", "characterEncoding=utf8&serverTimezone=Asia/Shanghai&useSSL=false");
        return "jdbc:mysql://" + values.get("db.host") + ":" + values.get("db.port") + "/"
                + values.get("db.name") + "?" + params;
    }

    public String getUser() {
        return values.get("db.user");
    }

    public String getPassword() {
        return values.get("db.password");
    }

    public String getHost() {
        return values.get("db.host");
    }

    public String getPort() {
        return values.get("db.port");
    }

    public String getDatabase() {
        return values.get("db.name");
    }

    public int getPageSize() {
        return Integer.parseInt(get("app.page.size", "10"));
    }

    public String getLogLevel() {
        return get("app.log.level", "INFO");
    }

    public Path getScriptDirectory() {
        return Paths.get(get("app.sql.dir", "sql"));
    }
}
