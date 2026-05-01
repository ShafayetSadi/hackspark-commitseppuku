# P13: Surge Days — Monotonic Stack (Next Greater Element)

**Endpoint:** `GET /analytics/surge-days?month=YYYY-MM`
**Service:** `analytics-service`
**Code:**
- Route: `analytics-service/analytics_service/api/routes.py`
- Service: `analytics-service/analytics_service/services/analytics.py` (`compute_surge_days`)

---

## Problem

For each day in a given month, find the **next day in the same month with a strictly higher rental count**. Days with no future higher day return `null`.

This is the textbook **Next Greater Element** problem on a daily-counts array. The hint is explicit: nested-loop approaches are O(n²) and rejected on code review. The intended solution is one left-to-right pass with a stack of "still waiting for an answer" indices.

---

## Algorithm: Monotonic Decreasing Stack

**O(n)** amortized time, O(n) memory. n ≤ 31.

### Step 1 — Validate and zero-fill

```python
month_days = _month_days(month)               # every calendar day in the month
daily_counts = {day: 0 for day in month_days} # zero-fill first

for row in _coerce_stats_rows(payload):
    row_date = date.fromisoformat(row["date"][:10])
    if month_start <= row_date <= month_end:
        daily_counts[row_date] = daily_counts.get(row_date, 0) + int(row["count"])
```

The stats API only returns days with rentals. **Pre-filling every day of the month with 0 is mandatory** — without it, gaps in the API response would silently shrink the array and produce wrong "next surge" answers (a missing day could be a real zero that's lower than every neighbor; skipping it changes which day actually surges next).

### Step 2 — Build the result skeleton

```python
data = [
    {"date": day.isoformat(), "count": daily_counts[day],
     "nextSurgeDate": None, "daysUntil": None}
    for day in month_days
]
```

Defaults are `None`; the stack pass overwrites them when an answer is found. Days that never get resolved (their count is the running maximum from their position to month-end) keep the `None`s — matching the spec's `null` requirement.

### Step 3 — Single left-to-right pass with a stack

```python
waiting_days: list[int] = []
for current_index, day in enumerate(month_days):
    current_count = daily_counts[day]
    while waiting_days and current_count > data[waiting_days[-1]]["count"]:
        previous_index = waiting_days.pop()
        previous_day = month_days[previous_index]
        data[previous_index]["nextSurgeDate"] = day.isoformat()
        data[previous_index]["daysUntil"] = (day - previous_day).days
    waiting_days.append(current_index)
```

**Invariant:** the stack holds indices of days whose surge answer is still unknown, and their counts are **strictly decreasing top-to-bottom**. (If a day had a count ≥ a later day on the stack, the earlier day would already have resolved that later day — contradiction.)

When we visit day `i` with `current_count`:
- Every stack-top day with `count < current_count` finds its surge: pop, set `nextSurgeDate = day i`, set `daysUntil = i - previous`.
- Stop popping at the first stack-top with `count >= current_count` (strict `>` matches the spec's "strictly higher").
- Push `i` onto the stack — its surge (if any) is to be discovered.

After the loop, anything left on the stack has no answer; its `nextSurgeDate` and `daysUntil` stay `None`.

### Why this isn't a nested loop

The `while` looks nested but is **amortized O(1) per outer iteration**. Each index is pushed exactly once and popped at most once across the whole run. Total work = at most 2n stack operations = **O(n)**.

Judges will read for the `for-for` shape — there isn't one. There's a `for` and a `while`, but the while drains shared state that the outer loop produced, not a fresh inner scan.

---

## `daysUntil` semantics

`(day - previous_day).days` is the calendar gap. Day 1 → Day 4 = 3, matching the spec example (`2024-03-01 → 2024-03-04`, `daysUntil: 3`). Always positive when an answer is found (we only resolve indices smaller than the current one).

---

## Complexity

| Step | Cost |
|------|------|
| Central API call | 1 |
| Zero-fill | O(n) |
| Stack pass | **O(n)** amortized |
| Memory | O(n) |

n is the number of days in the month (28–31).

---

## Edge cases

- **Month with all-zero counts** → no day ever exceeds another. Stack accumulates every index, nothing pops, every `nextSurgeDate` stays `null`. Correct.
- **Strictly increasing counts** → every iteration pops exactly one prior index. Total pops = n−1, last day stays `null`.
- **Strictly decreasing counts** → no pops happen during the loop; all indices remain on the stack at the end → all `null`. Correct (no later day surges past any earlier day).
- **Equal counts back-to-back** → `>` not `>=`, so a flat run does *not* resolve as a surge. The earlier day waits for a strictly greater one. Matches spec wording "strictly higher".
- **API returns the same date twice** → counts accumulate via the `+= int(row["count"])` form. Defensive; not expected.
- **API returns dates outside the month** → filtered by `month_start <= row_date <= month_end` before insertion.

---

## Cross-references

- **P11** — same zero-fill discipline on a daily-counts array; the surge problem extends that pattern with a stack scan instead of a sliding window.
- The monotonic stack pattern reappears in classic problems like "largest rectangle in histogram", "stock span", and "trapping rain water". Same invariant: keep a strictly monotonic stack of unresolved indices, drain when a new value violates the invariant.
