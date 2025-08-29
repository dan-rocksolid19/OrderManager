from librepy.jasper_reports import jasper_report_manager
from librepy.pybrex.values import pybrex_logger, DOCUMENT_REPORT_PATH

logger = pybrex_logger(__name__)
REPORT_PATH = DOCUMENT_REPORT_PATH

PRINT_ACTION_PRINT = 4
PRINT_ACTION_PDF = 2

def _generate_report(doc_id, doc_type, print_action):
    """
    Internal function to generate a report with the specified print action.
    
    Args:
        doc_id: Document ID
        doc_type: Document type (e.g., "Quote", "Job", "Invoice")
        print_action: Print action (4 for print, 2 for PDF)
    """
    logger.info(f"Generating report for document ID: {doc_id}, type: {doc_type}, action: {print_action}")
    logger.debug(f"Report path: {REPORT_PATH}")

    report_params = {
        "document_id": {
            "value": doc_id,
            "type": "long"
        },
        "doc_type": {
            "value": doc_type,
            "type": "string"
        }
    }

    jasper_report_manager.main(REPORT_PATH, report_params, print_action)

def print_doc(doc_id, doc_type):
    """
    Print a document to the default printer.
    
    Args:
        doc_id: Document ID
        doc_type: Document type (e.g., "Quote", "Job", "Invoice")
    """
    _generate_report(doc_id, doc_type, PRINT_ACTION_PRINT)
    logger.info("Document printed successfully")

def save_doc_as_pdf(doc_id, doc_type):
    """
    Save a document as PDF.
    
    Args:
        doc_id: Document ID
        doc_type: Document type (e.g., "Quote", "Job", "Invoice")
    """
    _generate_report(doc_id, doc_type, PRINT_ACTION_PDF)
    logger.info("Document saved as PDF successfully")


