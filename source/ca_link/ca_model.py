'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()           # Get the user path of the currently running instance
thisComponent           # Current component instance
getDefaultContext()     # Get the default context
MsgBox()                # Simple msgbox that takes the same arguments as the Basic MsgBox
mri(obj)                # Mri the object. MRI must be installed for this to work
doc_object              # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''

from librepy.ca_link.ca_base_model import BaseModel
from librepy.peewee.peewee import *

# Model definitions start here
class GlAcctType(BaseModel):
    balancefactor = IntegerField()
    gl_number_end = IntegerField(constraints=[SQL("DEFAULT 1000")])
    gl_number_start = IntegerField(constraints=[SQL("DEFAULT 1000")])
    glaccttypecode = CharField(primary_key=True)
    glaccttypename = CharField(null=True)
    orderseq = IntegerField()

    class Meta:
        table_name = 'gl_acct_type'

class GlAcct(BaseModel):
    accountname = CharField()
    accountnumber = CharField(null=True)
    active = BooleanField()
    balance = DecimalField()
    checks_on_hand = SmallIntegerField(null=True)
    checks_ordered = BooleanField(constraints=[SQL("DEFAULT false")])
    createdate = DateTimeField()
    description = CharField(null=True)
    endingbalance = DecimalField(null=True)
    gl_acct_id = BigAutoField()
    glaccttype = ForeignKeyField(column_name='glaccttype', field='glaccttypecode', model=GlAcctType)
    glnumber = IntegerField(unique=True)
    is_short_term = BooleanField(constraints=[SQL("DEFAULT false")])
    lastchknumber = CharField(null=True)
    lastreconciledate = DateField(null=True)
    moddate = DateTimeField(null=True)
    parentglaccountid = ForeignKeyField(column_name='parentglaccountid', field='gl_acct_id', model='self', null=True)
    permanent = BooleanField(constraints=[SQL("DEFAULT false")])
    retained_earnings_acct = BooleanField(null=True)

    class Meta:
        table_name = 'gl_acct'

class AcctSalesRep(BaseModel):
    active = BooleanField()
    create_date = DateTimeField()
    id = CharField(primary_key=True)
    mod_date = DateTimeField(null=True)
    rep_initials = CharField(null=True)
    rep_name = CharField(null=True)

    class Meta:
        table_name = 'acct_sales_rep'

class AcctViaMethod(BaseModel):
    active = BooleanField()
    createdate = DateTimeField()
    id = BigAutoField()
    moddate = DateTimeField(null=True)
    viamethodname = CharField(index=True)

    class Meta:
        table_name = 'acct_via_method'

class OrgType(BaseModel):
    active = BooleanField()
    id = BigAutoField()
    orgdiscriminator = CharField(index=True)
    orgtypename = CharField(null=True)

    class Meta:
        table_name = 'org_type'

class ItmPriceLevels(BaseModel):
    active = BooleanField()
    createdate = DateTimeField()
    defaultformula = CharField(null=True)
    defaultroundto = DecimalField(null=True)
    id = BigAutoField()
    levelname = CharField(null=True)
    moddate = DateTimeField(null=True)

    class Meta:
        table_name = 'itm_price_levels'

class AcctTerms(BaseModel):
    active = BooleanField()
    createdate = DateTimeField()
    discount_day_of_month = IntegerField(null=True)
    discountdays = IntegerField()
    discountpercentage = DecimalField()
    due_day_of_month = IntegerField(null=True)
    fixed_discount_date = DateField(null=True)
    fixed_due_date = DateField(null=True)
    moddate = DateTimeField(null=True)
    netduedays = IntegerField()
    terms_id = BigAutoField()
    terms_mode = CharField()
    termsname = CharField(unique=True)

    class Meta:
        table_name = 'acct_terms'

class Org(BaseModel):
    acctnumber = CharField(index=True, null=True)
    active = BooleanField(index=True)
    alertnotes = CharField(constraints=[SQL("DEFAULT ''::character varying")], null=True)
    autoactive = BooleanField()
    balance = DecimalField()
    checkname = CharField(null=True)
    companyname = CharField(null=True)
    contact1 = CharField(null=True)
    contact2 = CharField(null=True)
    createdate = DateTimeField()
    creditlimit = DecimalField(null=True)
    def_purchase_account = ForeignKeyField(column_name='def_purchase_account_id', field='gl_acct_id', model=GlAcct, null=True)
    def_sales_rep = ForeignKeyField(column_name='def_sales_rep_id', field='id', model=AcctSalesRep, null=True)
    default_ship_via_org = ForeignKeyField(column_name='default_ship_via_org_id', field='id', model=AcctViaMethod, null=True)
    eligible1099 = BooleanField(null=True)
    email = CharField(null=True)
    exported = BooleanField(null=True)
    fax1 = CharField(null=True)
    firstname = CharField(null=True)
    fiscalmonth = IntegerField(null=True)
    is_cash_customer = BooleanField(constraints=[SQL("DEFAULT false")])
    is_no_charge_sales = BooleanField(constraints=[SQL("DEFAULT false")])
    lastfcdate = DateField(null=True)
    lastname = CharField(null=True)
    logo = BlobField(null=True)
    midname = CharField(null=True)
    moddate = DateTimeField(null=True)
    notes = CharField(null=True)
    org_id = BigAutoField()
    org_name_extension = CharField(constraints=[SQL("DEFAULT ''::character varying")], index=True)
    orgdiscriminator = CharField(index=True)
    orgname = CharField(index=True, null=True)
    orgtypeid = ForeignKeyField(column_name='orgtypeid', field='id', model=OrgType, null=True)
    phone1 = CharField(null=True)
    phone2 = CharField(null=True)
    pricelevelid = ForeignKeyField(column_name='pricelevelid', field='id', model=ItmPriceLevels, null=True)
    tax_exempt_expiration_date = DateField(null=True)
    tax_exempt_number = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    taxable = BooleanField(null=True)
    taxidno = CharField(null=True)
    taxmonth = IntegerField(null=True)
    termsid = ForeignKeyField(column_name='termsid', field='terms_id', model=AcctTerms, null=True)
    title = CharField(null=True)
    website = CharField(null=True)

    class Meta:
        table_name = 'org'
        indexes = (
            (('orgdiscriminator', 'orgname', 'org_name_extension'), True),
        )

