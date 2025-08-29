#coding:utf-8
# Author:  Joshua Aguilar
# Purpose: Menubar manager for the contact list application
# Created: 01.07.2025

import traceback
from librepy.pybrex import menubar


class MenubarManager(object):
    def __init__(self, parent, ctx, smgr, frame):
        self.parent = parent
        self.ctx = ctx
        self.smgr = smgr
        self.frame = frame
        self.logger = parent.logger
        self.logger.info("MenubarManager initialized")
        self.menubar = self.create_menubar()

    def create_menubar(self):
        """Menubar for the contact list application"""
        
        #Menu bar items
        m = menubar.Menu
        sm = menubar.SubMenu
        menulist = [
            m(0, '~Settings', None, (
                sm(0, '~Statuses', 'p_statuses', graphic='list-add.png'),
                sm(None, 'Divider'),
                sm(1, '~Log Settings', 'p_log_settings', graphic='log-settings.png'),
                sm(2, '~Database Settings', 'p_settings', graphic='database-settings2.png'),
            )),
            m(1, '~About', None, (
                sm(0, '~About', 'h_about', graphic='help-about.png'),
            )),
        ]
        
        #Menu bar functions
        fn = {}
        fn['p_log_settings'] = self.log_settings
        fn['p_statuses'] = self.open_statuses_dialog
        fn['p_settings'] = self.settings
        fn['h_about'] = self.show_about
        
        return menubar.Menubar(self.parent, self.ctx, self.smgr, self.frame, menulist, fn)
    
    def dispose(self):
        """Dispose of the menubar manager"""
        try:
            self.menubar.dispose()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            self.logger.error(traceback.format_exc())

    # Menubar actions...
        
    def log_settings(self, *args):
        """Show log settings dialog"""
        from librepy.jobmanager.components.settings.log_settings_dlg import LogSettingsDialog
        dlg = LogSettingsDialog(self.ctx, self.parent, self.logger)
        dlg.execute()

    def open_statuses_dialog(self, *args):
        """Show statuses management dialog"""
        from librepy.jobmanager.components.settings.statuses_dlg import StatusesDialog
        dlg = StatusesDialog(self.ctx, self.parent, self.logger)
        dlg.execute()

    def _get_or_recover_current_user(self, auth_service):
        """
        Get current user from session, with recovery mechanism if session is lost.
        
        Args:
            auth_service: AuthService instance to use for auto-login attempts
            
        Returns:
            User object if available, None if no user is logged in
        """
        from librepy.auth import session
        
        # First check if we have a current user
        if session.current_user is not None:
            self.logger.debug(f"Current user found: {session.current_user.username}")
            return session.current_user
        
        # If no current user, try auto-login to recover session
        self.logger.info("No current user found, attempting auto-login recovery")
        try:
            recovered_user = auth_service.try_auto_login()
            if recovered_user:
                self.logger.info(f"Session recovered via auto-login for user: {recovered_user.username}")
                return recovered_user
            else:
                self.logger.info("Auto-login recovery failed - no valid remember token found")
                return None
        except Exception as e:
            self.logger.error(f"Error during auto-login recovery: {str(e)}")
            return None

    def settings(self, *args):
        """Show settings dialog"""
        from librepy.database import db_dialog
        
        from librepy.bootstrap import ensure_database_ready
        
        dialog = db_dialog.DBDialog(self.ctx, self.parent, self.logger)
        if dialog.execute():
            # Re-run bootstrap to ensure connection is refreshed and migrations are applied
            ensure_database_ready(self.logger)

    def show_about(self, *args):
        """Show about dialog"""
        from librepy.jobmanager.components.settings.about_dlg import AboutDialog
        dlg = AboutDialog(self.ctx, self.parent, self.logger)
        dlg.execute()