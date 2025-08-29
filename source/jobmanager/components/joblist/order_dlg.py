from datetime import date as _date
import traceback

from librepy.pybrex import dialog
from librepy.jobmanager.data.orders_dao import AcctTransDAO

# Calendar Entry dialog
try:
    from librepy.jobmanager.components.calendar.entry_dlg import EntryDialog
except Exception:
    from jobmanager.components.calendar.entry_dlg import EntryDialog


class OrderDialog(dialog.DialogBase):
    def _log_lifecycle(self, stage: str):
        try:
            import time, threading
            self._lifecycle_seq = getattr(self, '_lifecycle_seq', 0) + 1
            setattr(self, '_lifecycle_seq', self._lifecycle_seq)
            ts = time.perf_counter()
            tid = threading.get_ident()
            lbl_ready = bool(getattr(self, 'lbl_body', None) and hasattr(self.lbl_body, 'Model'))
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(
                    f"OrderDialog.lifecycle[{self._lifecycle_seq}] {stage} ts={ts:.6f} thread={tid} lbl_body_ready={lbl_ready}"
                )
        except Exception:
            pass
    POS_SIZE = (0, 0, 500, 280)
    MARGIN = 10
    LABEL_HEIGHT = 12
    TITLE_COLOR = 0x2B579A

    # def __init__(self, ctx, parent, logger, order_id: int, **props):
    def __init__(self, parent, ctx, smgr, frame, ps, order_id=None, **props):

        # Store context and params
        self.logger = parent.logger
        self.ctx = ctx
        self.parent = parent
        self.frame = frame
        self.ps = ps
        self.order_id = int(order_id)
        self.order = None  # Peewee model instance or None
        # UI state buffers/log sequence
        self._pending_label_text = None
        self._lifecycle_seq = 0
        # Visibility flag for Create Calendar Entry button; default hidden until data says otherwise
        self._show_create_cal_btn = False

        props.setdefault('Title', 'Order Details')
        props.setdefault('BackgroundColor', 0xFFFFFF)

        super().__init__(ctx, smgr, **props)

    def _set_create_btn_visible(self, visible: bool):
        """Centralize visibility toggling for the 'Create Calendar Entry' button with robust logging.
        Prefer control-level visibility (setVisible) and fall back to model.Visible only if present.
        """
        # Update flag and log transition
        prev = getattr(self, '_show_create_cal_btn', False)
        self._show_create_cal_btn = bool(visible)
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(
                    f"OrderDialog._set_create_btn_visible: changing visibility from {prev} to {self._show_create_cal_btn}"
                )
        except Exception:
            pass

        btn = getattr(self, 'btn_create_cal', None)
        if btn is None:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug("OrderDialog._set_create_btn_visible: btn_create_cal not yet created; will apply after _create")
            except Exception:
                pass
            return

        # Log capabilities prior to applying
        try:
            if hasattr(self, 'logger') and self.logger:
                has_set_visible = hasattr(btn, 'setVisible')
                mdl = getattr(btn, 'Model', None)
                has_model = mdl is not None
                model_has_visible = has_model and hasattr(mdl, 'Visible')
                self.logger.debug(
                    f"OrderDialog._set_create_btn_visible: caps setVisible={has_set_visible}, hasModel={has_model}, model.Visible={model_has_visible}"
                )
        except Exception:
            pass

        # Prefer control-level visibility via XWindow
        try:
            if hasattr(btn, 'setVisible'):
                btn.setVisible(self._show_create_cal_btn)
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug(f"OrderDialog._set_create_btn_visible: applied via control.setVisible({self._show_create_cal_btn})")
        except Exception:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.exception("OrderDialog._set_create_btn_visible: control.setVisible failed")
            except Exception:
                pass

        # Fallback to model.Visible if available
        try:
            mdl = getattr(btn, 'Model', None)
            if mdl is not None and hasattr(mdl, 'Visible'):
                mdl.Visible = self._show_create_cal_btn
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug(f"OrderDialog._set_create_btn_visible: applied via model.Visible={self._show_create_cal_btn}")
            else:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug("OrderDialog._set_create_btn_visible: model.Visible not available; cannot apply fallback")
        except Exception:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.exception("OrderDialog._set_create_btn_visible: model.Visible fallback failed")
            except Exception:
                pass

        # Apply layout after visibility change
        try:
            self._layout_buttons(self._show_create_cal_btn)
        except Exception:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug("OrderDialog._set_create_btn_visible: layout apply failed (non-fatal)")
            except Exception:
                pass

    def _layout_buttons(self, show_create: bool):
        """Compute and apply positions for OK and Create buttons.
        Ensures OK always renders; when Create is visible, both are centered as a group
        with OK to the right; when hidden, OK is centered alone. Positions kept at the same Y.
        """
        try:
            ok = getattr(self, 'ok_btn', None)
            create = getattr(self, 'btn_create_cal', None)
            if ok is None:
                return

            # Dimensions and spacing
            bw, bh, spacing = 160, 22, 10
            # Compute the Y position consistently (matches _create math):
            # y_btn = MARGIN + (LABEL_HEIGHT + 12) + LABEL_HEIGHT*10 + 10
            y_btn = self.MARGIN + (self.LABEL_HEIGHT + 12) + self.LABEL_HEIGHT * 10 + 10

            # X positions based on visibility
            if show_create and create is not None:
                total_w = bw * 2 + spacing
                start_x = (self.POS_SIZE[2] - total_w) // 2
                create_x = start_x
                ok_x = start_x + bw + spacing
                # Apply for Create button
                try:
                    mdl = getattr(create, 'Model', None)
                    if mdl is not None:
                        mdl.PositionX, mdl.PositionY, mdl.Width, mdl.Height = create_x, y_btn, bw, bh
                    elif hasattr(create, 'setPosSize'):
                        create.setPosSize(create_x, y_btn, bw, bh, 15)
                except Exception:
                    pass
            else:
                # Center OK alone
                ok_x = (self.POS_SIZE[2] - bw) // 2

            # Apply for OK button
            try:
                mdl_ok = getattr(ok, 'Model', None)
                if mdl_ok is not None:
                    mdl_ok.PositionX, mdl_ok.PositionY, mdl_ok.Width, mdl_ok.Height = ok_x, y_btn, bw, bh
                elif hasattr(ok, 'setPosSize'):
                    ok.setPosSize(ok_x, y_btn, bw, bh, 15)
            except Exception:
                pass
        except Exception:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.exception('OrderDialog._layout_buttons: unexpected error')
            except Exception:
                pass


    def _prepare(self):
        self._log_lifecycle('prepare:start')
        # Fetch a single sale order via DAO using provided ID, then populate the label
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug(f"OrderDialog._prepare: Loading order_id={self.order_id}")
        except Exception:
            pass
        try:
            dao = AcctTransDAO(self.logger)
            # Fetch order with a preferred address joined (BILLING by default)
            self.order = dao.get_sale_order_with_address_by_id(self.order_id)
        except Exception:
            # Log and keep None so UI can show friendly message
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.exception(f"Failed to load order {self.order_id}")
            except Exception:
                pass
            self.order = None
        # Build display text now that data is available
        # Decide create-button visibility based on has_calendar_entry flag projected by DAO
        try:
            visible = False
            if self.order is not None:
                has_cal = bool(getattr(self.order, 'has_calendar_entry', False))
                visible = not has_cal
                try:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.debug(f"OrderDialog._prepare: has_calendar_entry={has_cal} -> show_create_button={visible}")
                except Exception:
                    pass
            self._set_create_btn_visible(visible)
        except Exception:
            # On any error, keep it hidden to avoid offering an action that may fail
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.exception("OrderDialog._prepare: error deciding button visibility")
            except Exception:
                pass
            self._set_create_btn_visible(False)
        if not self.order:
            lines = [
                f"Order #: {self.order_id}",
                "Status: Not found or not a SALE order",
            ]
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.warning(f"OrderDialog._prepare: Order not found for id {self.order_id}")
            except Exception:
                pass
        else:
            o = self.order
            transid = getattr(o, 'transid', self.order_id)
            transdate = getattr(o, 'transdate', '')
            if isinstance(transdate, _date):
                transdate = transdate.strftime('%m/%d/%y')
            else:
                transdate = str(transdate) if transdate else ''
            referencenumber = getattr(o, 'referencenumber', '') or ''
            notes = getattr(o, 'notes', '') or ''
            org_obj = getattr(o, 'org', None)
            orgname = getattr(org_obj, 'orgname', '') if org_obj else ''
            phone = getattr(org_obj, 'phone', '') if org_obj else ''

            # Try to read the joined OrgAddress instance
            addr_obj = None
            chosen_attr = None
            for attr in ('orgaddress', 'org_address', 'OrgAddress'):
                if hasattr(o, attr):
                    addr_obj = getattr(o, attr)
                    chosen_attr = attr
                    break
            try:
                if hasattr(self, 'logger') and self.logger:
                    if addr_obj:
                        self.logger.debug(f"OrderDialog._prepare: Found joined OrgAddress via attribute '{chosen_attr}'")
                    else:
                        self.logger.debug("OrderDialog._prepare: No OrgAddress attribute present on order row (address not joined)")
            except Exception:
                pass

            # If no joined address is attached, fetch preferred address directly via DAO
            if not addr_obj and org_obj and getattr(org_obj, 'org_id', None):
                try:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.debug(f"OrderDialog._prepare: Fetching preferred address for org_id={org_obj.org_id}")
                    addr_obj = AcctTransDAO(self.logger).get_preferred_org_address(org_obj.org_id)
                except Exception as e:
                    try:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.error(f"OrderDialog._prepare: Error fetching preferred address: {e}")
                    except Exception:
                        pass

            # Build formatted address lines if available
            addr_lines = []
            if addr_obj:
                street = getattr(addr_obj, 'streetone', None)
                city = getattr(addr_obj, 'city', None)
                state = getattr(addr_obj, 'state', None)
                zip_code = getattr(addr_obj, 'zip', None)
                country = getattr(addr_obj, 'country', None)

                try:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.debug(f"OrderDialog._prepare: Address fields street='{street}', city='{city}', state='{state}', zip='{zip_code}', country='{country}'")
                except Exception:
                    pass

                if street:
                    addr_lines.append(street)
                # City, State ZIP
                parts = []
                if city:
                    parts.append(city)
                cs = ''
                if state:
                    cs = state
                if zip_code:
                    cs = f"{cs} {zip_code}".strip()
                if parts or cs:
                    if parts and cs:
                        addr_lines.append(f"{parts[0]}, {cs}")
                    elif parts:
                        addr_lines.append(parts[0])
                    elif cs:
                        addr_lines.append(cs)
                if country:
                    addr_lines.append(country)

                try:
                    if hasattr(self, 'logger') and self.logger:
                        self.logger.debug(f"OrderDialog._prepare: Formatted address lines: {addr_lines}")
                except Exception:
                    pass

            lines = [
                f"Order #: {transid}",
                f"Date: {transdate}",
                f"Reference: {referencenumber}",
                f"Customer: {orgname}",
                f"Phone: {phone}",
            ]
            if addr_lines:
                lines.append("Address:")
                lines.extend(addr_lines)
            lines.extend(["", f"Notes: {notes}"])

            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug(f"OrderDialog._prepare: Loaded order transid={transid}, reference='{referencenumber}'")
            except Exception:
                pass
        # Update label safely with buffering if label not yet created
        final_text = "\n".join(lines)
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug("OrderDialog._prepare: Final label text to apply:\n" + final_text)
                self.logger.debug(f"OrderDialog._prepare: lbl_body ready={bool(getattr(self, 'lbl_body', None) and hasattr(self.lbl_body, 'Model'))}")
        except Exception:
            pass
        try:
            if getattr(self, 'lbl_body', None) is not None and hasattr(self.lbl_body, 'Model'):
                self.lbl_body.Model.Label = final_text
                self._pending_label_text = None
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug("OrderDialog._prepare: Applied label to lbl_body")
            else:
                self._pending_label_text = final_text
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug("OrderDialog._prepare: lbl_body not ready; buffered label text")
        except Exception as e:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.error(f"OrderDialog._prepare: Failed to update label: {e}")
            except Exception:
                pass
        # Lifecycle log end
        self._log_lifecycle('prepare:end')

    def _create(self):
        self._log_lifecycle('create:start')
        x = self.MARGIN
        y = self.MARGIN
        width = self.POS_SIZE[2] - self.MARGIN * 2

        # Title
        self.add_label(
            'LblTitle', x, y, width, self.LABEL_HEIGHT + 6,
            Label='Order Details', FontHeight=14, FontWeight=150,
            TextColor=self.TITLE_COLOR, Align=1
        )
        y += self.LABEL_HEIGHT + 12

        # Body placeholder label; will be populated in _prepare
        self.lbl_body = self.add_label(
            'LblBody', x, y, width, self.LABEL_HEIGHT * 10,
            Label='Loading…', MultiLine=True, FontHeight=11, Align=0
        )
        # If _prepare ran earlier and buffered text, apply it now
        try:
            if getattr(self, '_pending_label_text', None) is not None and hasattr(self.lbl_body, 'Model'):
                self.lbl_body.Model.Label = self._pending_label_text
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug("OrderDialog._create: Applied buffered label text to lbl_body")
                self._pending_label_text = None
        except Exception:
            pass

        # Create Calendar Entry button under the body label
        y_btn = y + self.LABEL_HEIGHT * 10 + 10
        spacing = 10
        create_w, create_h = 160, 22
        ok_w, ok_h = 60, 20

        self.btn_create_cal = self.add_button(
            'CreateCalEntryBtn', x, y_btn, create_w, create_h,
            Label='Create Calendar Entry',
            callback=self.open_calendar_entry
        )
        # Apply visibility computed in _prepare (or keep default False)
        try:
            self._set_create_btn_visible(bool(getattr(self, '_show_create_cal_btn', False)))
        except Exception:
            # Ensure we do not crash UI creation due to visibility issues
            if hasattr(self, 'logger') and self.logger:
                try:
                    self.logger.error("OrderDialog._create: error applying button visibility via helper")
                    self.logger.error(traceback.format_exc())
                except Exception:
                    pass
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"OrderDialog: Added 'Create Calendar Entry' button at x={x}, y={y_btn}; visible={bool(getattr(self,'_show_create_cal_btn', False))}")
        except Exception:
            pass

        default_ok_x = int(self.POS_SIZE[2] / 2 - ok_w / 2)
        ok_x = (x + create_w + spacing) if bool(getattr(self, '_show_create_cal_btn', False)) else default_ok_x
        self.ok_btn = self.add_button(
            'OkButton', ok_x, y_btn,
            ok_w, ok_h, Label='OK',
            PushButtonType=2
        )

        # Ensure initial layout is applied (in case _prepare runs later)
        try:
            self._layout_buttons(show_create)
        except Exception:
            pass

        self._log_lifecycle('create:end')

    def _dispose(self):
        pass

    def _done(self, ret):
        return ret

    def open_calendar_entry(self, event=None):
        """Open the Calendar Entry dialog pre-populated from this order. Do not persist here."""
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"OrderDialog: 'Create Calendar Entry' clicked for order_id={self.order_id}")
        except Exception:
            pass

        # Ensure we have an order loaded
        if not self.order:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.warning("OrderDialog: No order loaded; cannot open calendar entry dialog")
            except Exception:
                pass
            return

        o = self.order

        # Prefill fields from order (UI convenience only)
        title = (getattr(o, 'referencenumber', '') or '').strip() or str(getattr(o, 'transid', self.order_id))
        start_date = getattr(o, 'transdate', None)

        # End date: try common names; OK if None
        end_date = None
        for nm in ('expecteddate', 'expected_date', 'duedate', 'due_date'):
            if hasattr(o, nm):
                val = getattr(o, nm)
                if val:
                    end_date = val
                    break

        description = getattr(o, 'notes', '') or ''

        entry_data = {
            'title': title,
            'start_date': start_date,
            'end_date': end_date,
            'description': description,
            'order_id': getattr(o, 'transid', self.order_id),
        }

        try:
            if hasattr(self, 'logger') and self.logger:
                # Avoid logging huge objects; show types for dates
                sd_t = type(start_date).__name__ if start_date is not None else None
                ed_t = type(end_date).__name__ if end_date is not None else None
                self.logger.debug(f"OrderDialog: Prepopulating EntryDialog with title='{title}', start_date={start_date}({sd_t}), end_date={end_date}({ed_t}), desc_len={len(description)}")
        except Exception:
            pass

        # Open the calendar entry dialog in add mode; do not persist here
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug("OrderDialog: Instantiating EntryDialog (edit_mode=False)")
            dlg = EntryDialog(parent=self, ctx=self.ctx, smgr=getattr(self, 'smgr', None), frame=self.frame, ps=self.ps, edit_mode=False, entry_data=entry_data)
        except Exception as e:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.debug(f"OrderDialog: Fallback EntryDialog signature due to error: {e}")
            except Exception:
                pass
            dlg = EntryDialog(self, self.ctx, getattr(self, 'smgr', None), self.frame, self.ps, edit_mode=False, entry_data=entry_data)

        # Execute the dialog
        rc = None
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.debug("OrderDialog: Executing EntryDialog")
            # Execute without arguments (matches calendar component usage)
            rc = dlg.execute()
        except Exception as e:
            try:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.error(f"OrderDialog: Error executing EntryDialog: {e}")
                    self.logger.error(traceback.format_exc())
            except Exception:
                pass
            return

        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(f"OrderDialog: EntryDialog closed with rc={rc}")
        except Exception:
            pass

        # Close the Order dialog after a successful creation (EntryDialog returns 1 on Save)
        try:
            if rc == 1:
                if hasattr(self, 'logger') and self.logger:
                    self.logger.info("OrderDialog: Calendar entry created; closing Order dialog")
                # End this dialog's execution and dispose
                try:
                    self.end_execute(0)
                except Exception:
                    # Fallback directly to UNO endExecute if helper fails
                    try:
                        self._dialog.endExecute()
                    except Exception:
                        if hasattr(self, 'logger') and self.logger:
                            self.logger.exception("OrderDialog: Failed to close Order dialog after calendar entry creation")
        except Exception:
            if hasattr(self, 'logger') and self.logger:
                self.logger.exception("OrderDialog: Error handling post-EntryDialog close")

        # No further payload handling – by design
        return
