package edu.scut.db.tests;

import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;

import java.util.Objects;

public final class Assert {

    private Assert() {
    }

    public static void assertEquals(Object expected, Object actual) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError("期望 " + expected + "，实际 " + actual);
        }
    }

    public static void assertEquals(Object expected, Object actual, String message) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(message + "：期望 " + expected + "，实际 " + actual);
        }
    }

    public static void assertTrue(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }

    public static void assertNotNull(Object value, String message) {
        if (value == null) {
            throw new AssertionError(message);
        }
    }

    public static void assertThrows(ErrorCode expectedCode, Runnable action) {
        try {
            action.run();
        } catch (BizException e) {
            if (e.getErrorCode() != expectedCode) {
                throw new AssertionError("期望错误码 " + expectedCode + "，实际 " + e.getErrorCode());
            }
            return;
        }
        throw new AssertionError("期望抛出 " + expectedCode + "，但没有抛出异常");
    }

    public static void assertThrowsAny(Runnable action) {
        try {
            action.run();
        } catch (RuntimeException e) {
            return;
        }
        throw new AssertionError("期望抛出异常，但没有抛出");
    }

    public static void assertSqlState(String expectedState, SqlAction action) {
        try {
            action.run();
        } catch (java.sql.SQLException e) {
            if (!expectedState.equals(e.getSQLState())) {
                throw new AssertionError("期望 SQLSTATE " + expectedState + "，实际 " + e.getSQLState()
                        + "（" + e.getMessage() + "）");
            }
            return;
        }
        throw new AssertionError("期望抛出 SQLSTATE " + expectedState + "，但没有抛出");
    }

    @FunctionalInterface
    public interface SqlAction {
        void run() throws java.sql.SQLException;
    }
}
