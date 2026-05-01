# P11: Seven-Day Peak Window — Sliding Window Sum

**Endpoint:** `GET /analytics/peak-window?from=YYYY-MM&to=YYYY-MM`
**Service:** `analytics-service`
**Code:**
- Route: `analytics-service/analytics_service/api/routes.py` (`peak_window`)
- Service: `analytics-service/analytics_service/services/analytics.py` (`compute_peak_window`, `_validate_peak_window_range`)

---

## Problem

Find the **7 consecutive calendar days** in a `[from, to]` month range with the highest combined platform-wide rental count. Return the window's start, end, and total.

Two traps the spec calls out:

1. **The stats API only returns days that had at least one rental.** Missing days mean zero, not no-data. If you slide a window over only the dates the API returned, the "window" silently changes size and you get nonsense.
2. **No inner-loop recomputation.** Judges will read the code and reject any `sum(window)` inside the slide. The intended solution is O(n).

---

## Algorithm: Fixed-Width Sliding Window

**O(n)** time, O(n) memory where n = number of days in the range.

### Step 1 — Validate the range

`_validate_peak_window_range`:
- Both `from` and `to` parse as `YYYY-MM` → 400 otherwise.
- `from <= to` → 400 otherwise.
- `len(months) <= 12` → 400 otherwise.
- `(end - start).days + 1 >= 7` → 400 otherwise (the spec's "less than 7 days" check).

### Step 2 — Pull stats per month

One Central API call per month (≤ 12 calls), each `GET /api/data/rentals/stats?group_by=date&month=YYYY-MM`. Rows go into a `dict[date, int]`. Rows outside `[start, end]` are filtered (some month-stat APIs return slightly outside the requested window, so guarding here keeps the slide safe).

### Step 3 — **Zero-fill every calendar day** (the critical step)

```python
all_days = []
cursor = start
while cursor <= end:
    all_days.append(cursor)
    cursor += timedelta(days=1)
```

Now we have a dense, ordered list of every day in `[start, end]`. Days the API didn't return get pulled as `daily_counts.get(day, 0)` — implicit zero. **This is what keeps the window width fixed at exactly 7 calendar days.** Without it, a sparse stretch of low-activity days would compress and you'd compare 5-real-day windows against 7-real-day ones.

### Step 4 — Slide the window

```python
running_total = sum(daily_counts.get(day, 0) for day in all_days[:7])
best_total = running_total
best_start_index = 0

for right_index in range(7, len(all_days)):
    running_total += daily_counts.get(all_days[right_index], 0)         # entering
    running_total -= daily_counts.get(all_days[right_index - 7], 0)     # leaving
    if running_total > best_total:
        best_total = running_total
        best_start_index = right_index - 6
```

The loop body is **two dict lookups, two integer ops, one compare**. No nested sum, no slice, no recomputation. Each day is visited exactly twice across the whole run (once as it enters, once as it leaves).

The initial sum over the first 7 days is the only O(window) work, and it happens once outside the loop — the bonus pattern judges look for.

### Step 5 — Reconstruct the window

`best_start_index` is enough; `best_end = all_days[best_start_index + 6]`. Both are real `date` objects, so formatting is `.isoformat()`.

---

## Why "running total" and not "prefix sum"?

Both give O(n). For a **fixed window width**, a running total is simpler — one variable, two ops per step. Prefix sums shine when window widths are queried dynamically (`O(1)` query for any `[i, j]`), but here every window is exactly 7 days. The running total is the right tool.

---

## Complexity

| Step | Cost |
|------|------|
| Central API calls | up to 12 (one per month) |
| Building `daily_counts` | O(rows returned) |
| Zero-fill `all_days` | O(n), n ≤ ~370 |
| Initial 7-day sum | O(7) — one-time |
| Slide | **O(n)** — two ops per step |
| Memory | O(n) |

A naive solution that recomputes the window sum at each position is O(7 × n). With a 12-month range that's only ~2,500 ops, so it's fast enough — but the judges grade approach. The hint and the "no inner-loop sum recalculation" verification line are explicit about wanting the running-total form.

---

## Edge cases

- **`from == to` and the month has 31 days** → 31 ≥ 7, valid. One month, slide as normal.
- **`(end - start).days + 1 == 7`** → exactly one window position. Initial sum is the answer; the slide loop never executes. Still correct.
- **Entire range has zero rentals** → all counts are 0, every window ties at 0, `best_start_index` stays at 0. The first 7 days are returned with `totalRentals: 0`.
- **Ties on `best_total`** → the *first* window encountered wins (we use `>`, not `>=`). Deterministic.
- **API returns dates outside `[start, end]`** → guarded by the `if start <= row_date <= end` check before insertion.
- **API returns the same date in multiple month responses** (shouldn't happen, but defensively) → `daily_counts.get(day, 0) + int(row["count"])` accumulates rather than overwrites.

---

## Cross-references

- **P13 (surge days)** uses a different scan over a similar daily-count structure (monotonic stack for next-greater-element). Both rely on the same zero-fill discipline — never trust the stats API to return every calendar day.
- **P8 (kth busiest date)** queries the same endpoint for a different question; it doesn't need zero-fill because missing days can't be in the top-k anyway.
