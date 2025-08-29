from librepy.model.base_dao import BaseDAO
from librepy.model.model import Request, Documents, Customers, Addresses, DocumentAddress, Quote
from librepy.peewee.peewee import prefetch
from datetime import datetime, timezone
from librepy.utils import project_folder_manager


class RequestDAO(BaseDAO):
    
    def __init__(self, logger):
        super().__init__(Request, logger)
    
    def create_request_with_customer_and_address(self, customer_name, phone_number, 
                                               company_name=None, email=None,
                                               address_line=None, city=None, state=None, zip_code=None,
                                               information=None, residential_commercial=None,
                                               day_works_best=None, another_day=None, preferred_time=None,
                                               project_folder=None):
        
        with self.database.connection_context():
            # Create customer
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
            
            # Create address if provided
            address = None
            if address_line and city and state and zip_code:
                address = self.safe_execute(
                    "creating address",
                    lambda: Addresses.create(
                        address_line=address_line,
                        city=city,
                        state=state,
                        zip_code=zip_code
                    ),
                    reraise_integrity=True
                )
            
            # Create document
            document = self.safe_execute(
                "creating document",
                lambda: Documents.create(
                    customer=customer,
                    doc_type="Request",
                    project_folder=project_folder
                ),
                reraise_integrity=True
            )
            
            # Link address to document if address was created
            if address:
                self.safe_execute(
                    "linking address to document",
                    lambda: DocumentAddress.create(
                        document=document,
                        address=address,
                        address_type="service"
                    ),
                    reraise_integrity=True
                )
            
            # Create request
            request = self.safe_execute(
                "creating request",
                lambda: Request.create(
                    document=document,
                    information=information,
                    residential_commercial=residential_commercial,
                    day_works_best=day_works_best,
                    another_day=another_day,
                    preferred_time=preferred_time
                ),
                reraise_integrity=True
            )
            
            return document.id if document else None
    
    def convert_request_to_quote(self, document_id):
        """
        Convert a request to a quote by creating a new quote document 
        and marking the original request as converted.
        
        Args:
            document_id (int): The document ID of the request to convert
            
        Returns:
            int: The new quote document ID if successful, None otherwise
        """
        with self.database.connection_context():
            # Get the full request data
            request_data = self.get_request_by_document_id(document_id)
            if not request_data:
                self.logger.error(f"Request not found for document ID {document_id}")
                return None
            
            request = request_data['request']
            customer = request_data['customer']
            address = request_data['address']
            original_document = request_data['document']
            
            # Create new document for the quote
            new_document = self.safe_execute(
                "creating new quote document",
                lambda: Documents.create(
                    customer=customer,
                    doc_type="Quote",
                    project_folder=original_document.project_folder
                ),
                reraise_integrity=True
            )
            
            if not new_document:
                return None
            
            # Duplicate address if it exists
            if address:
                self.safe_execute(
                    "linking address to new quote document",
                    lambda: DocumentAddress.create(
                        document=new_document,
                        address=address,
                        address_type="service"  # Will be used as site address in quote
                    ),
                    reraise_integrity=True
                )
            
            # Create the quote record (with conversion tracking)
            quote = self.safe_execute(
                "creating quote record",
                lambda: Quote.create(
                    document=new_document,
                    notes=None,
                    private_notes=request.information,
                    converted_from_request=original_document
                ),
                reraise_integrity=True
            )
            
            if not quote:
                return None
            
            # Mark the original request as converted
            converted = self.safe_execute(
                f"marking request document as converted for ID {document_id}",
                lambda: Documents.update(status='converted').where(Documents.id == document_id).execute(),
                reraise_integrity=True
            )
            
            if converted > 0:
                self.logger.info(f"Successfully converted request {document_id} to quote {new_document.id}")
                return new_document.id
            else:
                self.logger.error(f"Failed to mark request {document_id} as converted")
                return None
    
    def get_request_by_document_id(self, document_id):
        return self.safe_execute(
            f"fetching request for document ID {document_id}",
            lambda: self._get_request_with_full_details(document_id)
        )
    
    def _get_request_with_full_details(self, document_id):
        query = (Request
                .select()
                .join(Documents)
                .join(Customers)
                .where(Request.document == document_id))
        
        request = query.get()
        
        # Get address if exists
        address_query = (DocumentAddress
                        .select()
                        .join(Addresses)
                        .where(DocumentAddress.document == document_id))
        
        try:
            doc_address = address_query.get()
            address = doc_address.address
        except:
            address = None
        
        # Return a dict with all the data the UI expects
        return {
            'request': request,
            'customer': request.document.customer,
            'address': address,
            'document': request.document
        }
    
    def update_request_with_customer_and_address(self, document_id, customer_name, phone_number,
                                               company_name=None, email=None,
                                               address_line=None, city=None, state=None, zip_code=None,
                                               information=None, residential_commercial=None,
                                               day_works_best=None, another_day=None, preferred_time=None,
                                               project_folder=None):
        
        with self.database.connection_context():
            # Get the request and related data
            request_data = self.get_request_by_document_id(document_id)
            if not request_data:
                return False
            
            request = request_data['request']
            customer = request_data['customer']
            address = request_data['address']
            
            # Update customer
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
            
            # Update or create address
            if address_line and city and state and zip_code:
                if address:
                    # Update existing address
                    self.safe_execute(
                        f"updating address ID {address.id}",
                        lambda: Addresses.update(
                            address_line=address_line,
                            city=city,
                            state=state,
                            zip_code=zip_code
                        ).where(Addresses.id == address.id).execute(),
                        reraise_integrity=True
                    )
                else:
                    # Create new address
                    new_address = self.safe_execute(
                        "creating new address",
                        lambda: Addresses.create(
                            address_line=address_line,
                            city=city,
                            state=state,
                            zip_code=zip_code
                        ),
                        reraise_integrity=True
                    )
                    
                    # Link to document
                    if new_address:
                        self.safe_execute(
                            "linking new address to document",
                            lambda: DocumentAddress.create(
                                document=request.document,
                                address=new_address,
                                address_type="service"
                            ),
                            reraise_integrity=True
                        )
            
            # Update request
            request_updated = self.safe_execute(
                f"updating request for document ID {document_id}",
                lambda: Request.update(
                    information=information,
                    residential_commercial=residential_commercial,
                    day_works_best=day_works_best,
                    another_day=another_day,
                    preferred_time=preferred_time
                ).where(Request.document == document_id).execute(),
                reraise_integrity=True
            )
            
            # Update document timestamp and project folder
            self.safe_execute(
                f"updating document timestamp and project_folder for ID {document_id}",
                lambda: Documents.update(
                    updated_at=datetime.now(timezone.utc),
                    project_folder=project_folder
                ).where(Documents.id == document_id).execute(),
                reraise_integrity=True
            )
            
            return customer_updated > 0 and request_updated > 0 
    
    def list_requests(self):
        """Return list of dicts representing open requests for list view"""
        def _query():
            result = []
            requests = (Request
                        .select()
                        .join(Documents)
                        .join(Customers)
                        .where(Documents.status == 'open')  # Only show open requests
                        .order_by(Documents.created_at.desc()))
            for req in requests:
                doc = req.document
                cust = doc.customer
                try:
                    doc_address = DocumentAddress.get(DocumentAddress.document == doc)
                    addr = doc_address.address
                except DocumentAddress.DoesNotExist:
                    addr = None
                result.append({
                    'id': doc.id,
                    'date': doc.created_at.strftime('%Y-%m-%d'),
                    'customer_name': cust.customer_name or '',
                    'company_name': cust.company_name or '',
                    'phone_number': cust.phone_number or '',
                    'city': addr.city if addr else '',
                    'state': addr.state if addr else ''
                })
            return result
        return self.safe_execute("listing requests", _query, default_return=[]) 