class ItmInventoryGroup(BaseModel):
    create_date = DateTimeField()
    group_name = CharField(null=True)
    group_path_string = CharField(null=True)
    id = BigAutoField()
    mod_date = DateTimeField(null=True)
    parent_group = ForeignKeyField(column_name='parent_group_id', field='id', model='self', null=True)

    class Meta:
        table_name = 'itm_inventory_group'

class ItmItemType(BaseModel):
    itemtypecode = CharField(primary_key=True)
    itemtypename = CharField()
    weighable = BooleanField(constraints=[SQL("DEFAULT false")])

    class Meta:
        table_name = 'itm_item_type'

class GeogrRegon(BaseModel):
    active = BooleanField()
    georegionparentid = ForeignKeyField(column_name='georegionparentid', field='id', model='self', null=True)
    georegiontype = CharField()
    georegonname = CharField(index=True)
    id = BigAutoField()

    class Meta:
        table_name = 'geogr_regon'

class ItmItems(BaseModel):
    active = BooleanField(constraints=[SQL("DEFAULT true")])
    alert_note_purchases = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    alert_note_sales = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    alertlevel = DecimalField(constraints=[SQL("DEFAULT 0.0000")])
    apply_discount_on = CharField(constraints=[SQL("DEFAULT 'NULL::character varying'")], null=True)
    apply_to_all = BooleanField(constraints=[SQL("DEFAULT false")])
    assetaccountid = ForeignKeyField(column_name='assetaccountid', field='gl_acct_id', model=GlAcct, null=True)
    averagecost = DecimalField(constraints=[SQL("DEFAULT 0.00000000")])
    base_item_cost_on_comp_cost = BooleanField(constraints=[SQL("DEFAULT false")], null=True)
    cost = DecimalField()
    createdate = DateTimeField()
    default_customer_exempt = BooleanField(constraints=[SQL("DEFAULT false")])
    default_item_exempt = BooleanField(constraints=[SQL("DEFAULT false")])
    discounted_item_action = CharField(constraints=[SQL("DEFAULT 'NULL::character varying'")], null=True)
    exported = BooleanField(constraints=[SQL("DEFAULT false")], null=True)
    inventory_group = ForeignKeyField(column_name='inventory_group_id', field='id', model=ItmInventoryGroup, null=True)
    item_code = CharField(constraints=[SQL("DEFAULT 'NULL::character varying'")], null=True)
    itemid = BigAutoField()
    itemlocation = CharField(null=True)
    itemname = CharField(constraints=[SQL("DEFAULT ''::character varying")], index=True)
    itemnumber = CharField(constraints=[SQL("DEFAULT ''::character varying")], index=True)
    itemtypecode = ForeignKeyField(column_name='itemtypecode', field='itemtypecode', model=ItmItemType)
    markupformula = CharField(null=True)
    moddate = DateTimeField(null=True)
    notes = TextField(constraints=[SQL("DEFAULT ''::text")])
    ordermax = DecimalField(constraints=[SQL("DEFAULT 0.0000")])
    ordermin = DecimalField(constraints=[SQL("DEFAULT 0.0000")])
    org = ForeignKeyField(column_name='org', field='org_id', model=Org, null=True)
    parentitemid = ForeignKeyField(column_name='parentitemid', field='itemid', model='self', null=True)
    price = DecimalField()
    pricetype = CharField(constraints=[SQL("DEFAULT 'Fixed'::character varying")])
    purchaseaccountid = ForeignKeyField(backref='gl_acct_purchaseaccountid_set', column_name='purchaseaccountid', field='gl_acct_id', model=GlAcct, null=True)
    purchasedesc = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    qtyonhand = DecimalField(constraints=[SQL("DEFAULT 0.000000")])
    qtyonpo = DecimalField(constraints=[SQL("DEFAULT 0.000000")])
    qtyonso = DecimalField(constraints=[SQL("DEFAULT 0.000000")])
    rec_version = BigIntegerField(constraints=[SQL("DEFAULT 0")], null=True)
    round_to = DecimalField(null=True)
    salesaccountid = ForeignKeyField(backref='gl_acct_salesaccountid_set', column_name='salesaccountid', field='gl_acct_id', model=GlAcct, null=True)
    salesdesc = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    tax_region = ForeignKeyField(column_name='tax_region_id', field='id', model=GeogrRegon, null=True)
    taxable = BooleanField(constraints=[SQL("DEFAULT false")])
    total_asset_value = DecimalField(constraints=[SQL("DEFAULT 0.00")])
    upccode = CharField(index=True, null=True)
    updatecost = BooleanField(constraints=[SQL("DEFAULT false")])
    varianceaccountid = ForeignKeyField(backref='gl_acct_varianceaccountid_set', column_name='varianceaccountid', field='gl_acct_id', model=GlAcct, null=True)
    vendor_part_number = CharField(null=True)
    weight = DecimalField(null=True)

    class Meta:
        table_name = 'itm_items'

