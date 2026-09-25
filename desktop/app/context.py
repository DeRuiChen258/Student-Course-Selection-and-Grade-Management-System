"""全局状态：连接、角色、当前账号与后台执行器。"""

import logging

from PySide6.QtCore import QObject, Signal

from db import DatabaseManager
from services import (AuthService, EnrollmentService, EntityService, IoService,
                      MetaService, ReportService)
from utils import config as config_util
from utils.async_runner import AsyncRunner
from .permissions import ROLE_LABEL, can_do, can_view

log = logging.getLogger(__name__)


class AppContext(QObject):
    connectionChanged = Signal(dict)
    roleChanged = Signal(str)
    tracesUpdated = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = config_util.load_config()
        self.profile_name, self.profile = config_util.active_profile(self.config)
        self.db = DatabaseManager(self.profile, pool_size=5)
        self.db.add_trace_listener(self.tracesUpdated.emit)
        self.runner = AsyncRunner(self, max_threads=4)
        self.account = None
        self.role = "ADMIN"
        self.meta = MetaService(self.db)
        self.entities = EntityService(self.db)
        self.enrollment = EnrollmentService(self.db)
        self.report = ReportService(self.db)
        self.auth = AuthService(self.db)
        self.io = IoService(self.db)
        self._maintenance = None
        self._maintenance_checked = False

    def maintenance_db(self):
        """可选的维护连接：用于读取完整权限矩阵（配置缺失或连不上时返回 None）。"""
        if self._maintenance_checked:
            return self._maintenance
        self._maintenance_checked = True
        user = self.profile.get("maintenance_user")
        if not user:
            return None
        profile = dict(self.profile)
        profile["user"] = user
        profile["password"] = self.profile.get("maintenance_password", "")
        candidate = DatabaseManager(profile)
        try:
            candidate.health()
        except Exception:
            candidate.close()
            log.info("维护连接不可用，权限矩阵回退到应用账号可见范围")
            self._maintenance = None
        else:
            self._maintenance = candidate
        return self._maintenance

    def switch_profile(self, name, profile):
        self.profile_name = name
        self.profile = dict(profile)
        self.config.setdefault("profiles", {})[name] = dict(profile)
        self.config["active"] = name
        config_util.save_config(self.config)
        self.db.configure(self.profile)
        self.entities.clear_cache()
        self.meta.clear_cache()
        self.connectionChanged.emit(dict(self.profile))

    def set_account(self, account):
        self.account = account
        self.role = (account or {}).get("role") or "ADMIN"
        self.roleChanged.emit(self.role)

    @property
    def role_label(self):
        return ROLE_LABEL.get(self.role, self.role)

    @property
    def username(self):
        return (self.account or {}).get("username", "未登录")

    def can_view(self, page_key):
        return can_view(self.role, page_key)

    def can_do(self, action):
        return can_do(self.role, action)

    def shutdown(self):
        self.runner.wait(2000)
        if self._maintenance is not None:
            self._maintenance.close()
        self.db.close()
