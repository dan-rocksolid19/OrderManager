import uno

#Message box modules
from com.sun.star.awt.MessageBoxButtons import BUTTONS_OK, BUTTONS_OK_CANCEL, BUTTONS_YES_NO, BUTTONS_YES_NO_CANCEL, BUTTONS_RETRY_CANCEL, BUTTONS_ABORT_IGNORE_RETRY
from com.sun.star.awt.MessageBoxButtons import DEFAULT_BUTTON_OK, DEFAULT_BUTTON_CANCEL, DEFAULT_BUTTON_RETRY, DEFAULT_BUTTON_YES, DEFAULT_BUTTON_NO, DEFAULT_BUTTON_IGNORE
from com.sun.star.awt.MessageBoxType import MESSAGEBOX, INFOBOX, WARNINGBOX, ERRORBOX, QUERYBOX

def msgbox(msg, Title="Message"):
    MessageBox(None, msg, Title, INFOBOX)

def confirm_action(msg, Title = 'Question'):
    rn = MessageBox(None, msg, Title, MsgType=QUERYBOX, MsgButtons = BUTTONS_YES_NO)
    if rn == 2 :
        return True
    else : 
        return False
        
def msgboxYesNoCancel(msg, Title = 'Save?'):
    'Yes = 2, No = 3, Cancel = 0'
    return MessageBox(None, msg, Title, MsgType=QUERYBOX, MsgButtons = BUTTONS_YES_NO_CANCEL)    
    
def MessageBox(ParentWin, MsgText, MsgTitle, MsgType=MESSAGEBOX, MsgButtons=BUTTONS_OK):
    ctx = uno.getComponentContext()
    sm = ctx.ServiceManager
    sv = sm.createInstanceWithContext("com.sun.star.awt.Toolkit", ctx) 
    myBox = sv.createMessageBox(ParentWin, MsgType, MsgButtons, MsgTitle, str(MsgText))
    return myBox.execute()
