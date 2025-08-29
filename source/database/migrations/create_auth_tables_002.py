from librepy.auth.auth_model import User, Role, Permission, UserRole, RolePermission, AuditLog

def migrate(migrator, db):
    models = [
        User,
        Role,
        Permission,
        UserRole,
        RolePermission,
        AuditLog,
    ]
    
    original_databases = {}
    for model in models:
        original_databases[model] = model._meta.database
        model._meta.database = db
    
    try:
        db.create_tables(models)
    finally:
        for model in models:
            model._meta.database = original_databases[model] 