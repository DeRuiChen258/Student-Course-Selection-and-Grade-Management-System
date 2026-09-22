package edu.scut.db.util;

import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;

import java.math.BigDecimal;
import java.util.regex.Pattern;

public final class Validators {

    private static final Pattern STUDENT_NO = Pattern.compile("^\\d{12}$");
    private static final Pattern TEACHER_NO = Pattern.compile("^\\d{8}$");
    private static final Pattern COURSE_CODE = Pattern.compile("^[A-Z0-9]{2,16}$");
    private static final Pattern SEMESTER = Pattern.compile("^\\d{4}-\\d{4}-[12]$");
    private static final Pattern PHONE = Pattern.compile("^\\d{7,20}$");
    private static final Pattern EMAIL = Pattern.compile("^[\\w.+-]+@[\\w-]+\\.[\\w.-]+$");

    private Validators() {
    }

    public static boolean isStudentNo(String value) {
        return value != null && STUDENT_NO.matcher(value).matches();
    }

    public static boolean isTeacherNo(String value) {
        return value != null && TEACHER_NO.matcher(value).matches();
    }

    public static boolean isCourseCode(String value) {
        return value != null && COURSE_CODE.matcher(value).matches();
    }

    public static boolean isSemester(String value) {
        return value != null && SEMESTER.matcher(value).matches();
    }

    public static boolean isPhone(String value) {
        return value == null || value.isBlank() || PHONE.matcher(value).matches();
    }

    public static boolean isEmail(String value) {
        return value == null || value.isBlank() || EMAIL.matcher(value).matches();
    }

    public static boolean isScore(BigDecimal value) {
        return value != null && value.compareTo(BigDecimal.ZERO) >= 0
                && value.compareTo(new BigDecimal("100")) <= 0;
    }

    public static boolean isCredit(BigDecimal value) {
        return value != null && value.compareTo(new BigDecimal("0.5")) >= 0
                && value.compareTo(new BigDecimal("10.0")) <= 0;
    }

    public static boolean isHours(Integer value) {
        return value != null && value >= 8 && value <= 200;
    }

    public static boolean isCapacity(Integer value) {
        return value != null && value >= 1 && value <= 300;
    }

    public static boolean isName(String value) {
        return value != null && !value.isBlank() && value.length() <= 30;
    }

    public static boolean isMaxLength(String value, int max) {
        return value == null || value.length() <= max;
    }

    public static void require(boolean condition, String message) {
        if (!condition) {
            throw BizException.of(ErrorCode.E001, message);
        }
    }
}
