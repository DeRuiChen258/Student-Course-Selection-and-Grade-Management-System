"""角色裁剪：应用层角色决定可见页面与可用动作。"""

ROLES = ("ADMIN", "TEACHER", "STUDENT")

ROLE_LABEL = {"ADMIN": "管理员", "TEACHER": "教师", "STUDENT": "学生"}

PAGE_ROLES = {
    "dashboard": ("ADMIN", "TEACHER", "STUDENT"),
    "tables": ("ADMIN", "TEACHER", "STUDENT"),
    "query": ("ADMIN", "TEACHER", "STUDENT"),
    "students": ("ADMIN",),
    "teachers": ("ADMIN",),
    "courses": ("ADMIN", "TEACHER"),
    "offerings": ("ADMIN", "TEACHER"),
    "enrollments": ("ADMIN", "TEACHER", "STUDENT"),
    "grades": ("ADMIN", "TEACHER"),
    "stats": ("ADMIN", "TEACHER", "STUDENT"),
    "permissions": ("ADMIN",),
    "logs": ("ADMIN", "TEACHER"),
    "io": ("ADMIN",),
    "settings": ("ADMIN", "TEACHER", "STUDENT"),
}

ACTION_ROLES = {
    "create": ("ADMIN",),
    "update": ("ADMIN", "TEACHER"),
    "delete": ("ADMIN",),
    "enroll": ("ADMIN", "STUDENT"),
    "drop": ("ADMIN", "STUDENT"),
    "score": ("ADMIN", "TEACHER"),
}


def can_view(role, page_key):
    return role in PAGE_ROLES.get(page_key, ())


def can_do(role, action):
    return role in ACTION_ROLES.get(action, ("ADMIN",))


def visible_pages(role):
    return [key for key, roles in PAGE_ROLES.items() if role in roles]
