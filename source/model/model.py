from datetime import datetime, timezone
from librepy.model.base_model import BaseModel, BaseOrderModel
from librepy.peewee.peewee import (
    AutoField,
    CharField,
    TextField,
    IntegerField,
    DateTimeField,
    DateField,
    TimeField,
    DecimalField,
    ForeignKeyField,
    BooleanField,
)


class Org(BaseModel):
    org_id = AutoField(primary_key=True)
    orgname = CharField(max_length=255)
    phone = CharField(max_length=50, column_name='phone1')

    class Meta:
        table_name = 'org'


class OrgAddress(BaseModel):
    addr_id = AutoField(primary_key=True, column_name='gen_addr_id')
    addrtype = CharField(max_length=31, column_name='addresstype')
    org = ForeignKeyField(Org, backref='addresses', column_name='orgid')
    streetone = CharField(max_length=255, column_name='streetone')
    city = CharField(max_length=255, column_name='txtcity')
    state = CharField(max_length=255, column_name='txtstate')
    zip = CharField(max_length=255, column_name='txtzip')
    country = CharField(max_length=255, column_name='txtcountry')

    class Meta:
        table_name = 'org_address'


class AcctTrans(BaseModel):
    transtypecode = CharField(max_length=31, column_name='transtypecode')   # FK to acct_trans_type
    transid = AutoField(primary_key=True)
    referencenumber = CharField(max_length=45, null=True, column_name='referencenumber')
    notes = TextField(null=True, column_name='notes')
    transdate = DateField(column_name='transdate')
    expecteddate = DateField(null=True, column_name='expecteddate')

    # FK to Org
    org = ForeignKeyField(Org, backref='transactions', column_name='orgid', null=True)

    class Meta:
        table_name = 'acct_trans'


class CalendarEntryStatus(BaseOrderModel):
    status_id = AutoField(primary_key=True)
    status = CharField(max_length=50, unique=True)
    color = CharField(max_length=20)  # e.g. hex string "#3498db" or named color

    class Meta:
        table_name = "calendar_entry_status"


class CalendarEntryOrder(BaseOrderModel):
    entry_id = AutoField(primary_key=True)
    start_date = DateField()
    end_date = DateField()
    event_name = CharField(max_length=255)
    event_description = TextField(null=True)
    order = ForeignKeyField(
        AcctTrans,
        unique=True,
        backref='calendar_entry',
        on_delete='CASCADE',
        null=True,
    )
    reminder = BooleanField(default=False)
    days_before = IntegerField(null=True)
    lock_dates = BooleanField(default=False)
    status = ForeignKeyField(CalendarEntryStatus, backref='entries', null=True, on_delete='SET NULL')

    class Meta:
        table_name = 'calendar_entry_order'


class Settings(BaseModel):
    id = AutoField(primary_key=True)
    setting_key = CharField(max_length=255, unique=True)
    setting_value = TextField(null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = 'settings'