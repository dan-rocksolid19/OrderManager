from librepy.pybrex.dialog import DialogBase


class RescheduleChoiceDialog(DialogBase):
    POS_SIZE = 0, 0, 360, 180
    DISPOSE = True

    def __init__(self, ctx, smgr, title: str, message: str, parent=None, **props):
        self.choice = None
        self._title = title
        self._message = message
        self._parent = parent
        super().__init__(ctx, smgr, **props)

    def _create(self):
        # Basic window
        self._dialog.Title = self._title or "Confirm Reschedule"
        # Message label
        x, y, w, h = 10, 15, self.POS_SIZE[2] - 20, 60
        self.add_label("MessageLabel", x, y, w, h, Label=self._message, MultiLine=True)
        # Buttons
        bw, bh, bs = 90, 24, 10
        total_w = bw * 3 + bs * 2
        btn_y = self.POS_SIZE[3] - bh - 20
        start_x = (self.POS_SIZE[2] - total_w) // 2
        # Continue without reschedule
        self.btn_no_res = self.add_button(
            "NoResBtn", start_x, btn_y, bw, bh, Label="Continue without reschedule",
            callback=self._on_continue_no_res, BackgroundColor=0x2E7D32, TextColor=0xFFFFFF
        )
        # Cancel (middle)
        self.btn_cancel = self.add_button(
            "CancelBtn", start_x + bw + bs, btn_y, bw, bh, Label="Cancel",
            callback=self._on_cancel, BackgroundColor=0x808080, TextColor=0xFFFFFF
        )
        # Continue
        self.btn_continue = self.add_button(
            "ContinueBtn", start_x + (bw + bs) * 2, btn_y, bw, bh, Label="Continue",
            callback=self._on_continue, BackgroundColor=0x2C3E50, TextColor=0xFFFFFF
        )

    def _on_continue(self, event=None):
        self.choice = "continue"
        self.end_execute(1)

    def _on_continue_no_res(self, event=None):
        self.choice = "continue_no_reschedule"
        self.end_execute(1)

    def _on_cancel(self, event=None):
        self.choice = "cancel"
        self.end_execute(0)
