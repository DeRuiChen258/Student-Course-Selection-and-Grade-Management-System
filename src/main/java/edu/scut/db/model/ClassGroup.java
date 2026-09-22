package edu.scut.db.model;

public class ClassGroup {

    private Integer classId;
    private String classCode;
    private String className;
    private Integer deptId;
    private Integer gradeYear;
    private Integer advisorTeacherId;
    private String deptName;
    private String advisorName;

    public Integer getClassId() {
        return classId;
    }

    public void setClassId(Integer classId) {
        this.classId = classId;
    }

    public String getClassCode() {
        return classCode;
    }

    public void setClassCode(String classCode) {
        this.classCode = classCode;
    }

    public String getClassName() {
        return className;
    }

    public void setClassName(String className) {
        this.className = className;
    }

    public Integer getDeptId() {
        return deptId;
    }

    public void setDeptId(Integer deptId) {
        this.deptId = deptId;
    }

    public Integer getGradeYear() {
        return gradeYear;
    }

    public void setGradeYear(Integer gradeYear) {
        this.gradeYear = gradeYear;
    }

    public Integer getAdvisorTeacherId() {
        return advisorTeacherId;
    }

    public void setAdvisorTeacherId(Integer advisorTeacherId) {
        this.advisorTeacherId = advisorTeacherId;
    }

    public String getDeptName() {
        return deptName;
    }

    public void setDeptName(String deptName) {
        this.deptName = deptName;
    }

    public String getAdvisorName() {
        return advisorName;
    }

    public void setAdvisorName(String advisorName) {
        this.advisorName = advisorName;
    }

    @Override
    public String toString() {
        return classCode + " " + className;
    }
}
