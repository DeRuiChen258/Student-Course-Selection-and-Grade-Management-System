"""离屏自检：连接 / 对象计数 / 页面实例化 / 端到端业务链 / 权限 / 导入导出。

用法：QT_QPA_PLATFORM=offscreen .venv/bin/python tools/selfcheck.py
退出码 = 失败项数量。
"""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from app import specs
from app.context import AppContext
from db.errors import DbError
from ui.main_window import MainWindow, PAGE_DEFS

RESULTS = []
SNOOZE = 0.35


def check(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    RESULTS.append((status, name, detail))
    print(f"[{status}] {name}" + (f" | {detail}" if detail else ""), flush=True)
    return condition


def expect_error(name, fn, code):
    try:
        fn()
    except DbError as exc:
        return check(name, str(exc.code) == str(code), f"实际错误码 {exc.code} · {exc.message}")
    except Exception as exc:  # noqa: BLE001
        return check(name, False, f"未预期的异常 {exc!r}")
    return check(name, False, f"预期错误码 {code}，但调用成功")


def pump(app, seconds=SNOOZE):
    deadline = time.time() + seconds
    while time.time() < deadline:
        app.processEvents()
        time.sleep(0.02)


def cleanup(context, demo_no, scratch_table):
    """清除上一次自检可能残留的数据，保证脚本可重复执行。"""
    context.db.execute(f"DROP TABLE IF EXISTS {scratch_table}", source="自检: 清理导入表")
    ids = [row["offering_id"] for row in context.db.query(
        "SELECT offering_id FROM course_offering WHERE classroom = %s",
        ("自检教室",), source="自检: 查找残留开课")]
    for offering_id in ids:
        context.db.execute("DELETE FROM enrollment WHERE offering_id = %s",
                           (offering_id,), source="自检: 清理残留选课")
        context.db.execute("DELETE FROM course_offering WHERE offering_id = %s",
                           (offering_id,), source="自检: 清理残留开课")
    context.db.execute("DELETE FROM student WHERE student_no = %s", (demo_no,),
                       source="自检: 清理残留学生")
    return len(ids)


def main():
    app = QApplication(sys.argv[:1])
    context = AppContext()
    specs.register(context.entities)
    demo_no = "202301019999"
    scratch_table = "zz_selftest_import"
    removed = cleanup(context, demo_no, scratch_table)
    if removed:
        print(f"[提示] 已清理上一轮残留开课 {removed} 条")

    print("== G1 依赖与连接 ==")
    import importlib.metadata as metadata
    import PySide6
    import pymysql
    from PySide6 import QtCharts  # noqa: F401
    check("PySide6 / PyMySQL 导入", True,
          f"PySide6 {PySide6.__version__} / PyMySQL {metadata.version('pymysql')}")
    health = context.db.health()
    check("数据库连通", bool(health.get("db_name")),
          f"{health.get('db_user')} @ {health.get('db_name')} · {health.get('version')}")

    print("== G2 数据库对象与演示数据 ==")
    counts = context.db.object_counts()
    check("基础表 = 9", counts["tables"] == 9, str(counts["tables"]))
    check("视图 = 4", counts["views"] == 4, str(counts["views"]))
    check("触发器 = 5", counts["triggers"] == 5, str(counts["triggers"]))
    check("例程 = 5", counts["routines"] == 5, str(counts["routines"]))
    overview = context.meta.overview()
    check("演示数据规模（模拟数据集）",
          overview["students"] >= 20 and overview["offerings"] >= 15,
          f"学生 {overview['students']} · 开课 {overview['offerings']} · "
          f"选课 {overview['enrollments']}")

    print("== G4 页面实例化与真实查询 ==")
    window = MainWindow(context)
    window.resize(1500, 900)
    window.show()
    failed_pages = []
    for key, _title, _tag, _factory in PAGE_DEFS:
        try:
            window.navigate(key)
            pump(app, 0.5)
            page = window.pages.get(key)
            if page is None:
                failed_pages.append(f"{key}: 页面未创建")
        except Exception as exc:  # noqa: BLE001
            failed_pages.append(f"{key}: {exc!r}")
    check("14 个页面全部可打开", not failed_pages, "; ".join(failed_pages))

    print("== G5 CRUD 端到端（F01–F10） ==")
    cleanup(context, demo_no, scratch_table)
    classes = context.entities.lookup("classes")
    student_id = context.entities.create("student", {
        "student_no": demo_no, "student_name": "自检同学", "gender": "男",
        "birth_date": "2005-05-05", "class_id": classes[0]["id"],
        "enroll_date": "2023-09-01", "phone": "13800009999", "email": "selftest@scut.edu.cn",
        "status": "在读"})
    check("F01 新增学生", student_id > 0, f"student_id={student_id}")
    context.entities.update("student", student_id, {
        "student_no": demo_no, "student_name": "自检同学", "gender": "男",
        "birth_date": "2005-05-05", "class_id": classes[0]["id"],
        "enroll_date": "2023-09-01", "phone": "13800008888",
        "email": "selftest@scut.edu.cn", "status": "在读"})
    row = context.entities.get("student", student_id)
    check("F02 修改学生", row["phone"] == "13800008888", row["phone"])
    page_rows, filtered_total = context.entities.page(
        "student", {"student_name": "自检", "status": "在读"}, 1, 10)
    check("F04 条件 + 模糊查询", filtered_total >= 1,
          f"命中 {filtered_total} 条：{[r['student_name'] for r in page_rows]}")

    courses = context.entities.lookup("courses")
    teachers = context.entities.lookup("teachers")
    offering_id = context.entities.create("offering", {
        "course_id": courses[0]["id"], "teacher_id": teachers[0]["id"],
        "semester": "2026-2027-1", "capacity": 2, "classroom": "自检教室"})
    check("F05/F10 课程与开课联动创建", offering_id > 0, f"offering_id={offering_id}")
    print("== G6 事务 / 触发器 / 存储过程错误码（F11–F14） ==")
    message = context.enrollment.enroll(demo_no, offering_id)
    detail = context.enrollment.offering_detail(offering_id)
    check("F11 选课成功且触发器联动计数",
          detail["enrolled"] == 1 and "已选 1/2" in message, message)
    expect_error("F11 重复选课 → 40004",
                 lambda: context.enrollment.enroll(demo_no, offering_id), 40004)
    expect_error("F11 学生不存在 → 40001",
                 lambda: context.enrollment.enroll("999999999999", offering_id), 40001)
    second_no = None
    for row in context.enrollment.student_options(limit=50):
        if row["student_no"] != demo_no and row["status"] == "在读":
            second_no = row["student_no"]
            break
    context.enrollment.enroll(second_no, offering_id)
    detail = context.enrollment.offering_detail(offering_id)
    check("F11 触发器把已选人数累加到容量上限",
          detail["enrolled"] == 2 and detail["remain"] == 0,
          f"已选 {detail['enrolled']}/{detail['capacity']} · 余量 {detail['remain']}")
    try:
        context.entities.update("offering", offering_id, {
            "course_id": courses[0]["id"], "teacher_id": teachers[0]["id"],
            "semester": "2026-2027-1", "capacity": 1, "classroom": "自检教室",
        }, {"enrolled_count": 2})
        check("F10 容量调整不得小于已选人数", False, "未触发校验")
    except DbError as exc:
        check("F10 容量调整不得小于已选人数", "容量不得小于已选人数" in exc.message,
              exc.message)
    third_no = next(row["student_no"] for row in context.enrollment.student_options(limit=50)
                    if row["student_no"] not in (demo_no, second_no) and row["status"] == "在读")
    expect_error("F11 名额已满 → 触发器 E005 / 过程 40005",
                 lambda: context.enrollment.enroll(third_no, offering_id), 40005)
    context.enrollment.save_score(demo_no, offering_id, 88.5)
    roster = {row["student_no"]: row for row in context.enrollment.roster(offering_id)}
    check("F13 成绩录入", float(roster[demo_no]["score"]) == 88.5,
          f"score={roster[demo_no]['score']} · score_time={roster[demo_no]['score_time']}")
    expect_error("F13 成绩越界 → 40008",
                 lambda: context.enrollment.save_score(demo_no, offering_id, 101), 40008)
    expect_error("F12 已出分退课 → 40007",
                 lambda: context.enrollment.drop(demo_no, offering_id), 40007)
    summary = context.enrollment.student_summary(demo_no)
    check("F15 课表与 GPA（视图 + 标量函数）",
          summary["course_count"] >= 1 and summary["gpa"] is not None,
          f"选课 {summary['course_count']} 门 · GPA {summary['gpa']}")
    context.enrollment.drop(second_no, offering_id)
    check("F12 未出分退课成功", True, f"{second_no} 已退课")

    print("== G7 统计分析（F16） ==")
    check("课程统计（v_course_stat）", len(context.report.course_stat()) > 0)
    check("成绩分布（CASE 分箱）",
          sum(row["cnt"] for row in context.report.score_distribution()) > 0)
    check("学期汇总", len(context.report.semester_summary()) >= 2)
    check("课程类型占比", len(context.report.course_type_share()) >= 3)
    check("GPA 排名（f_gpa）", len(context.report.gpa_ranking(top=5)) > 0)
    plan_with, plan_without = context.report.explain_compare(offering_id)
    check("EXPLAIN 索引对比", bool(plan_with) and bool(plan_without),
          f"索引计划 key={plan_with[0].get('key')} · 忽略索引 key={plan_without[0].get('key')}")

    print("== G8 权限矩阵与越权实测 ==")
    privileges = context.auth.privileges(context.maintenance_db())
    table_priv = privileges["table"]
    schema_priv = privileges["schema"]
    db_accounts = privileges["accounts"]
    check("四类数据库账号授权可读",
          len(db_accounts) >= 4 and (len(table_priv) + len(schema_priv)) > 0,
          f"账号 {db_accounts} · 表级 {len(table_priv)} 条 · 模式级 {len(schema_priv)} 条 · "
          f"来源 {privileges['source']}")
    probe = window.pages["permissions"]._probe("edu_teacher")
    check("越权实测回显 1142", "1142" in probe, probe.splitlines()[2] if probe else "")

    print("== G9 导入导出 ==")
    out_dir = Path(__file__).resolve().parent.parent / "out"
    out_dir.mkdir(exist_ok=True)
    csv_path = out_dir / "selftest_courses.csv"
    columns = [("课程代码", "course_code"), ("课程名", "course_name"), ("学分", "credit")]
    course_rows = context.db.query(
        "SELECT course_code, course_name, credit FROM course ORDER BY course_code",
        source="自检: 导出课程")
    exported = context.io.export(csv_path, columns, course_rows, "csv", "course")
    check("导出 CSV", exported == len(course_rows), f"{exported} 行 → {csv_path.name}")
    xlsx_path = out_dir / "selftest_courses.xlsx"
    context.io.export(xlsx_path, columns, course_rows, "xlsx", "course")
    check("导出 Excel", xlsx_path.exists() and xlsx_path.stat().st_size > 2000,
          f"{xlsx_path.stat().st_size} 字节")
    context.db.execute(f"DROP TABLE IF EXISTS {scratch_table}", source="自检: 重建导入表")
    context.db.execute(
        f"CREATE TABLE {scratch_table} (course_code VARCHAR(16) NOT NULL, "
        f"course_name VARCHAR(60) NOT NULL, credit DECIMAL(3,1) NOT NULL)",
        source="自检: 建导入表")
    headers, rows = context.io.preview(csv_path, limit=None)
    report = context.io.import_rows(scratch_table,
                                    {"课程代码": "course_code", "课程名": "course_name",
                                     "学分": "credit"},
                                    rows, mode="atomic")
    imported = context.db.scalar(f"SELECT COUNT(*) FROM {scratch_table}",
                                 source="自检: 导入核对")
    check("导入 CSV（字段映射 + 事务）",
          report["inserted"] == len(rows) and imported == len(rows),
          f"写入 {report['inserted']} 行 · 表内 {imported} 行")
    bad_rows = [{"course_code": None, "course_name": "缺主键", "credit": "3.0"}]
    failed = context.io.import_rows(scratch_table,
                                    {"course_code": "course_code",
                                     "course_name": "course_name", "credit": "credit"},
                                    bad_rows, mode="skip")
    check("导入失败行报告", failed["failed"] == 1,
          failed["failures"][0]["error"] if failed["failures"] else "")
    context.db.execute(f"DROP TABLE IF EXISTS {scratch_table}", source="自检: 清理导入表")

    print("== 收尾：清理自检数据 ==")
    context.entities.delete("student", student_id)
    pending = context.db.scalar("SELECT COUNT(*) FROM enrollment WHERE offering_id = %s",
                                (offering_id,), source="自检: 残留选课检查")
    if pending:
        context.db.execute("DELETE FROM enrollment WHERE offering_id = %s", (offering_id,),
                           source="自检: 清理已退选课记录")
        print(f"[说明] 该开课仍有 {pending} 条选课记录（退课为软删除，状态置「已退」），"
              f"外键 ON DELETE RESTRICT 会阻止直接删除开课，故先清理后删除。")
    context.entities.delete("offering", offering_id)
    leftovers = context.db.scalar("SELECT COUNT(*) FROM student WHERE student_no = %s",
                                  (demo_no,), source="自检: 残留检查")
    check("自检数据已清理", leftovers == 0, f"残留 {leftovers} 行")
    audit_total = context.db.scalar("SELECT COUNT(*) FROM audit_log", source="自检: 审计留痕")
    check("审计日志留痕", audit_total >= 1, f"audit_log 共 {audit_total} 条")

    context.shutdown()
    failures = [item for item in RESULTS if item[0] == "FAIL"]
    print(f"\n汇总：通过 {len(RESULTS) - len(failures)} / {len(RESULTS)}，失败 {len(failures)}")
    for _status, name, detail in failures:
        print(f"  - {name} | {detail}")
    return len(failures)


if __name__ == "__main__":
    raise SystemExit(main())
