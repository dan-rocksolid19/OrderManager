from datetime import datetime, timezone
from decimal import Decimal
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


class Org(BaseOrderModel):
    org_id = AutoField(primary_key=True)
    orgname = CharField(max_length=255)
    phone = CharField(max_length=50, column_name='phone1')

    class Meta:
        table_name = 'org'


class OrgAddress(BaseOrderModel):
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


class AcctTrans(BaseOrderModel):
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
        on_delete='CASCADE'
    )
    reminder = BooleanField(default=False)
    days_before = IntegerField(null=True)
    lock_dates = BooleanField(default=False)
    status = ForeignKeyField(CalendarEntryStatus, backref='entries', null=True, on_delete='SET NULL')

    class Meta:
        table_name = 'calendar_entry_order'


class Customers(BaseModel):
    id = AutoField()
    customer_name = CharField(max_length=255)
    company_name = CharField(max_length=255, null=True)
    phone_number = CharField(max_length=50)
    email = CharField(max_length=255, null=True)

    class Meta:
        table_name = "customers"

class Addresses(BaseModel):
    id = AutoField()
    address_line = CharField(max_length=255)
    city = CharField(max_length=100)
    state = CharField(max_length=100)
    zip_code = CharField(max_length=20)

    class Meta:
        table_name = "addresses"

class Documents(BaseModel):
    id = AutoField()
    customer = ForeignKeyField(Customers, backref="documents", on_delete="CASCADE")
    doc_type = CharField(max_length=20)
    project_folder = CharField(max_length=1024, null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    status = CharField(max_length=20, default='open')
    notes = TextField(null=True)
    private_notes = TextField(null=True)

    class Meta:
        table_name = "documents"

class DocumentAddress(BaseModel):
    document = ForeignKeyField(Documents, backref="document_addresses", on_delete="CASCADE")
    address = ForeignKeyField(Addresses, backref="document_addresses", on_delete="CASCADE")
    address_type = CharField(max_length=20)

    class Meta:
        table_name = "document_addresses"
        indexes = (
            (("document", "address_type"), True),
        )

class Request(BaseModel):
    document = ForeignKeyField(Documents, backref="request", primary_key=True, on_delete="CASCADE")
    information = TextField(null=True)
    residential_commercial = CharField(max_length=20, null=True)
    day_works_best = DateField(null=True)
    another_day = DateField(null=True)
    preferred_time = TimeField(null=True)

    class Meta:
        table_name = "requests"

class Quote(BaseModel):
    document = ForeignKeyField(Documents, backref="quote", primary_key=True, on_delete="CASCADE")
    converted_from_request = ForeignKeyField(Documents, null=True, on_delete="SET NULL")

    class Meta:
        table_name = "quotes"

class Job(BaseModel):
    document = ForeignKeyField(Documents, backref="job", primary_key=True, on_delete="CASCADE")
    converted_from_quote = ForeignKeyField(Documents, null=True, on_delete="SET NULL")

    class Meta:
        table_name = "jobs"

class Invoice(BaseModel):
    document = ForeignKeyField(Documents, backref="invoice", primary_key=True, on_delete="CASCADE")

    class Meta:
        table_name = "invoices"

class Items(BaseModel):
    id = AutoField()
    document = ForeignKeyField(Documents, backref="items", null=True, on_delete="CASCADE")
    item_number = CharField(max_length=50)
    product_service = CharField(max_length=255)
    quantity = IntegerField()
    unit_price = DecimalField(max_digits=10, decimal_places=2)
    total = DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        table_name = "items"
        indexes = (
            (("document", "item_number"), False),
        )

class Steps(BaseModel):
    id = AutoField()
    document = ForeignKeyField(Documents, backref="steps", on_delete="CASCADE")
    step_order = IntegerField()
    step = CharField(max_length=150)
    start_date = DateField(null=True)
    end_date = DateField(null=True)
    crew_assigned = CharField(max_length=100, null=True)

    class Meta:
        table_name = "steps"
        indexes = (
            (("document", "step_order"), True),
        )

class Settings(BaseModel):
    id = AutoField()
    setting_key = CharField(max_length=255, unique=True)
    setting_value = TextField(null=True)
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "settings"

class Crews(BaseModel):
    id = AutoField()
    crew_name = CharField(max_length=150, unique=True)

    class Meta:
        table_name = "crews"

class Hours(BaseModel):
    id = AutoField()
    document = ForeignKeyField(Documents, backref="hours", on_delete="CASCADE")
    employee = CharField(max_length=150)
    start_date = DateField()
    end_date = DateField()
    hours = DecimalField(max_digits=5, decimal_places=2)
    rate = DecimalField(max_digits=10, decimal_places=2)
    total = DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        table_name = "hours"

class Events(BaseModel):
    id = AutoField()
    title = CharField(max_length=255)
    start_date = DateField(null=True)
    end_date = DateField(null=True)
    description = TextField(null=True)
    status = CharField(max_length=50, default='Unassigned')
    created_at = DateTimeField(default=lambda: datetime.now(timezone.utc))
    updated_at = DateTimeField(default=lambda: datetime.now(timezone.utc))

    class Meta:
        table_name = "events"