class ItmItemUnit(BaseModel):
    active = BooleanField(constraints=[SQL("DEFAULT true")])
    createdate = DateTimeField()
    defaultpurchasing = BooleanField(constraints=[SQL("DEFAULT false")])
    defaultselling = BooleanField(constraints=[SQL("DEFAULT false")])
    id = BigAutoField()
    itemid = ForeignKeyField(column_name='itemid', field='itemid', model=ItmItems)
    mainunit = BooleanField(constraints=[SQL("DEFAULT false")])
    mathoper = CharField(constraints=[SQL("DEFAULT 'Multiply'::character varying")])
    moddate = DateTimeField(null=True)
    quantity = DecimalField()
    sellable = BooleanField()
    unitname = CharField()
    upccode = CharField(index=True, null=True)

    class Meta:
        table_name = 'itm_item_unit'

class OrgJob(BaseModel):
    end_date = DateField(null=True)
    job_id = BigAutoField()
    job_name = CharField()
    job_type = CharField()
    notes = TextField(null=True)
    org = ForeignKeyField(column_name='org_id', field='org_id', model=Org)
    start_date = DateField()

    class Meta:
        table_name = 'org_job'

class PyRefTaxTrackingType(BaseModel):
    active = BooleanField()
    orderseq = IntegerField()
    reftaxtrackingcode = CharField(primary_key=True)
    taxtrackingname = CharField()

    class Meta:
        table_name = 'py_ref_tax_tracking_type'

class PyRefPayrollItemType(BaseModel):
    defaulttaxtrackingtype = ForeignKeyField(column_name='defaulttaxtrackingtype', field='reftaxtrackingcode', model=PyRefTaxTrackingType, null=True)
    orderseq = IntegerField()
    parentpayrollitemtypecode = ForeignKeyField(column_name='parentpayrollitemtypecode', field='payrollitemtypecode', model='self', null=True)
    payrollitemtypecode = CharField(primary_key=True)
    payrollitemtypename = CharField()

    class Meta:
        table_name = 'py_ref_payroll_item_type'

class PyPayrollItem(BaseModel):
    active = BooleanField()
    affectstaxes = BooleanField()
    allowance = DecimalField()
    basetype = CharField()
    createdate = DateTimeField()
    defaultlimit = DecimalField()
    defaultrate = DecimalField()
    defaultratetype = CharField()
    expenseglaccount = ForeignKeyField(column_name='expenseglaccount', field='gl_acct_id', model=GlAcct, null=True)
    geographicregion = ForeignKeyField(column_name='geographicregion', field='id', model=GeogrRegon, null=True)
    grossornet = CharField()
    isannuallimit = BooleanField()
    liabilityglaccount = ForeignKeyField(backref='gl_acct_liabilityglaccount_set', column_name='liabilityglaccount', field='gl_acct_id', model=GlAcct, null=True)
    moddate = DateTimeField(null=True)
    overtimemultiplier = DecimalField()
    paidby = CharField()
    payableorg = ForeignKeyField(column_name='payableorg', field='org_id', model=Org, null=True)
    payableorgacctnumber = CharField(null=True)
    payrollitemid = BigAutoField()
    payrollitemname = CharField()
    payrollitemtype = ForeignKeyField(column_name='payrollitemtype', field='payrollitemtypecode', model=PyRefPayrollItemType)
    ratemethod = CharField()
    taxtrackingcode = ForeignKeyField(column_name='taxtrackingcode', field='reftaxtrackingcode', model=PyRefTaxTrackingType)

    class Meta:
        table_name = 'py_payroll_item'

class AcctPayMethodType(BaseModel):
    paymethodtype = CharField(primary_key=True)
    paymethodtypename = CharField(null=True)

    class Meta:
        table_name = 'acct_pay_method_type'

class AcctPayMethod(BaseModel):
    active = BooleanField()
    createdate = DateTimeField()
    id = BigAutoField()
    moddate = DateTimeField(null=True)
    paymethodname = CharField(null=True)
    paymethodtype = ForeignKeyField(column_name='paymethodtype', field='paymethodtype', model=AcctPayMethodType)

    class Meta:
        table_name = 'acct_pay_method'

class PyRefPayFrequency(BaseModel):
    active = BooleanField()
    annualpayfreq = IntegerField()
    orderseq = IntegerField()
    payfreqcode = CharField(primary_key=True)
    payfreqname = CharField()

    class Meta:
        table_name = 'py_ref_pay_frequency'

class PyPayPeriods(BaseModel):
    bonuspayperiod = BooleanField()
    closed = BooleanField(index=True)
    createdate = DateTimeField()
    description = CharField(null=True)
    enddate = DateField()
    id = BigAutoField()
    moddate = DateTimeField(null=True)
    paydate = DateField(index=True)
    payfrequency = ForeignKeyField(column_name='payfrequency', field='payfreqcode', model=PyRefPayFrequency)
    startdate = DateField()

    class Meta:
        table_name = 'py_pay_periods'

class OrgAddress(BaseModel):
    active = BooleanField()
    addresstype = CharField()
    addrname = CharField(null=True)
    createdate = DateTimeField()
    gen_addr_id = BigAutoField()
    is_default = BooleanField(constraints=[SQL("DEFAULT false")])
    moddate = DateTimeField(null=True)
    orgid = ForeignKeyField(column_name='orgid', field='org_id', model=Org, null=True)
    streetone = CharField(null=True)
    streettwo = CharField(null=True)
    txtcity = CharField(index=True, null=True)
    txtcountry = CharField(null=True)
    txtstate = CharField(index=True, null=True)
    txtzip = CharField(index=True, null=True)

    class Meta:
        table_name = 'org_address'

class AcctTransStatus(BaseModel):
    statuscode = CharField(primary_key=True)
    statusname = CharField(null=True)

    class Meta:
        table_name = 'acct_trans_status'

