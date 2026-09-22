package edu.scut.db.service;

import edu.scut.db.dao.TeacherDao;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.Teacher;
import edu.scut.db.util.Validators;

import java.util.List;

public class TeacherService {

    private final Tx tx;
    private final TeacherDao teacherDao;

    public TeacherService(Tx tx) {
        this.tx = tx;
        this.teacherDao = new TeacherDao(tx.provider());
    }

    public List<Teacher> search(String keyword, String deptCode, String title) {
        return teacherDao.search(keyword, deptCode, title);
    }

    public Teacher findByNo(String teacherNo) {
        Teacher teacher = teacherDao.findByNo(teacherNo);
        if (teacher == null) {
            throw BizException.of(ErrorCode.E001, "工号 " + teacherNo + " 不存在");
        }
        return teacher;
    }

    public void create(Teacher teacher) {
        Validators.require(Validators.isTeacherNo(teacher.getTeacherNo()), "工号必须是 8 位数字");
        Validators.require(Validators.isName(teacher.getTeacherName()), "姓名不能为空且不超过 30 字");
        tx.runInTx(connection -> {
            if (teacherDao.findByNo(teacher.getTeacherNo()) != null) {
                throw BizException.of(ErrorCode.E001, "工号 " + teacher.getTeacherNo() + " 已存在");
            }
            teacherDao.insert(connection, teacher);
            return null;
        });
    }

    public void update(Teacher teacher) {
        tx.runInTx(connection -> {
            if (teacherDao.findByNo(teacher.getTeacherNo()) == null) {
                throw BizException.of(ErrorCode.E001, "工号 " + teacher.getTeacherNo() + " 不存在");
            }
            teacherDao.update(connection, teacher);
            return null;
        });
    }

    public void delete(String teacherNo) {
        tx.runInTx(connection -> {
            Teacher teacher = teacherDao.findByNo(teacherNo);
            if (teacher == null) {
                throw BizException.of(ErrorCode.E001, "工号 " + teacherNo + " 不存在");
            }
            int offerings = teacherDao.countOfferings(connection, teacher.getTeacherId());
            if (offerings > 0) {
                throw BizException.of(ErrorCode.E001,
                        "教师 " + teacher.getTeacherName() + " 已有 " + offerings + " 条开课记录，禁止删除");
            }
            teacherDao.deleteByNo(connection, teacherNo);
            return null;
        });
    }
}
