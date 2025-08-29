from librepy.pybrex.dialog import DialogBase
from librepy.pybrex.msgbox import msgbox
from librepy.auth.auth_service import AuthService

class CreateAdminDialog(DialogBase):
    POS_SIZE = 0, 0, 250, 280

    FIELD_WIDTH = 260
    FIELD_HEIGHT = 22
    LABEL_HEIGHT = 16

    def __init__(self, ctx, smgr, logger, **props):
        props["Title"] = "Create Admin User"
        self.ctx = ctx
        self.smgr = smgr
        self.logger = logger
        self.auth_service = AuthService()
        self.username_edit = None
        self.password_edit = None
        self.confirm_edit = None
        self.show_password_btn = None
        self.password_visible = False
        self.save_successful = False
        super().__init__(ctx, smgr, **props)

    def _create(self):
        content_margin = 25
        header_height = 25
        field_width = 200
        label_spacing = 2
        
        self.add_label("LblHeader", 0, 15, self.POS_SIZE[2], header_height, 
                      Label="Create Admin User", 
                      FontWeight=150, 
                      FontHeight=18,
                      Align=1)
        
        self.add_label("LblSubtitle", 0, 15 + header_height - 10, self.POS_SIZE[2], 15,
                      Label="No users found in system. Create an admin user to get started.",
                      FontHeight=10,
                      Align=1,
                      TextColor=0x808080)
        
        form_y = header_height + 15
        
        y = form_y + 5
        
        self.add_label("LblUsername", content_margin + 5, y, field_width - 10, self.LABEL_HEIGHT, 
                      Label="Username:",
                      VerticalAlign=2,
                      FontWeight=120, 
                      FontHeight=12)
        y += self.LABEL_HEIGHT + label_spacing
        self.username_edit = self.add_edit("EdtUsername", content_margin + 5, y, field_width - 10, self.FIELD_HEIGHT)
        
        y += self.FIELD_HEIGHT + 12
        
        self.add_label("LblPassword", content_margin + 5, y, field_width - 10, self.LABEL_HEIGHT, 
                      Label="Password:", 
                      VerticalAlign=2,
                      FontWeight=120, 
                      FontHeight=12)
        y += self.LABEL_HEIGHT + label_spacing
        self.password_edit = self.add_edit("EdtPassword", content_margin + 5, y, field_width - 35, self.FIELD_HEIGHT, 
                                         EchoChar=42)
        
        self.show_password_btn = self.add_button("BtnShowPassword", content_margin + 5 + field_width - 30, y, 25, self.FIELD_HEIGHT,
                                                Label="👁",
                                                FontHeight=10)
        
        y += self.FIELD_HEIGHT + 12
        
        self.add_label("LblConfirm", content_margin + 5, y, field_width - 10, self.LABEL_HEIGHT, 
                      Label="Confirm Password:", 
                      VerticalAlign=2,
                      FontWeight=120, 
                      FontHeight=12)
        y += self.LABEL_HEIGHT + label_spacing
        self.confirm_edit = self.add_edit("EdtConfirm", content_margin + 5, y, field_width - 10, self.FIELD_HEIGHT, 
                                        EchoChar=42)
        
        y += self.FIELD_HEIGHT + 25
        
        line_width = int(self.POS_SIZE[2] * 0.8)
        line_x = (self.POS_SIZE[2] - line_width) // 2
        self.add_line("LineButtons", line_x, y, line_width, 1)
        
        y += 15
        
        button_width = 90
        button_spacing = 15
        buttons_total_width = (button_width * 2) + button_spacing
        button_start_x = (self.POS_SIZE[2] - buttons_total_width) // 2
        
        ok_btn = self.add_button("BtnOK", button_start_x, y, button_width, 24,
                               DefaultButton=True,
                               Label="OK",
                               PushButtonType=0,
                               BackgroundColor=0x3498DB,
                               FontWeight=150,
                               TextColor=0xFFFFFF)
        cancel_btn = self.add_cancel("BtnCancel", button_start_x + button_width + button_spacing, y, button_width, 24,
                                   BackgroundColor=0x95A5A6,
                                   FontWeight=150,
                                   TextColor=0xFFFFFF)
        
        self.add_action_listener(ok_btn, self._handle_ok)
        self.add_action_listener(self.show_password_btn, self._toggle_password_visibility)

    def _prepare(self):
        pass

    def _dispose(self):
        pass

    def _toggle_password_visibility(self, event):
        self.password_visible = not self.password_visible
        
        # Store current text and cursor positions
        password_text = self.password_edit.getText()
        confirm_text = self.confirm_edit.getText()
        
        # Try to get current selection positions if available
        try:
            password_selection = self.password_edit.getSelection()
            confirm_selection = self.confirm_edit.getSelection()
        except:
            password_selection = None
            confirm_selection = None
        
        if self.password_visible:
            # Clear fields first
            self.password_edit.setText("")
            self.confirm_edit.setText("")
            
            # Change echo character
            self.password_edit.Model.EchoChar = 0
            self.confirm_edit.Model.EchoChar = 0
            self.show_password_btn.Label = "🙈"
            
            # Set text back
            self.password_edit.setText(password_text)
            self.confirm_edit.setText(confirm_text)
        else:
            # Clear fields first
            self.password_edit.setText("")
            self.confirm_edit.setText("")
            
            # Change echo character
            self.password_edit.Model.EchoChar = 42
            self.confirm_edit.Model.EchoChar = 42
            self.show_password_btn.Label = "👁"
            
            # Set text back
            self.password_edit.setText(password_text)
            self.confirm_edit.setText(confirm_text)
        
        # Try to restore cursor positions if they were available
        try:
            if password_selection:
                self.password_edit.setSelection(password_selection)
            if confirm_selection:
                self.confirm_edit.setSelection(confirm_selection)
        except:
            pass

    def _handle_ok(self, event):
        username = self.username_edit.Text.strip()
        pwd = self.password_edit.Text
        confirm = self.confirm_edit.Text
        if not username:
            msgbox("Username required", "Validation Error")
            return
        if not pwd:
            msgbox("Password required", "Validation Error")
            return
        if pwd != confirm:
            msgbox("Passwords do not match", "Validation Error")
            return
        try:
            user = self.auth_service.register(username, pwd, roles=["admin"])
            if not user:
                msgbox("Failed to create admin user", "Error")
                return
            
            from librepy.auth.session import login
            login(user)
            self.logger.info(f"Admin user {username} created successfully")
            
            msgbox("Admin account created. Please log in to continue.", "Success")
            self.save_successful = True
            self.end_execute(1)
        except Exception as e:
            self.logger.error(str(e))
            msgbox(str(e), "Error") 