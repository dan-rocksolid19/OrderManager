"""
BootManager - Synchronous application initialization manager.

Handles the complete startup sequence without threading or polling loops.
"""

import traceback
from librepy.pybrex.values import pybrex_logger
from librepy.pybrex.msgbox import msgbox
from librepy.bootstrap import ensure_database_ready
from librepy.auth.bootstrap import ensure_auth_ready

logger = pybrex_logger(__name__)

class BootError(Exception):
    """Raised when boot process fails at any stage"""
    def __init__(self, stage, message, original_exception=None):
        self.stage = stage
        self.message = message
        self.original_exception = original_exception
        super().__init__(f"Boot failed at {stage}: {message}")

class BootManager:
    """
    Manages the complete application boot sequence synchronously.
    
    This replaces the threaded approach with a simple, deterministic flow:
    1. Database bootstrap
    2. Auth bootstrap  
    3. JobManager creation
    4. Return initialized application
    """
    
    def __init__(self, ctx, smgr):
        self.ctx = ctx
        self.smgr = smgr
        self.logger = logger
        self.current_stage = "STARTING"
        
    def boot_application(self):
        """
        Run the complete boot sequence and return the initialized JobManager.
        
        Returns:
            JobManager instance if successful, None if failed
            
        Raises:
            BootError: If any stage fails critically
        """
        try:
            self.logger.info("BootManager: Starting application boot sequence")
            
            due_reminders = []
            
            # Stage 1: Database bootstrap
            self.current_stage = "DATABASE_BOOTSTRAP"
            self.logger.info("BootManager: Running database bootstrap")
            if not ensure_database_ready(self.logger):
                raise BootError("DATABASE_BOOTSTRAP", "Database configuration or connection failed")
            
            # Stage 2: Due reminders check at startup
            self.current_stage = "REMINDER_CHECK"
            try:
                self.logger.info("BootManager: Checking for due calendar reminders at startup")
                from librepy.jobmanager.data.calendar_entry_order_dao import CalendarEntryOrderDAO

                reminders_dao = CalendarEntryOrderDAO(self.logger)
                due_reminders = reminders_dao.get_due_reminders()

                count = len(due_reminders)
                self.logger.info(f"BootManager: Due reminders found: {count}")

                for idx, r in enumerate(due_reminders[:5], start=1):
                    self.logger.debug(
                        f"BootManager: Due reminder {idx}/{count}: "
                        f"id={r.get('id')} title={r.get('title')} "
                        f"start_date={r.get('start_date')} days_before={r.get('days_before')} "
                        f"order_id={r.get('order_id')} orgname={r.get('orgname', '')}"
                    )
            except Exception as e:
                self.logger.error(f"BootManager: Error while checking due reminders: {str(e)}")
                self.logger.debug(traceback.format_exc())
            
            # Stage 3: JobManager creation
            self.current_stage = "JOBMANAGER_INIT"
            self.logger.info("BootManager: Creating JobManager")
            from librepy.jobmanager.command_ctr.main import JobManager
            jobmanager = JobManager(self.ctx, self.smgr)
            
            # Stage 4: Verify initialization completed
            self.current_stage = "VERIFICATION"
            if not hasattr(jobmanager, '_initialization_complete') or not jobmanager._initialization_complete:
                raise BootError("VERIFICATION", "JobManager initialization did not complete properly")
            
            # After the application UI is initialized, show reminder dialogs
            try:
                if due_reminders:
                    self.logger.info("BootManager: Displaying reminder dialogs after application initialization")
                for r in due_reminders:
                    title = (r.get('title') or 'Calendar Reminder')
                    orgname = (r.get('orgname') or '')
                    refer = (r.get('referencenumber') or '')
                    sd = r.get('start_date')
                    sd_text = sd.strftime('%Y-%m-%d') if hasattr(sd, 'strftime') else str(sd)
                    days_before = r.get('days_before')
                    desc = (r.get('description') or '')

                    dialog_title_parts = ['Reminder']
                    if title:
                        dialog_title_parts.append(f': {title}')
                    if orgname:
                        dialog_title_parts.append(f' — {orgname}')
                    dialog_title = ''.join(dialog_title_parts)

                    details = [
                        f"Date: {sd_text}",
                        f"Days before: {days_before}",
                    ]
                    if refer:
                        details.append(f"Order ref: {refer}")
                    if desc:
                        details.append("")
                        details.append(desc)

                    message = '\n'.join(details)

                    self.logger.debug(
                        f"BootManager: Showing reminder dialog: id={r.get('id')} title={title}"
                    )
                    try:
                        msgbox(message, dialog_title)
                    except Exception as dlg_err:
                        self.logger.error(
                            f"BootManager: Failed to show reminder dialog for id={r.get('id')}: {dlg_err}"
                        )
            except Exception as e:
                self.logger.error(f"BootManager: Error while displaying reminder dialogs: {str(e)}")
                self.logger.debug(traceback.format_exc())

            self.current_stage = "COMPLETED"
            self.logger.info("BootManager: Application boot completed successfully")
            return jobmanager
            
        except BootError:
            # Re-raise BootError as-is
            raise
        except Exception as e:
            # Wrap any other exception in BootError
            self.logger.error(f"BootManager: Unexpected error in {self.current_stage}: {str(e)}")
            self.logger.error(traceback.format_exc())
            raise BootError(self.current_stage, f"Unexpected error: {str(e)}", e)
    
    def handle_boot_failure(self, boot_error):
        """
        Handle boot failure by logging and showing user-friendly message.
        
        Args:
            boot_error: BootError instance
        """
        error_msg = f"Application failed to start during {boot_error.stage}: {boot_error.message}"
        self.logger.error(f"BootManager: {error_msg}")
        
        # Show user-friendly message
        try:
            msgbox(f"Application startup failed.\n\nStage: {boot_error.stage}\nError: {boot_error.message}", 
                   "Startup Error")
        except:
            # If msgbox fails, at least we logged the error
            pass