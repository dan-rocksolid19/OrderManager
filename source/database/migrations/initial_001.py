from librepy.model.model import Org, OrgAddress, AcctTrans, CalendarEntryStatus, CalendarEntryOrder

def migrate(migrator, db):
    models = [Org, OrgAddress, AcctTrans, CalendarEntryStatus, CalendarEntryOrder]
    
    original_databases = {}
    for model in models:
        original_databases[model] = model._meta.database
        model._meta.database = db
    
    try:
        db.create_tables(models)
    finally:
        for model in models:
            model._meta.database = original_databases[model] 