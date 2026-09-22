package edu.scut.db.service;

import edu.scut.db.dao.CourseDao;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.Course;
import edu.scut.db.util.Validators;

import java.util.List;

public class CourseService {

    private final Tx tx;
    private final CourseDao courseDao;

    public CourseService(Tx tx) {
        this.tx = tx;
        this.courseDao = new CourseDao(tx.provider());
    }

    public Course findByCode(String courseCode) {
        Course course = courseDao.findByCode(courseCode);
        if (course == null) {
            throw BizException.of(ErrorCode.E001, "课程代码 " + courseCode + " 不存在");
        }
        return course;
    }

    public List<Course> search(String keyword, String deptCode, String courseType) {
        return courseDao.search(keyword, deptCode, courseType);
    }

    public void create(Course course) {
        Validators.require(Validators.isCourseCode(course.getCourseCode()), "课程代码必须是 2-16 位大写字母或数字");
        Validators.require(!course.getCourseName().isBlank(), "课程名称不能为空");
        Validators.require(Validators.isCredit(course.getCredit()), "学分必须在 0.5 到 10.0 之间");
        Validators.require(Validators.isHours(course.getHours()), "学时必须在 8 到 200 之间");
        tx.runInTx(connection -> {
            if (courseDao.findByCode(course.getCourseCode()) != null) {
                throw BizException.of(ErrorCode.E001, "课程代码 " + course.getCourseCode() + " 已存在");
            }
            courseDao.insert(connection, course);
            return null;
        });
    }

    public void update(Course course) {
        Validators.require(Validators.isCredit(course.getCredit()), "学分必须在 0.5 到 10.0 之间");
        Validators.require(Validators.isHours(course.getHours()), "学时必须在 8 到 200 之间");
        tx.runInTx(connection -> {
            Course old = courseDao.findByCode(course.getCourseCode());
            if (old == null) {
                throw BizException.of(ErrorCode.E001, "课程代码 " + course.getCourseCode() + " 不存在");
            }
            courseDao.update(connection, course);
            return null;
        });
    }

    public void delete(String courseCode) {
        tx.runInTx(connection -> {
            Course course = courseDao.findByCode(courseCode);
            if (course == null) {
                throw BizException.of(ErrorCode.E001, "课程代码 " + courseCode + " 不存在");
            }
            int offerings = courseDao.countOfferings(connection, course.getCourseId());
            if (offerings > 0) {
                throw BizException.of(ErrorCode.E001,
                        "课程 " + course.getCourseName() + " 已有 " + offerings + " 条开课记录，禁止删除");
            }
            courseDao.deleteByCode(connection, courseCode);
            return null;
        });
    }
}
