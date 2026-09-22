package edu.scut.db.service;

import edu.scut.db.dao.CourseOfferingDao;
import edu.scut.db.dao.EnrollmentDao;
import edu.scut.db.dao.StudentDao;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.CourseOffering;
import edu.scut.db.model.Enrollment;
import edu.scut.db.model.Student;

import java.util.List;

public class EnrollmentService {

    private final Tx tx;
    private final StudentDao studentDao;
    private final CourseOfferingDao offeringDao;
    private final EnrollmentDao enrollmentDao;

    public EnrollmentService(Tx tx) {
        this.tx = tx;
        this.studentDao = new StudentDao(tx.provider());
        this.offeringDao = new CourseOfferingDao(tx.provider());
        this.enrollmentDao = new EnrollmentDao(tx.provider());
    }

    public String enroll(String studentNo, Integer offeringId) {
        return tx.runInTx(connection -> {
            Student student = studentDao.findByNo(studentNo);
            if (student == null) {
                throw BizException.of(ErrorCode.E002, "学号 " + studentNo + " 不存在");
            }
            if (!"在读".equals(student.getStatus())) {
                throw BizException.of(ErrorCode.E001, "学籍状态为「" + student.getStatus() + "」，不能选课");
            }

            CourseOffering offering = offeringDao.findByIdForUpdate(connection, offeringId);
            if (offering == null) {
                throw BizException.of(ErrorCode.E003, "开课号 " + offeringId + " 不存在");
            }

            Enrollment existing = enrollmentDao.findByStudentAndOffering(connection,
                    student.getStudentId(), offeringId);
            if (existing != null && "已选".equals(existing.getStatus())) {
                throw BizException.of(ErrorCode.E004, "该生已选此开课，不能重复选课");
            }
            if (offering.getEnrolledCount() >= offering.getCapacity()) {
                throw BizException.of(ErrorCode.E005, "开课 " + offeringId + " 名额已满（"
                        + offering.getEnrolledCount() + "/" + offering.getCapacity() + "）");
            }

            if (existing != null) {
                return enrollAgain(connection, existing, offering, student);
            }
            enrollmentDao.insert(connection, student.getStudentId(), offeringId);
            CourseOffering display = offeringDao.findById(offeringId);
            return "选课成功：" + student.getStudentName() + " -> " + display.getCourseCode()
                    + "（已选 " + (offering.getEnrolledCount() + 1) + "/" + offering.getCapacity() + "）";
        });
    }

    private String enrollAgain(java.sql.Connection connection, Enrollment existing, CourseOffering offering,
                               Student student) {
        enrollmentDao.markSelected(connection, existing.getEnrollmentId());
        CourseOffering display = offeringDao.findById(offering.getOfferingId());
        return "重新选课成功：" + student.getStudentName() + " -> " + display.getCourseCode();
    }

    public String drop(String studentNo, Integer offeringId) {
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
            if (enrollment.getScore() != null) {
                throw BizException.of(ErrorCode.E006, "该记录已有成绩 " + enrollment.getScore() + "，不能退课");
            }
            enrollmentDao.markDropped(connection, enrollment.getEnrollmentId());
            return "退课成功：学号 " + studentNo + " 开课 " + offeringId;
        });
    }

    public List<Enrollment> myCourses(String studentNo) {
        Student student = studentDao.findByNo(studentNo);
        if (student == null) {
            throw BizException.of(ErrorCode.E002, "学号 " + studentNo + " 不存在");
        }
        return enrollmentDao.findByStudent(studentNo);
    }

    public List<Enrollment> roster(Integer offeringId) {
        return enrollmentDao.findByOffering(offeringId);
    }
}