class AcctTransType(BaseModel):
    accttranstypecode = CharField(primary_key=True)
    accttranstypename = CharField()
    is_expense = BooleanField()
    is_income = BooleanField()
    is_pl_eligible = BooleanField()
    java_class = CharField()
    lastsequence = CharField(null=True)
    multiplier = IntegerField()
    transferable = BooleanField(constraints=[SQL("DEFAULT false")])

    class Meta:
        table_name = 'acct_trans_type'

class AcctTrans(BaseModel):
    billtotx = CharField(null=True)
    createdate = DateTimeField()
    expecteddate = DateField(null=True)
    exported = BooleanField(null=True)
    fixed_discount_date = DateField(null=True)
    fixed_due_date = DateField(null=True)
    fobtx = CharField(null=True)
    fromdate = DateField(null=True)
    glaccountidfrom = ForeignKeyField(column_name='glaccountidfrom', field='gl_acct_id', model=GlAcct, null=True)
    glaccountidto = ForeignKeyField(backref='gl_acct_glaccountidto_set', column_name='glaccountidto', field='gl_acct_id', model=GlAcct, null=True)
    is_jrn_deposit_eligible = BooleanField(constraints=[SQL("DEFAULT true")])
    memo = CharField(constraints=[SQL("DEFAULT ''::character varying")], null=True)
    moddate = DateTimeField(null=True)
    notes = CharField(constraints=[SQL("DEFAULT ''::character varying")], null=True)
    orgid = ForeignKeyField(column_name='orgid', field='org_id', model=Org, null=True)
    parent_trans = ForeignKeyField(column_name='parent_trans_id', field='transid', model='self', null=True)
    paydate = DateField(null=True)
    paymethodid = ForeignKeyField(column_name='paymethodid', field='id', model=AcctPayMethod, null=True)
    payperiodid = ForeignKeyField(column_name='payperiodid', field='id', model=PyPayPeriods, null=True)
    paytotx = CharField(constraints=[SQL("DEFAULT 'NULL::character varying'")], null=True)
    pmtreference = CharField(null=True)
    pricelevelid = ForeignKeyField(column_name='pricelevelid', field='id', model=ItmPriceLevels, null=True)
    printed = BooleanField(index=True)
    rec_version = BigIntegerField(constraints=[SQL("DEFAULT 0")], null=True)
    referencenumber = CharField(index=True, null=True)
    repeat_frequency = CharField(index=True, null=True)
    sales_rep = ForeignKeyField(column_name='sales_rep_id', field='id', model=AcctSalesRep, null=True)
    ship_to_address = ForeignKeyField(column_name='ship_to_address_id', field='gen_addr_id', model=OrgAddress, null=True)
    shiporg = ForeignKeyField(backref='org_shiporg_set', column_name='shiporg', field='org_id', model=Org, null=True)
    shiptotx = CharField(constraints=[SQL("DEFAULT ''::character varying")], null=True)
    sourcerefnumber = CharField(constraints=[SQL("DEFAULT ''::character varying")], null=True)
    taxes_migrated = BooleanField(null=True)
    tendered_amount = DecimalField(null=True)
    termsid = ForeignKeyField(column_name='termsid', field='terms_id', model=AcctTerms, null=True)
    todate = DateField(null=True)
    transdate = DateField(index=True)
    transid = BigAutoField()
    transstatus = ForeignKeyField(column_name='transstatus', field='statuscode', model=AcctTransStatus)
    transtotal = DecimalField()
    transtotalwordtx = CharField(null=True)
    transtypecode = ForeignKeyField(column_name='transtypecode', field='accttranstypecode', model=AcctTransType)
    undep_funds_total = DecimalField(null=True)
    viaid = ForeignKeyField(column_name='viaid', field='id', model=AcctViaMethod, null=True)

    class Meta:
        table_name = 'acct_trans'

class AcctEntry(BaseModel):
    active = BooleanField()
    applic_taxes_migrated = BooleanField(null=True)
    asset_value_verified = BooleanField(constraints=[SQL("DEFAULT false")])
    billable = BooleanField()
    billableorg = ForeignKeyField(column_name='billableorg', field='org_id', model=Org, null=True)
    billed = BooleanField()
    cleared = BooleanField(index=True)
    createdate = DateTimeField()
    discount_applied = DecimalField(constraints=[SQL("DEFAULT 0.00")])
    end_time = DateTimeField(null=True)
    entryamnt = DecimalField()
    entrydate = DateField(null=True)
    entryid = BigAutoField()
    entryqty = DecimalField()
    entrytotal = DecimalField()
    entrytypecode = CharField(index=True)
    glacctid = ForeignKeyField(column_name='glacctid', field='gl_acct_id', model=GlAcct, null=True)
    inventory_group = ForeignKeyField(column_name='inventory_group_id', field='id', model=ItmInventoryGroup, null=True)
    item_number = CharField(null=True)
    itemid = ForeignKeyField(column_name='itemid', field='itemid', model=ItmItems, null=True)
    itemunitid = ForeignKeyField(column_name='itemunitid', field='id', model=ItmItemUnit, null=True)
    job = ForeignKeyField(column_name='job_id', field='job_id', model=OrgJob, null=True)
    main_unit_qty = DecimalField(constraints=[SQL("DEFAULT 0.00")])
    measure_qty = DecimalField(constraints=[SQL("DEFAULT 1.0")])
    memotx = TextField(null=True)
    moddate = DateTimeField(null=True)
    notes = TextField(null=True)
    order_link_entryid = ForeignKeyField(column_name='order_link_entryid', field='entryid', model='self', null=True)
    orderseq = IntegerField(null=True)
    parententryid = ForeignKeyField(backref='acct_entry_parententryid_set', column_name='parententryid', field='entryid', model='self', null=True)
    payrollitemid = ForeignKeyField(column_name='payrollitemid', field='payrollitemid', model=PyPayrollItem, null=True)
    rec_version = BigIntegerField(constraints=[SQL("DEFAULT 0")], null=True)
    start_time = DateTimeField(null=True)
    total_asset_value = DecimalField(constraints=[SQL("DEFAULT 0.00")])
    transid = ForeignKeyField(column_name='transid', field='transid', model=AcctTrans)
    weight = DecimalField(null=True)

    class Meta:
        table_name = 'acct_entry'

