"""生成设计说明书所需 6 张插图（300dpi）。用法：python3 tools/gen_figs.py [--only er]"""

import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(ROOT, "docs", "figs")

FONT_CANDIDATES = ["Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Serif CJK SC",
                   "AR PL UMing CN", "AR PL SungtiL GB", "WenQuanYi Zen Hei", "DejaVu Sans"]
FONT_FILES = ["/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
              "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
              "/usr/share/fonts/truetype/arphic/uming.ttc"]


def setup_font():
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in FONT_CANDIDATES:
        if name in available:
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name
    for path in FONT_FILES:
        if os.path.exists(path):
            font_manager.fontManager.addfont(path)
            name = font_manager.FontProperties(fname=path).get_name()
            plt.rcParams["font.family"] = name
            plt.rcParams["axes.unicode_minus"] = False
            return name
    raise SystemExit("未找到中文字体，请安装 fonts-noto-cjk 或 fonts-arphic-uming")


def new_canvas(width=11, height=8):
    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100 * height / width)
    ax.axis("off")
    return fig, ax


def box(ax, x, y, w, h, text, face="#eef3fb", edge="#2b5d8c", fontsize=10, weight="normal"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.6,rounding_size=1.2",
                                linewidth=1.2, edgecolor=edge, facecolor=face))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize,
            weight=weight, linespacing=1.5)


