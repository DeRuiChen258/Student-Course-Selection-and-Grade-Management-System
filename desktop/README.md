# 学生选课与成绩管理系统 · 桌面端（Python + PySide6）

《数据库原理与应用》大作业的**图形界面展示层**，与 `../学生选课与成绩管理系统/`（Java + JDBC
控制台版，109 文件提交物）共用同一个 `edu_system` 数据库。本项目不修改提交物的任何文件，
只把同一个库里的表、视图、存储过程、触发器、索引与权限矩阵可视化，用于答辩现场演示。

## 一、技术栈

| 项目 | 版本 | 说明 |
| --- | --- | --- |
| Python | 3.12.13 | 独立 venv，不污染系统环境 |
| PySide6 | 6.8.3 | Qt 6.8 LTS 线，含 QtCharts |
| PyMySQL | 1.1.1 | 纯 Python 驱动，手写参数化 SQL（提交物红线禁止 ORM） |
| openpyxl | 3.1.5 | Excel 导入导出 |
| cryptography | 50.0.1 | MySQL 8 `caching_sha2_password` 认证 |
| PyInstaller | 6.11.1 | one-folder 打包 |
| MySQL | 8.4.11 | 用户态实例 127.0.0.1:3307，模拟数据集 |

## 二、快速开始

```bash
# ① 依赖（首次）
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements.txt
# 没有 uv 时：python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt

# ② 演示数据（会重建库；重跑即还原演示数据）
cd ../学生选课与成绩管理系统 && bash scripts/init_db.sh -u root -P 3307 && cd ../edu_desktop

# ③ 启动
bash run.sh
# 演示账号：admin / Admin@123 · teacher01 / Teacher@123 · student01 / Student@123

# ④ 自检与截图
QT_QPA_PLATFORM=offscreen .venv/bin/python tools/selfcheck.py
QT_QPA_PLATFORM=offscreen .venv/bin/python tools/capture_pages.py

# ⑤ 打包
bash build_exe.sh && ./dist/EduDesktop/EduDesktop

# ⑥ 安装桌面图标 + 启动器（应用菜单与桌面各一份）
bash install_desktop_entry.sh
```

连接参数默认从 `../学生选课与成绩管理系统/config/db.properties` 读取（不复制口令）；
在界面里保存连接后写入 `config/connection.json`（权限 600，已加入 `.gitignore`）。

## 三、目录结构

```text
edu_desktop/
├── main.py                    入口：日志 / 主题 / 连接 / 登录
├── run.sh / build_exe.sh      运行与打包
├── install_desktop_entry.sh   生成图标 + 安装桌面启动器（应用菜单与桌面）
├── config/                    连接配置模板与本机配置
├── app/                       上下文、路由表、实体规格、主题、功能标注、角色裁剪
├── db/                        连接池、DatabaseManager、事务、SQL 追踪、6 个 DAO
├── services/                  业务服务：实体 CRUD、选课退课成绩、报表、账号、导入导出
├── models/                    表格模型与声明式实体规格（FieldSpec / FilterSpec）
├── utils/                     配置、日志、异步执行器、校验、格式化、导入导出
├── ui/
│   ├── main_window.py         主窗口：工具栏 / 导航 / 工作区 / 详情抽屉 / SQL 抽屉 / 状态栏
│   ├── pages/                 14 个功能页面
│   ├── dialogs/               登录 / 连接 / 表单 / 选课 / 成绩 / 导入导出 / 帮助
│   └── widgets/               页头、表格、筛选条、分页、SQL 预览、空态、忙态、Toast、指标卡、图表
├── resources/                 light.qss / dark.qss / icon.png / icons（16–512 多尺寸）
├── tools/                     selfcheck.py（37 项自检）/ capture_pages.py（14 张截图）
└── out/screenshots/           答辩与报告用截图
```

## 四、功能对照（F01–F16）

| 编号 | 功能 | 界面入口 | 对应数据库对象 |
| --- | --- | --- | --- |
| F01 | 学生信息新增 | 学生管理 → 新增 | `student`、UNIQUE `uk_student_no` |
| F02 | 学生信息修改 | 学生管理 → 编辑 | `UPDATE student` + 变更前后对比 |
| F03 | 学生信息删除 | 学生管理 → 删除 | `enrollment` CASCADE、`trg_student_ad` 写审计 |
| F04 | 学生信息查询 | 学生管理 / 查询与筛选 | `student ⋈ class_group ⋈ department` |
| F05 | 课程录入 | 课程管理 → 新增 | `course`、CHECK 学分 / 学时 |
| F06 | 课程信息修改 | 课程管理 → 编辑 | UNIQUE `uk_course_code` |
| F07 | 课程信息删除 | 课程管理 → 删除 | `course_offering` RESTRICT 保护 |
| F08 | 课程信息查询 | 课程管理 / 数据表浏览 | `course ⋈ department` |
| F09 | 教师信息管理 | 教师管理 | `teacher`、UNIQUE `uk_teacher_no` |
| F10 | 开课管理与容量调整 | 开课管理 | `uk_offering`、CHECK `ck_offering_enrolled` |
| F11 | 学生选课 | 选课与成绩 → 学生选课 | `p_enroll_student`、`trg_enrollment_bi/ai` |
| F12 | 学生退课 | 选课与成绩 → 学生退课 | `p_drop_course`、`trg_enrollment_au` |
| F13 | 成绩录入 | 成绩管理 → 录入 / 修改成绩 | `p_save_score`、`trg_enrollment_bu` |
| F14 | 成绩修改 | 同上（选中已出分学生） | `score_time` 自动刷新 |
| F15 | 选课信息查询 | 学生课表 / 开课名单 | `v_student_transcript`、`v_offering_detail` |
| F16 | 统计报表 | 统计分析（6 个页签） | `v_course_stat`、`f_gpa`、`GROUP BY` 聚合 |

