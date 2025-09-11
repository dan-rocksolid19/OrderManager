from datetime import datetime
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex.msgbox import msgbox, confirm_action
from librepy.pybrex.uno_date_time_converters import uno_date_to_python, python_date_to_uno
from librepy.jobmanager.data.status_dao import StatusDAO


class EntryDialog(DialogBase):
    POS_SIZE = 0, 0, 360, 320
    DISPOSE = True

    def __init__(self, parent, ctx, smgr, frame, ps, edit_mode=False, entry_data=None, **props):
        self.edit_mode = edit_mode
        self.entry_data = entry_data or {}
        self.entry_result = None
        self.delete_requested = False
        self.parent = parent
        self.logger = parent.logger if hasattr(parent, 'logger') else None
        self.ctx, self.smgr, self.frame, self.ps = ctx, smgr, frame, ps
        # Status data
        self.status_items = []  # list of (id, name, color)
        self.status_names = []
        # DAO for statuses (managed DB connection)
        self.status_dao = StatusDAO(self.logger)
        super().__init__(ctx, smgr, **props)

    def _create(self):
        self._dialog.Title = "Edit Calendar Entry" if self.edit_mode else "Add Calendar Entry"
        label_h, field_h, field_w, label_w = 15, 20, 180, 110
        x, y, dy = 10, 20, 30

        self.add_label("lbl_title", x, y, label_w, label_h, Label="Title:")
        self.title_edit = self.add_edit("TitleEdit", x + label_w + 10, y, field_w, field_h)

        self.add_label("lbl_sd", x, y + dy, label_w, label_h, Label="Start Date:")
        self.start_date = self.add_date("StartDate", x + label_w + 10, y + dy, field_w, field_h, Dropdown=True)

        self.add_label("lbl_ed", x, y + dy * 2, label_w, label_h, Label="End Date:")
        self.end_date = self.add_date("EndDate", x + label_w + 10, y + dy * 2, field_w, field_h, Dropdown=True)

        self.add_label("lbl_desc", x, y + dy * 3, label_w, label_h, Label="Description:")
        self.desc_edit = self.add_edit("DescEdit", x + label_w + 10, y + dy * 3, field_w, field_h)

        # Status dropdown
        self.add_label("lbl_status", x, y + dy * 4, label_w, label_h, Label="Status:")
        self.status_combo = self.add_combo("StatusCombo", x + label_w + 10, y + dy * 4, field_w, field_h, Dropdown=True)

        # New fields: Reminder, Days Before, Lock Dates
        self.reminder_chk = self.add_checkbox("ReminderChk", x + label_w + 10, y + dy * 5, 100, field_h, Label="Reminder")
        self.add_label("lbl_days_before", x, y + dy * 6, label_w, label_h, Label="Days before:")
        self.days_before_edit = self.add_edit("DaysBeforeEdit", x + label_w + 10, y + dy * 6, 60, field_h)
        self.lock_dates_chk = self.add_checkbox("LockDatesChk", x + label_w + 10, y + dy * 7, 120, field_h, Label="Lock dates")

        btn_y = y + dy * 8 + 10
        bw, bh, bs = 90, 25, 10
        if self.edit_mode:
            total_w = bw * 3 + bs * 2
            start_x = (self.POS_SIZE[2] - total_w) // 2
            self.delete_btn = self.add_button("DeleteButton", start_x, btn_y, bw, bh, Label="Delete", callback=self.delete_entry, BackgroundColor=0xD93025, TextColor=0xFFFFFF)
            self.cancel_btn = self.add_cancel("CancelButton", start_x + bw + bs, btn_y, bw, bh, BackgroundColor=0x808080, TextColor=0xFFFFFF)
            self.save_btn = self.add_button("SaveButton", start_x + (bw + bs) * 2, btn_y, bw, bh, Label="Save", callback=self.save_entry, BackgroundColor=0x2C3E50, TextColor=0xFFFFFF)
        else:
            cx = (self.POS_SIZE[2] - (bw * 2 + bs)) // 2
            self.cancel_btn = self.add_cancel("CancelButton", cx, btn_y, bw, bh, BackgroundColor=0x808080, TextColor=0xFFFFFF)
            self.save_btn = self.add_button("SaveButton", cx + bw + bs, btn_y, bw, bh, Label="Save", callback=self.save_entry, BackgroundColor=0x2C3E50, TextColor=0xFFFFFF)

    def _load_statuses(self):
        try:
            rows = self.status_dao.get_all_statuses()
            self.status_items = [(r.status_id, r.status, r.color) for r in rows]
            self.status_names = [r.status for r in rows]
            self.status_combo.Model.StringItemList = tuple(self.status_names)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error loading CalendarEntryStatus: {e}")
            self.status_items = []
            self.status_names = []
            self.status_combo.Model.StringItemList = tuple()

    def _prepare(self):
        self._load_statuses()
        if self.entry_data:
            # Title
            self.title_edit.Text = self.entry_data.get('title') or self.entry_data.get('event_name', '')
            # Start date
            sd = self.entry_data.get('start_date')
            if sd:
                try:
                    d = sd if hasattr(sd, 'year') else datetime.strptime(str(sd), '%Y-%m-%d').date()
                    self.start_date.setDate(python_date_to_uno(d))
                except Exception:
                    pass
            # End date
            ed = self.entry_data.get('end_date')
            if ed:
                try:
                    d = ed if hasattr(ed, 'year') else datetime.strptime(str(ed), '%Y-%m-%d').date()
                    self.end_date.setDate(python_date_to_uno(d))
                except Exception:
                    pass
            # Description
            self.desc_edit.Text = self.entry_data.get('description') or self.entry_data.get('event_description', '')
            # New fields
            self.reminder_chk.State = 1 if self.entry_data.get('reminder') else 0
            db = self.entry_data.get('days_before')
            self.days_before_edit.Text = '' if db is None else str(db)
            self.lock_dates_chk.State = 1 if self.entry_data.get('lock_dates') else 0
            # Preselect status
            desired_id = self.entry_data.get('status_id')
            desired_name = self.entry_data.get('status')
            idx = -1
            if desired_id is not None:
                for i, (sid, name, _c) in enumerate(self.status_items):
                    if sid == desired_id:
                        idx = i
                        break
            elif desired_name:
                for i, (_sid, name, _c) in enumerate(self.status_items):
                    if name == desired_name:
                        idx = i
                        break
            if 0 <= idx < len(self.status_names):
                self.status_combo.Text = self.status_names[idx]

    def _get_selected_status_id(self):
        sname = (self.status_combo.getText() or '').strip()
        if not sname:
            return None
        for sid, name, _c in self.status_items:
            if name == sname:
                return sid
        return None

    def save_entry(self, event=None):
        title = self.title_edit.Text.strip()
        sd_uno = self.start_date.getDate()
        ed_uno = self.end_date.getDate()
        if not hasattr(sd_uno, 'Year') or sd_uno.Year <= 0:
            msgbox("Start Date is required.", "Validation Error")
            return
        sd_py = uno_date_to_python(sd_uno)
        ed_py = None
        if hasattr(ed_uno, 'Year') and ed_uno.Year > 0:
            ed_py = uno_date_to_python(ed_uno)
        # Default end date to start date if empty
        if ed_py and ed_py < sd_py:
            msgbox("End Date cannot be before Start Date.", "Validation Error")
            return
        # Validate reminder/days_before
        reminder = bool(self.reminder_chk.State)
        days_before_val = self.days_before_edit.Text.strip()
        days_before = None
        if reminder:
            if days_before_val == '':
                days_before = 0
            else:
                try:
                    days_before = int(days_before_val)
                except ValueError:
                    msgbox("Days before must be a whole number.", "Validation Error")
                    return
                if days_before < 0:
                    msgbox("Days before cannot be negative.", "Validation Error")
                    return
        lock_dates = bool(self.lock_dates_chk.State)
        status_id = self._get_selected_status_id()
        status_text = (self.status_combo.getText() or '').strip()
        self.logger.debug(f"EntryDialog.save_entry: status_text='{status_text}', status_id={status_id}")

        self.entry_result = {
            'event_name': title,
            'start_date': sd_py,
            'end_date': ed_py,
            'event_description': self.desc_edit.Text.strip(),
            'reminder': reminder,
            'days_before': days_before,
            'lock_dates': lock_dates,
            'status_id': status_id,
        }

        if 'order_id' in self.entry_data and self.entry_data.get('order_id') is not None:
                    self.entry_result['order_id'] = self.entry_data['order_id']

        if not self.entry_result.get('end_date') and self.entry_result.get('start_date'):
            self.entry_result['end_date'] = self.entry_result['start_date']

        if not self.edit_mode:
            from librepy.jobmanager.data.calendar_entry_order_dao import CalendarEntryOrderDAO

            dao = CalendarEntryOrderDAO(self.logger)
            new_id = dao.create_entry(self.entry_result)
            if new_id:
                self.logger.info(f"EntryDialog.save_entry: created CalendarEntryOrder entry_id={new_id}")
            else:
                self.logger.error(f"EntryDialog.save_entry: DAO create failed; payload={self.entry_result}")
                msgbox("Failed to create the calendar entry.", "Error")
                return
        else:
            # Edit mode: only reschedule neighbors when dates changed
            from librepy.jobmanager.data.calendar_entry_order_dao import CalendarEntryOrderDAO
            from librepy.jobmanager.components.calendar import job_scheduler as scheduler

            dao = CalendarEntryOrderDAO(self.logger)
            entry_id = self.entry_data.get('id') if self.entry_data else None
            if not entry_id:
                msgbox("Missing entry id for edit.", "Error")
                return

            # Original dates
            orig_sd = self.entry_data.get('start_date')
            orig_ed = self.entry_data.get('end_date') or orig_sd

            # New dates
            new_sd = self.entry_result.get('start_date')
            new_ed = self.entry_result.get('end_date') or new_sd

            dates_changed = (orig_sd != new_sd) or (orig_ed != new_ed)

            if not dates_changed:
                ok = dao.update_entry(entry_id, self.entry_result)
                if not ok:
                    msgbox("Failed to update the calendar entry.", "Error")
                    return
                self.logger.info(f"EntryDialog.save_entry: updated entry_id={entry_id} (no date change)")
            else:
                try:
                    moves = scheduler.apply_block_shift(
                        dao=dao,
                        entry_id=entry_id,
                        updated_data=self.entry_result,
                        logger=self.logger
                    )
                except scheduler.SchedulerError as e:
                    msgbox(f"Failed to save changes: {e}", "Error")
                    return
                self.logger.info(f"EntryDialog.save_entry: rescheduled entry_id={entry_id}; applied {len(moves)} moves")

        self.logger.debug(f"EntryDialog.save_entry: payload={self.entry_result}")
        self.end_execute(1)

    def delete_entry(self, event=None):
        # Ask for confirmation while dialog is still open; only close on confirm
        try:
            if confirm_action("Delete this entry?", "Confirm"):
                self.delete_requested = True
                self.end_execute(2)
            else:
                # User canceled; keep the dialog open for further editing
                return
        except Exception as e:
            if self.logger:
                try:
                    self.logger.error(f"Error during delete confirmation: {e}")
                except Exception:
                    pass

    def get_entry_data(self):
        return self.entry_result