class AcctEntryApplicTaxes(BaseModel):
    entry = ForeignKeyField(column_name='entry_id', field='entryid', model=AcctEntry)
    order_seq = IntegerField()
    tax_item = ForeignKeyField(column_name='tax_item_id', field='itemid', model=ItmItems)

    class Meta:
        table_name = 'acct_entry_applic_taxes'
        indexes = (
            (('entry', 'order_seq'), True),
        )
        primary_key = CompositeKey('entry', 'order_seq')

class AcctEntryType(BaseModel):
    acctentrytypecode = CharField(primary_key=True)
    acctentrytypename = CharField()

    class Meta:
        table_name = 'acct_entry_type'

class AcctYear(BaseModel):
    id = BigAutoField()
    trans_year = IntegerField(unique=True)

    class Meta:
        table_name = 'acct_year'

class AcctMonth(BaseModel):
    closed = BooleanField()
    id = BigAutoField()
    trans_month = CharField()
    year = ForeignKeyField(column_name='year_id', field='id', model=AcctYear, null=True)

    class Meta:
        table_name = 'acct_month'

class AcctTransRelations(BaseModel):
    childaccttransid = ForeignKeyField(column_name='childaccttransid', field='transid', model=AcctTrans)
    createdate = DateTimeField()
    discountamnt = DecimalField()
    discountglaccount = ForeignKeyField(column_name='discountglaccount', field='gl_acct_id', model=GlAcct, null=True)
    id = BigAutoField()
    moddate = DateTimeField(null=True)
    parentaccttransid = ForeignKeyField(backref='acct_trans_parentaccttransid_set', column_name='parentaccttransid', field='transid', model=AcctTrans)
    paymentamnt = DecimalField()
    refund_amnt = DecimalField()

    class Meta:
        table_name = 'acct_trans_relations'

class AcctTransTaxRegions(BaseModel):
    order_seq = IntegerField()
    tax_item = ForeignKeyField(column_name='tax_item_id', field='itemid', model=ItmItems)
    trans = ForeignKeyField(column_name='trans_id', field='transid', model=AcctTrans)

    class Meta:
        table_name = 'acct_trans_tax_regions'
        indexes = (
            (('trans', 'order_seq'), True),
        )
        primary_key = CompositeKey('order_seq', 'trans')

class UserProfile(BaseModel):
    active = BooleanField()
    allow_cards = BooleanField(constraints=[SQL("DEFAULT false")])
    createdate = DateTimeField()
    def_sales_rep = ForeignKeyField(column_name='def_sales_rep_id', field='id', model=AcctSalesRep, null=True)
    id = BigAutoField()
    log_off_to_guest_enabled = BooleanField(null=True)
    log_off_to_guest_seconds = IntegerField(constraints=[SQL("DEFAULT 600")])
    moddate = DateTimeField(null=True)
    name = CharField()
    password_hash = CharField(null=True)
    user_name = CharField(index=True)

    class Meta:
        table_name = 'user_profile'

class Attachment(BaseModel):
    attach_item = ForeignKeyField(column_name='attach_item_id', field='itemid', model=ItmItems, null=True)
    attach_name = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    attach_notes = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    attach_org = ForeignKeyField(column_name='attach_org_id', field='org_id', model=Org, null=True)
    attach_trans = ForeignKeyField(column_name='attach_trans_id', field='transid', model=AcctTrans, null=True)
    attachment_id = BigAutoField()
    date_attached = DateTimeField()
    doc_name = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    from_location = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    user = ForeignKeyField(column_name='user_id', field='id', model=UserProfile)

    class Meta:
        table_name = 'attachment'

class BnkBankingSettings(BaseModel):
    def_payment_acct = ForeignKeyField(column_name='def_payment_acct_id', field='gl_acct_id', model=GlAcct, null=True)
    deposit_sort_mode = CharField(constraints=[SQL("DEFAULT 'CUSTOMER_NAME'::character varying")])
    id = BigAutoField()

    class Meta:
        table_name = 'bnk_banking_settings'

class CorePostalCodeRecord(BaseModel):
    city = CharField(null=True)
    country = CharField(null=True)
    id = CharField(primary_key=True)
    postal_code = CharField(index=True, null=True)
    state_or_province = CharField(null=True)

    class Meta:
        table_name = 'core_postal_code_record'

class CoreSchemaUpdaterRecord(BaseModel):
    execution_timestamp = DateTimeField(null=True)
    id = CharField(primary_key=True)
    is_skipped = BooleanField(null=True)
    schema_updater_id = CharField(null=True)
    skip_reason = CharField(null=True)
    software_version = CharField(null=True)

    class Meta:
        table_name = 'core_schema_updater_record'

class DbVersion(BaseModel):
    db_version = IntegerField()
    min_app_version = IntegerField()
    update_timestamp = DateTimeField(constraints=[SQL("DEFAULT now()")])

    class Meta:
        table_name = 'db_version'

