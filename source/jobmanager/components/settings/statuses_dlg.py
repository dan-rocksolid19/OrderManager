from librepy.pybrex import dialog
from librepy.pybrex import listeners
from librepy.jobmanager.data.status_dao import StatusDAO
from librepy.pybrex.msgbox import MsgBox, confirm_action
from librepy.pybrex.dialogs.misc_dialogs import ColorPickerDlg
import traceback
import re


HEX_COLOR_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


def int_to_hex_color(value):
    try:
        return f"#{int(value) & 0xFFFFFF:06x}"
    except Exception:
        return "#000000"


def normalize_hex(color):
    c = color.strip()
    if c.startswith('#') and len(c) == 4:  # #RGB -> #RRGGBB
        r, g, b = c[1], c[2], c[3]
        return f"#{r}{r}{g}{g}{b}{b}".lower()
    return c.lower()


class StatusesDialog(dialog.DialogBase):

    POS_SIZE = 0, 0, 500, 340
    DISPOSE = True

    MARGIN = 8
    LABEL_HEIGHT = 15
    FIELD_HEIGHT = 20
    FIELD_WIDTH = 220
    SECTION_SPACING = 15

    BTN_WIDTH = 80
    BTN_HEIGHT = 25
    BTN_NORMAL_COLOR = 0x0078D7
    BTN_TEXT_COLOR = 0xFFFFFF

    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = 'Statuses'
        self.ctx = ctx
        self.parent = parent
        self.smgr = self.parent.smgr
        self.logger = logger

        self.status_dao = None
        self.listeners = listeners.Listeners()

        self.txt_status_name = None
        self.txt_color = None
        self.btn_pick_color = None
        self.btn_add = None
        self.btn_remove = None
        self.statuses_grid = None
        self.statuses_grid_model = None
        self.statuses_data = []

        try:
            self.status_dao = StatusDAO(logger)
        except Exception as e:
            error_msg = f"Error initializing status DAO: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())

        super().__init__(ctx, self.parent, **props)

    def _create(self):
        try:
            x_left = self.MARGIN
            y = self.MARGIN

            self.add_label(
                'LblStatusesTitle',
                x_left, y,
                320,
                self.LABEL_HEIGHT + 5,
                Label="Manage Statuses",
                FontWeight=150,
                FontHeight=14
            )

            y += self.LABEL_HEIGHT + 10

            self.add_label(
                'LblStatusName',
                x_left, y,
                self.FIELD_WIDTH,
                self.LABEL_HEIGHT,
                Label="Status Name:",
                VerticalAlign=2,
                FontHeight=12,
                FontWeight=150,
            )

            y += self.LABEL_HEIGHT + 2

            self.txt_status_name = self.add_edit(
                'TxtStatusName',
                x_left, y,
                self.FIELD_WIDTH,
                self.FIELD_HEIGHT,
                Border=1
            )

            # Color label and input
            y += self.FIELD_HEIGHT + 6
            self.add_label(
                'LblColor',
                x_left, y,
                self.FIELD_WIDTH,
                self.LABEL_HEIGHT,
                Label="Color:",
                VerticalAlign=2,
                FontHeight=12,
                FontWeight=150,
            )
            y += self.LABEL_HEIGHT + 2

            self.txt_color = self.add_edit(
                'TxtColor',
                x_left, y,
                120,
                self.FIELD_HEIGHT,
                Text='#3498db',
                Border=1
            )

            self.btn_pick_color = self.add_button(
                'BtnPickColor',
                x_left + 120 + self.MARGIN, y,
                80,
                self.FIELD_HEIGHT,
                Label='Pick...',
                FontWeight=150,
                BackgroundColor=self.BTN_NORMAL_COLOR,
                TextColor=self.BTN_TEXT_COLOR,
                callback=self._choose_color
            )

            # Add/Remove buttons aligned to the right side
            self.btn_add = self.add_button(
                'BtnAdd',
                x_left + self.FIELD_WIDTH + self.MARGIN,
                y - (self.FIELD_HEIGHT + 6 + self.LABEL_HEIGHT + 2),
                self.BTN_WIDTH,
                self.FIELD_HEIGHT,
                Label='Add',
                FontWeight=150,
                BackgroundColor=self.BTN_NORMAL_COLOR,
                TextColor=self.BTN_TEXT_COLOR,
                callback=self._handle_add_status
            )

            self.btn_remove = self.add_button(
                'BtnRemove',
                x_left + self.FIELD_WIDTH + self.MARGIN + self.BTN_WIDTH + self.MARGIN,
                y - (self.FIELD_HEIGHT + 6 + self.LABEL_HEIGHT + 2),
                self.BTN_WIDTH,
                self.FIELD_HEIGHT,
                Label='Remove',
                FontWeight=150,
                BackgroundColor=0xD93025,
                TextColor=self.BTN_TEXT_COLOR,
                callback=self._handle_remove_status
            )

            y += self.FIELD_HEIGHT + self.SECTION_SPACING

            grid_width = 480
            grid_height = 180

            self.statuses_grid, self.statuses_grid_model = self.add_grid(
                'StatusesGrid',
                x_left, y,
                grid_width, grid_height,
                titles=[
                    # ("ID", "status_id", 0, 1),
                    ("Status", "status", 280, 1),
                    ("Color", "color", 180, 1)
                ]
            )

            y += grid_height + self.SECTION_SPACING

            self.add_ok_cancel()

        except Exception as e:
            error_msg = f"Error creating statuses dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "UI Creation Error")
            raise

    def _prepare(self):
        try:
            self._load_statuses_into_grid()
        except Exception as e:
            error_msg = f"Error preparing statuses dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Data Loading Error")

    def _dispose(self):
        try:
            if self.listeners:
                self.listeners.dispose()
            if self.statuses_grid_model:
                self.statuses_grid_model = None
        except Exception as e:
            self.logger.error(f"Error disposing statuses dialog: {str(e)}")

    def _load_statuses_into_grid(self):
        if not self.status_dao or not self.statuses_grid:
            return
        try:
            statuses = self.status_dao.get_all_statuses()
            self.statuses_data = [
                {'status_id': s.status_id, 'status': s.status, 'color': s.color}
                for s in statuses
            ]
            self.statuses_grid.set_data(self.statuses_data, heading='status_id')
        except Exception as e:
            error_msg = f"Error loading statuses into grid: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Data Loading Error")

    def _is_status_duplicate(self, name):
        return any(sd['status'].lower() == name.lower() for sd in self.statuses_data)

    def _validate_color(self, color_text):
        c = normalize_hex(color_text)
        return HEX_COLOR_RE.match(c) is not None

    def _choose_color(self, event):
        # Create a color picker dialog instance
        color_picker = self.smgr.createInstanceWithContext("com.sun.star.ui.dialogs.ColorPicker", self.ctx)

        if color_picker is not None:
            # Set the title of the color picker
            color_picker.setTitle("Select Color")

            # Show the dialog and check if the user pressed OK
            dialog_result = color_picker.execute()

            if dialog_result == 1:  # User pressed OK
                # Retrieve the color property
                color_property = color_picker.getPropertyValues()

                # Search for the 'Color' property in the properties list
                for prop in color_property:
                    if prop.Name == "Color":
                        selected_color = prop.Value
                        self.selected_color = "#{:06X}".format(selected_color)  # Convert integer to hex

                        # Set the color in the hidden text box
                        self.txt_color.Text = self.selected_color
                        break
                else:
                    MsgBox("No color property found.", 16, "Error")
            else:
                MsgBox("No color selected.", 64, "Info")
        else:
            MsgBox("Error: Unable to open the color picker.", 16, "Error")

    def _handle_add_status(self, event):
        try:
            name = self.txt_status_name.getText().strip()
            color = self.txt_color.getText().strip()

            if not name:
                MsgBox("Please enter a status name", 16, "Validation Error")
                return
            if len(name) > 50:
                MsgBox("Status name cannot exceed 50 characters", 16, "Validation Error")
                return
            if self._is_status_duplicate(name):
                MsgBox("A status with this name already exists", 16, "Duplicate Name")
                return
            if not color:
                MsgBox("Please enter a color (e.g., #3498db)", 16, "Validation Error")
                return
            if not self._validate_color(color):
                MsgBox("Please enter a valid hex color (e.g., #3498db)", 16, "Invalid Color")
                return

            # Normalize color to #RRGGBB and name to UPPERCASE for consistency
            color = normalize_hex(color)
            name = name.upper()

            self.statuses_data.append({'status_id': 0, 'status': name, 'color': color})
            self.statuses_grid.set_data(self.statuses_data, heading='status_id')

            self.txt_status_name.setText("")
            # keep last color
        except Exception as e:
            error_msg = f"Error adding status: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Add Status Error")

    def _handle_remove_status(self, event):
        try:
            row_index = self.statuses_grid_model.getCurrentRow()
            if row_index == -1:
                MsgBox("Please select a status to remove", 16, "No Selection")
                return
            status_name = self.statuses_data[row_index]['status'] if 0 <= row_index < len(self.statuses_data) else ''
            msg = (
                f"Are you sure you want to remove '{status_name}'?\n\n"
                "Any calendar entries with this status will have it cleared."
            )
            if confirm_action(msg, "Confirm Removal"):
                if 0 <= row_index < len(self.statuses_data):
                    self.statuses_data.pop(row_index)
                    self.statuses_grid.set_data(self.statuses_data, heading='status_id')
        except Exception as e:
            error_msg = f"Error removing status: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Remove Status Error")

    def _done(self, ret):
        if ret == 1:
            try:
                if not self.status_dao:
                    MsgBox("Status DAO not available", 16, "Save Failed")
                    return 0
                # Collect and persist
                pairs = [(sd['status'], sd['color']) for sd in self.statuses_data if sd['status'].strip()]
                success = self.status_dao.replace_all(pairs)
                if success:
                    return 1
                else:
                    MsgBox("Failed to save statuses", 16, "Save Failed")
                    return 0
            except Exception as e:
                error_msg = f"Error saving statuses: {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                MsgBox(error_msg, 16, "Save Error")
                return 0
        return ret
