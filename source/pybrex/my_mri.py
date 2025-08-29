#Simple mri wrapper for librepy

import sys
import uno
import traceback

IMPLE_NAME = "mytools.Mri"

def mri(obj):
    try:
        from mytools_Mri import component
        ctx = uno.getComponentContext()
        mri = component.create(IMPLE_NAME, ctx)
        mri.trigger(args='object', obj = obj)
    except Exception as e:
        traceback.print_exc()
    
