from librepy.pybrex.dialog import DialogBase
from librepy.pybrex.msgbox import msgbox
from librepy.auth.auth_service import AuthService
from librepy.pybrex.values import pybrex_logger


class UserEditDialog(DialogBase):
    POS_SIZE = 0, 0, 220, 290

    def __init__(self, ctx, smgr, user_data=None, **props):
        props["Title"] = "Edit User" if user_data else "Add User"
        self.ctx = ctx
        self.smgr = smgr
        self.auth_service = AuthService()
        self.logger = pybrex_logger(__name__)
        self.user_data = user_data
        self.is_edit_mode = user_data is not None
        
        self.username_edit = None
        self.password_edit = None
        self.confirm_edit = None
        self.active_check = None
        self.roles_list = None
        self.show_password_btn = None
        self.password_visible = False
        
        super().__init__(ctx, smgr, **props)

    def _create(self):
        margin = 10
        y = margin
        field_width = 200
        label_height = 16
        field_height = 22
        
        self.add_label("LblUsername", margin, y, field_width, label_height, 
                      Label="Username:", FontWeight=120)
        y += label_height + 2
        self.username_edit = self.add_edit("EdtUsername", margin, y, field_width, field_height)
        
        y += field_height + 10
        
        password_label = "New Password:" if self.is_edit_mode else "Password:"
        self.add_label("LblPassword", margin, y, field_width, label_height,
                      Label=password_label, FontWeight=120)
        y += label_height + 2
        self.password_edit = self.add_edit("EdtPassword", margin, y, field_width - 30, field_height,
                                         EchoChar=42)
        self.show_password_btn = self.add_button("BtnShowPassword", margin + field_width - 25, y, 25, field_height,
                                                Label="👁", FontHeight=10)
        
        y += field_height + 5
        confirm_label = "Confirm New Password:" if self.is_edit_mode else "Confirm Password:"
        self.add_label("LblConfirm", margin, y, field_width, label_height,
                      Label=confirm_label, FontWeight=120)
        y += label_height + 2
        self.confirm_edit = self.add_edit("EdtConfirm", margin, y, field_width, field_height,
                                        EchoChar=42)
        y += field_height + 10
        
        if self.is_edit_mode:
            self.add_label("LblPasswordNote", margin, y, field_width, label_height,
                          Label="Leave blank to keep current password", FontHeight=9, FontSlant=1)
            y += label_height + 5
        
        self.active_check = self.add_check("ChkActive", margin, y, field_width, field_height,
                                          Label="User is active", State=1)
        y += field_height + 10
        
        self.add_label("LblRoles", margin, y, field_width, label_height,
                      Label="Assigned Roles:", FontWeight=120)
        y += label_height + 2
        
        self.roles_list = self.add_listbox("LstRoles", margin, y, field_width, field_height,
                                          Dropdown=True)
        y += field_height + 15
        
        button_width = 70
        button_spacing = 10
        total_button_width = (button_width * 2) + button_spacing
        button_x = (self.POS_SIZE[2] - total_button_width) // 2
        
        ok_btn = self.add_button("BtnOK", button_x, y, button_width, 24,
                               Label="Save", DefaultButton=True,
                               BackgroundColor=0x4A90E2, TextColor=0xFFFFFF, FontWeight=150)
        cancel_btn = self.add_button("BtnCancel", button_x + button_width + button_spacing, y, button_width, 24,
                                   Label="Cancel",
                                   BackgroundColor=0x95A5A6, TextColor=0xFFFFFF, FontWeight=150)
        
        self.add_action_listener(ok_btn, self._handle_save)
        self.add_action_listener(cancel_btn, self._handle_cancel)
        self.add_action_listener(self.show_password_btn, self._toggle_password_visibility)

    def _prepare(self):
        self._populate_roles()
        if self.is_edit_mode:
            self._populate_user_data()

    def _populate_roles(self):
        try:
            roles = self.auth_service.list_roles()
            role_items = []
            for role in roles:
                role_items.append(role.name)
            
            if role_items:
                self.roles_list.addItems(tuple(role_items), 0)
        except Exception as e:
            self.logger.error(f"Error populating roles: {str(e)}")
            msgbox(f"Error loading roles: {str(e)}", "Error")

    def _populate_user_data(self):
        if not self.user_data:
            return
            
        self.username_edit.setText(self.user_data["username"])
        self.active_check.setState(1 if self.user_data["active"] == "Yes" else 0)
        
        try:
            user_roles = self.auth_service.get_user_roles(self.user_data["id"])
            user_role_names = [role.name for role in user_roles]
            
            for i in range(self.roles_list.getItemCount()):
                item_text = self.roles_list.getItem(i)
                if item_text in user_role_names:
                    self.roles_list.selectItemPos(i, True)
        except Exception as e:
            self.logger.error(f"Error populating user roles: {str(e)}")

    def _toggle_password_visibility(self, event):
        self.password_visible = not self.password_visible
        
        password_text = self.password_edit.getText()
        confirm_text = self.confirm_edit.getText()
        
        if self.password_visible:
            self.password_edit.setText("")
            self.confirm_edit.setText("")
            self.password_edit.Model.EchoChar = 0
            self.confirm_edit.Model.EchoChar = 0
            self.show_password_btn.Label = "🙈"
            self.password_edit.setText(password_text)
            self.confirm_edit.setText(confirm_text)
        else:
            self.password_edit.setText("")
            self.confirm_edit.setText("")
            self.password_edit.Model.EchoChar = 42
            self.confirm_edit.Model.EchoChar = 42
            self.show_password_btn.Label = "👁"
            self.password_edit.setText(password_text)
            self.confirm_edit.setText(confirm_text)

    def _handle_save(self, event):
        username = self.username_edit.getText().strip()
        is_active = self.active_check.getState() == 1
        
        if not username:
            msgbox("Username is required", "Validation Error")
            return
        
        # Check for assigned role requirement
        selected_indices = self.roles_list.getSelectedItemsPos()
        
        if not selected_indices:
            msgbox("Please assign a role to the user", "Role Required")
            return
        
        selected_role = self.roles_list.getItem(selected_indices[0])
        
        # Check for duplicate username
        try:
            existing_user = self.auth_service._user_dao.get_by_username(username)
            if existing_user and (not self.is_edit_mode or existing_user.id != self.user_data["id"]):
                msgbox(f"Username '{username}' already exists. Please choose a different username.", "Duplicate Username")
                return
        except Exception as e:
            self.logger.error(f"Error checking username uniqueness: {str(e)}")
            msgbox("Error validating username. Please try again.", "Validation Error")
            return
        
        password = self.password_edit.getText()
        confirm = self.confirm_edit.getText()
        
        if not self.is_edit_mode:
            if not password:
                msgbox("Password is required", "Validation Error")
                return
            
            if password != confirm:
                msgbox("Passwords do not match", "Validation Error")
                return
        else:
            if password or confirm:
                if not password:
                    msgbox("New password cannot be empty", "Validation Error")
                    return
                
                if password != confirm:
                    msgbox("New passwords do not match", "Validation Error")
                    return
        
        try:
            if self.is_edit_mode:
                current_roles = self.auth_service.get_user_roles(self.user_data["id"])
                current_role_names = [role.name for role in current_roles]
                is_admin_user = "admin" in [r.lower() for r in current_role_names]
                changing_from_admin = is_admin_user and selected_role.lower() != "admin"
                
                if changing_from_admin:
                    if self.auth_service._is_current_user(self.user_data["id"]):
                        msgbox("You cannot remove the admin role from your own account", "Self-Modification Not Allowed")
                        return
                    admin_count = self.auth_service._count_active_admins()
                    if admin_count <= 1:
                        msgbox("Cannot remove admin role: must have at least one active admin user", "Admin Required")
                        return
                
                if is_active is False:
                    if self.auth_service._is_current_user(self.user_data["id"]):
                        msgbox("You cannot deactivate your own account", "Self-Deactivation Not Allowed")
                        return
                    elif is_admin_user:
                        admin_count = self.auth_service._count_active_admins()
                        if admin_count <= 1:
                            msgbox("Cannot deactivate user: must have at least one active admin user", "Admin Required")
                            return
                
                success = self.auth_service.update_user(self.user_data["id"], username, is_active)
                if not success:
                    msgbox("Failed to update user", "Error")
                    return
                
                if password:
                    password_success = self.auth_service.change_password(self.user_data["id"], password)
                    if not password_success:
                        msgbox("Failed to update password", "Error")
                        return
                
                # Remove all current roles
                for role in current_roles:
                    if not self.auth_service.remove_role(self.user_data["id"], role.name):
                        if role.name.lower() == "admin":
                            if self.auth_service._is_current_user(self.user_data["id"]):
                                msgbox("You cannot remove the admin role from your own account", "Self-Modification Not Allowed")
                            else:
                                msgbox("Cannot remove admin role: must have at least one active admin user", "Admin Required")
                            return
                        else:
                            msgbox(f"Failed to remove role {role.name}", "Error")
                            return
                
                # Assign the selected role
                if not self.auth_service.assign_role(self.user_data["id"], selected_role):
                    msgbox(f"Failed to assign role {selected_role}", "Error")
                    return
            else:
                user = self.auth_service.create_user(username, password, [selected_role], is_active)
                if not user:
                    msgbox("Failed to create user", "Error")
                    return
                            
            self.end_execute(1)
        except Exception as e:
            self.logger.error(f"Error saving user: {str(e)}")
            msgbox(f"Error saving user: {str(e)}", "Error")

    def _handle_cancel(self, event):
        self.end_execute(0)

    def _dispose(self):
        pass


