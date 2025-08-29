'''
These functions and variables are made available by LibrePy
Check out the help manual for a full list

createUnoService()      # Implementation of the Basic CreateUnoService command
getUserPath()           # Get the user path of the currently running instance
thisComponent           # Current component instance
getDefaultContext()     # Get the default context
MsgBox()                # Simple msgbox that takes the same arguments as the Basic MsgBox
mri(obj)                # Mri the object. MRI must be installed for this to work
doc_object              # A generic object with a dict_values and list_values that are persistent

To import files inside this project, use the 'librepy' keyword
For example, to import a file named config, use the following:
from librepy import config
'''

import traceback
import time
from librepy.pybrex.values import pybrex_logger
from librepy.pybrex.msgbox import msgbox

logger = pybrex_logger(__name__)

def main(*args): 
    ''' Main method that is run when start is clicked in librepy '''
    logger.info("Main method started")
    try:
        # Obtain context first so LibrePy globals are available for dialogs
        ctx = getDefaultContext()
        smgr = ctx.getServiceManager()

        # Use BootManager for synchronous initialization
        from librepy.boot_manager import BootManager, BootError
        boot_manager = BootManager(ctx, smgr)
        
        try:
            jobmanager = boot_manager.boot_application()
            logger.info("JobManager initialized successfully")
            return jobmanager
        except BootError as e:
            boot_manager.handle_boot_failure(e)
            return None
            
    except Exception as e:
        logger.error(f"Error in main method: {str(e)}")
        logger.error(traceback.format_exc())
        msgbox(f"An error occurred while starting the application: {str(e)}", "Application Error")
        return None
    
myDocument = None
def startup(*args):
    start_time = time.time()
    logger.info("Startup method called")
    
    global myDocument
    myDocument = thisComponent
    
    try:
        # Obtain LibreOffice context first
        ctx = getDefaultContext()
        smgr = ctx.getServiceManager()
        logger.info("Document reference saved")
        
        try:
            # Hide document window right away
            thisComponent.getCurrentController().getFrame().getContainerWindow().Visible = False
            logger.info("Document window hidden")
        except Exception as e:
            logger.error(f"Failed to hide document window: {str(e)}")
            logger.error(traceback.format_exc())
        
        # Use BootManager for synchronous initialization
        from librepy.boot_manager import BootManager, BootError
        boot_manager = BootManager(ctx, smgr)
        
        try:
            # Run complete boot sequence synchronously
            logger.info("Starting synchronous boot sequence")
            jobmanager = boot_manager.boot_application()
            
            # Store the app instance globally for cleanup
            global jobmanager_instance
            jobmanager_instance = jobmanager
            
            # Close document after successful initialization
            if myDocument:
                myDocument.close(True)
                end_time = time.time()
                duration = end_time - start_time
                logger.info(f"Total initialization time: {duration:.2f} seconds")
                logger.info("Document closed successfully")
            else:
                logger.warning("Document reference is None, cannot close")
                
        except BootError as e:
            # Handle boot failure gracefully
            boot_manager.handle_boot_failure(e)
            if myDocument:
                myDocument.close(True)
            return None
        
    except Exception as e:
        logger.error(f"Error in startup method: {str(e)}")
        logger.error(traceback.format_exc())
        try:
            msgbox(f"Critical error during application startup: {str(e)}", "Application Error")
        except:
            pass
        if myDocument:
            myDocument.close(True)
        return None
    
def close_file(*args):
    logger.info("Attempting to close document")
    try:
        if myDocument:
            myDocument.close(True)
            logger.info("Document closed successfully")
        else:
            logger.warning("Document reference is None, cannot close")
    except Exception as e:
        logger.error(f"Error closing document: {str(e)}")
        logger.error(traceback.format_exc())
 
    
