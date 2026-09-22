package edu.scut.db.util;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.time.format.ResolverStyle;

public final class DateUtils {

    private static final DateTimeFormatter DATE = DateTimeFormatter.ofPattern("uuuu-MM-dd")
            .withResolverStyle(ResolverStyle.STRICT);

    private DateUtils() {
    }

    public static LocalDate parseDate(String text) {
        try {
            return LocalDate.parse(text, DATE);
        } catch (DateTimeParseException e) {
            return null;
        }
    }

    public static String format(LocalDate date) {
        return date == null ? "" : date.format(DATE);
    }

    public static String formatDateTime(LocalDateTime time) {
        return time == null ? "" : time.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));
    }

    public static String currentSemester() {
        return semesterOf(LocalDate.now());
    }

    public static String semesterOf(LocalDate date) {
        int year = date.getYear();
        int month = date.getMonthValue();
        if (month >= 9) {
            return year + "-" + (year + 1) + "-1";
        }
        if (month <= 1) {
            return (year - 1) + "-" + year + "-1";
        }
        return (year - 1) + "-" + year + "-2";
    }

    public static boolean isEarlier(String leftSemester, String rightSemester) {
        return leftSemester.compareTo(rightSemester) < 0;
    }
}
