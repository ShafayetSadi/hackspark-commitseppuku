import re
from datetime import date, datetime

MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def parse_iso_to_date(value: str) -> date:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def parse_yyyy_mm_dd(value: str) -> date:
    return date.fromisoformat(value)


def format_date(value: date) -> str:
    return value.isoformat()


def parse_year_month(value: str) -> tuple[int, int]:
    if not MONTH_RE.fullmatch(value):
        raise ValueError("Invalid month format; expected YYYY-MM")

    year_str, month_str = value.split("-", maxsplit=1)
    year = int(year_str)
    month = int(month_str)
    if month < 1 or month > 12:
        raise ValueError("Invalid month value; expected 01-12")
    return year, month


def iter_month_strings(start_month: str, end_month: str) -> list[str]:
    start_year, start_mon = parse_year_month(start_month)
    end_year, end_mon = parse_year_month(end_month)

    months: list[str] = []
    year = start_year
    month = start_mon

    while (year, month) <= (end_year, end_mon):
        months.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1

    return months
