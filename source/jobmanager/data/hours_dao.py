from datetime import date
from decimal import Decimal
from librepy.model.base_dao import BaseDAO
from librepy.model.model import Hours, Documents

class HoursDAO(BaseDAO):
    def __init__(self, logger):
        super().__init__(Hours, logger)

    def add_hours(self, document_id: int, employee: str, work_date: date, hours: Decimal, rate: Decimal):
        total = hours * rate
        return self.safe_execute(
            f"adding hours for document ID {document_id}",
            lambda: Hours.create(
                document=document_id,
                employee=employee,
                work_date=work_date,
                hours=hours,
                rate=rate,
                total=total,
            ),
            reraise_integrity=True,
        )

    def get_hours(self, document_id: int):
        def _query():
            q = Hours.select().where(Hours.document == document_id).order_by(Hours.work_date)
            return [
                {
                    "id": h.id,
                    "employee": h.employee,
                    "work_date": h.work_date,
                    "hours": h.hours,
                    "rate": h.rate,
                    "total": h.total,
                }
                for h in q
            ]

        return self.safe_execute(
            f"fetching hours for document ID {document_id}", _query, default_return=[]
        )

    def update_hours(self, entry_id: int, employee=None, work_date=None, hours=None, rate=None):
        fields = {}
        if employee is not None:
            fields["employee"] = employee
        if work_date is not None:
            fields["work_date"] = work_date
        if hours is not None:
            fields["hours"] = hours
        if rate is not None:
            fields["rate"] = rate
        if hours is not None or rate is not None:
            if "hours" not in fields:
                rec = self.get_by_id(entry_id)
                if rec:
                    fields["hours"] = rec.hours
            if "rate" not in fields:
                rec = self.get_by_id(entry_id)
                if rec:
                    fields["rate"] = rec.rate
            if "hours" in fields and "rate" in fields:
                fields["total"] = Decimal(fields["hours"]) * Decimal(fields["rate"])
        return self.safe_execute(
            f"updating hours ID {entry_id}",
            lambda: Hours.update(**fields).where(Hours.id == entry_id).execute(),
            reraise_integrity=True,
        )

    def delete_hours(self, entry_id: int):
        rows = self.safe_execute(
            f"deleting hours ID {entry_id}",
            lambda: Hours.delete().where(Hours.id == entry_id).execute(),
            default_return=0,
            reraise_integrity=False,
        )
        if rows == 0:
            raise Exception(f"Failed to delete hours ID {entry_id}")
        return True 