class RoleEditDialog(DialogBase):
    POS_SIZE = 0, 0, 250, 120

    def __init__(self, ctx, smgr, **props):
        props["Title"] = "Add Role"
        self.ctx = ctx
        self.smgr = smgr
        self.auth_service = AuthService()
        self.logger = pybrex_logger(__name__)
        
        self.role_name_edit = None
        
        super().__init__(ctx, smgr, **props)

    def _create(self):
        margin = 15
        y = margin
        field_width = 200
        label_height = 16
        field_height = 22
        
        self.add_label("LblRoleName", margin, y, field_width, label_height,
                      Label="Role Name:", FontWeight=120)
        y += label_height + 2
        self.role_name_edit = self.add_edit("EdtRoleName", margin, y, field_width, field_height)
        
        y += field_height + 20
        
        button_width = 60
        button_spacing = 10
        total_button_width = (button_width * 2) + button_spacing
        button_x = (self.POS_SIZE[2] - total_button_width) // 2
        
        ok_btn = self.add_button("BtnOK", button_x, y, button_width, 24,
                               Label="Create", DefaultButton=True,
                               BackgroundColor=0x4A90E2, TextColor=0xFFFFFF, FontWeight=150)
        cancel_btn = self.add_button("BtnCancel", button_x + button_width + button_spacing, y, button_width, 24,
                                   Label="Cancel",
                                   BackgroundColor=0x95A5A6, TextColor=0xFFFFFF, FontWeight=150)
        
        self.add_action_listener(ok_btn, self._handle_create)
        self.add_action_listener(cancel_btn, self._handle_cancel)

    def _prepare(self):
        self.role_name_edit.setFocus()

    def _handle_create(self, event):
        role_name = self.role_name_edit.getText().strip()
        
        if not role_name:
            msgbox("Role name is required", "Validation Error")
            return
        
        try:
            role = self.auth_service.create_role(role_name)
            if not role:
                msgbox("Failed to create role", "Error")
                return
                
            self.end_execute(1)
        except Exception as e:
            self.logger.error(f"Error creating role: {str(e)}")
            msgbox(f"Error creating role: {str(e)}", "Error")

    def _handle_cancel(self, event):
        self.end_execute(0)

    def _dispose(self):
        pass


