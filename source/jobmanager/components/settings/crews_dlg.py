from librepy.pybrex import dialog
from librepy.pybrex import listeners
from librepy.jobmanager.data.crew_dao import CrewDAO
from librepy.pybrex.msgbox import MsgBox, confirm_action
import traceback


class CrewsDialog(dialog.DialogBase):

    POS_SIZE = 0, 0, 400, 300
    DISPOSE = True
    
    MARGIN = 8
    LABEL_HEIGHT = 15
    FIELD_HEIGHT = 20
    FIELD_WIDTH = 200
    SECTION_SPACING = 15
    
    BTN_WIDTH = 80
    BTN_HEIGHT = 25
    BTN_NORMAL_COLOR = 0x0078D7
    BTN_TEXT_COLOR = 0xFFFFFF
    
    def __init__(self, ctx, parent, logger, **props):
        props['Title'] = 'Crews'
        self.ctx = ctx
        self.parent = parent
        self.logger = logger
        
        self.crew_dao = None
        self.listeners = listeners.Listeners()
        
        self.txt_crew_name = None
        self.btn_add = None
        self.btn_remove = None
        self.crews_grid = None
        self.crews_grid_model = None
        self.crews_data = []
        
        try:
            self.crew_dao = CrewDAO(logger)
        except Exception as e:
            error_msg = f"Error initializing crew DAO: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
        
        super().__init__(ctx, self.parent, **props)

    def _create(self):
        try:
            x_left = self.MARGIN
            y = self.MARGIN
            
            self.add_label(
                'LblCrewsTitle',
                x_left, y,
                300,
                self.LABEL_HEIGHT + 5,
                Label="Manage Crews",
                FontWeight=150,
                FontHeight=14
            )
            
            y += self.LABEL_HEIGHT + 10
            
            self.add_label(
                'LblCrewName',
                x_left, y,
                self.FIELD_WIDTH,
                self.LABEL_HEIGHT,
                Label="Crew Name:",
                VerticalAlign=2,
                FontHeight=12,
                FontWeight=150,
            )
            
            y += self.LABEL_HEIGHT + 2
            
            self.txt_crew_name = self.add_edit(
                'TxtCrewName',
                x_left, y,
                self.FIELD_WIDTH,
                self.FIELD_HEIGHT,
                Border=1
            )
            
            self.btn_add = self.add_button(
                'BtnAdd',
                x_left + self.FIELD_WIDTH + self.MARGIN,
                y,
                self.BTN_WIDTH,
                self.FIELD_HEIGHT,
                Label='Add',
                FontWeight=150,
                BackgroundColor=self.BTN_NORMAL_COLOR,
                TextColor=self.BTN_TEXT_COLOR,
                callback=self._handle_add_crew
            )
            
            self.btn_remove = self.add_button(
                'BtnRemove',
                x_left + self.FIELD_WIDTH + self.MARGIN + self.BTN_WIDTH + self.MARGIN,
                y,
                self.BTN_WIDTH,
                self.FIELD_HEIGHT,
                Label='Remove',
                FontWeight=150,
                BackgroundColor=0xD93025,
                TextColor=self.BTN_TEXT_COLOR,
                callback=self._handle_remove_crew
            )
            
            y += self.FIELD_HEIGHT + self.SECTION_SPACING
            
            grid_width = 380
            grid_height = 180
            
            self.crews_grid, self.crews_grid_model = self.add_grid(
                'CrewsGrid',
                x_left, y,
                grid_width, grid_height,
                titles=[
                    ("ID", "crew_id", 0, 1),
                    ("Crew Name", "crew_name", 380, 1)
                ]
            )
            
            y += grid_height + self.SECTION_SPACING
            
            self.add_ok_cancel()
            
        except Exception as e:
            error_msg = f"Error creating crews dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "UI Creation Error")
            raise

    def _prepare(self):
        try:
            self._load_crews_into_grid()
                
        except Exception as e:
            error_msg = f"Error preparing crews dialog: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Data Loading Error")

    def _dispose(self):
        try:
            if self.listeners:
                self.listeners.dispose()
            if self.crews_grid_model:
                self.crews_grid_model = None
        except Exception as e:
            self.logger.error(f"Error disposing crews dialog: {str(e)}")
            
    def _load_crews_into_grid(self):
        if not self.crew_dao or not self.crews_grid:
            return
            
        try:
            crews = self.crew_dao.get_all_crews()
            
            self.crews_data = [
                {'crew_id': crew.id, 'crew_name': crew.crew_name}
                for crew in crews
            ]
            
            self.crews_grid.set_data(self.crews_data, heading='crew_id')
            
        except Exception as e:
            error_msg = f"Error loading crews into grid: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Data Loading Error")
            
    def _handle_add_crew(self, event):
        try:
            crew_name = self.txt_crew_name.getText().strip()
            
            if not crew_name:
                MsgBox("Please enter a crew name", 16, "Validation Error")
                return
                
            if self._is_crew_name_duplicate(crew_name):
                MsgBox("A crew with this name already exists", 16, "Duplicate Name")
                return
                
            self.crews_data.append({'crew_id': 0, 'crew_name': crew_name})
            self.crews_grid.set_data(self.crews_data, heading='crew_id')
            
            self.txt_crew_name.setText("")
            
        except Exception as e:
            error_msg = f"Error adding crew: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Add Crew Error")
            
    def _handle_remove_crew(self, event):
        try:
            row_index = self.crews_grid_model.getCurrentRow()

            if row_index == -1:
                MsgBox("Please select a crew to remove", 16, "No Selection")
                return

            crew_name = self.crews_data[row_index]['crew_name'] if 0 <= row_index < len(self.crews_data) else ''

            if confirm_action(f"Are you sure you want to remove '{crew_name}'?", "Confirm Removal"):
                if 0 <= row_index < len(self.crews_data):
                    self.crews_data.pop(row_index)
                    self.crews_grid.set_data(self.crews_data, heading='crew_id')

        except Exception as e:
            error_msg = f"Error removing crew: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(traceback.format_exc())
            MsgBox(error_msg, 16, "Remove Crew Error")
            
    def _is_crew_name_duplicate(self, crew_name):
        return any(cd['crew_name'].lower() == crew_name.lower() for cd in self.crews_data)
            
    def _done(self, ret):
        if ret == 1:
            try:
                if not self.crew_dao:
                    MsgBox("Crew DAO not available", 16, "Save Failed")
                    return 0
                
                crew_names = self._collect_crew_names_from_grid()
                
                success = self.crew_dao.replace_all(crew_names)
                
                if success:
                    return 1
                else:
                    MsgBox("Failed to save crews", 16, "Save Failed")
                    return 0
                        
            except Exception as e:
                error_msg = f"Error saving crews: {str(e)}"
                self.logger.error(error_msg)
                self.logger.error(traceback.format_exc())
                MsgBox(error_msg, 16, "Save Error")
                return 0
        
        return ret
        
    def _collect_crew_names_from_grid(self):
        return [cd['crew_name'] for cd in self.crews_data if cd['crew_name'].strip()] 