"""数据集准备：把 data/raw 的 OULAD 原始表映射为本系统四类实体的 clean CSV。

用法：
    python3 tools/prepare_dataset.py                     # 读取 data/raw（或 --raw-dir）
    python3 tools/prepare_dataset.py --generate 12000    # 无网络时生成同结构合成数据
"""

import argparse
import csv
import hashlib
import json
import os
import random
from datetime import date, timedelta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data", "raw")
CLEAN_DIR = os.path.join(ROOT, "data", "clean")

SEED = 20260921
CHUNK_CAPACITY = 300
TEACHER_POOL = 12

SURNAMES = "赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜"
GIVEN = ["嘉辰", "雨萱", "子墨", "思远", "梓涵", "浩然", "若曦", "宇航", "欣怡", "泽楷",
         "一鸣", "梦琪", "俊杰", "诗涵", "天佑", "静怡", "博文", "雅琳", "晨曦", "语彤"]

STUDENT_COLUMNS = ["student_no", "student_name", "gender", "birth_date", "class_code", "class_name",
                   "grade_year", "dept_code", "enroll_date", "phone", "email", "status"]
COURSE_COLUMNS = ["course_code", "course_name", "credit", "hours", "course_type", "dept_code"]
OFFERING_COLUMNS = ["course_code", "teacher_no", "semester", "capacity", "classroom", "open_time", "class_code"]
ENROLLMENT_COLUMNS = ["student_no", "course_code", "teacher_no", "semester", "score",
                      "score_time", "enroll_time", "status"]


def digest(value):
    return int(hashlib.sha256(str(value).encode()).hexdigest()[:12], 16)


