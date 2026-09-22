package edu.scut.db.service;

import edu.scut.db.dao.EnrollmentDao;
import edu.scut.db.dao.StudentDao;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.Enrollment;
import edu.scut.db.model.Student;
import edu.scut.db.model.enums.GradeLevel;
import edu.scut.db.util.Validators;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class GradeService {

    private final Tx tx;
    private final StudentDao studentDao;
    private final EnrollmentDao enrollmentDao;

    public GradeService(Tx tx) {
        this.tx = tx;
        this.studentDao = new StudentDao(tx.provider());
        this.enrollmentDao = new EnrollmentDao(tx.provider());
    }

    public String saveScore(String studentNo, Integer offeringId, BigDecimal score) {
        if (!Validators.isScore(score)) {
            throw BizException.of(ErrorCode.E007, "成绩必须在 0 到 100 之间");
        }
        return tx.runInTx(connection -> {
            Student student = studentDao.findByNo(studentNo);
            if (student == null) {
                throw BizException.of(ErrorCode.E002, "学号 " + studentNo + " 不存在");
            }
            Enrollment enrollment = enrollmentDao.findByStudentAndOffering(connection,
                    student.getStudentId(), offeringId);
            if (enrollment == null || !"已选".equals(enrollment.getStatus())) {
                throw BizException.of(ErrorCode.E001, "该生未选开课 " + offeringId);
            }
            enrollmentDao.updateScore(connection, enrollment.getEnrollmentId(), score);
            return "成绩保存成功：" + student.getStudentName() + " " + score + " 分，等级 "
                    + GradeLevel.of(score).label();
        });
    }

    public List<String> batchImport(List<String[]> rows) {
        List<String> failures = new ArrayList<>();
        for (String[] row : rows) {
            try {
                saveScore(row[0].trim(), Integer.valueOf(row[1].trim()), new BigDecimal(row[2].trim()));
            } catch (RuntimeException e) {
                failures.add(String.join(",", row) + " -> " + e.getMessage());
            }
        }
        return failures;
    }

    public String gradeOf(BigDecimal score) {
        GradeLevel level = GradeLevel.of(score);
        return level == null ? "未出分" : level.label() + "（绩点 " + level.gradePoint() + "）";
    }

    public BigDecimal gpa(Integer studentId) {
        return enrollmentDao.gpa(studentId);
    }
}