class UsersRolesDialog(DialogBase):
    POS_SIZE = 0, 0, 500, 350

    def __init__(self, ctx, smgr, **props):
        props["Title"] = "User & Role Management"
        self.ctx = ctx
        self.smgr = smgr
        self.auth_service = AuthService()
        self.logger = pybrex_logger(__name__)
        
        self.tab_control = None
        self.users_tab = None
        self.roles_tab = None
        self.permissions_tab = None
        
        self.users_grid = None
        self.roles_grid = None
        self.permissions_grid = None
        
        self.add_user_btn = None
        self.add_role_btn = None
        self.delete_role_btn = None
        self.grant_all_btn = None
        self.revoke_all_btn = None
        
        super().__init__(ctx, smgr, **props)

    def _create(self):
        margin = 5
        tab_height = self.POS_SIZE[3] - 40
        
        self.tab_control = self.add_page_container("TabControl", 
                                                   margin, margin, 
                                                   self.POS_SIZE[2] - (margin * 2), 
                                                   tab_height)
        
        self.users_tab = self.add_page(self.tab_control, "UsersTab", "Users")
        self.roles_tab = self.add_page(self.tab_control, "RolesTab", "Roles")
        self.permissions_tab = self.add_page(self.tab_control, "PermissionsTab", "Permissions")
        
        self._create_users_tab()
        self._create_roles_tab()
        self._create_permissions_tab()
        
        self._create_dialog_buttons()

    def _create_users_tab(self):
        grid_width = 320
        grid_height = 250
        
        self.users_grid, self.users_grid_model = self.add_grid("UsersGrid",
                                       5, 5,
                                       grid_width, grid_height,
                                       titles=[
                                           ("Username", "username", 100, 1),
                                           ("Active", "active", 50, 1),
                                           ("Roles", "roles", 120, 1)
                                       ],
                                       page=self.users_tab)
        
        button_x = grid_width + 15
        button_width = 80
        button_height = 22
        button_spacing = 3
        
        self.add_user_btn = self.add_button("AddUserBtn", 
                                           button_x, 5, 
                                           button_width, button_height,
                                           Label="Add User",
                                           BackgroundColor=0x4A90E2,
                                           TextColor=0xFFFFFF,
                                           FontWeight=150,
                                           page=self.users_tab)
        
        self.add_label("LblEditHint", 
                      button_x, 5 + button_height + button_spacing, 
                      button_width + 20, button_height,
                      Label="Double-click to edit",
                      FontHeight=9,
                      FontWeight=100,
                      page=self.users_tab)
        
        self.add_action_listener(self.add_user_btn, self._add_user)

    def _create_roles_tab(self):
        grid_width = 280
        grid_height = 250
        
        self.roles_grid, self.roles_grid_model = self.add_grid("RolesGrid",
                                       5, 5,
                                       grid_width, grid_height,
                                       titles=[
                                           ("Role Name", "role_name", 140, 1),
                                           ("Users", "users_assigned", 80, 1)
                                       ],
                                       page=self.roles_tab)
        
        button_x = grid_width + 15
        button_width = 80
        button_height = 22
        button_spacing = 3
        
        self.add_role_btn = self.add_button("AddRoleBtn", 
                                           button_x, 5, 
                                           button_width, button_height,
                                           Label="Add Role",
                                           BackgroundColor=0x4A90E2,
                                           TextColor=0xFFFFFF,
                                           FontWeight=150,
                                           page=self.roles_tab)
        
        self.delete_role_btn = self.add_button("DeleteRoleBtn", 
                                              button_x, 5 + button_height + button_spacing, 
                                              button_width, button_height,
                                              Label="Delete Role",
                                              BackgroundColor=0xD93025,
                                              TextColor=0xFFFFFF,
                                              FontWeight=150,
                                              page=self.roles_tab)
        
        self.add_action_listener(self.add_role_btn, self._add_role)
        self.add_action_listener(self.delete_role_btn, self._delete_role)

    def _create_permissions_tab(self):
        filter_height = 25
        
        self.add_label("LblPermFilter", 5, 5, 80, 16,
                      Label="Filter:", FontWeight=120,
                      page=self.permissions_tab)
        
        self.permissions_filter = self.add_edit("PermissionsFilter", 90, 5, 150, 18,
                                               page=self.permissions_tab)
        
        self.add_text_listener(self.permissions_filter, self._on_permissions_filter_change)
        
        grid_y = filter_height + 10
        grid_width = 320
        grid_height = 220
        
        self.permissions_grid, self.permissions_grid_model = self.add_grid("PermissionsGrid",
                                       5, grid_y,
                                       grid_width, grid_height,
                                       titles=[],
                                       page=self.permissions_tab)
        
        button_x = grid_width + 15
        button_width = 80
        button_height = 22
        button_spacing = 5
        button_y = grid_y
        
        self.grant_all_btn = self.add_button("GrantAllBtn", 
                                            button_x, button_y, 
                                            button_width, button_height,
                                            Label="Grant All",
                                            BackgroundColor=0x2E7D32,
                                            TextColor=0xFFFFFF,
                                            FontWeight=150,
                                            page=self.permissions_tab)
        
        button_y += button_height + button_spacing
        self.revoke_all_btn = self.add_button("RevokeAllBtn", 
                                             button_x, button_y, 
                                             button_width, button_height,
                                             Label="Revoke All",
                                             BackgroundColor=0xD32F2F,
                                             TextColor=0xFFFFFF,
                                             FontWeight=150,
                                             page=self.permissions_tab)
        
        button_y += button_height + button_spacing * 2
        self.add_label("LblPermHint", 
                      button_x, button_y, 
                      button_width + 20, button_height * 2,
                      Label="Click matrix cells to toggle permissions",
                      FontHeight=9,
                      FontWeight=100,
                      page=self.permissions_tab)
        
        self.add_action_listener(self.grant_all_btn, self._grant_all_permissions)
        self.add_action_listener(self.revoke_all_btn, self._revoke_all_permissions)
        self.add_mouse_listener(self.permissions_grid_model, pressed=self._on_permissions_cell_click)

    def _create_dialog_buttons(self):
        button_y = self.POS_SIZE[3] - 30
        button_width = 50
        
        close_btn = self.add_button("CloseBtn", 
                                   self.POS_SIZE[2] - button_width - 5, button_y, 
                                   button_width, 20,
                                   Label="Close",
                                   DefaultButton=True,
                                   BackgroundColor=0x808080,
                                   TextColor=0xFFFFFF,
                                   FontWeight=150)
        
        self.add_action_listener(close_btn, self._close_dialog)

    def _prepare(self):
        self._refresh_users_grid()
        self._refresh_roles_grid()
        self._refresh_permissions_grid()
        self.add_mouse_listener(self.users_grid_model, pressed=self._on_user_double_click)

    def _dispose(self):
        pass

    def _refresh_users_grid(self):
        try:
            with self.auth_service._user_dao.database.connection_context():
                users = self.auth_service.list_users()
                data = []
                for user in users:
                    roles = self.auth_service.get_user_roles(user.id)
                    role_names = ", ".join([role.name for role in roles])
                    data.append({
                        "id": user.id,
                        "username": user.username,
                        "active": "Yes" if user.is_active else "No",
                        "roles": role_names
                    })
                self.users_grid.set_data(data, heading="id")
        except Exception as e:
            self.logger.error(f"Error refreshing users grid: {str(e)}")
            msgbox(f"Error loading users: {str(e)}", "Error")

    def _refresh_roles_grid(self):
        try:
            roles = self.auth_service.list_roles()
            data = []
            from librepy.auth.auth_model import UserRole
            with self.auth_service._role_dao.database.connection_context():
                for role in roles:
                    user_count = UserRole.select().where(UserRole.role == role.id).count()
                    data.append({
                        "id": role.id,
                        "role_name": role.name,
                        "users_assigned": str(user_count)
                    })
            self.roles_grid.set_data(data, heading="id")
        except Exception as e:
            self.logger.error(f"Error refreshing roles grid: {str(e)}")
            msgbox(f"Error loading roles: {str(e)}", "Error")

    def _refresh_permissions_grid(self):
        try:
            permissions = self.auth_service.list_permissions()
            roles = self.auth_service.list_roles()
            
            if not permissions or not roles:
                return
            
            filter_text = getattr(self.permissions_filter, 'getText', lambda: '')()
            if hasattr(self.permissions_filter, 'getText'):
                filter_text = self.permissions_filter.getText().lower()
            else:
                filter_text = ''
            
            filtered_permissions = [p for p in permissions 
                                  if filter_text in p.code.lower() or filter_text in (p.description or '').lower()]
            
            titles = [("Permission (Code & Description)", "permission_code", 200, 1)]
            for role in roles:
                titles.append((f"{role.name} Role", f"role_{role.id}", 60, 2))
            
            self.permissions_grid.titles = titles
            self.permissions_grid._create_columns(titles)
            
            data = []
            for perm in filtered_permissions:
                row_data = {
                    "id": perm.code,
                    "permission_code": f"{perm.code}\n({perm.description or 'No description'})"
                }
                
                for role in roles:
                    role_permissions = self.auth_service.get_role_permissions(role.id)
                    has_permission = any(rp.code == perm.code for rp in role_permissions)
                    row_data[f"role_{role.id}"] = "☑" if has_permission else "☐"
                
                data.append(row_data)
            
            self.permissions_grid.set_data(data, heading="id")
            
        except Exception as e:
            self.logger.error(f"Error refreshing permissions grid: {str(e)}")
            msgbox(f"Error loading permissions: {str(e)}", "Error")

    def _on_user_double_click(self, event):
        try:
            if event.Buttons == 1 and event.ClickCount == 2:
                row = self.users_grid_model.getCurrentRow()
                if row == -1:
                    return
                selected_id = self.users_grid._data_model.getRowHeading(row)
                if selected_id:
                    self.logger.info(f"Double-clicked user ID: {selected_id}")
                    
                    users = self.auth_service.list_users()
                    user_data = None
                    for user in users:
                        if str(user.id) == str(selected_id):
                            roles = self.auth_service.get_user_roles(user.id)
                            role_names = ", ".join([role.name for role in roles])
                            user_data = {
                                "id": user.id,
                                "username": user.username,
                                "active": "Yes" if user.is_active else "No",
                                "roles": role_names
                            }
                            break
                    
                    if user_data:
                        dlg = UserEditDialog(self.ctx, self.smgr, user_data)
                        result = dlg.execute()
                        if result == 1:
                            self._refresh_users_grid()
        except Exception as e:
            self.logger.error(f"Error in user double click: {str(e)}")
            msgbox(f"Error: {str(e)}", "Error")

    def _add_user(self, event):
        try:
            dlg = UserEditDialog(self.ctx, self.smgr)
            result = dlg.execute()
            if result == 1:
                self._refresh_users_grid()
        except Exception as e:
            self.logger.error(f"Error in add user: {str(e)}")
            msgbox(f"Error: {str(e)}", "Error")

    def _add_role(self, event):
        try:
            dlg = RoleEditDialog(self.ctx, self.smgr)
            result = dlg.execute()
            if result == 1:
                self._refresh_roles_grid()
                self._refresh_permissions_grid()
        except Exception as e:
            self.logger.error(f"Error in add role: {str(e)}")
            msgbox(f"Error: {str(e)}", "Error")

    def _delete_role(self, event):
        try:
            selected_role_id = self.roles_grid.active_row_heading()
            if not selected_role_id:
                msgbox("Please select a role to delete", "No Selection")
                return
            
            roles = self.auth_service.list_roles()
            role_to_delete = None
            for role in roles:
                if str(role.id) == str(selected_role_id):
                    role_to_delete = role
                    break
            
            if not role_to_delete:
                msgbox("Selected role not found", "Error")
                return
            
            success, message = self.auth_service.delete_role(role_to_delete.id)
            if success:
                msgbox(message, "Success")
                self._refresh_roles_grid()
                self._refresh_permissions_grid()
            else:
                msgbox(message, "Error")
        except Exception as e:
            self.logger.error(f"Error deleting role: {str(e)}")
            msgbox(f"Error: {str(e)}", "Error")

    def _on_permissions_filter_change(self, event):
        try:
            self._refresh_permissions_grid()
        except Exception as e:
            self.logger.error(f"Error filtering permissions: {str(e)}")

    def _on_permissions_cell_click(self, event):
        try:
            if event.Buttons == 1 and event.ClickCount == 1:
                row = self.permissions_grid_model.getCurrentRow()
                if row == -1:
                    return
                
                col = self.permissions_grid._ctr.getColumnAtPoint(event.X, event.Y)
                if col <= 0:
                    return
                
                perm_code = self.permissions_grid._data_model.getRowHeading(row)
                if not perm_code:
                    return
                
                roles = self.auth_service.list_roles()
                if col - 1 >= len(roles):
                    return
                
                role = roles[col - 1]
                role_permissions = self.auth_service.get_role_permissions(role.id)
                has_permission = any(rp.code == perm_code for rp in role_permissions)
                
                if has_permission:
                    success = self.auth_service.remove_permission(role.id, perm_code)
                    action = "removed from"
                else:
                    success = self.auth_service.assign_permission(role.id, perm_code)
                    action = "granted to"
                
                if success:
                    self.logger.info(f"Permission {perm_code} {action} role {role.name}")
                    self._refresh_permissions_grid()
                else:
                    msgbox(f"Failed to toggle permission", "Error")
                    
        except Exception as e:
            self.logger.error(f"Error toggling permission: {str(e)}")
            msgbox(f"Error: {str(e)}", "Error")

    def _grant_all_permissions(self, event):
        try:
            permissions = self.auth_service.list_permissions()
            roles = self.auth_service.list_roles()
            
            success_count = 0
            total_count = len(permissions) * len(roles)
            
            for role in roles:
                for perm in permissions:
                    if self.auth_service.assign_permission(role.id, perm.code):
                        success_count += 1
            
            self._refresh_permissions_grid()
            msgbox(f"Granted {success_count}/{total_count} permissions", "Grant All Complete")
            
        except Exception as e:
            self.logger.error(f"Error granting all permissions: {str(e)}")
            msgbox(f"Error: {str(e)}", "Error")

    def _revoke_all_permissions(self, event):
        try:
            permissions = self.auth_service.list_permissions()
            roles = self.auth_service.list_roles()
            
            success_count = 0
            total_count = len(permissions) * len(roles)
            
            for role in roles:
                for perm in permissions:
                    if self.auth_service.remove_permission(role.id, perm.code):
                        success_count += 1
            
            self._refresh_permissions_grid()
            msgbox(f"Revoked {success_count}/{total_count} permissions", "Revoke All Complete")
            
        except Exception as e:
            self.logger.error(f"Error revoking all permissions: {str(e)}")
            msgbox(f"Error: {str(e)}", "Error")

    def _close_dialog(self, event):
        self.end_execute(0) 