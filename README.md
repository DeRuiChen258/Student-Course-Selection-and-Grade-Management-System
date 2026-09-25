# 学生选课与成绩管理系统

《数据库原理与应用》大作业（类型一：数据库应用系统）。MySQL 8 存储数据，Java 控制台程序提供增删改查、
选课退课、成绩管理、统计报表与权限演示，配套建库脚本、开源大数据集、测试脚本与设计说明书。

## 一、环境要求

| 项目 | 要求 | 本机实测 |
| --- | --- | --- |
| 操作系统 | Linux / macOS / WSL | Ubuntu（中文环境） |
| JDK | 17 或更高（编译参数固定 `--release 17`） | OpenJDK 25.0.4 |
| MySQL | 8.0 或更高（InnoDB、utf8mb4） | 8.4.11 |
| Python | 3.8 或更高（仅生成图表与文档） | 3.12.13，matplotlib 3.11.1 |
| 文档转换 | LibreOffice（soffice） | /usr/bin/soffice |
| JDBC 驱动 | `lib/mysql-connector-j-9.1.0.jar` | 见 `lib/README.md` |

## 二、五步运行法

```bash
# ① 建库与创建 4 类账号（本机 root 为 socket 认证，必须用 sudo 执行一次）
sudo mysql < sql/00_create_database.sql

# ② 填写连接配置
cp config/db.properties.example config/db.properties   # 然后填写 db.password

# ③ 建表、建视图/过程/触发器并装载演示数据
bash scripts/init_db.sh -u edu_app -p

# ④ 编译
bash scripts/build.sh

# ⑤ 运行
bash scripts/run.sh
```

第 ③ 步真实输出（本机 2026-09-22 实测，实例 127.0.0.1:3307）：

```text
[完成] sql/01_schema_tables.sql
[完成] sql/02_schema_indexes.sql
[完成] sql/03_views.sql
[完成] sql/04_procedures.sql
[完成] sql/05_triggers.sql
[完成] sql/06_privileges.sql
[完成] sql/07_seed_data.sql
表=9 视图=4 触发器=5 例程=5 学生=20 开课=15 选课=82
下一步: bash scripts/build.sh && bash scripts/run.sh
```

第 ④ 步真实输出：

```text
源文件数量: 58
编译完成: out/classes 下 61 个 class 文件
```

## 三、数据集三步（可重复、幂等）

```bash
bash scripts/fetch_dataset.sh                 # 下载 OULAD 到 data/raw 并校验 sha256
python3 tools/prepare_dataset.py              # 字段映射、去重、脱敏 → data/clean/*.csv
bash scripts/import_dataset.sh                # 备份 → 导入 → 重新备份
```

本机实测：清洗后 4 个 CSV 合计 61505 行，导入后学生 28805、课程 19、开课 135、选课 32675；
连续执行三次导入，各表行数完全不变（幂等）。台账见 `data/README.md`。

离线环境可改用合成数据（代码链路完全相同）：

```bash
python3 tools/prepare_dataset.py --generate 12000
```

## 四、目录导航

| 目录 | 作用 |
| --- | --- |
| `sql/` | 建库、建表、索引、视图、过程、触发器、权限、演示数据、事务演示（11 个脚本） |
| `scripts/` | 建库、编译、运行、测试、冒烟、备份、数据集下载与导入、文档导出（9 个脚本） |
| `tools/` | 文档转换、图表生成、数据准备、提交自检（4 个 Python 工具） |
| `src/main/java/` | 入口、配置、数据访问、业务、交互四层共 58 个源文件 |
| `src/test/java/` | 6 个测试用例与断言工具（纯 JDK，无第三方测试框架） |
| `docs/` | 设计说明书源文件、演示脚本、6 张插图、docx 与 pdf 交付物 |
| `data/` | 数据集台账、原始 CSV、清洗后 CSV |
| `config/` | 连接配置模板与本机配置（后者被忽略） |

## 五、演示账号

| 用户名 | 角色 | 绑定 | 说明 |
| --- | --- | --- | --- |
| `admin` | ADMIN | —— | 全功能 |
| `teacher01` | TEACHER | 教师 10000001 | 只能录成绩、看报表 |
| `student01` | STUDENT | 学生 202301010001 | 只读 |

