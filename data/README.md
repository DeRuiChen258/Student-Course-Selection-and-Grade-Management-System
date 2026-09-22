# 数据集台账

## 一、基本信息

| 项目 | 内容 |
| --- | --- |
| 数据集名称 | Open University Learning Analytics Dataset（OULAD） |
| 发布方 | The Open University（英国开放大学） |
| 官方页面 | https://research.stem.open.ac.uk/ouanalyse/dataset/ |
| 官方直链 | `http://schools.stem.open.ac.uk/cdn/files/anonymisedData.zip`（2026-09-22 实测返回 404） |
| 实际获取地址 | `https://raw.githubusercontent.com/gopi-0707/OULAD-Analysis/main/<文件名>`（官方 CSV 镜像） |
| 许可协议 | CC BY 4.0（署名 4.0 国际） |
| 获取日期 | 2026-09-22 |
| 引用要求 | 使用或再分发时须署名 The Open University，并引用 Kuzilek J, Hlosta M, Zdrahal Z. Open University Learning Analytics dataset[J]. Scientific Data, 2017, 4: 170171. |
| 用途 | 分页查询、索引命中对比、统计报表与性能演示（不参与自动化测试） |

## 二、原始文件清单（data/raw/）

| 文件 | 行数 | 字段数 | 文件大小 | sha256 |
| --- | --- | --- | --- | --- |
| courses.csv | 22 | 3 | 526 字节 | `4f16eee7454b15e109b0a21a0e43be820e6846ed6f9301bb7feb5ab5ad737a75` |
| assessments.csv | 206 | 6 | 8200 字节 | `8cc738fb88ad760571d6f2a23059bfee0ffcae3bcd830514c9cbd5c6d5a046f1` |
| vle.csv | 6364 | 6 | 260126 字节 | `d1b28303dea802ad87b4484e1196e878e06824850b9a4fe8aa34693439fe87e9` |
| studentInfo.csv | 32593 | 12 | 3461652 字节 | `7e6f3e474a5eee00639d2a414a6c7e928745823c2d2c2563ca1780145f99b0d6` |
| studentRegistration.csv | 32593 | 5 | 1109984 字节 | `0d32676285372aaf2e7a80304e5b274b4fba24313e2ca4c04317225e1ec90170` |
| studentAssessment.csv | 173912 | 5 | 5690310 字节 | `fd5320786328d05af841ee7dd4b5871b9dada3b9fe9d6a3642b2f42635510a6e` |

下载与校验命令：

```bash
bash scripts/fetch_dataset.sh                 # 默认下载到 data/raw 并逐文件校验 sha256
sha256sum data/raw/*.csv                      # 应与上表一致
```

原始数据缓存目录可自行指定（例如 `/path/to/SCUT_DB/oulad/`，含 `SHA256SUMS.txt`），
`data/raw/*.csv` 为项目内副本；两者都不进入版本库（`.gitignore` 已忽略）。

## 三、字段映射（原始字段 → 本系统字段）

| 原始文件 | 原始字段 | 本系统对象 | 本系统字段 | 处理规则 |
| --- | --- | --- | --- | --- |
| studentInfo.csv | id_student | student | student_no | 前缀 90 + 左侧补零到 10 位 → 12 位数字 |
| studentInfo.csv | gender | student | gender | M→男，F→女 |
| studentInfo.csv | age_band | student | birth_date | 按年龄区间回推（0-35→注册年-25，35-55→-40，55<=→-60） |
| studentInfo.csv | code_module / code_presentation | class_group | class_code / class_name | `OU` + 模块 + 期次，如 OUAAA2013J |
| studentInfo.csv | final_result | student | status | Withdrawn→退学，其余→在读 |
| studentRegistration.csv | date_registration | student / enrollment | enroll_date / enroll_time | 期次起始日 + 偏移天数 |
| courses.csv | code_module | course | course_code / course_name | `OU` + 模块名，如 OUAAA |
| courses.csv | module_presentation_length | course | credit / hours | 学分=长度/60（截断到 0.5–10.0），学时=长度/2（截断到 8–200） |
| courses.csv | code_presentation | course_offering | semester | 2013J→2013-2014-1，2013B→2012-2013-2 |
| assessments.csv + studentAssessment.csv | score | enrollment | score | 同一学生同一期次全部作业成绩取平均，保留 2 位 |
| （派生） | —— | course_offering | capacity / enrolled_count | 每个期次按 300 人分块成教学班，容量 300 |
| （派生） | —— | teacher | teacher_no / teacher_name | 合成教师：90000001–90000012，姓名「数据集教师NN」 |

## 四、脱敏处理说明

1. 原始数据本身已由 The Open University 匿名化，不含姓名、手机号、邮箱、身份证号等直接身份信息。
2. 入库前进一步处理：姓名按学号哈希函数生成合成中文姓名；手机号由学号哈希生成；
   邮箱统一替换为 `s<学号>@stu.example.edu`；地区、教育背景、剥夺指数等人口学字段一律不导入。
3. 导入的学生学号统一以 `90` 开头，与课程演示数据（`2023…`）物理隔离，便于识别与清理。
4. `tools/prepare_dataset.py` 固定随机种子 20260921，重复执行输出一致，不含真实个人信息。

## 五、清洗结果（data/clean/）

| 文件 | 行数 | 对应表 | 说明 |
| --- | --- | --- | --- |
| student.csv | 28785 | student | 去重后的学生（按 id_student 唯一） |
| course.csv | 7 | course | 7 个模块 |
| offering.csv | 120 | course_offering | 22 个模块期次按 300 人分块后的教学班 |
| enrollment.csv | 32593 | enrollment | 选课与成绩，其中已出分 25820 条、已退 10156 条 |
| 合计 | 61505 | —— | 满足 ≥1 万行的要求 |

导入结果（2026-09-22 实测）：

```text
学生=28805 课程=19 开课=135 选课=32675 导入行数=28785
```

连续执行三次 `bash scripts/import_dataset.sh`，上述四个计数完全不变（幂等）。

## 六、幂等与回滚

1. 导入脚本先把 CSV 装入临时表，再「先更新、后插入」，因此重复执行不会新增行。
2. 导入前、导入后各执行一次 `scripts/backup.sh`，备份文件位于 `backup/`。
3. 需要回到纯演示数据时执行 `bash scripts/init_db.sh -u edu_app -p`（会重建库并只装载 07 号脚本的 20 名学生）。

## 七、许可与署名

本项目对 OULAD 的使用遵循 CC BY 4.0：在任何再分发或展示（包括设计说明书第 4 章与附录 C、
README 以及本文件）中均标注数据集名称、发布方、官方页面与获取日期，并引用原始论文。
原始 CSV 不随源码版本库分发，只保留下载脚本与校验值。
