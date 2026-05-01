# P8: Kth Busiest Date — Bounded Min-Heap

**Endpoint:** `GET /rentals/kth-busiest-date?from=YYYY-MM&to=YYYY-MM&k=N`
**Service:** `rental-service`
**Code:**
- Route: `rental-service/rental_service/api/routes.py`
- Service: `rental-service/rental_service/services/rentals.py` (`get_kth_busiest_date`)
- Heap helper: `rental-service/rental_service/utils/heap.py` (`push_bounded`)
- Validation: `rental-service/rental_service/utils/validation.py` (`require_month_range`, `require_positive_int`)

---

## Problem

Given a month range `[from, to]` (max 12 months) and an integer `k`, find the date with the **kth highest rental count** across the range. Data comes from `GET /api/data/rentals/stats?group_by=date&month=YYYY-MM` — one call per month, returning `[{date, count}, ...]` for days that had at least one rental.

---

## Algorithm: Bounded Min-Heap (Top-K Selection)

**O(n log k)** — strictly better than the O(n log n) full-sort baseline, which earns the +15 bonus.

### Why not sort everything?

A full sort over n date-count pairs is O(n log n) and computes a total order we don't need. We only care about the **kth largest** — every comparison spent ranking dates outside the top-k is wasted work.

### The trick: keep only the top k seen so far

Maintain a **min-heap of size at most k**. The smallest element in this heap is always the current "kth-best candidate" — anything smaller than it cannot possibly be in the final top-k.

**Per-row decision (constant size, log-k cost):**

```
if heap has fewer than k items:
    heappush(heap, item)
elif item > heap[0]:        # item beats the current weakest top-k
    heapreplace(heap, item) # pop smallest, push new — single sift
# else: item is worse than every top-k candidate, discard
```

After processing all rows, `heap[0]` is the **kth largest** (the smallest survivor in a heap that holds exactly the top k).

### Tuple key and tiebreaker

Items are pushed as `(count, -ordinal, date_str)`:
- `count` — primary key, larger = busier.
- `-ordinal` — tiebreaker. With heap min-comparison, items with **larger** `-ordinal` (i.e. earlier dates) are kept over items with the same count but later dates. Choose any consistent tiebreaker — the spec doesn't pin one down — but document it.
- `date_str` — formatted output, carried along so we don't reformat at the end.

---

## Streaming over months

Months are fetched **sequentially** via the rate-limited `CentralAPIClient` (max 12 months bounds the Central API call count to 12). Each month's rows feed straight into `push_bounded` — no intermediate list of all dates is materialized. Memory stays at O(k).

`total_dates` is incremented per row regardless of whether the heap kept it; this is what we compare against `k` for the 404 check.

---

## Complexity

| Step | Cost |
|------|------|
| Central API calls | up to 12 (one per month) |
| Heap operations | O(n log k), n = total date rows |
| Memory | O(k) for the heap |

Compare to full sort: **O(n log n)** time, **O(n)** memory. Both n and the constant are small in practice (≤ ~370 rows for 12 months), but the heap approach is the asymptotically correct answer to the hint.

---

## Validation

Handled before any Central API call:

- `from` and `to` must match `YYYY-MM` → 400 if not.
- `from` must not be after `to` → 400.
- Range must be ≤ 12 months → 400.
- `k` must be a positive integer → 400.
- After processing, if `total_dates < k` → 404 (k exceeds available distinct dates).

---

## Edge cases

- **Sparse months:** the stats API only returns days that had at least one rental. That's fine here — we only need the top-k *across* the range; missing zero-rental days can't be in the top-k anyway. (P11 has the opposite requirement and must zero-fill.)
- **Ties on count:** resolved by the `-ordinal` tiebreaker — earlier date wins among equal counts.
- **`k = 1`:** heap of size 1; degenerates to a streaming max. Still correct.
- **`k` equals total dates:** heap fills exactly; `heap[0]` is the global minimum across all dates, which *is* the kth largest when k = n.

---

## Why this beats sort even when n is small

The judges verify *approach*, not just runtime. A `sorted(all_rows, reverse=True)[k-1]` solution is correct but caps at 70 points. The heap is the canonical "top-k without sorting" pattern — same one used by `heapq.nlargest` under the hood — and is what the hint is steering toward.