class ExpExpenseSettings(BaseModel):
    assign_check_num_from_bill_pay = BooleanField(null=True)
    bill_per_check = SmallIntegerField(constraints=[SQL("DEFAULT 0")])
    def_bill_disc_acct = ForeignKeyField(column_name='def_bill_disc_acct_id', field='gl_acct_id', model=GlAcct, null=True)
    def_purchase_order_copy_number = IntegerField(null=True)
    default_bill_pmnt_acct = ForeignKeyField(backref='gl_acct_default_bill_pmnt_acct_set', column_name='default_bill_pmnt_acct', field='gl_acct_id', model=GlAcct, null=True)
    default_org_type = ForeignKeyField(column_name='default_org_type', field='id', model=OrgType, null=True)
    default_ship_via = ForeignKeyField(column_name='default_ship_via_id', field='id', model=AcctViaMethod, null=True)
    default_terms = ForeignKeyField(column_name='default_terms_id', field='terms_id', model=AcctTerms, null=True)
    id = BigAutoField()
    po_item_on_order_alert_enabled = BooleanField(null=True)
    quote_request_customer_msg = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    quote_request_title = CharField(constraints=[SQL("DEFAULT 'Quote Request'::character varying")])

    class Meta:
        table_name = 'exp_expense_settings'

class GlReconciliation(BaseModel):
    createdate = DateTimeField()
    id = BigAutoField()
    is_reconciled = BooleanField()
    moddate = DateTimeField(null=True)
    reconcile_acct = ForeignKeyField(column_name='reconcile_acct_id', field='gl_acct_id', model=GlAcct, null=True)
    reconcile_date = DateField(null=True)
    statement_bal = DecimalField(null=True)

    class Meta:
        table_name = 'gl_reconciliation'

class GlReconciliationClearedEntries(BaseModel):
    gl_entry = ForeignKeyField(column_name='gl_entry_id', field='entryid', model=AcctEntry)
    reconciliation = ForeignKeyField(column_name='reconciliation_id', field='id', model=GlReconciliation)

    class Meta:
        table_name = 'gl_reconciliation_cleared_entries'
        indexes = (
            (('reconciliation', 'gl_entry'), True),
        )
        primary_key = CompositeKey('gl_entry', 'reconciliation')

class IncIncomeSettings(BaseModel):
    acct_credit_pay_method = ForeignKeyField(column_name='acct_credit_pay_method', field='id', model=AcctPayMethod, null=True)
    annual_interest_rate = DecimalField(null=True)
    auto_fill_date_so = BooleanField(constraints=[SQL("DEFAULT false")])
    clear_salesreceipt_on_tender_close = CharField(constraints=[SQL("DEFAULT 'No'::character varying")])
    create_drop_ship_po = CharField(constraints=[SQL("DEFAULT 'Ask'::character varying")])
    def_customer_credit_copy_number = IntegerField(null=True)
    def_customer_invoice_copy_number = IntegerField(null=True)
    def_estimate_copy_number = IntegerField(null=True)
    def_payment_discount_account = ForeignKeyField(column_name='def_payment_discount_account_id', field='gl_acct_id', model=GlAcct, null=True)
    def_sales_order_copy_number = IntegerField(null=True)
    def_sales_receipt_copy_number = IntegerField(null=True)
    default_credit_limit = DecimalField(null=True)
    default_customer_for_sales_receipt = BigIntegerField(null=True)
    default_org_type = ForeignKeyField(column_name='default_org_type', field='id', model=OrgType, null=True)
    default_price_level = ForeignKeyField(column_name='default_price_level_id', field='id', model=ItmPriceLevels, null=True)
    default_ship_via = ForeignKeyField(column_name='default_ship_via_id', field='id', model=AcctViaMethod, null=True)
    default_terms = ForeignKeyField(column_name='default_terms_id', field='terms_id', model=AcctTerms, null=True)
    disable_insufficient_qty_alert = BooleanField(constraints=[SQL("DEFAULT false")])
    estimate_customer_msg = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    estimate_title = CharField(constraints=[SQL("DEFAULT 'Estimate'::character varying")])
    finance_charge_date = CharField(null=True)
    finance_charge_item = ForeignKeyField(column_name='finance_charge_item_id', field='itemid', model=ItmItems, null=True)
    grace_days = IntegerField(null=True)
    id = BigAutoField()
    invoice_customer_msg = TextField(null=True)
    lock_printed_invoices = BooleanField(constraints=[SQL("DEFAULT false")])
    min_finance_charge = DecimalField(null=True)
    new_invoice_use_ship_date = BooleanField(constraints=[SQL("DEFAULT true")])
    new_invoice_via_method = ForeignKeyField(backref='acct_via_method_new_invoice_via_method_set', column_name='new_invoice_via_method', field='id', model=AcctViaMethod, null=True)
    po_use_custom_doc_item_number = BooleanField(constraints=[SQL("DEFAULT false")])
    po_use_itm_item_number = BooleanField(constraints=[SQL("DEFAULT false")])
    po_use_purchase_description_if_exists = BooleanField(constraints=[SQL("DEFAULT true")])
    po_use_vpn_if_exists = BooleanField(constraints=[SQL("DEFAULT true")])
    require_sales_rep_on_est = BooleanField(constraints=[SQL("DEFAULT false")])
    require_sales_rep_on_inv = BooleanField(constraints=[SQL("DEFAULT false")])
    require_sales_rep_on_so = BooleanField(constraints=[SQL("DEFAULT false")])
    require_sales_rep_on_sr = BooleanField(constraints=[SQL("DEFAULT false")])
    sales_receipt_auto_focus_to_scanner = BooleanField(constraints=[SQL("DEFAULT false")])
    sales_receipt_customer_msg = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    show_balance_on_invoice = BooleanField(constraints=[SQL("DEFAULT false")])
    show_discount_on_invoice = BooleanField(constraints=[SQL("DEFAULT false")])
    show_qty_ordered_backordered_on_invoice = BooleanField(constraints=[SQL("DEFAULT false")])
    show_qty_shipped_on_packing = BooleanField(constraints=[SQL("DEFAULT false")])
    show_qty_shipped_on_sales_order = BooleanField(constraints=[SQL("DEFAULT false")])
    show_signature_line_on_invoice = BooleanField(constraints=[SQL("DEFAULT true")])
    show_signature_line_on_sales_order = BooleanField(constraints=[SQL("DEFAULT true")])
    show_zero_dollar_taxes_on_invoice = BooleanField(constraints=[SQL("DEFAULT true")])
    sr_to_inv_allow_cash_cust = BooleanField(constraints=[SQL("DEFAULT false")])
    sr_to_inv_via_method = ForeignKeyField(backref='acct_via_method_sr_to_inv_via_method_set', column_name='sr_to_inv_via_method', field='id', model=AcctViaMethod, null=True)
    use_number_nine_envelopes = BooleanField(constraints=[SQL("DEFAULT false")])

    class Meta:
        table_name = 'inc_income_settings'

