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