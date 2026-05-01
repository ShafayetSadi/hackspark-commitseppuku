from datetime import date

from fastapi import HTTPException
from rental_service.utils.dates import iter_month_strings, parse_year_month, parse_yyyy_mm_dd


def require_positive_int(value: int, *, field_name: str) -> int:
    if value <= 0:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}; must be positive")
    return value


def require_date_range(from_date: str, to_date: str) -> tuple[date, date]:
    try:
        start = parse_yyyy_mm_dd(from_date)
        end = parse_yyyy_mm_dd(to_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="Invalid date format; expected YYYY-MM-DD"
        ) from exc

    if start > end:
        raise HTTPException(status_code=400, detail="'from' must not be after 'to'")

    return start, end


def require_month_range(from_month: str, to_month: str) -> list[str]:
    try:
        start = parse_year_month(from_month)
        end = parse_year_month(to_month)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if start > end:
        raise HTTPException(status_code=400, detail="'from' must not be after 'to'")

    months = iter_month_strings(from_month, to_month)
    if len(months) > 12:
        raise HTTPException(status_code=400, detail="Month range must not exceed 12 months")

    return months


def require_year(year: int) -> int:
    if year < 1:
        raise HTTPException(status_code=400, detail="Invalid year")
    return year
