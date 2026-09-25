"""配置管理：优先读 edu_desktop 自己的连接配置，缺失时复用 Java 提交物的 db.properties。"""

import json
import logging
import os
import re
import sys
from pathlib import Path

log = logging.getLogger(__name__)

JAVA_CONFIG = Path("学生选课与成绩管理系统") / "config" / "db.properties"


def app_root():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_path(relative):
    base = Path(getattr(sys, "_MEIPASS", app_root()))
    return base / relative


def config_file():
    return app_root() / "config" / "connection.json"


def java_properties_file():
    root = app_root()
    for candidate in (root / JAVA_CONFIG, root.parent / JAVA_CONFIG,
                      root / "config" / "db.properties"):
        if candidate.exists():
            return candidate
    return None


def read_properties(path):
    props = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        props[key.strip()] = value.strip()
    return props


def profile_from_properties(path):
    props = read_properties(path)
    if not props.get("db.host"):
        return None
    return {
        "label": f"Java 提交物配置（{Path(path).name}）",
        "host": props.get("db.host", "127.0.0.1"),
        "port": int(props.get("db.port", 3306) or 3306),
        "database": props.get("db.name", "edu_system"),
        "user": props.get("db.user", "edu_app"),
        "password": props.get("db.password", ""),
        "charset": "utf8mb4",
        "connect_timeout": 5,
        "page_size": int(props.get("app.page.size", 20) or 20),
        "maintenance_user": "root",
        "maintenance_password": "",
    }


def default_config():
    config = {"active": "demo3307", "profiles": {}}
    source = java_properties_file()
    profile = profile_from_properties(source) if source else None
    if profile:
        config["profiles"]["demo3307"] = profile
        config["profiles"]["system3306"] = dict(profile, label="系统实例 3306", port=3306)
    else:
        config["profiles"]["demo3307"] = {
            "label": "演示库 3307", "host": "127.0.0.1", "port": 3307,
            "database": "edu_system", "user": "edu_app", "password": "",
            "charset": "utf8mb4", "connect_timeout": 5,
        }
    return config


def load_config():
    path = config_file()
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if data.get("profiles"):
                return data
            log.warning("配置文件缺少 profiles，回退默认配置")
        except Exception:
            log.exception("配置文件解析失败，回退默认配置")
    return default_config()


def save_config(config):
    path = config_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def active_profile(config=None, key=None):
    config = config or load_config()
    profiles = config.get("profiles", {})
    name = key or config.get("active")
    profile = profiles.get(name)
    if not profile and profiles:
        name, profile = next(iter(profiles.items()))
    if not profile:
        raise RuntimeError("没有可用的数据库连接配置")
    return name, dict(profile)


def mask_password(profile):
    text = json.dumps(profile, ensure_ascii=False)
    return re.sub(r'("password"\s*:\s*")[^"]*(")', r"\1***\2", text)
