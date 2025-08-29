from librepy.model.model import Events

def migrate(migrator, db):
    models = [Events]
    
    original_databases = {}
    for model in models:
        original_databases[model] = model._meta.database
        model._meta.database = db
    
    try:
        db.create_tables(models)
    finally:
        for model in models:
            model._meta.database = original_databases[model]