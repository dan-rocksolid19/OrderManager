from librepy.auth.auth_dao import UserDAO, RoleDAO
from librepy.auth.create_admin_dlg import CreateAdminDialog
from librepy.auth.auth_service import AuthService
from librepy.pybrex.values import pybrex_logger

# Create a module-specific logger
logger = pybrex_logger(__name__)

def ensure_auth_ready(ctx, smgr, *args, **kwargs):
    logger.info("Auth bootstrap: ensuring admin role exists")
    role_dao = RoleDAO(logger)
    admin_role = role_dao.get_by_name("admin")
    if not admin_role:
        logger.info("Auth bootstrap: creating admin role")
        admin_role = role_dao.create("admin")
        if admin_role:
            logger.info(f"Auth bootstrap: admin role created successfully with ID {admin_role.id}")
        else:
            logger.warning("Auth bootstrap: failed to create admin role")
    else:
        logger.info(f"Auth bootstrap: admin role already exists with ID {admin_role.id}")

    logger.info("Auth bootstrap: checking user count")
    dao = UserDAO(logger)
    total = dao.safe_execute("count users", lambda: dao.model_class.select().count(), default_return=0)
    logger.info(f"Auth bootstrap: total users found = {total}")

    if total == 0:
        logger.info("Auth bootstrap: no users found, launching CreateAdminDialog")
        dlg = CreateAdminDialog(ctx, smgr, logger)
        res = dlg.execute()
        if res != 1:
            logger.warning("Auth bootstrap: admin dialog cancelled, aborting startup")
            return False
        total = dao.safe_execute("count users", lambda: dao.model_class.select().count(), default_return=0)
        if total == 0:
            logger.warning("Auth bootstrap: admin user creation failed, aborting startup")
            return False
        logger.info("Auth bootstrap: admin user created successfully")

    auth_service = AuthService()
    user = auth_service.try_auto_login()
    if user:
        logger.info(f"Auth bootstrap: auto-login succeeded for {user.username}")
    else:
        logger.info("Auth bootstrap: auto-login not performed or failed")

    return True 