class IncIncomeSettingsDefTaxRegions(BaseModel):
    inc_settings = ForeignKeyField(column_name='inc_settings_id', field='id', model=IncIncomeSettings)
    order_seq = IntegerField()
    tax_item = ForeignKeyField(column_name='tax_item_id', field='itemid', model=ItmItems)

    class Meta:
        table_name = 'inc_income_settings_def_tax_regions'
        indexes = (
            (('inc_settings', 'order_seq'), True),
        )
        primary_key = CompositeKey('inc_settings', 'order_seq')

class ItmItemAssetAdjustment(BaseModel):
    adjust_amount = DecimalField()
    createdate = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    id = BigAutoField()
    item = ForeignKeyField(column_name='item_id', field='itemid', model=ItmItems)
    moddate = DateTimeField(null=True)
    notes = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    rec_version = IntegerField(constraints=[SQL("DEFAULT 1")])

    class Meta:
        table_name = 'itm_item_asset_adjustment'

class ItmItemLink(BaseModel):
    childitemid = ForeignKeyField(column_name='childitemid', field='itemid', model=ItmItems)
    createdate = DateTimeField()
    description = CharField(null=True)
    exempt = BooleanField(constraints=[SQL("DEFAULT false")])
    id = BigAutoField()
    itemunitid = ForeignKeyField(column_name='itemunitid', field='id', model=ItmItemUnit)
    linktype = CharField()
    moddate = DateTimeField(null=True)
    ordinal = IntegerField(null=True)
    parentitemid = ForeignKeyField(backref='itm_items_parentitemid_set', column_name='parentitemid', field='itemid', model=ItmItems)
    qty = DecimalField()

    class Meta:
        table_name = 'itm_item_link'

class ItmItemPriceLevels(BaseModel):
    createdate = DateTimeField()
    formula = CharField()
    id = BigAutoField()
    itemid = ForeignKeyField(column_name='itemid', field='itemid', model=ItmItems)
    itemunitid = ForeignKeyField(column_name='itemunitid', field='id', model=ItmItemUnit)
    moddate = DateTimeField(null=True)
    price = DecimalField()
    pricelevelid = ForeignKeyField(column_name='pricelevelid', field='id', model=ItmPriceLevels)
    rec_version = BigIntegerField(constraints=[SQL("DEFAULT 0")], null=True)
    roundto = DecimalField(null=True)

    class Meta:
        table_name = 'itm_item_price_levels'

class ItmItemSettings(BaseModel):
    def_asset_gl_acct = ForeignKeyField(column_name='def_asset_gl_acct', field='gl_acct_id', model=GlAcct, null=True)
    def_markup_formula = CharField(null=True)
    def_purchase_gl_acct = ForeignKeyField(backref='gl_acct_def_purchase_gl_acct_set', column_name='def_purchase_gl_acct', field='gl_acct_id', model=GlAcct, null=True)
    def_sales_gl_acct = ForeignKeyField(backref='gl_acct_def_sales_gl_acct_set', column_name='def_sales_gl_acct', field='gl_acct_id', model=GlAcct, null=True)
    def_variance_gl_acct = ForeignKeyField(backref='gl_acct_def_variance_gl_acct_set', column_name='def_variance_gl_acct', field='gl_acct_id', model=GlAcct, null=True)
    id = BigAutoField()
    inventory_method = CharField(null=True)
    is_items_mananger_preload_items = BooleanField(null=True)
    purchase_cost_update = BooleanField(constraints=[SQL("DEFAULT false")])
    upc_price_patterns = CharField(constraints=[SQL("DEFAULT ''::character varying")])

    class Meta:
        table_name = 'itm_item_settings'

class Logs(BaseModel):
    id = BigAutoField()
    logdatetime = DateTimeField()
    logdesc = CharField(null=True)
    logstacktrace = CharField(null=True)
    logtext = TextField(constraints=[SQL("DEFAULT ''::text")], null=True)

    class Meta:
        table_name = 'logs'

class OrgAddressType(BaseModel):
    active = BooleanField()
    addresstypecode = CharField(primary_key=True)
    addresstypename = CharField()

    class Meta:
        table_name = 'org_address_type'

class OrgGroup(BaseModel):
    active = BooleanField(constraints=[SQL("DEFAULT true")])
    customer_eligible = BooleanField(constraints=[SQL("DEFAULT false")])
    default_value = BooleanField(constraints=[SQL("DEFAULT false")])
    employee_eligible = BooleanField(constraints=[SQL("DEFAULT false")])
    group_id = BigAutoField()
    group_name = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    notes = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    vendor_eligible = BooleanField(constraints=[SQL("DEFAULT false")])

    class Meta:
        table_name = 'org_group'

class OrgGroupLink(BaseModel):
    group = ForeignKeyField(column_name='group_id', field='group_id', model=OrgGroup)
    org = ForeignKeyField(column_name='org_id', field='org_id', model=Org)

    class Meta:
        table_name = 'org_group_link'
        indexes = (
            (('group', 'org'), True),
        )
        primary_key = CompositeKey('group', 'org')

