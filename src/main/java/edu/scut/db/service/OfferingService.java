package edu.scut.db.service;

import edu.scut.db.dao.CourseDao;
import edu.scut.db.dao.CourseOfferingDao;
import edu.scut.db.dao.TeacherDao;
import edu.scut.db.db.Tx;
import edu.scut.db.exception.BizException;
import edu.scut.db.exception.ErrorCode;
import edu.scut.db.model.Course;
import edu.scut.db.model.CourseOffering;
import edu.scut.db.model.Teacher;
import edu.scut.db.util.Validators;

import java.time.LocalDateTime;
import java.util.List;

public class OfferingService {

    private final Tx tx;
    private final CourseOfferingDao offeringDao;
    private final CourseDao courseDao;
    private final TeacherDao teacherDao;

    public OfferingService(Tx tx) {
        this.tx = tx;
        this.offeringDao = new CourseOfferingDao(tx.provider());
        this.courseDao = new CourseDao(tx.provider());
        this.teacherDao = new TeacherDao(tx.provider());
    }

    public List<CourseOffering> search(String semester, String teacherNo, String courseCode) {
        return offeringDao.search(semester, teacherNo, courseCode);
    }

    public CourseOffering findById(Integer offeringId) {
        CourseOffering offering = offeringDao.findById(offeringId);
        if (offering == null) {
            throw BizException.of(ErrorCode.E003, "开课号 " + offeringId + " 不存在");
        }
        return offering;
    }

    public void create(String courseCode, String teacherNo, String semester, Integer capacity, String classroom) {
        Validators.require(Validators.isSemester(semester), "学期格式应为 2026-2027-1");
        Validators.require(Validators.isCapacity(capacity), "容量必须在 1 到 300 之间");
        tx.runInTx(connection -> {
            Course course = courseDao.findByCode(courseCode);
            if (course == null) {
                throw BizException.of(ErrorCode.E001, "课程代码 " + courseCode + " 不存在");
            }
            Teacher teacher = teacherDao.findByNo(teacherNo);
            if (teacher == null) {
                throw BizException.of(ErrorCode.E001, "工号 " + teacherNo + " 不存在");
            }
            CourseOffering offering = new CourseOffering();
            offering.setCourseId(course.getCourseId());
            offering.setTeacherId(teacher.getTeacherId());
            offering.setSemester(semester);
            offering.setCapacity(capacity);
            offering.setClassroom(classroom);
            offering.setOpenTime(LocalDateTime.now());
            try {
                offeringDao.insert(connection, offering);
            } catch (RuntimeException e) {
                throw BizException.of(ErrorCode.E001, "同一课程、教师、学期只能开一次课");
            }
            return null;
        });
    }

    public int adjustCapacity(Integer offeringId, Integer capacity) {
        Validators.require(Validators.isCapacity(capacity), "容量必须在 1 到 300 之间");
        return tx.runInTx(connection -> {
            CourseOffering offering = offeringDao.findByIdForUpdate(connection, offeringId);
            if (offering == null) {
                throw BizException.of(ErrorCode.E003, "开课号 " + offeringId + " 不存在");
            }
            if (capacity < offering.getEnrolledCount()) {
                throw BizException.of(ErrorCode.E001,
                        "容量不能小于已选人数 " + offering.getEnrolledCount());
            }
            return offeringDao.updateCapacity(connection, offeringId, capacity);
        });
    }
}
