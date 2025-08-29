from decimal import Decimal

from librepy.pybrex.dialog import DialogBase
from librepy.pybrex.msgbox import msgbox


class QuantityDialog(DialogBase):
    POS_SIZE = 0, 0, 150, 60
    DISPOSE = True

    def __init__(self, parent, ctx, smgr, frame, ps, initial_quantity=None, **props):
        self.quantity = initial_quantity if initial_quantity is not None else Decimal("1")
        self.initial_quantity = initial_quantity
        super().__init__(ctx, smgr, **props)

    def _create(self):
        self._dialog.Title = "Quantity"
        self.add_label("QtyLabel", 5, 20, 40, 15, Label="Quantity:", FontHeight=12, FontWeight=150, Align=2, VerticalAlign=1)
        self.qty_numeric = self.add_numeric("QtyNumeric", 50, 20, 90, 15, DecimalAccuracy=2, ValueMin=0)
        if self.initial_quantity is not None:
            self.qty_numeric.setValue(float(self.quantity))
        self.add_ok_cancel()

    def _done(self, ret):
        if ret == 1:
            val = self.qty_numeric.getValue()
            if val <= 0:
                msgbox("Quantity must be greater than 0.", "Invalid Quantity")
                return
            else:
                self.quantity = Decimal(str(val))
        return ret

    def get_quantity(self):
        return self.quantity 