def synth_name(key):
    h = digest(key)
    return SURNAMES[h % len(SURNAMES)] + GIVEN[(h // 97) % len(GIVEN)]


def student_no_of(raw_id):
    return "90" + str(raw_id).zfill(10)


def teacher_no_of(index):
    return str(90000000 + index + 1)


def teacher_name_of(index):
    return "数据集教师" + str(index + 1).zfill(2)


def module_code(module):
    return "OU" + module.upper()


def class_code_of(module, presentation):
    return "OU" + module.upper() + presentation


def semester_of(presentation):
    year = int(presentation[:4])
    term = presentation[4:5]
    if term == "J":
        return "%d-%d-1" % (year, year + 1)
    return "%d-%d-2" % (year - 1, year)


def presentation_start(presentation):
    year = int(presentation[:4])
    return date(year, 10, 1) if presentation[4:5] == "J" else date(year, 2, 1)


def to_credit(length):
    value = round(float(length) / 60.0, 1)
    return min(10.0, max(0.5, value))


def to_hours(length):
    return min(200, max(8, int(round(float(length) / 2.0))))


def birth_date_of(age_band, presentation):
    year = int(presentation[:4])
    if age_band == "0-35":
        return date(year - 25, 1, 1)
    if age_band == "35-55":
        return date(year - 40, 1, 1)
    return date(year - 60, 1, 1)


def mask_phone(raw_id):
    return "139" + str(digest("phone" + str(raw_id))).zfill(8)[:8]


def mask_email(raw_id):
    return "s" + student_no_of(raw_id) + "@stu.example.edu"


def status_of(final_result):
    return "退学" if final_result == "Withdrawn" else "在读"


def enroll_status_of(final_result):
    return "已退" if final_result == "Withdrawn" else "已选"


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path, columns, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_from_oulad(raw_dir):
    courses = read_csv(os.path.join(raw_dir, "courses.csv"))
    student_info = read_csv(os.path.join(raw_dir, "studentInfo.csv"))
    registration = read_csv(os.path.join(raw_dir, "studentRegistration.csv"))
    assessments = read_csv(os.path.join(raw_dir, "assessments.csv"))
    assessment_scores = read_csv(os.path.join(raw_dir, "studentAssessment.csv"))

    length_by_presentation = {(c["code_module"], c["code_presentation"]): c["module_presentation_length"]
                              for c in courses}
    assessment_meta = {a["id_assessment"]: (a["code_module"], a["code_presentation"]) for a in assessments}

    score_acc = {}
    for row in assessment_scores:
        if not row.get("score"):
            continue
        meta = assessment_meta.get(row["id_assessment"])
        if meta is None:
            continue
        key = (meta[0], meta[1], row["id_student"])
        total, count = score_acc.get(key, (0.0, 0))
        score_acc[key] = (total + float(row["score"]), count + 1)

    register = {}
    for row in registration:
        register[(row["code_module"], row["code_presentation"], row["id_student"])] = row

    groups = {}
    for row in student_info:
        groups.setdefault((row["code_module"], row["code_presentation"]), []).append(row)
    for key in groups:
        groups[key].sort(key=lambda r: int(r["id_student"]))
    position_of = {}
    for key, members in groups.items():
        for index, member in enumerate(members):
            position_of[(key[0], key[1], member["id_student"])] = index

    offering_rows = []
    group_of_student = {}
    for key in sorted(groups):
        module, presentation = key
        members = groups[key]
        chunks = [members[i:i + CHUNK_CAPACITY] for i in range(0, len(members), CHUNK_CAPACITY)]
        base = digest(module + presentation) % TEACHER_POOL
        for index, chunk in enumerate(chunks):
            offering_rows.append({
                "course_code": module_code(module),
                "teacher_no": teacher_no_of((base + index) % TEACHER_POOL),
                "semester": semester_of(presentation),
                "capacity": CHUNK_CAPACITY,
                "classroom": "线上教学班%02d" % (index + 1),
                "open_time": presentation_start(presentation).isoformat() + " 09:00:00",
                "class_code": class_code_of(module, presentation),
            })
            for member in chunk:
                group_of_student.setdefault(member["id_student"], key)

    seen_student = {}
    for row in student_info:
        sid = row["id_student"]
        if sid in seen_student:
            continue
        key = group_of_student.get(sid, (row["code_module"], row["code_presentation"]))
        registration_row = register.get((key[0], key[1], sid), {})
        start = presentation_start(key[1])
        offset = registration_row.get("date_registration") or 0
        enroll_date = start + timedelta(days=int(float(offset)))
        seen_student[sid] = {
            "student_no": student_no_of(sid),
            "student_name": synth_name(sid),
            "gender": "男" if row["gender"] == "M" else "女",
            "birth_date": birth_date_of(row["age_band"], key[1]).isoformat(),
            "class_code": class_code_of(key[0], key[1]),
            "class_name": "开放大学 %s %s 教学班" % (key[0], key[1]),
            "grade_year": key[1][:4],
            "dept_code": "OU",
            "enroll_date": enroll_date.isoformat(),
            "phone": mask_phone(sid),
            "email": mask_email(sid),
            "status": status_of(row["final_result"]),
        }

    student_rows = [seen_student[sid] for sid in sorted(seen_student, key=lambda v: int(v))]

    course_rows = []
    for row in sorted(courses, key=lambda r: (r["code_module"], r["code_presentation"])):
        length = length_by_presentation[(row["code_module"], row["code_presentation"])]
        code = module_code(row["code_module"])
        if any(c["course_code"] == code for c in course_rows):
            continue
        course_rows.append({
            "course_code": code,
            "course_name": "开放大学模块 " + row["code_module"].upper(),
            "credit": "%.1f" % to_credit(length),
            "hours": str(to_hours(length)),
            "course_type": "选修",
            "dept_code": "OU",
        })

    enrollment_rows = []
    used = set()
    chunk_index = {}
    for key, members in sorted(groups.items()):
        module, presentation = key
        base = digest(module + presentation) % TEACHER_POOL
        for index, chunk in enumerate([members[i:i + CHUNK_CAPACITY] for i in range(0, len(members), CHUNK_CAPACITY)]):
            chunk_index[(key, index)] = teacher_no_of((base + index) % TEACHER_POOL)

    for row in sorted(student_info, key=lambda r: (r["code_module"], r["code_presentation"], int(r["id_student"]))):
        key = (row["code_module"], row["code_presentation"])
        sid = row["id_student"]
        index = position_of[(key[0], key[1], sid)] // CHUNK_CAPACITY
        unique = (student_no_of(sid), module_code(row["code_module"]), chunk_index[(key, index)], semester_of(row["code_presentation"]))
        if unique in used:
            continue
        used.add(unique)
        total, count = score_acc.get((key[0], key[1], sid), (None, 0))
        score = "" if count == 0 else "%.2f" % (total / count)
        registration_row = register.get((key[0], key[1], sid), {})
        start = presentation_start(row["code_presentation"])
        offset = registration_row.get("date_registration") or 0
        enroll_time = start + timedelta(days=int(float(offset)))
        length = int(float(length_by_presentation[key]))
        score_time = "" if count == 0 else (start + timedelta(days=length)).isoformat() + " 10:00:00"
        enrollment_rows.append({
            "student_no": student_no_of(sid),
            "course_code": module_code(row["code_module"]),
            "teacher_no": chunk_index[(key, index)],
            "semester": semester_of(row["code_presentation"]),
            "score": score,
            "score_time": score_time,
            "enroll_time": enroll_time.isoformat() + " 09:00:00",
            "status": enroll_status_of(row["final_result"]),
        })

    return student_rows, course_rows, offering_rows, enrollment_rows


def build_synthetic(total):
    rng = random.Random(SEED)
    student_rows, course_rows, offering_rows, enrollment_rows = [], [], [], []
    group_size = CHUNK_CAPACITY
    group_count = max(1, (total + group_size - 1) // group_size)

    for index in range(total):
        raw_id = 800000 + index
        group = index // group_size
        module = "S%04d" % group
        presentation = "%d%s" % (2019 + (group // 12) % 6, "J" if group % 2 == 0 else "B")
        course_code = module_code(module)
        if index % group_size == 0:
            course_rows.append({
                "course_code": course_code,
                "course_name": "合成模块 " + module,
                "credit": "%.1f" % rng.choice([2.0, 3.0, 3.5, 4.0, 5.0]),
                "hours": str(rng.choice([32, 40, 48, 56, 64])),
                "course_type": rng.choice(["必修", "选修", "通识"]),
                "dept_code": "OU",
            })
            offering_rows.append({
                "course_code": course_code,
                "teacher_no": teacher_no_of(group % TEACHER_POOL),
                "semester": semester_of(presentation),
                "capacity": CHUNK_CAPACITY,
                "classroom": "线上教学班%02d" % (group % 5 + 1),
                "open_time": presentation_start(presentation).isoformat() + " 09:00:00",
                "class_code": class_code_of(module, presentation),
            })
        student_rows.append({
            "student_no": student_no_of(raw_id),
            "student_name": synth_name(raw_id),
            "gender": rng.choice(["男", "女"]),
            "birth_date": date(2000 + rng.randint(0, 5), rng.randint(1, 12), rng.randint(1, 28)).isoformat(),
            "class_code": class_code_of(module, presentation),
            "class_name": "合成班级 " + module + presentation,
            "grade_year": presentation[:4],
            "dept_code": "OU",
            "enroll_date": presentation_start(presentation).isoformat(),
            "phone": mask_phone(raw_id),
            "email": mask_email(raw_id),
            "status": "在读",
        })
        enrollment_rows.append({
            "student_no": student_no_of(raw_id),
            "course_code": course_code,
            "teacher_no": teacher_no_of(group % TEACHER_POOL),
            "semester": semester_of(presentation),
            "score": "" if index % 7 == 0 else "%.2f" % rng.uniform(45, 99),
            "score_time": "" if index % 7 == 0 else presentation_start(presentation).isoformat() + " 10:00:00",
            "enroll_time": presentation_start(presentation).isoformat() + " 09:00:00",
            "status": "已退" if index % 11 == 0 else "已选",
        })
    assert len(offering_rows) == group_count
    return student_rows, course_rows, offering_rows, enrollment_rows


def main():
    parser = argparse.ArgumentParser(description="OULAD → 本系统 clean CSV")
    parser.add_argument("--raw-dir", default=RAW_DIR)
    parser.add_argument("--clean-dir", default=CLEAN_DIR)
    parser.add_argument("--generate", type=int, default=0, help="生成 N 行合成数据（离线降级方案）")
    args = parser.parse_args()

    if args.generate > 0:
        student_rows, course_rows, offering_rows, enrollment_rows = build_synthetic(args.generate)
        source = "合成数据（--generate %d，seed=%d）" % (args.generate, SEED)
    else:
        student_rows, course_rows, offering_rows, enrollment_rows = build_from_oulad(args.raw_dir)
        source = "OULAD（Open University Learning Analytics Dataset）"

    write_csv(os.path.join(args.clean_dir, "student.csv"), STUDENT_COLUMNS, student_rows)
    write_csv(os.path.join(args.clean_dir, "course.csv"), COURSE_COLUMNS, course_rows)
    write_csv(os.path.join(args.clean_dir, "offering.csv"), OFFERING_COLUMNS, offering_rows)
    write_csv(os.path.join(args.clean_dir, "enrollment.csv"), ENROLLMENT_COLUMNS, enrollment_rows)

    summary = {
        "source": source,
        "student": len(student_rows),
        "course": len(course_rows),
        "offering": len(offering_rows),
        "enrollment": len(enrollment_rows),
        "total_rows": len(student_rows) + len(course_rows) + len(offering_rows) + len(enrollment_rows),
        "enrollment_scored": sum(1 for r in enrollment_rows if r["score"] != ""),
        "enrollment_dropped": sum(1 for r in enrollment_rows if r["status"] == "已退"),
    }
    with open(os.path.join(args.clean_dir, "summary.json"), "w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)

    print("数据来源:", summary["source"])
    for key in ("student", "course", "offering", "enrollment"):
        print("  %-10s %d 行" % (key, summary[key]))
    print("  %-10s %d 行" % ("合计", summary["total_rows"]))
    print("已出分选课:", summary["enrollment_scored"], " 已退选课:", summary["enrollment_dropped"])


if __name__ == "__main__":
    main()
