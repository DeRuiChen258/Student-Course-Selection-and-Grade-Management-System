package edu.scut.db.model.enums;

import java.math.BigDecimal;

public enum GradeLevel {

    A("A", new BigDecimal("90"), new BigDecimal("4.0")),
    B("B", new BigDecimal("80"), new BigDecimal("3.0")),
    C("C", new BigDecimal("70"), new BigDecimal("2.0")),
    D("D", new BigDecimal("60"), new BigDecimal("1.0")),
    F("F", new BigDecimal("0"), new BigDecimal("0.0"));

    private final String label;
    private final BigDecimal lowerBound;
    private final BigDecimal gradePoint;

    GradeLevel(String label, BigDecimal lowerBound, BigDecimal gradePoint) {
        this.label = label;
        this.lowerBound = lowerBound;
        this.gradePoint = gradePoint;
    }

    public String label() {
        return label;
    }

    public BigDecimal gradePoint() {
        return gradePoint;
    }

    public static GradeLevel of(BigDecimal score) {
        if (score == null) {
            return null;
        }
        for (GradeLevel level : values()) {
            if (score.compareTo(level.lowerBound) >= 0) {
                return level;
            }
        }
        return F;
    }
}
