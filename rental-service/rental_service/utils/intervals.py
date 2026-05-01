from datetime import date, timedelta

type Interval = tuple[date, date]


def overlaps(a_start: date, a_end: date, b_start: date, b_end: date) -> bool:
    return not (a_end < b_start or a_start > b_end)


def clip_interval(start: date, end: date, bound_start: date, bound_end: date) -> Interval | None:
    clipped_start = max(start, bound_start)
    clipped_end = min(end, bound_end)
    if clipped_start > clipped_end:
        return None
    return clipped_start, clipped_end


def merge_intervals(intervals: list[Interval]) -> list[Interval]:
    if not intervals:
        return []

    ordered = sorted(intervals, key=lambda item: (item[0], item[1]))
    merged = [ordered[0]]

    for start, end in ordered[1:]:
        last_start, last_end = merged[-1]
        if start <= last_end + timedelta(days=1):
            merged[-1] = (last_start, max(last_end, end))
        else:
            merged.append((start, end))

    return merged


def gap_length_days(interval: Interval) -> int:
    start, end = interval
    return (end - start).days + 1


def overlapping_busy_periods(
    request_start: date, request_end: date, merged_busy: list[Interval]
) -> list[Interval]:
    return [
        (start, end)
        for start, end in merged_busy
        if overlaps(start, end, request_start, request_end)
    ]


def compute_free_windows(
    request_start: date, request_end: date, merged_busy: list[Interval]
) -> list[Interval]:
    clipped_busy = []
    for start, end in merged_busy:
        clipped = clip_interval(start, end, request_start, request_end)
        if clipped is not None:
            clipped_busy.append(clipped)

    free_windows: list[Interval] = []
    cursor = request_start

    for start, end in clipped_busy:
        if cursor < start:
            free_windows.append((cursor, start - timedelta(days=1)))
        cursor = max(cursor, end + timedelta(days=1))

    if cursor <= request_end:
        free_windows.append((cursor, request_end))

    return free_windows


def longest_free_streak(
    year_start: date, year_end: date, merged_busy: list[Interval]
) -> Interval | None:
    if not merged_busy:
        return year_start, year_end

    best: Interval | None = None

    first_start, _ = merged_busy[0]
    if year_start < first_start:
        best = (year_start, first_start - timedelta(days=1))

    for index in range(1, len(merged_busy)):
        prev_end = merged_busy[index - 1][1]
        next_start = merged_busy[index][0]
        gap_start = prev_end + timedelta(days=1)
        gap_end = next_start - timedelta(days=1)
        if gap_start <= gap_end:
            candidate = (gap_start, gap_end)
            if best is None or gap_length_days(candidate) > gap_length_days(best):
                best = candidate

    _, last_end = merged_busy[-1]
    if last_end < year_end:
        candidate = (last_end + timedelta(days=1), year_end)
        if best is None or gap_length_days(candidate) > gap_length_days(best):
            best = candidate

    if best is None:
        return None

    return best