`admin` 的初始口令为 `Admin@123`，`teacher01` 为 `Teacher@123`，`student01` 为 `Student@123`，
口令以 `salt$SHA-256(salt+口令)` 形式存于 `sys_account`，可用 `util/PasswordUtils` 校验。

数据库账号（`edu_app` / `edu_teacher` / `edu_student` / `edu_readonly`）的口令由
`scripts/init_db.sh --app-password 口令` 或 `sql/00_create_database.sql` 顶部变量决定，
默认取 `config/db.properties` 的 `db.password`。

## 六、验收命令清单（真实执行过）

```bash
sudo mysql < sql/00_create_database.sql          # 4 个账号创建成功
bash scripts/init_db.sh -u edu_app -p            # 表=9 视图=4 触发器=5 例程=5 学生=20 选课=82
bash scripts/build.sh                            # 退出码 0，out/classes 61 个 class
bash scripts/test.sh                             # passed=6 failed=0
bash scripts/smoke_test.sh                       # 全绿，退出码 0
bash scripts/backup.sh                           # backup/edu_system_时间戳.sql，含 9 表 5 例程 5 触发器
bash scripts/export_docs.sh                      # docs/out 下 docx 与 pdf
python3 tools/check_submission.py                # 缺失文件数 0
bash scripts/fetch_dataset.sh && python3 tools/prepare_dataset.py && bash scripts/import_dataset.sh
```

## 七、恢复数据库

```bash
mysql -u edu_app -p edu_system < backup/edu_system_20260922_075005.sql
```

备份由 `mysqldump --single-transaction --routines --triggers --events` 生成，包含表结构与数据、
视图、存储过程、函数与触发器定义。

## 八、常见问题

| 现象 | 原因与处理 |
| --- | --- |
| `Access denied for user 'root'@'localhost'` | 本机 root 为 socket 认证，请用 `sudo mysql < sql/00_create_database.sql` |
| `[失败] lib/ 下没有 JDBC 驱动` | 按 `lib/README.md` 下载 `mysql-connector-j-9.1.0.jar` 后重试 |
| `public key retrieval is not allowed` | 确认 `db.params` 含 `allowPublicKeyRetrieval=true` |
| 忘记 edu_app 口令 | 重新执行 `sudo mysql < sql/00_create_database.sql` 会重建库与账号 |
| 无网络 | 使用 `python3 tools/prepare_dataset.py --generate 12000` 生成合成数据 |

## 九、已知不足（如实说明）

1. 未使用连接池，`ConnectionProvider` 为单连接复用，适合课程演示规模，不适合高并发服务。
2. 未做 Web 化与图形界面，界面是题目允许的控制台字符菜单。
3. 批量成绩导入是逐条事务，未做批量合并优化。
4. 大数据集仅用于查询与统计演示，导入后会覆盖演示数据的规模假设，需重新执行 `init_db.sh` 还原。

## 十、图形界面客户端（desktop/）

仓库除本控制台版以外，另含一套 **Python + PySide6 桌面端**，见 [`desktop/`](desktop/README.md)。
它不改动本目录（Java 提交物）的任何文件，只作为数据库可视化演示层，复用同一套
9 表 / 4 视图 / 3 过程 / 2 函数 / 5 触发器与 4 类数据库账号：

- 14 个功能页面，界面显式标注 F01–F16 功能归属；
- 选课 / 退课 / 成绩全部调用存储过程，触发器联动计数实时可见；
- 每次操作在 SQL 面板显示数据库真正收到的语句（参数内联）、耗时与影响行数；
- 表结构 / 索引 / 外键 / CHECK 约束读 `information_schema` 后在界面上可视化；
- 权限页展示 4 类数据库账号的授权矩阵，并可实测越权返回 `ERROR 1142`；
- 统计分析页含柱状 / 折线 / 饼图与 `EXPLAIN` 索引效果对比；
- 附带 37 项离屏自检（`desktop/tools/selfcheck.py`）与 14 张页面截图。

```bash
cd desktop
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python -r requirements.txt
bash run.sh          # 演示账号 admin / Admin@123
```
