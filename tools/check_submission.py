"""提交自检：文件清单、文档章节、数据库对象脚本、脚本可执行位、交付物是否齐全。

用法：python3 tools/check_submission.py
退出码 = 缺失项数量（0 表示全部通过）。
"""

import os
import re
import stat
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FILES = [
    "README.md", ".gitignore", "pom.xml",
    "config/db.properties.example", "config/db.properties", "lib/README.md",
    "data/README.md", "data/raw/.gitkeep", "data/clean/.gitkeep",
    "sql/00_create_database.sql", "sql/01_schema_tables.sql", "sql/02_schema_indexes.sql",
    "sql/03_views.sql", "sql/04_procedures.sql", "sql/05_triggers.sql", "sql/06_privileges.sql",
    "sql/07_seed_data.sql", "sql/08_demo_queries.sql", "sql/09_transaction_demo.sql",
    "sql/99_rebuild_all.sql",
    "scripts/init_db.sh", "scripts/build.sh", "scripts/run.sh", "scripts/test.sh",
    "scripts/smoke_test.sh", "scripts/backup.sh", "scripts/fetch_dataset.sh",
    "scripts/import_dataset.sh", "scripts/export_docs.sh",
    "tools/md2docx.py", "tools/gen_figs.py", "tools/prepare_dataset.py", "tools/check_submission.py",
]

JAVA_MAIN = [
    "App.java", "config/AppConfig.java", "db/ConnectionProvider.java", "db/Tx.java",
    "db/SqlScriptRunner.java", "db/RowMapper.java",
    "model/Department.java", "model/Teacher.java", "model/ClassGroup.java", "model/Student.java",
    "model/Course.java", "model/CourseOffering.java", "model/Enrollment.java", "model/SysAccount.java",
    "model/AuditLog.java", "model/enums/GradeLevel.java",
    "dao/BaseDao.java", "dao/DepartmentDao.java", "dao/TeacherDao.java", "dao/ClassGroupDao.java",
    "dao/StudentDao.java", "dao/CourseDao.java", "dao/CourseOfferingDao.java", "dao/EnrollmentDao.java",
    "dao/SysAccountDao.java", "dao/AuditLogDao.java",
    "service/StudentService.java", "service/TeacherService.java", "service/CourseService.java",
    "service/OfferingService.java", "service/EnrollmentService.java", "service/GradeService.java",
    "service/AccountService.java", "service/ReportService.java",
    "service/dto/StudentTranscript.java", "service/dto/CourseStat.java", "service/dto/GpaRow.java",
    "exception/ErrorCode.java", "exception/BizException.java", "exception/DataAccessException.java",
    "ui/console/ConsoleUI.java", "ui/console/MenuItem.java", "ui/console/Action.java",
    "ui/console/InputReader.java", "ui/console/TablePrinter.java", "ui/console/StudentMenu.java",
    "ui/console/TeacherMenu.java", "ui/console/CourseMenu.java", "ui/console/OfferingMenu.java",
    "ui/console/EnrollmentMenu.java", "ui/console/GradeMenu.java", "ui/console/ReportMenu.java",
    "ui/console/AccountMenu.java", "ui/console/DbMaintenanceMenu.java",
    "util/Validators.java", "util/DateUtils.java", "util/PasswordUtils.java", "util/Logger.java",
]

JAVA_TEST = [
    "TestRunner.java", "Assert.java", "ValidatorsTest.java", "SqlObjectTest.java", "DaoCrudTest.java",
    "ServiceFlowTest.java", "EnrollmentConcurrencyTest.java", "SmokeTest.java",
]

DOCS = [
    "docs/设计说明书.md", "docs/演示与答辩脚本.md",
    "docs/figs/er_diagram.png", "docs/figs/relation_schema.png", "docs/figs/architecture.png",
    "docs/figs/function_modules.png", "docs/figs/enroll_flow.png", "docs/figs/db_object_map.png",
    "docs/out/设计说明书.docx", "docs/out/设计说明书.pdf",
]


