package edu.scut.db.model;

import java.time.LocalDateTime;

public class CourseOffering {

    private Integer offeringId;
    private Integer courseId;
    private Integer teacherId;
    private String semester;
    private Integer capacity;
    private Integer enrolledCount;
    private String classroom;
    private LocalDateTime openTime;
    private String courseCode;
    private String courseName;
    private String teacherName;

    public Integer getOfferingId() {
        return offeringId;
    }

    public void setOfferingId(Integer offeringId) {
        this.offeringId = offeringId;
    }

    public Integer getCourseId() {
        return courseId;
    }

    public void setCourseId(Integer courseId) {
        this.courseId = courseId;
    }

    public Integer getTeacherId() {
        return teacherId;
    }

    public void setTeacherId(Integer teacherId) {
        this.teacherId = teacherId;
    }

    public String getSemester() {
        return semester;
    }

    public void setSemester(String semester) {
        this.semester = semester;
    }

    public Integer getCapacity() {
        return capacity;
    }

    public void setCapacity(Integer capacity) {
        this.capacity = capacity;
    }

    public Integer getEnrolledCount() {
        return enrolledCount;
    }

    public void setEnrolledCount(Integer enrolledCount) {
        this.enrolledCount = enrolledCount;
    }

    public String getClassroom() {
        return classroom;
    }

    public void setClassroom(String classroom) {
        this.classroom = classroom;
    }

    public LocalDateTime getOpenTime() {
        return openTime;
    }

    public void setOpenTime(LocalDateTime openTime) {
        this.openTime = openTime;
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

    public String getTeacherName() {
        return teacherName;
    }

    public void setTeacherName(String teacherName) {
        this.teacherName = teacherName;
    }

    public int remaining() {
        return capacity == null || enrolledCount == null ? 0 : capacity - enrolledCount;
    }

    @Override
    public String toString() {
        return offeringId + " " + courseCode + " " + semester + " 已选 " + enrolledCount + "/" + capacity;
    }
}
