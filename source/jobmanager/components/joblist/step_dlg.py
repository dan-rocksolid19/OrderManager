import uno
import traceback
from datetime import datetime
from librepy.pybrex.dialog import DialogBase
from librepy.pybrex import listeners
from librepy.pybrex.msgbox import msgbox
from librepy.pybrex.uno_date_time_converters import uno_date_to_python, python_date_to_uno
from librepy.jobmanager.data.crew_dao import CrewDAO

class StepDialog(DialogBase):
    POS_SIZE = 0, 0, 260, 220
    DISPOSE = True

    def __init__(self, parent, ctx, smgr, frame, ps, edit_mode=False, step_data=None, **props):
        self.edit_mode = edit_mode
        self.step_data = step_data or {}
        self.step_result = None
        self.listeners = listeners.Listeners()
        self.parent = parent
        self.logger = parent.logger
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.ps = ps
        self.crew_dao = CrewDAO(self.logger)
        super().__init__(ctx, smgr, **props)

    def _create(self):
        title = "Edit Step" if self.edit_mode else "Add Step"
        self._dialog.Title = title
        label_height = 15
        field_height = 20
        field_width = 140
        label_width = 70
        start_x = 10
        start_y = 20
        row_spacing = 30
        self.add_label("lbl_step", start_x, start_y, label_width, label_height, Label="Step:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.step_name = self.add_edit("StepName", start_x + label_width + 10, start_y, field_width, field_height)
        self.add_label("lbl_start_date", start_x, start_y + row_spacing, label_width, label_height, Label="Start Date:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.start_date = self.add_date("StartDate", start_x + label_width + 10, start_y + row_spacing, field_width, field_height, Dropdown=True)
        self.add_label("lbl_end_date", start_x, start_y + row_spacing * 2, label_width, label_height, Label="End Date:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.end_date = self.add_date("EndDate", start_x + label_width + 10, start_y + row_spacing * 2, field_width, field_height, Dropdown=True)
        self.add_label("lbl_crew", start_x, start_y + row_spacing * 3, label_width, label_height, Label="Crew:", FontHeight=12, FontWeight=120, Align=2, VerticalAlign=2)
        self.crew_combo = self.add_combo("CrewCombo", start_x + label_width + 10, start_y + row_spacing * 3, field_width, field_height, Dropdown=True)
        crews = self.crew_dao.get_all_crews()
        self.crew_names = [c.crew_name for c in crews]
        self.crew_combo.Model.StringItemList = tuple(self.crew_names)
        button_y = start_y + row_spacing * 4 + 10
        button_width = 80
        button_height = 25
        button_spacing = 10
        total_width = button_width * 2 + button_spacing
        center_x = (self.POS_SIZE[2] - total_width) // 2
        self.cancel_btn = self.add_cancel("CancelButton", center_x, button_y, button_width, button_height, BackgroundColor=0x808080, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)
        self.save_btn = self.add_button("SaveButton", center_x + button_width + button_spacing, button_y, button_width, button_height, Label="Save", callback=self.save_step, BackgroundColor=0xD93025, TextColor=0xFFFFFF, FontHeight=13, FontWeight=150)

    def _prepare(self):
        if self.edit_mode and self.step_data:
            self.step_name.Text = self.step_data.get('step', '')
            sd_str = self.step_data.get('start_date', '')
            ed_str = self.step_data.get('end_date', '')
            if sd_str:
                try:
                    d = datetime.strptime(sd_str, '%Y-%m-%d').date()
                    self.start_date.setDate(python_date_to_uno(d))
                except Exception:
                    pass
            if ed_str:
                try:
                    d = datetime.strptime(ed_str, '%Y-%m-%d').date()
                    self.end_date.setDate(python_date_to_uno(d))
                except Exception:
                    pass
            crew = self.step_data.get('crew_assigned', '')
            if crew in self.crew_names:
                self.crew_combo.Text = crew

    def save_step(self, event):
        if not self.step_name.Text.strip():
            msgbox("Step is required.", "Validation Error")
            return
        try:
            sd_uno = self.start_date.getDate()
            ed_uno = self.end_date.getDate()
            sd_py = uno_date_to_python(sd_uno) if sd_uno.Year > 0 else None
            ed_py = uno_date_to_python(ed_uno) if ed_uno.Year > 0 else None
            crew = self.crew_combo.getText()
            self.step_result = {
                'step': self.step_name.Text.strip(),
                'start_date': sd_py,
                'end_date': ed_py,
                'crew_assigned': crew
            }
            self.end_execute(1)
        except Exception as e:
            self.logger.error(f"Error saving step: {e}")
            self.logger.error(traceback.format_exc())
            msgbox(f"Error saving step: {e}", "Error")

    def get_step_data(self):
        return self.step_result

    def dispose(self):
        try:
            if hasattr(self, 'container'):
                self.container.dispose()
        except Exception as e:
            self.logger.error(f"Error during disposal: {e}")
            self.logger.error(traceback.format_exc()) 