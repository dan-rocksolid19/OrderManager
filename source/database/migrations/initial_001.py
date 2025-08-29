from librepy.model.model import Customers, Addresses, Documents, DocumentAddress, Request, Quote, Job, Invoice, Items, Steps, Settings, Crews, Hours

def migrate(migrator, db):
    models = [Customers, Addresses, Documents, DocumentAddress, Request, Quote, Job, Invoice, Items, Steps, Settings, Crews, Hours]
    
    original_databases = {}
    for model in models:
        original_databases[model] = model._meta.database
        model._meta.database = db
    
    try:
        db.create_tables(models)
    finally:
        for model in models:
            model._meta.database = original_databases[model] 