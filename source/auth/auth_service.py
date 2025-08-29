import uuid
import hmac
import hashlib
import base64
import os
from datetime import datetime, timedelta, timezone

from librepy.utils.config_manager import ConfigManager
from librepy.auth.auth_dao import UserDAO, RoleDAO, AuditLogDAO, PermissionDAO
from librepy.auth.session import login as session_login, logout as session_logout
from librepy.auth import session
from librepy.auth.auth_exceptions import UserLockedError, UserNotFoundError, IncorrectPasswordError, UserInactiveError
from librepy.pybrex.values import pybrex_logger

_PBKDF2_ROUNDS_DEFAULT = 260000


class AuthService:
    def __init__(self):
        self._cfg = ConfigManager("auth.conf")
        self._user_dao = UserDAO()
        self._role_dao = RoleDAO()
        self._permission_dao = PermissionDAO()
        self._audit_dao = AuditLogDAO()
        self.logger = pybrex_logger(__name__)

    def _get_int(self, section, key, default):
        val = self._cfg.get_value(section, key, None)
        try:
            return int(val)
        except (TypeError, ValueError):
            return default

    def _get_lock_settings(self):
        max_attempts = self._get_int("security", "max_attempts", 5)
        lock_minutes = self._get_int("security", "lock_minutes", 15)
        return max_attempts, lock_minutes

    def _pbkdf2_hash(self, password: str, salt: bytes, rounds: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, rounds, dklen=32)

    def hash_password(self, plain: str, rounds: int = _PBKDF2_ROUNDS_DEFAULT) -> str:
        salt = os.urandom(16)
        dk = self._pbkdf2_hash(plain, salt, rounds)
        return f"{rounds}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

    def verify_password(self, plain: str, stored: str) -> bool:
        try:
            rounds_s, salt_b64, dk_b64 = stored.split("$")
            rounds = int(rounds_s)
            salt = base64.b64decode(salt_b64)
            expected = base64.b64decode(dk_b64)
        except Exception:
            return False
        calculated = self._pbkdf2_hash(plain, salt, rounds)
        return hmac.compare_digest(calculated, expected)

    def _normalize_ts(self, dt):
        """Ensure the datetime is timezone-aware (UTC). Accepts datetime or ISO string."""
        if dt is None:
            return None

        # Convert string timestamps that might have come from the DB default.
        if isinstance(dt, str):
            try:
                dt = datetime.fromisoformat(dt)
            except ValueError:
                try:
                    dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return None

        if isinstance(dt, datetime):
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        # If it's neither str nor datetime, we cannot normalize – skip it.
        return None

    def _failed_attempts(self, username, since):
        logs = self._audit_dao.list_recent(1000)
        count = 0
        for l in logs:
            if l.username != username or l.success:
                continue
            ts = self._normalize_ts(l.timestamp)
            if ts is None:
                continue
            if ts >= since:
                count += 1
        return count

    def is_locked(self, username):
        max_attempts, lock_minutes = self._get_lock_settings()
        window_start = datetime.now(timezone.utc) - timedelta(minutes=lock_minutes)
        return self._failed_attempts(username, window_start) >= max_attempts

    def _record_attempt(self, username, success, msg=""):
        self._audit_dao.record(username, success, msg)

    def authenticate(self, username, plain_password, remember=False):
        if self.is_locked(username):
            raise UserLockedError()
        with self._user_dao.database.connection_context():
            user = self._user_dao.get_by_username(username)
            if not user:
                self._record_attempt(username, False, "user not found")
                raise UserNotFoundError()
            if not self.verify_password(plain_password, user.password_hash):
                self._record_attempt(username, False, "bad password")
                if self.is_locked(username):
                    raise UserLockedError()
                raise IncorrectPasswordError()
            if not user.is_active:
                self._record_attempt(username, False, "inactive")
                raise UserInactiveError()
            self._record_attempt(username, True, "login ok")
            session_login(user)
            if remember:
                self._store_token(username)
        return user

    def _store_token(self, username):
        secret = self._cfg.get_value("remember", "secret", str(uuid.uuid4()))
        self._cfg.set_value("remember", "secret", secret)
        tok = str(uuid.uuid4())
        sig = hmac.new(secret.encode(), tok.encode(), hashlib.sha256).hexdigest()
        self._cfg.set_value("remember", "token", f"{username}:{tok}:{sig}")
        self._cfg.set_value("remember", "expires", (datetime.now(timezone.utc) + timedelta(days=14)).isoformat())
        self._cfg.save_config()

    def try_auto_login(self):
        token = self._cfg.get_value("remember", "token", None)
        if not token:
            return None
        try:
            username, tok, sig = token.split(":")
        except ValueError:
            return None
        secret = self._cfg.get_value("remember", "secret", "")
        expected = hmac.new(secret.encode(), tok.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected, sig):
            return None
        exp = self._cfg.get_value("remember", "expires", "")
        try:
            if datetime.fromisoformat(exp) < datetime.now(timezone.utc):
                return None
        except ValueError:
            return None
        user = self._user_dao.get_by_username(username)
        if user:
            session_login(user)
        return user

    def register(self, username, plain_password, roles=None):
        hashed = self.hash_password(plain_password)
        return self._user_dao.create(username, hashed, roles)

    def change_password(self, user_id, new_plain):
        hashed = self.hash_password(new_plain)
        return self._user_dao.safe_execute(
            "change password",
            lambda: self._user_dao.model_class.update(
                password_hash=hashed,
                updated_at=datetime.now(timezone.utc)
            ).where(self._user_dao.model_class.id == user_id).execute(),
        )

    def logout(self):
        session_logout()

    def login_required(self, func):
        def inner(*args, **kwargs):
            if current_user is None:
                raise PermissionError("login required")
            return func(*args, **kwargs)
        return inner

    def create_user(self, username, password, roles=None, is_active=True):
        """
        Create a new user with optional roles.
        
        Args:
            username: Username for the new user
            password: Plain text password
            roles: List of role names to assign (optional)
            is_active: Whether user should be active (default True)
            
        Returns:
            User object if successful, None otherwise
        """
        hashed = self.hash_password(password)
        return self._user_dao.create(username, hashed, roles, is_active)

    def update_user(self, user_id, username=None, is_active=None):
        """
        Update user information.
        
        Args:
            user_id: ID of user to update
            username: New username (optional)
            is_active: New active status (optional)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if is_active is False:
            if self._is_current_user(user_id):
                self.logger.warning(f"User {user_id} cannot deactivate themselves")
                return False
                
            if not self._can_deactivate_user(user_id):
                self.logger.warning(f"Cannot deactivate user {user_id}: would leave no active admins")
                return False
        
        return self._user_dao.update_user(user_id, username, is_active)

    def deactivate_user(self, user_id):
        """
        Deactivate a user.
        
        Args:
            user_id: ID of user to deactivate
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self._is_current_user(user_id):
            self.logger.warning(f"User {user_id} cannot deactivate themselves")
            return False
            
        if not self._can_deactivate_user(user_id):
            self.logger.warning(f"Cannot deactivate user {user_id}: would leave no active admins")
            return False
        
        return self._user_dao.deactivate(user_id)

    def list_users(self, order_by=None):
        """
        Get list of all users.
        
        Args:
            order_by: Column to order by (optional)
            
        Returns:
            list: List of User objects
        """
        return self._user_dao.list_users(order_by)

    def create_role(self, name):
        """
        Create a new role.
        
        Args:
            name: Name of the role
            
        Returns:
            Role object if successful, None otherwise
        """
        return self._role_dao.create(name)

    def delete_role(self, role_id):
        """
        Safely delete a role (only if not assigned to users and not the admin role).
        
        Args:
            role_id: ID of role to delete
            
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            role = self._role_dao.get_by_id(role_id)
            if role and role.name.lower() == "admin":
                return False, "Cannot delete the admin role"
        except Exception as e:
            self.logger.error(f"Error checking role before deletion: {str(e)}")
            return False, "Error occurred while validating role"
        
        return self._role_dao.safe_delete(role_id)

    def list_roles(self):
        """
        Get list of all roles.
        
        Returns:
            list: List of Role objects
        """
        return self._role_dao.list_all()

    def assign_role(self, user_id, role_name):
        """
        Assign a role to a user.
        
        Args:
            user_id: ID of user
            role_name: Name of role to assign
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self._user_dao.assign_role(user_id, role_name)

    def remove_role(self, user_id, role_name):
        """
        Remove a role from a user.
        
        Args:
            user_id: ID of user
            role_name: Name of role to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        if role_name.lower() == "admin":
            if self._is_current_user(user_id):
                self.logger.warning(f"User {user_id} cannot remove admin role from themselves")
                return False
                
            if not self._can_remove_admin_role(user_id):
                self.logger.warning(f"Cannot remove admin role from user {user_id}: would leave no active admins")
                return False
        
        return self._user_dao.remove_role(user_id, role_name)

    def role_required(self, required_roles):
        """
        Decorator that checks if current user has required roles.
        
        Args:
            required_roles: List of role names that are required
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                if session.current_user is None:
                    raise PermissionError("Authentication required")
                
                user_roles = self.get_user_roles(session.current_user.id)
                user_role_names = [role.name for role in user_roles]
                
                if not any(role in user_role_names for role in required_roles):
                    raise PermissionError(f"Requires one of: {', '.join(required_roles)}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def get_user_roles(self, user_id):
        """
        Get roles assigned to a user.
        
        Args:
            user_id: ID of user
            
        Returns:
            list: List of Role objects
        """
        def op():
            from librepy.auth.auth_model import UserRole, Role
            roles = (Role
                    .select()
                    .join(UserRole)
                    .where(UserRole.user == user_id))
            role_list = list(roles)
            return role_list
        
        return self._user_dao.safe_execute("getting user roles", op, default_return=[])

    def get_available_usernames(self):
        """
        Get list of available usernames for login dropdown.
        
        Returns:
            list: List of username strings for active users
        """
        try:
            usernames = self._user_dao.list_active_usernames()
            self.logger.debug(f"Retrieved {len(usernames)} active usernames for login dropdown")
            return usernames
        except Exception as e:
            self.logger.error(f"Error retrieving available usernames: {str(e)}")
            return []

    def _can_deactivate_user(self, user_id):
        """
        Check if a user can be deactivated without leaving zero active admins.
        
        Args:
            user_id: ID of user to potentially deactivate
            
        Returns:
            bool: True if safe to deactivate, False otherwise
        """
        try:
            user_roles = self.get_user_roles(user_id)
            is_admin = any(role.name.lower() == "admin" for role in user_roles)
            
            if not is_admin:
                return True
            
            active_admin_count = self._count_active_admins()
            return active_admin_count > 1
        except Exception as e:
            self.logger.error(f"Error checking if user can be deactivated: {str(e)}")
            return False

    def _can_remove_admin_role(self, user_id):
        """
        Check if admin role can be removed from a user without leaving zero active admins.
        
        Args:
            user_id: ID of user to potentially remove admin role from
            
        Returns:
            bool: True if safe to remove admin role, False otherwise
        """
        try:
            user = self._user_dao.get_by_id(user_id)
            if not user or not user.is_active:
                return True
            
            active_admin_count = self._count_active_admins()
            return active_admin_count > 1
        except Exception as e:
            self.logger.error(f"Error checking if admin role can be removed: {str(e)}")
            return False

    def _count_active_admins(self):
        """
        Count the number of active users with admin role.
        
        Returns:
            int: Number of active admin users
        """
        def op():
            from librepy.auth.auth_model import UserRole, Role
            admin_role = Role.get_or_none(Role.name == "admin")
            if not admin_role:
                return 0
            
            active_admin_count = (UserRole
                                .select()
                                .join(self._user_dao.model_class)
                                .where(
                                    UserRole.role == admin_role.id,
                                    self._user_dao.model_class.is_active == True
                                )
                                .count())
            return active_admin_count
        
        return self._user_dao.safe_execute("counting active admins", op, default_return=0)

    def _is_current_user(self, user_id):
        """
        Check if the given user ID matches the currently logged-in user.
        
        Args:
            user_id: ID of user to check
            
        Returns:
            bool: True if user_id matches current user, False otherwise
        """
        try:
            return session.current_user is not None and session.current_user.id == user_id
        except Exception as e:
            self.logger.error(f"Error checking if user is current user: {str(e)}")
            return False

    def list_permissions(self):
        """
        Get list of all permissions.
        
        Returns:
            list: List of Permission objects
        """
        return self._permission_dao.list_all()

    def assign_permission(self, role_id, perm_code):
        """
        Assign a permission to a role.
        
        Args:
            role_id: ID of role
            perm_code: Permission code to assign
            
        Returns:
            bool: True if successful, False otherwise
        """
        def op():
            from librepy.auth.auth_model import RolePermission
            permission = self._permission_dao.get_by_code(perm_code)
            if not permission:
                return False
            
            RolePermission.get_or_create(role=role_id, permission=permission.id)
            return True
            
        return self._permission_dao.safe_execute("assign permission", op, default_return=False)

    def remove_permission(self, role_id, perm_code):
        """
        Remove a permission from a role.
        
        Args:
            role_id: ID of role
            perm_code: Permission code to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        def op():
            from librepy.auth.auth_model import RolePermission
            permission = self._permission_dao.get_by_code(perm_code)
            if not permission:
                return False
            
            RolePermission.delete().where(
                RolePermission.role == role_id,
                RolePermission.permission == permission.id
            ).execute()
            return True
            
        return self._permission_dao.safe_execute("remove permission", op, default_return=False)

    def get_role_permissions(self, role_id):
        """
        Get permissions assigned to a role.
        
        Args:
            role_id: ID of role
            
        Returns:
            list: List of Permission objects
        """
        def op():
            from librepy.auth.auth_model import RolePermission, Permission
            permissions = (Permission
                          .select()
                          .join(RolePermission)
                          .where(RolePermission.role == role_id))
            return list(permissions)
            
        return self._permission_dao.safe_execute("getting role permissions", op, default_return=[])

    def user_has_permission(self, user_id, perm_code):
        """
        Check if a user has a specific permission through their roles.
        
        Args:
            user_id: ID of user
            perm_code: Permission code to check
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        def op():
            from librepy.auth.auth_model import UserRole, RolePermission, Permission
            
            permission = self._permission_dao.get_by_code(perm_code)
            if not permission:
                return False
            
            user_roles = UserRole.select().where(UserRole.user == user_id)
            for user_role in user_roles:
                role_perms = RolePermission.select().where(
                    RolePermission.role == user_role.role,
                    RolePermission.permission == permission.id
                )
                if role_perms.exists():
                    return True
            return False
            
        return self._permission_dao.safe_execute("checking user permission", op, default_return=False)

    def permission_required(self, perm_code):
        """
        Decorator that checks if current user has required permission.
        
        Args:
            perm_code: Permission code that is required
            
        Returns:
            Decorator function
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                if session.current_user is None:
                    raise PermissionError("Authentication required")
                
                if not self.user_has_permission(session.current_user.id, perm_code):
                    raise PermissionError(f"Permission required: {perm_code}")
                
                return func(*args, **kwargs)
            return wrapper
        return decorator