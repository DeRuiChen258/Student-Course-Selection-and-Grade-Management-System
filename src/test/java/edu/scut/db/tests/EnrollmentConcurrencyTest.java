package edu.scut.db.tests;

import edu.scut.db.config.AppConfig;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.Statement;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

public final class EnrollmentConcurrencyTest {

    private static final int OFFERING_ID = 998;

    private EnrollmentConcurrencyTest() {
    }

    public static void run() throws Exception {
        AppConfig config = AppConfig.load(System.getProperty("db.config", "config/db.properties"));
        cleanup(config);
        boolean ok;
        try {
            prepare(config);
            ExecutorService pool = Executors.newFixedThreadPool(2);
            Callable<String> task = () -> grab(config, "202399900005");
            Callable<String> task2 = () -> grab(config, "202399900006");
            List<Future<String>> futures = pool.invokeAll(List.of(task, task2), 60, TimeUnit.SECONDS);
            pool.shutdownNow();

            String first = futures.get(0).get();
            String second = futures.get(1).get();
            long success = List.of(first, second).stream().filter("OK"::equals).count();
            long full = List.of(first, second).stream().filter("FULL"::equals).count();

            Assert.assertEquals(1L, success, "两个并发选课请求应只有一个成功（结果 " + first + "/" + second + "）");
            Assert.assertEquals(1L, full, "另一个请求应收到名额已满（结果 " + first + "/" + second + "）");
            try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                    config.getPassword());
                 Statement statement = connection.createStatement();
                 ResultSet rs = statement.executeQuery("SELECT enrolled_count, capacity FROM course_offering "
                         + "WHERE offering_id = " + OFFERING_ID)) {
                Assert.assertTrue(rs.next(), "应能查到测试开课");
                Assert.assertEquals(rs.getInt("capacity"), rs.getInt("enrolled_count"),
                        "并发结束后已选人数应等于容量");
            }
            ok = true;
        } finally {
            cleanup(config);
        }
        Assert.assertTrue(ok, "并发用例应执行完成");
    }

    private static String grab(AppConfig config, String studentNo) throws Exception {
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword())) {
            connection.setAutoCommit(false);
            try {
                int capacity;
                int enrolled;
                try (PreparedStatement lock = connection.prepareStatement(
                        "SELECT capacity, enrolled_count FROM course_offering WHERE offering_id = ? FOR UPDATE")) {
                    lock.setInt(1, OFFERING_ID);
                    try (ResultSet rs = lock.executeQuery()) {
                        if (!rs.next()) {
                            connection.rollback();
                            return "MISSING";
                        }
                        capacity = rs.getInt("capacity");
                        enrolled = rs.getInt("enrolled_count");
                    }
                }
                if (enrolled >= capacity) {
                    connection.rollback();
                    return "FULL";
                }
                try (PreparedStatement insert = connection.prepareStatement(
                        "INSERT INTO enrollment (student_id, offering_id, status) "
                                + "SELECT student_id, ?, '已选' FROM student WHERE student_no = ?")) {
                    insert.setInt(1, OFFERING_ID);
                    insert.setString(2, studentNo);
                    insert.executeUpdate();
                }
                connection.commit();
                return "OK";
            } catch (Exception e) {
                connection.rollback();
                return "ERROR:" + e.getMessage();
            }
        }
    }

    private static void prepare(AppConfig config) throws Exception {
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword()); Statement statement = connection.createStatement()) {
            statement.executeUpdate("INSERT INTO student (student_no, student_name, gender, birth_date, class_id, "
                    + "enroll_date, status) VALUES ('202399900005', '并发学生甲', '男', '2005-01-01', 1, "
                    + "'2023-09-01', '在读'), ('202399900006', '并发学生乙', '女', '2005-01-02', 1, "
                    + "'2023-09-01', '在读')");
            statement.executeUpdate("INSERT INTO course_offering (offering_id, course_id, teacher_id, semester, "
                    + "capacity, enrolled_count, classroom) VALUES (" + OFFERING_ID + ", 1, 1, '2099-2100-3', 1, 0, "
                    + "'并发测试教室')");
        }
    }

    private static void cleanup(AppConfig config) throws Exception {
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword()); Statement statement = connection.createStatement()) {
            statement.executeUpdate("DELETE FROM enrollment WHERE offering_id = " + OFFERING_ID);
            statement.executeUpdate("DELETE FROM course_offering WHERE offering_id = " + OFFERING_ID);
            statement.executeUpdate("DELETE FROM sys_account WHERE student_id IN (SELECT student_id FROM student "
                    + "WHERE student_no IN ('202399900005','202399900006'))");
            statement.executeUpdate("DELETE FROM student WHERE student_no IN ('202399900005','202399900006')");
        }
    }

}
