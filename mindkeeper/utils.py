from datetime import datetime

DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'


def format_datetime(dt: datetime) -> str:
    return dt.strftime(DATETIME_FORMAT)
