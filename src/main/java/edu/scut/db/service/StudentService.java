package edu.scut.db.service;

import edu.scut.db.dao.AuditLogDao;
import edu.scut.db.dao.ClassGroupDao;
import edu.scut.db.dao.EnrollmentDao;
import edu.scut.db.dao.StudentDao;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.AuditLog;
import edu.scut.db.model.ClassGroup;
import edu.scut.db.model.Student;
import edu.scut.db.util.Validators;

import java.util.List;

public class StudentService {

    private final Tx tx;
    private final StudentDao studentDao;
    private final ClassGroupDao classGroupDao;
    private final AuditLogDao auditLogDao;
    private final EnrollmentDao enrollmentDao;

    public StudentService(Tx tx) {
        this.tx = tx;
        this.studentDao = new StudentDao(tx.provider());
        this.classGroupDao = new ClassGroupDao(tx.provider());
        this.auditLogDao = new AuditLogDao(tx.provider());
        this.enrollmentDao = new EnrollmentDao(tx.provider());
    }

    public List<ClassGroup> classGroups() {
        return classGroupDao.findAll();
    }

    public Student findByNo(String studentNo) {
        Student student = studentDao.findByNo(studentNo);
        if (student == null) {
            throw BizException.of(ErrorCode.E002, "学号 " + studentNo + " 不存在");
        }
        return student;
    }

    public List<Student> search(String studentNo, String nameKeyword, String classCode, String status,
                                int page, int size) {
        return studentDao.search(studentNo, nameKeyword, classCode, status, page, size);
    }

    public int count(String studentNo, String nameKeyword, String classCode, String status) {
        return studentDao.count(studentNo, nameKeyword, classCode, status);
    }

    public void create(Student student) {
        Validators.require(Validators.isStudentNo(student.getStudentNo()), "学号必须是 12 位数字");
        Validators.require(Validators.isName(student.getStudentName()), "姓名不能为空且不超过 30 字");
        Validators.require(Validators.isPhone(student.getPhone()), "联系电话格式不正确");
        Validators.require(Validators.isEmail(student.getEmail()), "邮箱格式不正确");
        tx.runInTx(connection -> {
            ClassGroup group = classGroupDao.findById(connection, student.getClassId());
            if (group == null) {
                throw BizException.of(ErrorCode.E001, "班级不存在，请先选择有效班级");
            }
            if (studentDao.findByNo(student.getStudentNo()) != null) {
                throw BizException.of(ErrorCode.E001, "学号 " + student.getStudentNo() + " 已存在");
            }
            studentDao.insert(connection, student);
            AuditLog log = new AuditLog();
            log.setTableName("student");
            log.setAction("INSERT");
            log.setRecordId(student.getStudentNo());
            log.setOperator("edu_app");
            log.setDetail("新增学生 " + student.getStudentName());
            auditLogDao.insert(connection, log);
            return null;
        });
    }

    public void update(Student student) {
        Validators.require(Validators.isName(student.getStudentName()), "姓名不能为空且不超过 30 字");
        Validators.require(Validators.isPhone(student.getPhone()), "联系电话格式不正确");
        tx.runInTx(connection -> {
            Student old = studentDao.findByNo(student.getStudentNo());
            if (old == null) {
                throw BizException.of(ErrorCode.E002, "学号 " + student.getStudentNo() + " 不存在");
            }
            studentDao.update(connection, student);
            AuditLog log = new AuditLog();
            log.setTableName("student");
            log.setAction("UPDATE");
            log.setRecordId(student.getStudentNo());
            log.setOperator("edu_app");
            log.setDetail("电话 " + old.getPhone() + " -> " + student.getPhone()
                    + "，状态 " + old.getStatus() + " -> " + student.getStatus());
            auditLogDao.insert(connection, log);
            return null;
        });
    }

    public int delete(String studentNo) {
        return tx.runInTx(connection -> {
            Student student = studentDao.findByNo(studentNo);
            if (student == null) {
                throw BizException.of(ErrorCode.E002, "学号 " + studentNo + " 不存在");
            }
            int enrollments = studentDao.countEnrollments(connection, student.getStudentId());
            for (var enrollment : enrollmentDao.findByStudent(studentNo)) {
                enrollmentDao.markDropped(connection, enrollment.getEnrollmentId());
            }
            studentDao.deleteByNo(connection, studentNo);
            return enrollments;
        });
    }

}