## 五、答辩亮点（对应设计说明 §10.6）

1. **SQL 预览面板**：每次操作显示数据库真正收到的语句（参数内联）、耗时与影响行数。
2. **对象自检卡片**：表 9 / 视图 4 / 触发器 5 / 例程 5 / 显式索引 8 / 全部索引 23，与 `init_db.sh` 输出一致。
3. **事务与触发器可视化**：选课 1/2 → 2/2 由 `trg_enrollment_ai` 联动，退课回补，满员回显 40005。
4. **权限矩阵 + 越权实测**：4 类数据库账号授权可视化；以 `edu_teacher` 执行越权 UPDATE 回显真实 `ERROR 1142`。
5. **约束提示全覆盖**：1062 / 1451 / 1452 / 3819 / SIGNAL（E004、E005、E007）全部翻译成中文并保留原始错误码。
6. **索引效果对比**：同一统计 SQL 使用 / 忽略 `idx_enroll_offering` 的 EXPLAIN 并排对照。
7. **三层主从联跳**：院系 → 班级 → 学生 → 选课与成绩，详情抽屉展示外键去向与约束。
8. **配置驱动界面**：字段中文名与约束说明取自 `information_schema`，不是写死在界面里的文案。

## 六、验收记录（本机实测）

```text
QT_QPA_PLATFORM=offscreen .venv/bin/python tools/selfcheck.py
汇总：通过 37 / 37，失败 0

QT_QPA_PLATFORM=offscreen .venv/bin/python tools/capture_pages.py
共生成 14 张截图，目录：out/screenshots

bash build_exe.sh
产物：dist/EduDesktop/EduDesktop（223 MB，one-folder，实测可启动）
```

自检覆盖：连接与版本、9 表 / 4 视图 / 5 触发器 / 5 例程、14 个页面实例化、
F01–F10 增删改查、F11–F14 事务与错误码（40001 / 40004 / 40005 / 40007 / 40008）、
F15 课表与 GPA、F16 五类统计与 EXPLAIN、权限矩阵与 1142、CSV/Excel 导出与映射导入、
自检数据清理与审计留痕。

## 七、已知限制（如实说明）

1. 界面层为**独立展示层**，提交物仍是 Java 控制台版；本目录不计入 109 文件清单（红线 §11(6)）。
2. `audit_log.operator` 记录的是触发器 DEFINER（本机为 `root`），这是 MySQL 存储程序按
   DEFINER 执行的既有语义，不是界面写入的字段。
3. MySQL 8.4 未在 `information_schema` 暴露例程级授权，`mysql.procs_priv` 对应用账号不可读
   （实测 1142），因此权限页以**表级 + 模式级**授权呈现，例程权限由越权实测间接验证；
   若配置了可选维护连接（`maintenance_user`），表级授权矩阵会完整显示。
4. 演示数据集为 `sql/07_seed_data.sql` 的模拟数据（20 学生 / 15 开课 / 82 选课）。
   若要演示大数据集分页，可另跑 `scripts/import_dataset.sh` 导入 OULAD 数据。
5. 打包产物为 one-folder（启动快、稳定性高）；未做代码签名与安装包。
6. 图形界面未参与提交物 `scripts/test.sh` 的自动化验收，测试口径仍以控制台版为准。

## 八、桌面启动器与应用图标

`install_desktop_entry.sh` 会完成三件事，重复执行可用来刷新路径：

1. 由 `tools/make_icon.py` 把源图居中裁剪为正方形并平滑缩放，
   生成 `resources/icon.png`（512）与 `resources/icons/edu-desktop_{16..512}.png`；
2. 把 8 个尺寸安装到 `~/.local/share/icons/hicolor/*/apps/edu-desktop.png` 主题目录；
3. 写入启动器 `~/.local/share/applications/edu-desktop.desktop`，
   并复制到桌面目录（本机 `XDG_DESKTOP_DIR` 指向家目录 `~/`，因此同时放 `~/` 与 `~/Desktop/`）。

```bash
bash install_desktop_entry.sh                    # 使用默认源图
bash install_desktop_entry.sh /path/to/icon.png  # 换一张图重装
```

启动器要点：`Exec` 指向 `run.sh`，`Terminal=false`，`Icon` 用绝对路径（避免图标缓存未刷新），
`StartupWMClass=edu-desktop` 与 `main.py` 里的 `setDesktopFileName("edu-desktop")` 对应，
保证任务栏与图标正确归组。安装后用 `desktop-file-validate` 校验无告警；
实测 `gtk-launch edu-desktop` 可直接拉起应用。

首次点击桌面图标时，GNOME 可能提示「不受信任的启动器」，选择「允许启动」即可
（脚本已尝试用 `gio set ... metadata::trusted true` 预先标记）。
