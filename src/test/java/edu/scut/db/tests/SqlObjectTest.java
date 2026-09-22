package edu.scut.db.tests;

import edu.scut.db.config.AppConfig;

import java.sql.CallableStatement;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.Statement;
import java.sql.Types;

public final class SqlObjectTest {

    private SqlObjectTest() {
    }

    public static void run() throws Exception {
        AppConfig config = AppConfig.load(System.getProperty("db.config", "config/db.properties"));
        try (Connection connection = DriverManager.getConnection(config.getJdbcUrl(), config.getUser(),
                config.getPassword())) {
            for (String view : new String[]{"v_student_profile", "v_offering_detail", "v_student_transcript",
                    "v_course_stat"}) {
                Assert.assertTrue(queryInt(connection, "SELECT COUNT(*) FROM " + view) > 0,
                        "视图 " + view + " 应有数据");
            }

            prepare(connection);
            try {
                int[] codes = new int[2];
                codes[0] = callEnroll(connection, "202399900001", 999);
                Assert.assertEquals(0, codes[0], "第一个学生应选课成功");
                codes[1] = callEnroll(connection, "202399900002", 999);
                Assert.assertEquals(40005, codes[1], "容量 1 的开课第二个学生应收到 40005");
                Assert.assertEquals(1, queryInt(connection, "SELECT enrolled_count FROM course_offering "
                        + "WHERE offering_id = 999"), "过程与触发器联动后计数应为 1");

                Assert.assertEquals(40008, callScore(connection, "202399900001", 999, 101), "越界成绩应返回 40008");
                Assert.assertEquals(0, callScore(connection, "202399900001", 999, 66.5), "合法成绩应写入成功");
                Assert.assertEquals("66.50", queryString(connection, "SELECT score FROM enrollment "
                        + "WHERE offering_id = 999"), "成绩应为 66.50");
                Assert.assertEquals(40007, callDrop(connection, "202399900001", 999), "已有成绩不允许退课");
                execute(connection, "UPDATE enrollment SET score = NULL WHERE offering_id = 999");
                Assert.assertEquals(0, callDrop(connection, "202399900001", 999), "清空成绩后可退课");
                Assert.assertEquals(0, queryInt(connection, "SELECT enrolled_count FROM course_offering "
                        + "WHERE offering_id = 999"), "退课后计数应回到 0");
                Assert.assertSqlState("45000", () -> {
                    try (Statement statement = connection.createStatement()) {
                        statement.executeUpdate("UPDATE enrollment SET score = 120 WHERE offering_id = 999");
                    }
                });
            } finally {
                cleanup(connection);
            }

            String teacherSql = "UPDATE student SET phone = 'x' WHERE student_no = '202301010001'";
            try (Connection teacher = DriverManager.getConnection(config.getJdbcUrl(), "edu_teacher",
                    config.getPassword()); Statement statement = teacher.createStatement()) {
                statement.executeUpdate(teacherSql);
                throw new AssertionError("越权更新学生信息应被拒绝");
            } catch (java.sql.SQLException e) {
                Assert.assertEquals(1142, e.getErrorCode(), "越权更新应返回 ERROR 1142");
            }
        }
    }

    private static void prepare(Connection connection) throws Exception {
        cleanup(connection);
        execute(connection, "INSERT INTO course_offering (offering_id, course_id, teacher_id, semester, capacity, "
                + "enrolled_count, classroom) VALUES (999, 1, 1, '2099-2100-1', 1, 0, '测试教室')");
        execute(connection, "INSERT INTO student (student_no, student_name, gender, birth_date, class_id, "
                + "enroll_date, status) VALUES ('202399900001', '过程测试甲', '男', '2005-01-01', 1, "
                + "'2023-09-01', '在读'), ('202399900002', '过程测试乙', '女', '2005-02-02', 1, "
                + "'2023-09-01', '在读')");
    }

    private static void cleanup(Connection connection) throws Exception {
        execute(connection, "DELETE FROM enrollment WHERE offering_id = 999");
        execute(connection, "DELETE FROM course_offering WHERE offering_id = 999");
        execute(connection, "DELETE FROM student WHERE student_no IN ('202399900001','202399900002')");
    }

    private static int callEnroll(Connection connection, String studentNo, int offeringId) throws Exception {
        try (CallableStatement call = connection.prepareCall("{CALL p_enroll_student(?, ?, ?, ?)}")) {
            call.setString(1, studentNo);
            call.setInt(2, offeringId);
            call.registerOutParameter(3, Types.INTEGER);
            call.registerOutParameter(4, Types.VARCHAR);
            call.execute();
            return call.getInt(3);
        }
    }

    private static int callDrop(Connection connection, String studentNo, int offeringId) throws Exception {
        try (CallableStatement call = connection.prepareCall("{CALL p_drop_course(?, ?, ?, ?)}")) {
            call.setString(1, studentNo);
            call.setInt(2, offeringId);
            call.registerOutParameter(3, Types.INTEGER);
            call.registerOutParameter(4, Types.VARCHAR);
            call.execute();
            return call.getInt(3);
        }
    }

    private static int callScore(Connection connection, String studentNo, int offeringId, double score)
            throws Exception {
        try (CallableStatement call = connection.prepareCall("{CALL p_save_score(?, ?, ?, ?, ?)}")) {
            call.setString(1, studentNo);
            call.setInt(2, offeringId);
            call.setBigDecimal(3, new java.math.BigDecimal(String.valueOf(score)));
            call.registerOutParameter(4, Types.INTEGER);
            call.registerOutParameter(5, Types.VARCHAR);
            call.execute();
            return call.getInt(4);
        }
    }

    private static void execute(Connection connection, String sql) throws Exception {
        try (Statement statement = connection.createStatement()) {
            statement.executeUpdate(sql);
        }
    }

    private static int queryInt(Connection connection, String sql) throws Exception {
        try (Statement statement = connection.createStatement(); ResultSet rs = statement.executeQuery(sql)) {
            return rs.next() ? rs.getInt(1) : -1;
        }
    }

    private static String queryString(Connection connection, String sql) throws Exception {
        try (Statement statement = connection.createStatement(); ResultSet rs = statement.executeQuery(sql)) {
            return rs.next() ? rs.getString(1) : null;
        }
    }
}
