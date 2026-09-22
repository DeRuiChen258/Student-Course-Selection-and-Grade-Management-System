package edu.scut.db.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;

public class Enrollment {

    private Integer enrollmentId;
    private Integer studentId;
    private Integer offeringId;
    private LocalDateTime enrollTime;
    private BigDecimal score;
    private LocalDateTime scoreTime;
    private String status;
    private String studentNo;
    private String studentName;
    private String courseCode;
    private String courseName;
    private String semester;
    private String teacherName;

    public Integer getEnrollmentId() {
        return enrollmentId;
    }

    public void setEnrollmentId(Integer enrollmentId) {
        this.enrollmentId = enrollmentId;
    }

    public Integer getStudentId() {
        return studentId;
    }

    public void setStudentId(Integer studentId) {
        this.studentId = studentId;
    }

    public Integer getOfferingId() {
        return offeringId;
    }

    public void setOfferingId(Integer offeringId) {
        this.offeringId = offeringId;
    }

    public LocalDateTime getEnrollTime() {
        return enrollTime;
    }

    public void setEnrollTime(LocalDateTime enrollTime) {
        this.enrollTime = enrollTime;
    }

    public BigDecimal getScore() {
        return score;
    }

    public void setScore(BigDecimal score) {
        this.score = score;
    }

    public LocalDateTime getScoreTime() {
        return scoreTime;
    }

    public void setScoreTime(LocalDateTime scoreTime) {
        this.scoreTime = scoreTime;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getStudentNo() {
        return studentNo;
    }

    public void setStudentNo(String studentNo) {
        this.studentNo = studentNo;
    }

    public String getStudentName() {
        return studentName;
    }

    public void setStudentName(String studentName) {
        this.studentName = studentName;
    }

    public String getCourseCode() {
        return courseCode;
    }

    public void setCourseCode(String courseCode) {
        this.courseCode = courseCode;
    }

    public String getCourseName() {
        return courseName;
    }

    public void setCourseName(String courseName) {
        this.courseName = courseName;
    }

    public String getSemester() {
        return semester;
    }

    public void setSemester(String semester) {
        this.semester = semester;
    }

    public String getTeacherName() {
        return teacherName;
    }

    public void setTeacherName(String teacherName) {
        this.teacherName = teacherName;
    }

    @Override
    public String toString() {
        return studentNo + " " + courseCode + " " + (score == null ? "未出分" : score);
    }
}