class OrgItemLink(BaseModel):
    createdate = DateTimeField()
    exempt = BooleanField()
    id = BigAutoField()
    itemid = ForeignKeyField(column_name='itemid', field='itemid', model=ItmItems)
    linktype = CharField()
    moddate = DateTimeField(null=True)
    orgid = ForeignKeyField(column_name='orgid', field='org_id', model=Org)

    class Meta:
        table_name = 'org_item_link'

class OrgPaymentInfo(BaseModel):
    card_number = CharField()
    expiration_month = DecimalField(null=True)
    expiration_year = DecimalField(null=True)
    id = BigAutoField()
    notes = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    orgid = ForeignKeyField(column_name='orgid', field='org_id', model=Org, null=True)
    pay_method = ForeignKeyField(column_name='pay_method_id', field='id', model=AcctPayMethod, null=True)
    ref_number = CharField()
    seq = IntegerField(constraints=[SQL("DEFAULT 1")])

    class Meta:
        table_name = 'org_payment_info'

class OrgPaymentInfoLog(BaseModel):
    action = CharField()
    id = BigAutoField()
    info_id = BigIntegerField()
    info_notes = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    log_data = CharField()
    logdatetime = DateTimeField(constraints=[SQL("DEFAULT now()")], null=True)
    orgid = BigIntegerField()
    user = ForeignKeyField(column_name='user_id', field='id', model=UserProfile)

    class Meta:
        table_name = 'org_payment_info_log'

class Preferences(BaseModel):
    datevalue = DateField(null=True)
    notes = CharField(constraints=[SQL("DEFAULT ''::character varying")])
    prefkey = CharField(primary_key=True)
    prefvalue = CharField(null=True)

    class Meta:
        table_name = 'preferences'

class PyEmp(BaseModel):
    birthdate = DateField(null=True)
    empid = ForeignKeyField(column_name='empid', field='org_id', model=Org, primary_key=True)
    gender = CharField()
    hiredate = DateField(null=True)
    lastevaluationdate = DateField(null=True)
    lastraisedate = DateField(null=True)
    maritalstatus = CharField(null=True)
    payfreqcode = ForeignKeyField(column_name='payfreqcode', field='payfreqcode', model=PyRefPayFrequency)
    socialsecurity = CharField(null=True)
    termdate = DateField(null=True)
    usetimedata = BooleanField()

    class Meta:
        table_name = 'py_emp'

class PyRefFilingStatus(BaseModel):
    active = BooleanField()
    orderseq = IntegerField()
    reffilingstatuscode = CharField(primary_key=True)
    reffilingstatusname = CharField()

    class Meta:
        table_name = 'py_ref_filing_status'

class PyEmpPayrollItem(BaseModel):
    active = BooleanField()
    allowances = IntegerField()
    createdate = DateTimeField()
    defaultlimit = DecimalField()
    empid = ForeignKeyField(column_name='empid', field='empid', model=PyEmp)
    emppayrollitemid = BigAutoField()
    extradeduction = DecimalField()
    filingstatus = ForeignKeyField(column_name='filingstatus', field='reffilingstatuscode', model=PyRefFilingStatus)
    moddate = DateTimeField(null=True)
    orderseq = BigIntegerField(constraints=[SQL("DEFAULT 0")])
    payrollitemid = ForeignKeyField(column_name='payrollitemid', field='payrollitemid', model=PyPayrollItem)
    rate = DecimalField()
    ratetype = CharField()

    class Meta:
        table_name = 'py_emp_payroll_item'

class PyPayrollItemLink(BaseModel):
    childpayrollitemid = ForeignKeyField(column_name='childpayrollitemid', field='payrollitemid', model=PyPayrollItem)
    parentpayrollitemid = ForeignKeyField(backref='py_payroll_item_parentpayrollitemid_set', column_name='parentpayrollitemid', field='payrollitemid', model=PyPayrollItem)

    class Meta:
        table_name = 'py_payroll_item_link'
        indexes = (
            (('childpayrollitemid', 'parentpayrollitemid'), True),
        )
        primary_key = CompositeKey('childpayrollitemid', 'parentpayrollitemid')

class PyRateTable(BaseModel):
    active = BooleanField()
    createdate = DateTimeField()
    dollaramountbase = DecimalField()
    dollaramountupto = DecimalField()
    filingstatus = ForeignKeyField(column_name='filingstatus', field='reffilingstatuscode', model=PyRefFilingStatus)
    id = BigAutoField()
    moddate = DateTimeField(null=True)
    payrollitemid = ForeignKeyField(column_name='payrollitemid', field='payrollitemid', model=PyPayrollItem)
    taxpercentage = DecimalField()

    class Meta:
        table_name = 'py_rate_table'

class QrStatus(BaseModel):
    id = BigAutoField()
    is_closed = BooleanField(constraints=[SQL("DEFAULT false")])
    qr_status = CharField()
    seq = IntegerField()

    class Meta:
        table_name = 'qr_status'

class QrVendorLink(BaseModel):
    id = BigAutoField()
    import_date = DateField(null=True)
    org = ForeignKeyField(column_name='org_id', field='org_id', model=Org)
    qr = ForeignKeyField(column_name='qr_id', field='transid', model=AcctTrans)
    status = ForeignKeyField(column_name='status_id', field='id', model=QrStatus)
    vendor_note = CharField(null=True)

    class Meta:
        table_name = 'qr_vendor_link'

class UserSecurityZones(BaseModel):
    security_zone = CharField()
    user = ForeignKeyField(column_name='user_id', field='id', model=UserProfile)

    class Meta:
        table_name = 'user_security_zones'
        indexes = (
            (('user', 'security_zone'), True),
        )
        primary_key = CompositeKey('security_zone', 'user')

