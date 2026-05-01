# P10: Longest Free Streak — Clip + Merge + Gap Scan

**Endpoint:** `GET /rentals/products/:id/free-streak?year=YYYY`
**Service:** `rental-service`
**Code:**
- Route: `rental-service/rental_service/api/routes.py`
- Service: `rental-service/rental_service/services/rentals.py` (`get_longest_free_streak`)
- Helpers: `rental-service/rental_service/utils/intervals.py` (`clip_interval`, `merge_intervals`, `longest_free_streak`, `gap_length_days`)

---

## Problem

Given a product and a calendar year, find the **longest continuous period (in days)** during which the product was *not* rented, **within that year**.

Complications the spec calls out:
- Rentals can overlap each other.
- Rentals can start before Jan 1 or end after Dec 31 — they only count for the portion that intersects the year.
- A naive day-by-day scan over 365 days × N rentals is wrong (misses overlap consolidation) and wasteful.

---

## Algorithm

The hint says it directly: **once you have clean, non-overlapping intervals, the rest is a scan.** This is P7's sort+merge primitive plus a one-pass gap scan.

### Step 1 — Fetch and clip to the year

```python
year_start = date(year, 1, 1)
year_end   = date(year, 12, 31)

intervals = []
for rental in rentals:
    start = parse_iso_to_date(rental["rentalStart"])
    end   = parse_iso_to_date(rental["rentalEnd"])
    clipped = clip_interval(start, end, year_start, year_end)
    if clipped is not None:
        intervals.append(clipped)
```

`clip_interval` returns `(max(start, year_start), min(end, year_end))` or `None` if the rental is entirely outside the year. This handles the "starts before Jan 1 / ends after Dec 31" edge case in one place.

### Step 2 — Merge to non-overlapping busy spans

`merge_intervals` (the P7 primitive): sort by `(start, end)`, then linear sweep extending the rightmost merged span when the next interval overlaps or touches it. **O(n log n)** sort + **O(n)** sweep.

### Step 3 — Scan gaps

`longest_free_streak(year_start, year_end, merged_busy)` walks three kinds of gaps in one pass:

1. **Leading gap:** if `year_start < merged_busy[0].start`, candidate is `[year_start, merged_busy[0].start - 1 day]`.
2. **Between-pair gaps:** for each consecutive pair `(prev, next)`, candidate is `[prev.end + 1 day, next.start - 1 day]` if non-empty.
3. **Trailing gap:** if `merged_busy[-1].end < year_end`, candidate is `[merged_busy[-1].end + 1 day, year_end]`.

Track the longest candidate by `gap_length_days = (end - start).days + 1` (inclusive on both ends).

**Empty merged list** (no rentals in this year, including everything-clipped-away): return `(year_start, year_end)` — the entire year is one free span.

---

## Complexity

| Step | Cost |
|------|------|
| Fetch rentals | O(n) network (paginated) |
| Clip | O(n) |
| Merge (sort + sweep) | O(n log n) |
| Gap scan | O(m), m ≤ n |

Total: **O(n log n)**, dominated by the sort. Memory O(n).

A naive 365-day boolean array would be O(365 × n) and obscures the algorithm; the merge approach scales independently of year length.

---

## Edge cases

- **No rentals at all** → entire year is the longest free streak.
- **All rentals fall outside the year** → all clipped to `None`, merged list empty → entire year free (same path).
- **Rental spans the whole year** → merged list is `[(year_start, year_end)]`, no leading/trailing/between gaps → no free streak. Current code returns `{"from": "", "to": "", "days": 0}`. (Pragmatic sentinel; an explicit `null` would be cleaner if the spec required it.)
- **Rental starts in previous year and ends mid-year** → `clip_interval` snaps the start to Jan 1; merge treats it like any other interval.
- **Rentals that touch by exactly one day** (`prev.end + 1 day == next.start`) → coalesced into one busy run by `merge_intervals` (consistent with P7's convention). No spurious zero-length gap is produced.
- **Single-day rentals** (`start == end`) → handled identically; gap math uses inclusive day counts.
- **Multiple gaps tied for longest** → first encountered wins (deterministic by sweep order — earliest gap in the year).

---

## Why this shares P7's sub-problem

P7 returns busy + free windows inside an arbitrary `[from, to]`. P10 fixes that window to a calendar year and asks for the *single longest* free window. After clipping and merging, the gap-finding logic is essentially the same scan as `compute_free_windows` from P7 — just tracking `max` instead of emitting every gap.

If you've solved P7 cleanly, P10 is a 20-line addition.
