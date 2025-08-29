from librepy.jasper_reports import jasper_report_manager
from librepy.pybrex.values import pybrex_logger, JASPER_REPORTS_DIR

import os
from datetime import date, datetime
from librepy.jobmanager.data.calendar_entry_order_dao import CalendarEntryOrderDAO

logger = pybrex_logger(__name__)
REPORT_PATH = os.path.join(JASPER_REPORTS_DIR, 'CalendarReport.jrxml')

PRINT_ACTION_PRINT = 4
PRINT_ACTION_PDF = 2


def _normalize_date(d):
    if isinstance(d, datetime):
        return d.date()
    return d


def _generate_calendar_report(start_date, end_date, print_action):
    """
    Internal function to generate a calendar events report for the given date range.

    Args:
        start_date (date|datetime): range start (inclusive)
        end_date   (date|datetime): range end (inclusive)
        print_action (int): 4 for direct print, 2 for export as PDF
    """
    try:
        s = _normalize_date(start_date)
        e = _normalize_date(end_date)
        logger.info(f"Generating calendar report for range: {s} .. {e}, action: {print_action}")
        logger.debug(f"Report path: {REPORT_PATH}")

        title = f"Calendar: {s.strftime('%Y-%m-%d')} to {e.strftime('%Y-%m-%d')}"
        report_params = {
            "start_date":   {"value": s, "type": "date"},
            "end_date":     {"value": e, "type": "date"},
            "title":        {"value": title, "type": "string"},
        }

        jasper_report_manager.main(REPORT_PATH, report_params, print_action)
        logger.info("Calendar report generation request completed")
    except Exception as ex:
        logger.error(f"Error generating calendar report: {ex}")
        raise


def save_calendar_range_as_pdf(start_date, end_date):
    _generate_calendar_report(start_date, end_date, PRINT_ACTION_PDF)
    logger.info("Calendar saved as PDF successfully")