def check_files():
    missing = []
    for name in FILES + DOCS:
        if not os.path.exists(os.path.join(ROOT, name)):
            missing.append(name)
    for name in JAVA_MAIN:
        if not os.path.exists(os.path.join(ROOT, "src/main/java/edu/scut/db", name)):
            missing.append("src/main/java/edu/scut/db/" + name)
    for name in JAVA_TEST:
        if not os.path.exists(os.path.join(ROOT, "src/test/java/edu/scut/db/tests", name)):
            missing.append("src/test/java/edu/scut/db/tests/" + name)
    expected = 6 + 3 + 11 + 9 + 4 + len(JAVA_MAIN) + len(JAVA_TEST) + len(DOCS)
    print(f"清单文件数: {expected}（根与配置 6 + data 3 + sql 11 + scripts 9 + tools 4 + "
          f"Java 主代码 {len(JAVA_MAIN)} + 测试 {len(JAVA_TEST)} + 文档 {len(DOCS)}）")
    return missing


def check_chapters():
    path = os.path.join(ROOT, "docs/设计说明书.md")
    if not os.path.exists(path):
        return ["docs/设计说明书.md"]
    text = open(path, encoding="utf-8").read()
    problems = []
    for chapter in ["第 1 章", "第 2 章", "第 3 章", "第 4 章", "第 5 章", "第 6 章", "第 7 章", "第 8 章",
                    "参考文献", "附录 A", "附录 B", "附录 C"]:
        if chapter not in text:
            problems.append("说明书缺少 " + chapter)
    for figure in ["图 1-1", "图 2-1", "图 3-1", "图 4-1", "图 5-1", "图 6-1"]:
        if figure not in text:
            problems.append("说明书缺少 " + figure)
    if "待补充" in text:
        problems.append("说明书仍有「待补充」占位符")
    words = len(re.findall(r"[\u4e00-\u9fa5]", text))
    print(f"说明书中文字数: {words}（要求 12000–18000）")
    if words < 12000:
        problems.append(f"说明书中文正文只有 {words} 字，低于 12000 字")
    return problems


def check_sql_objects():
    problems = []
    tables = ["department", "teacher", "class_group", "student", "course", "course_offering",
              "enrollment", "sys_account", "audit_log"]
    schema = read("sql/01_schema_tables.sql")
    for table in tables:
        if f"CREATE TABLE {table}" not in schema:
            problems.append("01_schema_tables.sql 缺少表 " + table)
    views = ["v_student_profile", "v_offering_detail", "v_student_transcript", "v_course_stat"]
    view_sql = read("sql/03_views.sql")
    for view in views:
        if view not in view_sql:
            problems.append("03_views.sql 缺少视图 " + view)
    procedures = ["p_enroll_student", "p_drop_course", "p_save_score", "f_gpa", "f_offering_avg"]
    routine_sql = read("sql/04_procedures.sql")
    for routine in procedures:
        if routine not in routine_sql:
            problems.append("04_procedures.sql 缺少例程 " + routine)
    triggers = ["trg_enrollment_bi", "trg_enrollment_ai", "trg_enrollment_bu", "trg_enrollment_au",
                "trg_student_ad"]
    trigger_sql = read("sql/05_triggers.sql")
    for trigger in triggers:
        if trigger not in trigger_sql:
            problems.append("05_triggers.sql 缺少触发器 " + trigger)
    index_sql = read("sql/02_schema_indexes.sql")
    index_count = index_sql.count("CREATE INDEX")
    print(f"显式普通索引: {index_count} 条（唯一索引在 01 中定义，合计 17 条）")
    if index_count < 8:
        problems.append("02_schema_indexes.sql 普通索引少于 8 条")
    return problems


def check_executable():
    problems = []
    for name in sorted(os.listdir(os.path.join(ROOT, "scripts"))):
        path = os.path.join(ROOT, "scripts", name)
        mode = os.stat(path).st_mode
        if not mode & stat.S_IXUSR:
            problems.append(f"scripts/{name} 缺少可执行位")
    return problems


def check_artifacts():
    problems = []
    for name in ["docs/out/设计说明书.docx", "docs/out/设计说明书.pdf"]:
        path = os.path.join(ROOT, name)
        if not os.path.exists(path) or os.path.getsize(path) == 0:
            problems.append("交付物缺失或为空: " + name)
    return problems


def read(relative):
    path = os.path.join(ROOT, relative)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def main():
    problems = []
    problems += check_files()
    problems += check_chapters()
    problems += check_sql_objects()
    problems += check_executable()
    problems += check_artifacts()

    print("-" * 60)
    if problems:
        print(f"缺失或不符项: {len(problems)}")
        for item in problems:
            print("  -", item)
    else:
        print("缺失文件数 0，全部检查通过")
    return len(problems)


if __name__ == "__main__":
    sys.exit(min(255, main()))
