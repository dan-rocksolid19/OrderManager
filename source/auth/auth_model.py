from datetime import datetime, timezone
from librepy.model.base_model import BaseModel
from librepy.peewee.peewee import (
    AutoField,
    CharField,
    BooleanField,
    DateTimeField,
    ForeignKeyField,
)

class User(BaseModel):
    id = AutoField()
    username = CharField(max_length=150, unique=True)
    password_hash = CharField(max_length=255)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "users"

class Role(BaseModel):
    id = AutoField()
    name = CharField(max_length=100, unique=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "roles"

class Permission(BaseModel):
    id = AutoField()
    code = CharField(max_length=100, unique=True)
    description = CharField(max_length=255, null=True)

    class Meta:
        table_name = "permissions"

class UserRole(BaseModel):
    user = ForeignKeyField(User, backref="user_roles", on_delete="CASCADE")
    role = ForeignKeyField(Role, backref="user_roles", on_delete="CASCADE")

    class Meta:
        table_name = "user_roles"
        indexes = (
            (("user", "role"), True),
        )

class RolePermission(BaseModel):
    role = ForeignKeyField(Role, backref="role_permissions", on_delete="CASCADE")
    permission = ForeignKeyField(Permission, backref="role_permissions", on_delete="CASCADE")

    class Meta:
        table_name = "role_permissions"
        indexes = (
            (("role", "permission"), True),
        )

class AuditLog(BaseModel):
    id = AutoField()
    username = CharField(max_length=150)
    success = BooleanField()
    message = CharField(max_length=255, null=True)
    timestamp = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "audit_logs" 