def diamond(ax, x, y, w, h, text, face="#fdf3e3", edge="#9a6b20", fontsize=9):
    ax.add_patch(plt.Polygon([[x + w / 2, y + h], [x + w, y + h / 2], [x + w / 2, y],
                              [x, y + h / 2]], closed=True, facecolor=face, edgecolor=edge, linewidth=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, linespacing=1.3)


def arrow(ax, start, end, text=None, style="-|>", color="#333333", fontsize=9, offset=(0, 1.2),
          rad=0.0, dashed=False):
    ax.add_patch(FancyArrowPatch(start, end, arrowstyle=style, mutation_scale=14, color=color,
                                 linewidth=1.1, connectionstyle=f"arc3,rad={rad}",
                                 linestyle="--" if dashed else "-"))
    if text:
        ax.text((start[0] + end[0]) / 2 + offset[0], (start[1] + end[1]) / 2 + offset[1], text,
                ha="center", va="center", fontsize=fontsize, color="#1f1f1f")


def save(fig, name):
    os.makedirs(FIG_DIR, exist_ok=True)
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已生成", os.path.relpath(path, ROOT))


def draw_er():
    fig, ax = new_canvas(12, 9)
    box(ax, 6, 62, 20, 10, "院系 department\n(dept_id)", face="#e8f4ea", edge="#3d7a4b")
    box(ax, 40, 62, 20, 10, "教师 teacher\n(teacher_id)", face="#e8f4ea", edge="#3d7a4b")
    box(ax, 74, 62, 20, 10, "课程 course\n(course_id)", face="#e8f4ea", edge="#3d7a4b")
    box(ax, 40, 38, 20, 10, "开课 course_offering\n(offering_id)", face="#fdeaea", edge="#9c3b3b")
    box(ax, 6, 38, 20, 10, "班级 class_group\n(class_id)", face="#e8f4ea", edge="#3d7a4b")
    box(ax, 6, 12, 20, 10, "学生 student\n(student_id)", face="#e8f4ea", edge="#3d7a4b")
    box(ax, 40, 12, 20, 10, "选课 enrollment\n(enrollment_id)", face="#fdeaea", edge="#9c3b3b")
    box(ax, 74, 38, 20, 10, "账号 sys_account\n(account_id)", face="#eef3fb", edge="#2b5d8c")
    box(ax, 74, 12, 20, 10, "审计日志 audit_log\n(log_id)", face="#eef3fb", edge="#2b5d8c")

    diamond(ax, 32, 64.5, 8, 6, "拥有")
    diamond(ax, 66, 64.5, 8, 6, "开设")
    diamond(ax, 32, 40.5, 8, 6, "归属")
    diamond(ax, 32, 14.5, 8, 6, "选修")
    diamond(ax, 66, 40.5, 8, 6, "承担")

    arrow(ax, (26, 67), (32, 67), "1", fontsize=8, offset=(0, 1.0))
    arrow(ax, (40, 67), (46, 67), "N", fontsize=8, offset=(0, 1.0))
    arrow(ax, (60, 67), (66, 67), "1", fontsize=8, offset=(0, 1.0))
    arrow(ax, (74, 67), (80, 67), "N", fontsize=8, offset=(0, 1.0))
    arrow(ax, (16, 62), (16, 48), "1", fontsize=8, offset=(-1.6, 0))
    arrow(ax, (26, 43), (32, 43), "N", fontsize=8, offset=(0, 1.0))
    arrow(ax, (40, 43), (46, 43), "1", fontsize=8, offset=(0, 1.0))
    arrow(ax, (60, 43), (66, 43), "N", fontsize=8, offset=(0, 1.0))
    arrow(ax, (16, 38), (16, 22), "1", fontsize=8, offset=(-1.6, 0))
    arrow(ax, (26, 17), (32, 17), "N", fontsize=8, offset=(0, 1.0))
    arrow(ax, (40, 17), (46, 17), "M", fontsize=8, offset=(0, 1.0))
    arrow(ax, (60, 17), (66, 17), "1", fontsize=8, offset=(0, 1.0))
    arrow(ax, (50, 38), (50, 22), "N", fontsize=8, offset=(1.6, 0))
    arrow(ax, (84, 38), (84, 22), "1:1", fontsize=8, offset=(2.2, 0), dashed=True)
    arrow(ax, (60, 21), (74, 21), "记录", fontsize=8, offset=(0, 1.2), dashed=True)

    ax.text(50, 78, "图：学生选课与成绩管理系统 ER 图（9 个实体、8 组联系）", ha="center",
            fontsize=12, weight="bold")
    save(fig, "er_diagram.png")


def draw_relation():
    fig, ax = new_canvas(14, 11)
    width, height = 24, 19
    columns = [2, 38, 74]
    rows = [55, 30, 5]
    layout = {
        "department": (0, 0), "teacher": (1, 0), "class_group": (2, 0),
        "course": (0, 1), "course_offering": (1, 1), "student": (2, 1),
        "audit_log": (0, 2), "sys_account": (1, 2), "enrollment": (2, 2),
    }
    content = {
        "department": ("department", "dept_id  PK\ndept_code, dept_name\noffice, phone"),
        "teacher": ("teacher", "teacher_id  PK\nteacher_no, teacher_name, gender,\ntitle, dept_id  FK\nhire_date, phone, email"),
        "class_group": ("class_group", "class_id  PK\nclass_code, class_name,\ngrade_year, dept_id  FK\nadvisor_teacher_id  FK"),
        "course": ("course", "course_id  PK\ncourse_code, course_name,\ncredit, hours, course_type,\ndept_id  FK"),
        "course_offering": ("course_offering", "offering_id  PK\ncourse_id  FK, teacher_id  FK\nsemester, capacity, enrolled_count\nclassroom, open_time"),
        "student": ("student", "student_id  PK\nstudent_no, student_name, gender,\nbirth_date, class_id  FK\nenroll_date, phone, email, status"),
        "audit_log": ("audit_log", "log_id  PK\ntable_name, action, record_id,\noperator, action_time, detail"),
        "sys_account": ("sys_account", "account_id  PK\nusername, password_hash, role,\nstudent_id  FK, teacher_id  FK\nlast_login"),
        "enrollment": ("enrollment", "enrollment_id  PK\nstudent_id  FK, offering_id  FK\nenroll_time, score, score_time\nstatus"),
    }
    for name, (column, row) in layout.items():
        x, y = columns[column], rows[row]
        title, body = content[name]
        box(ax, x, y, width, height, "", face="#ffffff", edge="#000000")
        ax.text(x + width / 2, y + height - 3.4, title, ha="center", va="center",
                fontsize=10.5, weight="bold")
        ax.text(x + width / 2, y + (height - 7) / 2, body, ha="center", va="center",
                fontsize=8.2, linespacing=1.55)

    def label(text, x, y):
        ax.text(x, y, text, ha="center", va="center", fontsize=7.6)

    def link(points, text, text_position):
        for index in range(len(points) - 1):
            arrow(ax, points[index], points[index + 1], None, color="#000000",
                  style="-|>" if index == len(points) - 2 else "-")
        label(text, *text_position)

    link([(38, 70), (26, 70)], "dept_id", (32, 67.6))
    link([(86, 74), (86, 76.2), (14, 76.2), (14, 74)], "dept_id", (50, 75.3))
    link([(8, 49), (8, 55)], "dept_id", (11.4, 52))
    link([(74, 64), (62, 64)], "advisor_teacher_id", (68, 66.9))
    link([(86, 49), (86, 55)], "class_id", (89.2, 52))
    link([(44, 49), (44, 55)], "teacher_id", (48.4, 52))
    link([(38, 44), (26, 44)], "course_id", (34.4, 46.6))
    link([(80, 24), (80, 30)], "student_id", (83.2, 27))
    link([(74, 22), (68, 22), (68, 36), (62, 36)], "offering_id", (71.6, 28.5))
    link([(56, 24), (56, 26.4), (92, 26.4), (92, 30)], "student_id", (62, 28.3))
    link([(38, 12), (29, 12), (29, 62), (38, 62)], "teacher_id", (34.4, 41.4))

    ax.text(50, 77.6, "9 个关系模式与外键引用（PK 主键，FK 外键）", ha="center", va="center",
            fontsize=12, weight="bold")
    save(fig, "relation_schema.png")


def draw_arch():
    fig, ax = new_canvas(11, 8)
    box(ax, 10, 78, 80, 12, "表现层 ui/console（14 个类）\n菜单分发、输入校验、表格输出", face="#eef3fb")
    box(ax, 10, 58, 80, 12, "业务层 service（8 个服务 + 3 个 DTO）\n业务规则、事务边界、错误码映射", face="#e8f4ea")
    box(ax, 10, 38, 80, 12, "数据访问层 dao（BaseDao + 9 个 DAO）\nPreparedStatement、RowMapper、参数绑定", face="#fdf3e3")
    box(ax, 10, 18, 80, 12, "数据库 MySQL 8.4（edu_system）\n9 表、4 视图、3 过程、2 函数、5 触发器", face="#fdeaea")

    arrow(ax, (50, 78), (50, 70), "调用", fontsize=9, offset=(4.5, 0))
    arrow(ax, (50, 58), (50, 50), "SQL 与参数", fontsize=9, offset=(9.0, 0))
    arrow(ax, (50, 38), (50, 30), "JDBC", fontsize=9, offset=(4.0, 0))
    arrow(ax, (24, 30), (24, 38), "结果集", fontsize=8, offset=(-5.0, 0), dashed=True)
    arrow(ax, (24, 50), (24, 58), "领域对象", fontsize=8, offset=(-5.8, 0), dashed=True)
    arrow(ax, (24, 70), (24, 78), "异常与错误码", fontsize=8, offset=(-7.0, 0), dashed=True)

    ax.text(50, 53, "事务边界：Tx.runInTx（选课、退课、成绩、学生增删改）", ha="center", fontsize=9,
            color="#9c3b3b")
    ax.text(50, 95, "图：系统分层架构与异常流", ha="center", fontsize=12, weight="bold")
    save(fig, "architecture.png")


def draw_modules():
    fig, ax = new_canvas(11, 8)
    groups = [
        ("学生模块", "F01 新生入学\nF02 信息修改\nF03 信息删除\nF04 信息查询"),
        ("教师模块", "F09 教师增删改查"),
        ("课程模块", "F05 课程录入\nF06 信息修改\nF07 信息删除\nF08 信息查询"),
        ("开课模块", "F10 新建开课\nF10 容量调整"),
        ("选课模块", "F11 学生选课\nF12 学生退课\nF15 课表与名单"),
        ("成绩模块", "F13 成绩录入\nF14 成绩修改\n成绩分布统计"),
        ("报表模块", "F16 课程统计\nGPA 排名\n学期开课汇总"),
        ("维护模块", "演示数据初始化\n备份与恢复提示\n只读查询"),
    ]
    ax.text(50, 69, "学生选课与成绩管理系统 功能模块（F01–F16）", ha="center", va="center",
            fontsize=12, weight="bold")
    box(ax, 33, 58, 34, 7, "主菜单（ConsoleUI）", face="#ffffff", edge="#000000", fontsize=11,
        weight="bold")
    positions = [(2.5, 30), (26.5, 30), (50.5, 30), (74.5, 30),
                 (2.5, 4), (26.5, 4), (50.5, 4), (74.5, 4)]
    for (title, body), (x, y) in zip(groups, positions):
        box(ax, x, y, 21, 22, "", face="#ffffff", edge="#000000")
        ax.text(x + 10.5, y + 18.5, title, ha="center", va="center", fontsize=10.5, weight="bold")
        ax.text(x + 10.5, y + 9, body, ha="center", va="center", fontsize=9, linespacing=1.6)
    arrow(ax, (50, 57.4), (50, 54.8), "", color="#000000", style="-")
    arrow(ax, (13, 54.8), (85, 54.8), "", color="#000000", style="-")
    for x in (13, 37, 61, 85):
        arrow(ax, (x, 54.8), (x, 51.6), "", color="#000000")
    save(fig, "function_modules.png")


def draw_flow():
    fig, ax = new_canvas(10, 12)
    steps = [
        ("开始：enroll(studentNo, offeringId)", "#ffffff", "#666666"),
        ("Tx.runInTx 开启事务", "#eef3fb", "#2b5d8c"),
        ("校验学生存在且在读", "#eef3fb", "#2b5d8c"),
        ("SELECT ... FOR UPDATE 锁定开课行", "#fdf3e3", "#9a6b20"),
        ("是否重复选课？", "#fdeaea", "#9c3b3b"),
        ("已选人数是否小于容量？", "#fdeaea", "#9c3b3b"),
        ("INSERT enrollment（触发器校验并联动计数）", "#e8f4ea", "#3d7a4b"),
        ("COMMIT 提交", "#e8f4ea", "#3d7a4b"),
    ]
    y = 92
    for text, face, edge in steps:
        box(ax, 20, y - 8, 60, 8, text, face=face, edge=edge, fontsize=9.5)
        y -= 11
    arrow(ax, (50, 92), (50, 84))
    arrow(ax, (50, 81), (50, 73))
    arrow(ax, (50, 70), (50, 62))
    arrow(ax, (50, 59), (50, 51))
    arrow(ax, (50, 48), (50, 40))
    arrow(ax, (50, 37), (50, 29))
    arrow(ax, (50, 26), (50, 18))
    arrow(ax, (50, 15), (50, 7))
    ax.text(50, 5, "异常分支：E002 学生不存在 / E004 重复选课 / E005 名额已满 → ROLLBACK",
            ha="center", fontsize=9, color="#9c3b3b")
    arrow(ax, (20, 44), (6, 44), "", rad=0.2, dashed=True)
    arrow(ax, (20, 33), (6, 33), "", rad=0.2, dashed=True)
    save(fig, "enroll_flow.png")


def draw_object_map():
    fig, ax = new_canvas(11, 8)
    box(ax, 4, 44, 26, 40,
        "表（9）\ndepartment\nteacher\nclass_group\nstudent\ncourse\ncourse_offering\nenrollment\nsys_account\naudit_log",
        face="#e8f4ea", edge="#3d7a4b", fontsize=9)
    box(ax, 37, 66, 26, 18, "视图（4）\nv_student_profile\nv_offering_detail", face="#eef3fb", fontsize=9)
    box(ax, 37, 44, 26, 18, "视图（4）\nv_student_transcript\nv_course_stat", face="#eef3fb", fontsize=9)
    box(ax, 70, 66, 26, 18,
        "存储过程与函数（5）\np_enroll_student\np_drop_course\np_save_score\nf_gpa / f_offering_avg",
        face="#fdf3e3", edge="#9a6b20", fontsize=9)
    box(ax, 70, 44, 26, 18,
        "触发器（5）\ntrg_enrollment_bi/ai/bu/au\ntrg_student_ad", face="#fdeaea", edge="#9c3b3b", fontsize=9)
    box(ax, 4, 8, 92, 26,
        "索引与约束：9 个 UNIQUE + 8 个普通索引 + 7 个 CHECK + 11 个外键\n"
        "uk_student_no / idx_student_class / idx_offering_semester / idx_enroll_offering / ck_enroll_score ...",
        face="#f7f7f7", edge="#666666", fontsize=9.5)

    arrow(ax, (30, 72), (37, 74), "读取", fontsize=9, offset=(0, 1.4))
    arrow(ax, (30, 60), (37, 56), "读取", fontsize=9, offset=(0, 1.4))
    arrow(ax, (30, 68), (70, 74), "调用", fontsize=9, offset=(0, 3.2), rad=-0.1)
    arrow(ax, (30, 52), (70, 52), "联动维护", fontsize=9, offset=(0, 1.4))
    arrow(ax, (50, 44), (50, 34), "服务", fontsize=9, offset=(4.0, 0))
    save(fig, "db_object_map.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default=None, help="只重绘某一张：er/relation/arch/modules/flow/object")
    args = parser.parse_args()
    font = setup_font()
    print("使用字体:", font)
    actions = {
        "er": draw_er,
        "relation": draw_relation,
        "arch": draw_arch,
        "modules": draw_modules,
        "flow": draw_flow,
        "object": draw_object_map,
    }
    if args.only:
        actions[args.only]()
    else:
        for action in actions.values():
            action()


if __name__ == "__main__":
    main()
