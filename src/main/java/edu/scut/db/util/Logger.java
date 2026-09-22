package edu.scut.db.util;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public final class Logger {

    private static final DateTimeFormatter STAMP = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final Path LOG_FILE = Paths.get("logs/app.log");

    private static Level threshold = Level.INFO;
    private static PrintWriter fileWriter;

    public enum Level {
        DEBUG, INFO, WARN, ERROR
    }

    private Logger() {
    }

    public static synchronized void configure(String level) {
        try {
            threshold = Level.valueOf(level.toUpperCase());
        } catch (IllegalArgumentException e) {
            threshold = Level.INFO;
        }
        try {
            Files.createDirectories(LOG_FILE.getParent());
            fileWriter = new PrintWriter(Files.newBufferedWriter(LOG_FILE, StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND), true);
        } catch (IOException e) {
            fileWriter = null;
        }
    }

    public static void debug(String message) {
        write(Level.DEBUG, message);
    }

    public static void info(String message) {
        write(Level.INFO, message);
    }

    public static void warn(String message) {
        write(Level.WARN, message);
    }

    public static void error(String message) {
        write(Level.ERROR, message);
    }

    private static synchronized void write(Level level, String message) {
        if (level.ordinal() < threshold.ordinal()) {
            return;
        }
        String line = LocalDateTime.now().format(STAMP) + " [" + level + "] " + message;
        if (level != Level.INFO || threshold == Level.DEBUG) {
            System.out.println(line);
        }
        if (fileWriter != null) {
            fileWriter.println(line);
        }
    }
}
