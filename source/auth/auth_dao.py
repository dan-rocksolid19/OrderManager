from datetime import datetime, timezone
from librepy.model.base_dao import BaseDAO
from librepy.auth.auth_model import User, Role, Permission, UserRole, RolePermission, AuditLog
from librepy.pybrex.values import pybrex_logger


class UserDAO(BaseDAO):
    def __init__(self, logger=None):
        super().__init__(User, logger or pybrex_logger(__name__))

    def get_by_username(self, username):
        return self.safe_execute(
            f"fetching user {username}",
            lambda: User.get_or_none(User.username == username)
        )

    def create(self, username, password_hash, roles=None, is_active=True):
        def op():
            user = User.create(
                username=username,
                password_hash=password_hash,
                is_active=is_active,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.logger.info(f"Created user {username} with ID {user.id}")
            
            if roles:
                self.logger.info(f"Assigning roles {roles} to user {username}")
                for r in roles:
                    role, created = Role.get_or_create(name=r)
                    self.logger.info(f"Role '{r}': ID={role.id}, created={created}")
                    
                    user_role, ur_created = UserRole.get_or_create(user=user, role=role)
                    self.logger.info(f"UserRole created={ur_created} for user {user.id} and role {role.id}")
                    
                # Verify role assignment
                assigned_roles = UserRole.select().where(UserRole.user == user.id)
                role_count = assigned_roles.count()
                self.logger.info(f"User {username} now has {role_count} role(s) assigned")
                
            return user
        return self.safe_execute("creating user", op)

    def set_active(self, user_id, is_active):
        return self.safe_execute(
            "updating user active flag",
            lambda: User.update(is_active=is_active, updated_at=datetime.now(timezone.utc)).where(User.id == user_id).execute(),
        )

    def assign_role(self, user_id, role_name):
        def op():
            role, _ = Role.get_or_create(name=role_name)
            user = User.get_by_id(user_id)
            UserRole.get_or_create(user=user, role=role)
            return True
        return self.safe_execute("assign role", op, default_return=False)

    def remove_role(self, user_id, role_name):
        def op():
            role = Role.get_or_none(Role.name == role_name)
            if role:
                UserRole.delete().where(UserRole.user == user_id, UserRole.role == role).execute()
            return True
        return self.safe_execute("remove role", op, default_return=False)

    def list_active_usernames(self):
        """
        Get list of usernames for all active users, ordered alphabetically.
        
        Returns:
            list: List of username strings, empty list on error
        """
        def query_func():
            users = self.model_class.select().where(
                self.model_class.is_active == True
            ).order_by(self.model_class.username)
            return [user.username for user in users]
        
        return self.safe_execute(
            "fetching active usernames", 
            query_func, 
            default_return=[]
        )

    def list_users(self, order_by=None):
        """
        Get list of all users with optional ordering.
        
        Args:
            order_by: Column to order by, defaults to username
            
        Returns:
            list: List of User objects, empty list on error
        """
        if order_by is None:
            order_by = self.model_class.username
            
        return self.safe_execute(
            "listing users",
            lambda: list(self.model_class.select().order_by(order_by)),
            default_return=[]
        )

    def deactivate(self, user_id):
        """
        Deactivate a user by setting is_active to False.
        
        Args:
            user_id: ID of user to deactivate
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_active(user_id, False)

    def reactivate(self, user_id):
        """
        Reactivate a user by setting is_active to True.
        
        Args:
            user_id: ID of user to reactivate
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.set_active(user_id, True)

    def update_user(self, user_id, username=None, is_active=None):
        """
        Update user fields.
        
        Args:
            user_id: ID of user to update
            username: New username (optional)
            is_active: New active status (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        def op():
            updates = {'updated_at': datetime.now(timezone.utc)}
            if username is not None:
                updates['username'] = username
            if is_active is not None:
                updates['is_active'] = is_active
            
            if len(updates) > 1:
                return self.model_class.update(**updates).where(self.model_class.id == user_id).execute()
            return 0
            
        return self.safe_execute("updating user", op, default_return=False)


class RoleDAO(BaseDAO):
    def __init__(self, logger=None):
        super().__init__(Role, logger or pybrex_logger(__name__))

    def get_by_name(self, name):
        return self.safe_execute("get role", lambda: Role.get_or_none(Role.name == name))

    def create(self, name):
        return self.safe_execute("create role", lambda: Role.get_or_create(name=name)[0])

    def list_all(self):
        return self.get_all(order_by=Role.name)

    def safe_delete(self, role_id):
        """
        Safely delete a role, but only if it's not referenced in UserRole.
        
        Args:
            role_id: ID of role to delete
            
        Returns:
            tuple: (success: bool, message: str)
        """
        def op():
            from librepy.auth.auth_model import UserRole
            
            user_count = UserRole.select().where(UserRole.role == role_id).count()
            if user_count > 0:
                return False, f"Cannot delete role: still assigned to {user_count} user(s)"
            
            deleted = Role.delete().where(Role.id == role_id).execute()
            if deleted > 0:
                return True, "Role deleted successfully"
            else:
                return False, "Role not found"
                
        result = self.safe_execute("deleting role", op, default_return=(False, "Error occurred"))
        return result if isinstance(result, tuple) else (False, "Unexpected error")

    def update_role(self, role_id, name):
        """
        Update role name.
        
        Args:
            role_id: ID of role to update
            name: New role name
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.safe_execute(
            "updating role",
            lambda: Role.update(
                name=name, 
                updated_at=datetime.now(timezone.utc)
            ).where(Role.id == role_id).execute(),
            default_return=False
        )


class PermissionDAO(BaseDAO):
    def __init__(self, logger=None):
        super().__init__(Permission, logger or pybrex_logger(__name__))

    def get_by_code(self, code):
        return self.safe_execute("get permission", lambda: Permission.get_or_none(Permission.code == code))

    def create(self, code, description=""):
        return self.safe_execute(
            "create permission",
            lambda: Permission.get_or_create(code=code, defaults={"description": description})[0],
        )

    def list_all(self):
        return self.get_all(order_by=Permission.code)

    def delete(self, code_or_id):
        """
        Delete a permission by code or ID.
        
        Args:
            code_or_id: Permission code (str) or ID (int) to delete
            
        Returns:
            tuple: (success: bool, message: str)
        """
        def op():
            from librepy.auth.auth_model import RolePermission
            
            if isinstance(code_or_id, str):
                permission = Permission.get_or_none(Permission.code == code_or_id)
            else:
                permission = Permission.get_or_none(Permission.id == code_or_id)
            
            if not permission:
                return False, "Permission not found"
            
            role_count = RolePermission.select().where(RolePermission.permission == permission.id).count()
            if role_count > 0:
                return False, f"Cannot delete permission: still assigned to {role_count} role(s)"
            
            deleted = Permission.delete().where(Permission.id == permission.id).execute()
            if deleted > 0:
                return True, "Permission deleted successfully"
            else:
                return False, "Permission not found"
                
        result = self.safe_execute("deleting permission", op, default_return=(False, "Error occurred"))
        return result if isinstance(result, tuple) else (False, "Unexpected error")


class AuditLogDAO(BaseDAO):
    def __init__(self, logger=None):
        super().__init__(AuditLog, logger or pybrex_logger(__name__))

    def record(self, username, success, message=""):
        return self.safe_execute(
            "record audit log",
            lambda: AuditLog.create(
                username=username,
                success=success,
                message=message,
                timestamp=datetime.now(timezone.utc),
            ),
        )

    def list_recent(self, limit=100):
        return self.safe_execute(
            "list recent audit logs",
            lambda: list(
                AuditLog.select().order_by(AuditLog.timestamp.desc()).limit(limit)
            ),
            default_return=[],
        ) 