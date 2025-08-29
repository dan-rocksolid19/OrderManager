from librepy.model.base_dao import BaseDAO
from librepy.model.model import Job, Documents, Customers, Addresses, DocumentAddress, Steps, Invoice, Items, Hours, Crews
from datetime import datetime, timezone, timedelta
from librepy.utils import project_folder_manager
from decimal import Decimal


class JobDAO(BaseDAO):
    
    # Crew color coding configuration
    CREW_COLORS = {
        'Crew 1': 0x3498DB,      # Blue
        'Crew 2': 0xE74C3C,      # Red  
        'Crew 3': 0x2ECC71,      # Green
        'Crew 4': 0xF39C12,      # Orange
        'Crew 5': 0x9B59B6,      # Purple
        'Crew 6': 0x1ABC9C,      # Teal
        'Crew 7': 0xF1C40F,      # Yellow
        'Crew 8': 0xE67E22,      # Dark Orange
        'Multiple': 0x95A5A6,    # Gray for multiple crews
        'Unassigned': 0xBDC3C7,  # Light Gray for unassigned
    }

    def __init__(self, logger):
        super().__init__(Job, logger)
    
    def create_job_with_customer_and_address(self, customer_name, phone_number, 
                                           company_name=None, email=None,
                                           billing_address_line=None, billing_city=None, billing_state=None, billing_zip_code=None,
                                           site_address_line=None, site_city=None, site_state=None, site_zip_code=None,
                                           status="Scheduled", project_folder=None):
        
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
                    doc_type="Job",
                    project_folder=project_folder,
                    status=status
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
            
            job = self.safe_execute(
                "creating job",
                lambda: Job.create(
                    document=document
                ),
                reraise_integrity=True
            )
            
            return document.id if document else None
    
    def get_jobs_by_date_range(self, start_date, end_date, crew_filter=None):
        """
        Get all jobs with steps that fall within the specified date range.
        
        Args:
            start_date (date): Start of date range
            end_date (date): End of date range  
            crew_filter (str, optional): Filter by specific crew name
            
        Returns:
            list: List of job dictionaries with step and customer information
        """
        def _query():
            # Query steps that overlap with the date range
            # A step overlaps if: step_start <= end_date AND step_end >= start_date
            query = (Steps
                    .select(Steps, Documents, Customers, Job)
                    .join(Documents, on=(Steps.document == Documents.id))
                    .join(Customers, on=(Documents.customer == Customers.id))
                    .join(Job, on=(Job.document == Documents.id))
                    .where(
                        (Documents.doc_type == "Job") &
                        (
                            (Steps.start_date <= end_date) &
                            (Steps.end_date >= start_date)
                        )
                    ))
            
            if crew_filter and crew_filter != "All, Crew 1...":
                query = query.where(Steps.crew_assigned == crew_filter)
            
            query = query.order_by(Steps.start_date, Steps.step_order)
            
            result = []
            for step in query:
                doc = step.document
                customer = doc.customer
                job = step.document.job.get()
                
                result.append({
                    'step_id': step.id,
                    'document_id': doc.id,
                    'step': step.step,
                    'step_order': step.step_order,
                    'start_date': step.start_date,
                    'end_date': step.end_date,
                    'crew_assigned': step.crew_assigned,
                    'customer_name': customer.customer_name,
                    'company_name': customer.company_name,
                    'phone_number': customer.phone_number,
                    'job_status': doc.status,
                    'created_at': doc.created_at
                })
            
            return result
        
        return self.safe_execute(
            f"fetching jobs for date range {start_date} to {end_date}",
            _query,
            default_return=[]
        )

    def get_jobs_for_date(self, target_date):
        """
        Get all jobs with steps scheduled for a specific date.
        
        Args:
            target_date (date): The specific date to query
            
        Returns:
            list: List of job dictionaries for the specified date
        """
        def _query():
            # Find steps where the target_date falls within start_date and end_date
            query = (Steps
                    .select(Steps, Documents, Customers, Job)
                    .join(Documents, on=(Steps.document == Documents.id))
                    .join(Customers, on=(Documents.customer == Customers.id))
                    .join(Job, on=(Job.document == Documents.id))
                    .where(
                        (Documents.doc_type == "Job") &
                        (Steps.start_date <= target_date) &
                        (Steps.end_date >= target_date)
                    )
                    .order_by(Steps.step_order))
            
            result = []
            for step in query:
                doc = step.document
                customer = doc.customer
                job = step.document.job.get()
                
                result.append({
                    'step_id': step.id,
                    'document_id': doc.id,
                    'step': step.step,
                    'step_order': step.step_order,
                    'start_date': step.start_date,
                    'end_date': step.end_date,
                    'crew_assigned': step.crew_assigned or 'Unassigned',
                    'customer_name': customer.customer_name,
                    'company_name': customer.company_name,
                    'phone_number': customer.phone_number,
                    'job_status': doc.status,
                    'created_at': doc.created_at
                })
            
            return result
        
        return self.safe_execute(
            f"fetching jobs for date {target_date}",
            _query,
            default_return=[]
        )

    def get_calendar_summary(self, start_date, end_date, crew_filter=None):
        """
        Get a summary of jobs grouped by date for calendar display.
        
        Args:
            start_date (date): Start of date range
            end_date (date): End of date range
            crew_filter (str): Optional crew name to filter by
            
        Returns:
            dict: Dictionary with dates as keys and job lists as values
        """
        def _query():
            jobs = self.get_jobs_by_date_range(start_date, end_date, crew_filter)
            
            # Group jobs by date
            calendar_data = {}
            
            for job in jobs:
                # Generate all dates this job spans
                current_date = job['start_date']
                end_date_job = job['end_date']
                
                while current_date <= end_date_job:
                    # Only include dates within our query range
                    if start_date <= current_date <= end_date:
                        date_str = current_date.strftime('%Y-%m-%d')
                        
                        if date_str not in calendar_data:
                            calendar_data[date_str] = []
                        
                        # Add job info for this date
                        calendar_data[date_str].append({
                            'document_id': job['document_id'],
                            'customer_name': job['customer_name'],
                            'crew_assigned': job['crew_assigned'],
                            'step': job['step'],
                            'job_status': job['job_status'],
                            'step_id': job['step_id']
                        })
                    
                    # Move to next day
                    current_date = current_date + timedelta(days=1)
            
            return calendar_data
        
        return self.safe_execute(
            f"generating calendar summary for {start_date} to {end_date}",
            _query,
            default_return={}
        )
    
    def get_job_by_document_id(self, document_id):
        return self.safe_execute(
            f"fetching job for document ID {document_id}",
            lambda: self._get_job_with_full_details(document_id)
        )
    
    def _get_job_with_full_details(self, document_id):
        query = (Job
                .select()
                .join(Documents, on=(Job.document == Documents.id))
                .switch(Documents)
                .join(Customers, on=(Documents.customer == Customers.id))
                .where(Job.document == document_id))
        
        job = query.get()
        
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
            'job': job,
            'customer': job.document.customer,
            'billing_address': billing_address,
            'site_address': site_address,
            'document': job.document
        }
    
    def update_job_with_customer_and_address(self, document_id, customer_name, phone_number,
                                           company_name=None, email=None,
                                           billing_address_line=None, billing_city=None, billing_state=None, billing_zip_code=None,
                                           site_address_line=None, site_city=None, site_state=None, site_zip_code=None,
                                           status=None, project_folder=None):
        
        with self.database.connection_context():
            job_data = self.get_job_by_document_id(document_id)
            if not job_data:
                return False
            
            job = job_data['job']
            customer = job_data['customer']
            billing_address = job_data['billing_address']
            site_address = job_data['site_address']
            
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
                                document=job.document,
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
                                document=job.document,
                                address=new_site_address,
                                address_type="service"
                            ),
                            reraise_integrity=True
                        )
            
            document_fields = {
                'updated_at': datetime.now(timezone.utc),
                'project_folder': project_folder
            }
            if status is not None:
                document_fields['status'] = status
            
            document_updated = self.safe_execute(
                f"updating document for ID {document_id}",
                lambda: Documents.update(**document_fields).where(Documents.id == document_id).execute(),
                reraise_integrity=True
            )
            
            return customer_updated > 0 or document_updated > 0
    
    def list_jobs(self):
        def _query():
            result = []
            jobs = (Job
                   .select()
                   .join(Documents, on=(Job.document == Documents.id))
                   .switch(Documents)
                   .join(Customers, on=(Documents.customer == Customers.id))
                   .where(Documents.status != 'converted')  # Add filter to exclude converted jobs
                   .order_by(Documents.created_at.desc()))
            for job in jobs:
                doc = job.document
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
                    'site_state': site_address.state if site_address else '',
                    'status': doc.status or 'Scheduled'
                })
            return result
        return self.safe_execute("listing jobs", _query, default_return=[])
    
    def mark_job_complete(self, document_id):
        """Convert a job to an invoice and mark it as completed"""
        with self.database.connection_context():
            job_data = self.get_job_by_document_id(document_id)
            if not job_data:
                return None

            job = job_data["job"]
            customer = job_data["customer"]
            billing_address = job_data["billing_address"]
            site_address = job_data["site_address"]
            original_document = job_data["document"]

            # Create new document for invoice
            new_document = self.safe_execute(
                "creating new invoice document",
                lambda: Documents.create(
                    customer=customer,
                    doc_type="Invoice",
                    project_folder=original_document.project_folder,
                    notes=original_document.notes,
                    private_notes=original_document.private_notes,
                    status="open"
                ),
                reraise_integrity=True,
            )
            if not new_document:
                return None

            # Link addresses to new document
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

            # Create invoice record
            invoice = self.safe_execute(
                "create invoice",
                lambda: Invoice.create(document=new_document),
                reraise_integrity=True,
            )
            if not invoice:
                return None

            # Copy items
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

            # Update original document
            try:
                self.safe_execute(
                    "flag converted",
                    lambda: Documents.update(
                        private_notes=(original_document.private_notes or "") + f"\n[auto] Converted to Invoice {new_document.id}",
                    ).where(Documents.id == document_id).execute(),
                    reraise_integrity=False,
                )
            except Exception:
                pass

            # Mark job document as converted (not just completed)
            self.safe_execute(
                "update job document status",
                lambda: Documents.update(
                    status="converted",  # Changed from "Completed" to "converted"
                    updated_at=datetime.now(timezone.utc)
                ).where(Documents.id == document_id).execute(),
                reraise_integrity=False,
            )

            return {
                'job_updated': True,
                'invoice_created': True,
                'invoice_document_id': new_document.id
            }
    
    def add_job_step(self, document_id, step_order, step, start_date=None, end_date=None, crew_assigned=None):
        return self.safe_execute(
            f"adding step to job document ID {document_id}",
            lambda: Steps.create(
                document=document_id,
                step_order=step_order,
                step=step,
                start_date=start_date,
                end_date=end_date,
                crew_assigned=crew_assigned
            ),
            reraise_integrity=True
        )
    
    def get_job_steps(self, document_id):
        def _query():
            steps = (Steps
                    .select()
                    .where(Steps.document == document_id)
                    .order_by(Steps.step_order))
            return [
                {
                    'id': step.id,
                    'step_order': step.step_order,
                    'step': step.step,
                    'start_date': step.start_date.strftime('%Y-%m-%d') if step.start_date else '',
                    'end_date': step.end_date.strftime('%Y-%m-%d') if step.end_date else '',
                    'crew_assigned': step.crew_assigned or ''
                }
                for step in steps
            ]
        return self.safe_execute(f"fetching steps for job document ID {document_id}", _query, default_return=[])
    
    def update_job_step(self, step_id, step=None, start_date=None, end_date=None, crew_assigned=None):
        fields = {}
        if step is not None:
            fields['step'] = step
        if start_date is not None:
            fields['start_date'] = start_date
        if end_date is not None:
            fields['end_date'] = end_date
        if crew_assigned is not None:
            fields['crew_assigned'] = crew_assigned
        
        if not fields:
            return False
        
        return self.safe_execute(
            f"updating step ID {step_id}",
            lambda: Steps.update(**fields).where(Steps.id == step_id).execute(),
            reraise_integrity=True
        )
    
    def delete_job_step(self, step_id):
        rows = self.safe_execute(
            f"deleting step ID {step_id}",
            lambda: Steps.delete().where(Steps.id == step_id).execute(),
            default_return=0,
            reraise_integrity=False
        )
        if rows == 0:
            raise Exception(f"Failed to delete step ID {step_id}")
        return True

    def delete_items_by_document(self, document_id):
        """Delete all items associated with a document"""
        return self.safe_execute(
            f"deleting items for document ID {document_id}",
            lambda: Items.delete().where(Items.document == document_id).execute(),
            default_return=0,
            reraise_integrity=False
        )

    def delete_hours_by_document(self, document_id):
        """Delete all hours associated with a document"""
        return self.safe_execute(
            f"deleting hours for document ID {document_id}",
            lambda: Hours.delete().where(Hours.document == document_id).execute(),
            default_return=0,
            reraise_integrity=False
        )

    def add_job_item(self, document_id, item_number, product_service, quantity, unit_price):
        total = quantity * unit_price
        return self.safe_execute(
            f"adding item to job document ID {document_id}",
            lambda: Items.create(
                document=document_id,
                item_number=item_number,
                product_service=product_service,
                quantity=quantity,
                unit_price=unit_price,
                total=total,
            ),
            reraise_integrity=True,
        )

    def get_job_items(self, document_id):
        def _query():
            q = Items.select().where(Items.document == document_id).order_by(Items.item_number)
            return [
                {
                    "id": i.id,
                    "item_number": i.item_number,
                    "product_service": i.product_service,
                    "quantity": i.quantity,
                    "unit_price": i.unit_price,
                    "total": i.total,
                }
                for i in q
            ]

        return self.safe_execute(
            f"fetching items for job document ID {document_id}", _query, default_return=[]
        )

    def update_job_item(self, item_id, product_service=None, quantity=None, unit_price=None):
        fields = {}
        if product_service is not None:
            fields["product_service"] = product_service
        if quantity is not None:
            fields["quantity"] = quantity
        if unit_price is not None:
            fields["unit_price"] = unit_price
        if quantity is not None and unit_price is not None:
            fields["total"] = quantity * unit_price
        elif quantity is not None:
            rec = self.get_by_id(item_id, "fetching item for recalculation")
            if rec:
                fields["total"] = quantity * rec.unit_price
        elif unit_price is not None:
            rec = self.get_by_id(item_id, "fetching item for recalculation")
            if rec:
                fields["total"] = rec.quantity * unit_price
        return self.safe_execute(
            f"updating item ID {item_id}",
            lambda: Items.update(**fields).where(Items.id == item_id).execute(),
            reraise_integrity=True,
        )

    def delete_job_item(self, item_id):
        rows = self.safe_execute(
            f"deleting item ID {item_id}",
            lambda: Items.delete().where(Items.id == item_id).execute(),
            default_return=0,
            reraise_integrity=False,
        )
        if rows == 0:
            raise Exception(f"Failed to delete item ID {item_id}")
        return True

    def add_job_hours(self, document_id, employee, start_date, end_date, hours_val, rate):
        total = hours_val * rate
        return self.safe_execute(
            f"adding hours to job document ID {document_id}",
            lambda: Hours.create(
                document=document_id,
                employee=employee,
                start_date=start_date,
                end_date=end_date,
                hours=hours_val,
                rate=rate,
                total=total,
            ),
            reraise_integrity=True,
        )

    def get_job_hours(self, document_id):
        def _query():
            q = Hours.select().where(Hours.document == document_id).order_by(Hours.start_date)
            return [
                {
                    "id": h.id,
                    "employee": h.employee,
                    "start_date": h.start_date,
                    "end_date": h.end_date,
                    "hours": h.hours,
                    "rate": h.rate,
                    "total": h.total,
                }
                for h in q
            ]

        return self.safe_execute(
            f"fetching hours for job document ID {document_id}", _query, default_return=[]
        )

    def update_job_hours(self, entry_id, employee=None, start_date=None, end_date=None, hours_val=None, rate=None):
        fields = {}
        if employee is not None:
            fields["employee"] = employee
        if start_date is not None:
            fields["start_date"] = start_date
        if end_date is not None:
            fields["end_date"] = end_date
        if hours_val is not None:
            fields["hours"] = hours_val
        if rate is not None:
            fields["rate"] = rate
        if hours_val is not None or rate is not None:
            if "hours" not in fields or "rate" not in fields:
                rec = self.safe_execute(
                    f"fetching hours ID {entry_id} for recalc",
                    lambda: Hours.get_by_id(entry_id),
                )
                if rec:
                    if "hours" not in fields:
                        fields["hours"] = rec.hours
                    if "rate" not in fields:
                        fields["rate"] = rec.rate
            if "hours" in fields and "rate" in fields:
                fields["total"] = fields["hours"] * fields["rate"]
        return self.safe_execute(
            f"updating hours ID {entry_id}",
            lambda: Hours.update(**fields).where(Hours.id == entry_id).execute(),
            reraise_integrity=True,
        )

    def delete_job_hours(self, entry_id):
        rows = self.safe_execute(
            f"deleting hours ID {entry_id}",
            lambda: Hours.delete().where(Hours.id == entry_id).execute(),
            default_return=0,
            reraise_integrity=False,
        )
        if rows == 0:
            raise Exception(f"Failed to delete hours ID {entry_id}")
        return True

    def get_items_and_hours(self, document_id):
        items = self.get_job_items(document_id)
        hours_entries = self.get_job_hours(document_id)
        return {"items": items, "hours": hours_entries}

    def totals(self, document_id):
        items_total = sum([Decimal(str(i["total"])) for i in self.get_job_items(document_id)])
        hours_total = sum([Decimal(str(h["total"])) for h in self.get_job_hours(document_id)])
        grand_total = items_total + hours_total
        return {
            "items_total": items_total,
            "hours_total": hours_total,
            "grand_total": grand_total,
        }

    def get_crew_color(self, crew_name):
        """
        Get the color code for a specific crew.
        
        Args:
            crew_name (str): Name of the crew
            
        Returns:
            int: Color code in hex format
        """
        if not crew_name:
            return self.CREW_COLORS['Unassigned']
        return self.CREW_COLORS.get(crew_name, self.CREW_COLORS['Unassigned'])
    
    def get_day_primary_crew_color(self, jobs_for_day):
        """
        Determine the primary crew color for a day based on jobs.
        
        Args:
            jobs_for_day (list): List of job dictionaries for a specific day
            
        Returns:
            int: Color code for the day's primary crew
        """
        if not jobs_for_day:
            return self.CREW_COLORS['Unassigned']
        
        # Count crews for this day
        crew_counts = {}
        for job in jobs_for_day:
            crew = job.get('crew_assigned') or 'Unassigned'
            crew_counts[crew] = crew_counts.get(crew, 0) + 1
        
        # If multiple different crews, use 'Multiple' color
        if len(crew_counts) > 1:
            return self.CREW_COLORS['Multiple']
        
        # Single crew - return its color
        primary_crew = list(crew_counts.keys())[0]
        return self.get_crew_color(primary_crew)
    
    def get_available_crews(self):
        """
        Get list of available crews from the database.
        
        Returns:
            list: List of crew names
        """
        def _query():
            crews = Crews.select().order_by(Crews.crew_name)
            return [crew.crew_name for crew in crews]
        
        return self.safe_execute(
            "fetching available crews",
            _query,
            default_return=[]
        ) 