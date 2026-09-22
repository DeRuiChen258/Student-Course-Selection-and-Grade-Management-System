package edu.scut.db.tests;

import edu.scut.db.util.DateUtils;
import edu.scut.db.util.PasswordUtils;
import edu.scut.db.util.Validators;

import java.math.BigDecimal;
import java.time.LocalDate;

public final class ValidatorsTest {

    private ValidatorsTest() {
    }

    public static void run() {
        Assert.assertTrue(Validators.isStudentNo("202301010001"), "12 位数字学号应通过");
        Assert.assertTrue(!Validators.isStudentNo("20230101001"), "11 位学号应被拒绝");
        Assert.assertTrue(!Validators.isStudentNo("20230101000A"), "含字母学号应被拒绝");
        Assert.assertTrue(!Validators.isStudentNo(null), "空学号应被拒绝");

        Assert.assertTrue(Validators.isTeacherNo("10000001"), "8 位工号应通过");
        Assert.assertTrue(!Validators.isTeacherNo("1000000"), "7 位工号应被拒绝");
        Assert.assertTrue(!Validators.isTeacherNo("100000011"), "9 位工号应被拒绝");

        Assert.assertTrue(Validators.isCourseCode("CS101"), "大写课程代码应通过");
        Assert.assertTrue(Validators.isCourseCode("A1"), "最短 2 位应通过");
        Assert.assertTrue(!Validators.isCourseCode("cs101"), "小写课程代码应被拒绝");
        Assert.assertTrue(!Validators.isCourseCode("CS-101"), "含连字符应被拒绝");

        Assert.assertTrue(Validators.isScore(new BigDecimal("0")), "0 分应通过");
        Assert.assertTrue(Validators.isScore(new BigDecimal("59.99")), "59.99 分应通过");
        Assert.assertTrue(Validators.isScore(new BigDecimal("60")), "60 分应通过");
        Assert.assertTrue(Validators.isScore(new BigDecimal("100")), "100 分应通过");
        Assert.assertTrue(!Validators.isScore(new BigDecimal("100.01")), "超过 100 应被拒绝");
        Assert.assertTrue(!Validators.isScore(new BigDecimal("-1")), "负分应被拒绝");
        Assert.assertTrue(!Validators.isScore(null), "空成绩应被拒绝");

        Assert.assertTrue(Validators.isCredit(new BigDecimal("3.0")), "学分 3.0 应通过");
        Assert.assertTrue(!Validators.isCredit(new BigDecimal("0.4")), "学分 0.4 应被拒绝");
        Assert.assertTrue(Validators.isHours(48), "48 学时应通过");
        Assert.assertTrue(!Validators.isHours(7), "7 学时应被拒绝");
        Assert.assertTrue(Validators.isCapacity(1), "容量 1 应通过");
        Assert.assertTrue(!Validators.isCapacity(301), "容量 301 应被拒绝");

        Assert.assertTrue(Validators.isPhone("13800000000"), "手机号应通过");
        Assert.assertTrue(!Validators.isPhone("abc"), "非法电话应被拒绝");
        Assert.assertTrue(Validators.isEmail("s202301010001@scut.edu.cn"), "邮箱应通过");
        Assert.assertTrue(!Validators.isEmail("scut.edu.cn"), "非法邮箱应被拒绝");

        Assert.assertEquals("2026-2027-1", DateUtils.semesterOf(LocalDate.of(2026, 9, 1)));
        Assert.assertEquals("2025-2026-2", DateUtils.semesterOf(LocalDate.of(2026, 3, 1)));
        Assert.assertEquals("2025-2026-1", DateUtils.semesterOf(LocalDate.of(2026, 1, 5)));
        Assert.assertEquals("2026-09-22", DateUtils.format(LocalDate.of(2026, 9, 22)));
        Assert.assertTrue(DateUtils.parseDate("2026-02-30") == null, "不存在的日期应解析失败");

        String hash = PasswordUtils.hash("Admin@123");
        Assert.assertTrue(PasswordUtils.verify("Admin@123", hash), "正确口令应校验通过");
        Assert.assertTrue(!PasswordUtils.verify("admin@123", hash), "错误口令应校验失败");
        Assert.assertTrue(!PasswordUtils.hash("Admin@123").equals(hash), "相同口令两次哈希应不同（随机盐）");
    }
}
