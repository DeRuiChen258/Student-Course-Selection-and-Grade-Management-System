package edu.scut.db.exception;

public enum ErrorCode {

    E001("E001", "参数非法"),
    E002("E002", "学生不存在"),
    E003("E003", "开课不存在"),
    E004("E004", "重复选课"),
    E005("E005", "名额已满"),
    E006("E006", "已有成绩，不能退课"),
    E007("E007", "成绩越界"),
    E008("E008", "权限不足"),
    E009("E009", "数据访问异常");

    private final String code;
    private final String message;

    ErrorCode(String code, String message) {
        this.code = code;
        this.message = message;
    }

    public String code() {
        return code;
    }

    public String message() {
        return message;
    }
}
