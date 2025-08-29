from librepy.model.base_dao import BaseDAO
from librepy.model.model import Quote, Documents, Customers, Addresses, DocumentAddress, Items, Job
from datetime import datetime, timezone
from librepy.utils import project_folder_manager


class QuoteDAO(BaseDAO):
    
    def __init__(self, logger):
        super().__init__(Quote, logger)
    
    def create_quote_with_customer_and_address(self, customer_name, phone_number, 
                                             company_name=None, email=None,
                                             billing_address_line=None, billing_city=None, billing_state=None, billing_zip_code=None,
                                             site_address_line=None, site_city=None, site_state=None, site_zip_code=None,
                                             notes=None, private_notes=None, project_folder=None):
        
        with self.database.connection_context():
            customer = self.safe_execute(
                "creating customer",
                lambda: Customers.create(
                    customer_name=customer_name,
                    company_name=company_name,
                    phone_number=phone_number,
                    email=email
                ),
                reraise_integrity=True
            )
            
            billing_address = None
            if billing_address_line and billing_city and billing_state and billing_zip_code:
                billing_address = self.safe_execute(
                    "creating billing address",
                    lambda: Addresses.create(
                        address_line=billing_address_line,
                        city=billing_city,
                        state=billing_state,
                        zip_code=billing_zip_code
                    ),
                    reraise_integrity=True
                )
            
            site_address = None
            if site_address_line and site_city and site_state and site_zip_code:
                site_address = self.safe_execute(
                    "creating site address",
                    lambda: Addresses.create(
                        address_line=site_address_line,
                        city=site_city,
                        state=site_state,
                        zip_code=site_zip_code
                    ),
                    reraise_integrity=True
                )
            
            document = self.safe_execute(
                "creating document",
                lambda: Documents.create(
                    customer=customer,
                    doc_type="Quote",
                    project_folder=project_folder,
                    notes=notes,
                    private_notes=private_notes
                ),
                reraise_integrity=True
            )
            
            if billing_address:
                self.safe_execute(
                    "linking billing address to document",
                    lambda: DocumentAddress.create(
                        document=document,
                        address=billing_address,
                        address_type="billing"
                    ),
                    reraise_integrity=True
                )
            
            if site_address:
                self.safe_execute(
                    "linking site address to document",
                    lambda: DocumentAddress.create(
                        document=document,
                        address=site_address,
                        address_type="service"
                    ),
                    reraise_integrity=True
                )
            
            quote = self.safe_execute(
                "creating quote",
                lambda: Quote.create(
                    document=document
                ),
                reraise_integrity=True
            )
            
            return document.id if document else None
    
    def get_quote_by_document_id(self, document_id):
        return self.safe_execute(
            f"fetching quote for document ID {document_id}",
            lambda: self._get_quote_with_full_details(document_id)
        )
    
    def _get_quote_with_full_details(self, document_id):
        query = (Quote
                .select()
                .join(Documents, on=(Quote.document == Documents.id))
                .join(Customers)
                .where(Quote.document == document_id))
        
        quote = query.get()
        
        billing_address = None
        site_address = None
        
        address_queries = (DocumentAddress
                          .select()
                          .join(Addresses)
                          .where(DocumentAddress.document == document_id))
        
        for doc_address in address_queries:
            if doc_address.address_type == "billing":
                billing_address = doc_address.address
            elif doc_address.address_type == "service":
                site_address = doc_address.address
        
        return {
            'quote': quote,
            'customer': quote.document.customer,
            'billing_address': billing_address,
            'site_address': site_address,
            'document': quote.document
        }
    
    def update_quote_with_customer_and_address(self, document_id, customer_name, phone_number,
                                             company_name=None, email=None,
                                             billing_address_line=None, billing_city=None, billing_state=None, billing_zip_code=None,
                                             site_address_line=None, site_city=None, site_state=None, site_zip_code=None,
                                             notes=None, private_notes=None, project_folder=None):
        
        with self.database.connection_context():
            quote_data = self.get_quote_by_document_id(document_id)
            if not quote_data:
                return False
            
            quote = quote_data['quote']
            customer = quote_data['customer']
            billing_address = quote_data['billing_address']
            site_address = quote_data['site_address']
            
            old_customer_name = customer.customer_name
            customer_updated = self.safe_execute(
                f"updating customer ID {customer.id}",
                lambda: Customers.update(
                    customer_name=customer_name,
                    company_name=company_name,
                    phone_number=phone_number,
                    email=email
                ).where(Customers.id == customer.id).execute(),
                reraise_integrity=True
            )
            
            if old_customer_name != customer_name:
                try:
                    new_folder, _, _ = project_folder_manager.rename_project_folder(old_customer_name, customer_name, self.logger)
                    project_folder = str(new_folder)
                except Exception as e:
                    self.logger.warning(f"Failed to rename project folder: {e}")
            
            if billing_address_line and billing_city and billing_state and billing_zip_code:
                if billing_address:
                    self.safe_execute(
                        f"updating billing address ID {billing_address.id}",
                        lambda: Addresses.update(
                            address_line=billing_address_line,
                            city=billing_city,
                            state=billing_state,
                            zip_code=billing_zip_code
                        ).where(Addresses.id == billing_address.id).execute(),
                        reraise_integrity=True
                    )
                else:
                    new_billing_address = self.safe_execute(
                        "creating new billing address",
                        lambda: Addresses.create(
                            address_line=billing_address_line,
                            city=billing_city,
                            state=billing_state,
                            zip_code=billing_zip_code
                        ),
                        reraise_integrity=True
                    )
                    
                    if new_billing_address:
                        self.safe_execute(
                            "linking new billing address to document",
                            lambda: DocumentAddress.create(
                                document=quote.document,
                                address=new_billing_address,
                                address_type="billing"
                            ),
                            reraise_integrity=True
                        )
            
            if site_address_line and site_city and site_state and site_zip_code:
                if site_address:
                    self.safe_execute(
                        f"updating site address ID {site_address.id}",
                        lambda: Addresses.update(
                            address_line=site_address_line,
                            city=site_city,
                            state=site_state,
                            zip_code=site_zip_code
                        ).where(Addresses.id == site_address.id).execute(),
                        reraise_integrity=True
                    )
                else:
                    new_site_address = self.safe_execute(
                        "creating new site address",
                        lambda: Addresses.create(
                            address_line=site_address_line,
                            city=site_city,
                            state=site_state,
                            zip_code=site_zip_code
                        ),
                        reraise_integrity=True
                    )
                    
                    if new_site_address:
                        self.safe_execute(
                            "linking new site address to document",
                            lambda: DocumentAddress.create(
                                document=quote.document,
                                address=new_site_address,
                                address_type="service"
                            ),
                            reraise_integrity=True
                        )
            
            document_updated = self.safe_execute(
                f"updating document for ID {document_id}",
                lambda: Documents.update(
                    updated_at=datetime.now(timezone.utc),
                    project_folder=project_folder,
                    notes=notes,
                    private_notes=private_notes
                ).where(Documents.id == document_id).execute(),
                reraise_integrity=True
            )
            
            return customer_updated > 0 and document_updated > 0
    
    def list_quotes(self):
        def _query():
            result = []
            quotes = (Quote
                     .select()
                     .join(Documents, on=(Quote.document == Documents.id))
                     .join(Customers)
                     .where(Documents.status == 'open')
                     .order_by(Documents.created_at.desc()))
            for quote in quotes:
                doc = quote.document
                cust = doc.customer
                billing_address = None
                site_address = None
                
                try:
                    doc_addresses = DocumentAddress.select().where(DocumentAddress.document == doc)
                    for doc_addr in doc_addresses:
                        if doc_addr.address_type == "billing":
                            billing_address = doc_addr.address
                        elif doc_addr.address_type == "service":
                            site_address = doc_addr.address
                except DocumentAddress.DoesNotExist:
                    pass
                
                result.append({
                    'id': doc.id,
                    'date': doc.created_at.strftime('%Y-%m-%d'),
                    'customer_name': cust.customer_name or '',
                    'company_name': cust.company_name or '',
                    'phone_number': cust.phone_number or '',
                    'billing_city': billing_address.city if billing_address else '',
                    'billing_state': billing_address.state if billing_address else '',
                    'site_city': site_address.city if site_address else '',
                    'site_state': site_address.state if site_address else ''
                })
            return result
        return self.safe_execute("listing quotes", _query, default_return=[])
    
    def add_quote_item(self, document_id, item_number, product_service, quantity, unit_price):
        total = quantity * unit_price
        return self.safe_execute(
            f"adding item to quote document ID {document_id}",
            lambda: Items.create(
                document=document_id,
                item_number=item_number,
                product_service=product_service,
                quantity=quantity,
                unit_price=unit_price,
                total=total
            ),
            reraise_integrity=True
        )
    
    def get_quote_items(self, document_id):
        def _query():
            items = (Items
                    .select()
                    .where(Items.document == document_id)
                    .order_by(Items.item_number))
            return [
                {
                    'id': item.id,
                    'item_number': item.item_number,
                    'product_service': item.product_service,
                    'quantity': item.quantity,
                    'unit_price': item.unit_price,
                    'total': item.total
                }
                for item in items
            ]
        return self.safe_execute(f"fetching items for quote document ID {document_id}", _query, default_return=[])
    
    def update_quote_item(self, item_id, product_service=None, quantity=None, unit_price=None):
        fields = {}
        if product_service is not None:
            fields['product_service'] = product_service
        if quantity is not None:
            fields['quantity'] = quantity
        if unit_price is not None:
            fields['unit_price'] = unit_price
        
        if quantity is not None and unit_price is not None:
            fields['total'] = quantity * unit_price
        elif quantity is not None:
            item = self.safe_execute(
                f"fetching item ID {item_id} for total calculation",
                lambda: Items.get_by_id(item_id)
            )
            if item:
                fields['total'] = quantity * item.unit_price
        elif unit_price is not None:
            item = self.safe_execute(
                f"fetching item ID {item_id} for total calculation",
                lambda: Items.get_by_id(item_id)
            )
            if item:
                fields['total'] = item.quantity * unit_price
        
        return self.safe_execute(
            f"updating item ID {item_id}",
            lambda: Items.update(**fields).where(Items.id == item_id).execute(),
            reraise_integrity=True
        )
    
    def delete_quote_item(self, item_id):
        rows = self.safe_execute(
            f"deleting item ID {item_id}",
            lambda: Items.delete().where(Items.id == item_id).execute(),
            default_return=0,
            reraise_integrity=False
        )
        if rows == 0:
            raise Exception(f"Failed to delete item ID {item_id}")
        return True
    
    def convert_quote_to_job(self, document_id):
        with self.database.connection_context():
            quote_data = self.get_quote_by_document_id(document_id)
            if not quote_data:
                return None

            quote = quote_data["quote"]
            customer = quote_data["customer"]
            billing_address = quote_data["billing_address"]
            site_address = quote_data["site_address"]
            original_document = quote_data["document"]

            new_document = self.safe_execute(
                "creating new job document",
                lambda: Documents.create(
                    customer=customer,
                    doc_type="Job",
                    project_folder=original_document.project_folder,
                    status="Scheduled"
                ),
                reraise_integrity=True,
            )
            if not new_document:
                return None

            if billing_address:
                self.safe_execute(
                    "link billing",
                    lambda: DocumentAddress.create(
                        document=new_document,
                        address=billing_address,
                        address_type="billing",
                    ),
                    reraise_integrity=True,
                )
            if site_address:
                self.safe_execute(
                    "link site",
                    lambda: DocumentAddress.create(
                        document=new_document,
                        address=site_address,
                        address_type="service",
                    ),
                    reraise_integrity=True,
                )

            job = self.safe_execute(
                "create job",
                lambda: Job.create(document=new_document, converted_from_quote=original_document),
                reraise_integrity=True,
            )
            if not job:
                return None

            items = self.safe_execute(
                "collect items",
                lambda: list(Items.select().where(Items.document == document_id)),
                default_return=[],
            )
            for i in items:
                self.safe_execute(
                    "copy item",
                    lambda j=i: Items.create(
                        document=new_document,
                        item_number=j.item_number,
                        product_service=j.product_service,
                        quantity=j.quantity,
                        unit_price=j.unit_price,
                        total=j.total,
                    ),
                    reraise_integrity=True,
                )

            try:
                self.safe_execute(
                    "flag converted",
                    lambda: Documents.update(
                        private_notes=(original_document.private_notes or "") + f"\n[auto] Converted to Job {new_document.id}",
                    ).where(Documents.id == document_id).execute(),
                    reraise_integrity=False,
                )
            except Exception:
                pass

            # mark quote document as converted
            self.safe_execute(
                "update quote document status",
                lambda: Documents.update(status='converted').where(Documents.id == document_id).execute(),
                reraise_integrity=False,
            )

            return new_document.id

    def delete_items_by_document(self, document_id):
        return self.safe_execute(f"deleting items for quote document ID {document_id}", lambda: Items.delete().where(Items.document == document_id).execute(), reraise_integrity=False) 