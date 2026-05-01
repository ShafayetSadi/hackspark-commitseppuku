# P7: Product Availability — Interval Merge

**Endpoint:** `GET /rentals/products/:id/availability?from=YYYY-MM-DD&to=YYYY-MM-DD`
**Service:** `rental-service`
**Code:**
- Route: `rental-service/rental_service/api/routes.py` (`availability`)
- Service: `rental-service/rental_service/services/rentals.py` (`get_product_availability`)
- Helpers: `rental-service/rental_service/utils/intervals.py`

---

## Problem

Given a product and a requested date window `[from, to]`, fetch every rental for the product and answer:

1. Is the product free for the entire requested window?
2. Which (merged, non-overlapping) busy periods exist?
3. Which free sub-windows remain inside `[from, to]`?

Rentals can overlap each other. A naive pairwise check against each rental gives wrong answers when three or more rentals chain-overlap.

---

## Algorithm: Sort + Sweep Merge

Classic interval-merging. **O(n log n)** sort + **O(n)** sweep.

### Steps

1. **Fetch** all rentals for the product, paginating `/api/data/rentals?product_id=:id` through the rate-limited `CentralAPIClient`.
2. **Parse** each rental into a `(start_date, end_date)` tuple. Dates are treated as inclusive on both ends.
3. **Sort** intervals by `(start, end)` ascending. This is the key insight: once sorted, every overlap with anything earlier must be with the *current rightmost merged interval*. No pairwise comparison needed.
4. **Merge** in one pass:
   - Initialize `merged = [first_interval]`.
   - For each subsequent `(s, e)`:
     - If `s <= merged[-1].end + 1` day, extend: `merged[-1].end = max(merged[-1].end, e)`. (Adjacent intervals — touching by exactly one day — are coalesced; we treat busy periods as a continuous union.)
     - Otherwise, append `(s, e)` as a new run.
5. **Busy periods (response):** filter merged intervals that intersect `[from, to]`. Returned **unclipped** so the client can see the real extent of each busy span (matches the spec example where periods extend outside the requested window).
6. **Free windows (response):** clip merged intervals to `[from, to]`, then walk left-to-right with a `cursor`:
   - For each clipped busy `[bs, be]`: if `cursor < bs`, emit `[cursor, bs - 1]`. Then `cursor = max(cursor, be + 1)`.
   - After the loop, if `cursor <= to`, emit `[cursor, to]`.
7. **`available`** is `true` iff no merged interval overlaps `[from, to]`.

### Why sort first?

Without sorting, merging requires repeatedly scanning all prior intervals for any that overlap the new one — O(n²) at best, and easy to get wrong when overlaps cascade (A-B overlap, B-C overlap, but A-C don't directly overlap; a pairwise pass merges {A,B} and {B,C} as separate runs and double-counts B).

After sorting by start date, the invariant is: **every interval already placed in `merged` ends no later than the next interval's start, except possibly the last one.** So only the last merged interval can absorb the new one. Single comparison per step → linear sweep.

---

## Complexity

| Step | Cost |
|------|------|
| Fetch rentals | O(n) network (paginated) |
| Sort | O(n log n) |
| Merge sweep | O(n) |
| Busy filter | O(m) where m = merged count |
| Free windows | O(m) |

Total: **O(n log n)** dominated by the sort.

---

## Edge cases

- **No rentals:** entire `[from, to]` is one free window; `available = true`.
- **Rental fully containing the window:** zero free windows; `available = false`.
- **Rental starts before `from` or ends after `to`:** `busyPeriods` reports the full extent (unclipped); `freeWindows` is computed from the clipped version.
- **Rentals touching by one day** (`prev.end + 1 day == next.start`): merged into a single busy period. Pick a convention and stick with it across merge and free-window steps — this codebase coalesces adjacent days.
- **Single-day rental** (`start == end`): handled the same as any other interval (inclusive on both ends).
- **Invalid date range** (`from > to`, malformed strings): `require_date_range` raises a 400 before any work is done.

---

## Reused helpers

The same `merge_intervals` + `compute_free_windows` primitives back **P10 (longest free streak)** — once you have clean non-overlapping intervals, both problems reduce to a linear scan over gaps.
