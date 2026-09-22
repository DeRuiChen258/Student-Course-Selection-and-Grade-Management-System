-- 一键重建：在项目根目录执行 mysql -u root < sql/99_rebuild_all.sql
-- 与 scripts/init_db.sh 的分工：本文件供人工在 mysql 客户端内核一键还原，脚本供自动化流水线使用

SOURCE sql/00_create_database.sql;
SOURCE sql/01_schema_tables.sql;
SOURCE sql/02_schema_indexes.sql;
SOURCE sql/03_views.sql;
SOURCE sql/04_procedures.sql;
SOURCE sql/05_triggers.sql;
SOURCE sql/06_privileges.sql;
SOURCE sql/07_seed_data.sql;

SELECT CONCAT('重建完成：表=', (SELECT COUNT(*) FROM information_schema.tables
                               WHERE table_schema = 'edu_system' AND table_type = 'BASE TABLE'),
              ' 视图=', (SELECT COUNT(*) FROM information_schema.views WHERE table_schema = 'edu_system'),
              ' 触发器=', (SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_schema = 'edu_system'),
              ' 例程=', (SELECT COUNT(*) FROM information_schema.routines WHERE routine_schema = 'edu_system')) AS 汇总;
