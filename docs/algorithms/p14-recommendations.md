# P14: Seasonal Recommendations — Cross-Year Window + Bounded Top-K

**Endpoint:** `GET /analytics/recommendations?date=YYYY-MM-DD&limit=N`
**Service:** `analytics-service`
**Code:**
- Route: `analytics-service/analytics_service/api/routes.py`
- Service: `analytics-service/analytics_service/services/analytics.py` (`compute_recommendations`, `_shift_year`)

---

## Problem

For a target date, find products most frequently rented in the **same 15-day seasonal window** (±7 days) across the **past 2 years**, and return the top `limit` enriched with name and category.

Two algorithmic concerns:

1. **The seasonal window can cross year boundaries.** For `date=2024-01-03`, the window spans Dec 27 → Jan 10 — a calendar-arithmetic problem, not a string-arithmetic problem. The spec is explicit: use a date library, never subtract days from `YYYY-MM-DD` strings.
2. **Top-k selection.** P-counted products → top `limit`. Naive `sorted(...)[:limit]` is O(P log P); the bonus rewards an optimal selection (O(P log limit)).

---

## Algorithm

### Step 1 — Validate and shift to historical anchors

```python
anchor_day = _parse_yyyy_mm_dd(target_date)              # 400 if malformed
limit      = _require_recommendation_limit(limit)        # 1..50, 400 otherwise

for years_ago in range(1, PAST_SEASONAL_YEARS + 1):      # 1..2
    seasonal_anchor = _shift_year(anchor_day, -years_ago)
    window_start = seasonal_anchor - timedelta(days=SEASONAL_WINDOW_RADIUS_DAYS)
    window_end   = seasonal_anchor + timedelta(days=SEASONAL_WINDOW_RADIUS_DAYS)
```

`_shift_year` and `timedelta` are the boring-correct tools — they handle Feb 29 (leap-year anchor → Feb 28 fallback in non-leap years) and let the window naturally span year boundaries when needed. Subtracting 7 days from `2024-01-03` via `timedelta` produces `2023-12-27` without anyone manually thinking about month/year rollover.

### Step 2 — Fetch each historical window's rentals

```python
rentals = await _fetch_all_pages(
    client, "/api/data/rentals",
    params={"from": window_start.isoformat(), "to": window_end.isoformat()},
    max_total_pages=MAX_RECOMMENDATION_PAGES_PER_WINDOW,
)
```

Each window is one paginated query against the Central API's date-range filter. The page budget is capped to keep the total request count within the rate-limit ceiling (15-day windows × 2 years × pagination depth).

A second `if window_start <= rental_start <= window_end` check after parsing defends against the API returning stray rentals outside the requested range (defensive, not necessary if the API filter is exact).

### Step 3 — Tally product counts

```python
seasonal_counts: Counter[int] = Counter()
for rental in rentals:
    if window_start <= rental_start <= window_end:
        seasonal_counts[product_id] += 1
```

After both years are processed, `seasonal_counts` holds every product rented in either historical window, with its combined count across the two years (the "score" the spec uses).

If empty → return `{recommendations: []}` (spec is explicit: not a 404).

### Step 4 — Top-k via bounded min-heap (the bonus path)

```python
top_items = heapq.nlargest(
    limit,
    seasonal_counts.items(),
    key=lambda item: (item[1], -item[0]),
)
```

`heapq.nlargest(k, iterable, key)` is implemented as a **bounded min-heap of size k** internally — O(P log k) where P = distinct products counted. This is the same algorithmic shape as P8/P9's `push_bounded` helper, just using stdlib's pre-built version since we already need `heapq` for nothing else here.

**Sort key `(count, -productId)`:**
- Primary: `count` ascending → larger count is "larger" → kept by `nlargest`.
- Tiebreaker: `-productId` → smaller productId produces a larger key → kept on tie. Matches the prior implementation's `(-count, productId)` ascending sort behavior, deterministically.

### Step 5 — Enrich top-k with product details

```python
for batch in _chunked(ranked_product_ids, 50):
    payload = await client.get("/api/data/products/batch", params={"ids": ",".join(batch)})
```

Critical efficiency detail: **the batch lookup runs only on the top `limit` products**, not on every product seen in the windows. With `limit ≤ 50`, that's exactly one batch call regardless of how many distinct products were counted. If we batched every counted product before selecting top-k, we'd be paying Central API calls for products that never make the response.

Missing `productId` → fallback `name = "Product #<id>"` and `category = "UNKNOWN"` rather than dropping the row, so the response length always matches what the user asked for (up to `limit`).

---

## Why heap beats sort

| Approach | Selection cost |
|----------|---------------|
| `sorted(counts.items())[:limit]` | O(P log P) |
| `heapq.nlargest(limit, ...)` | **O(P log limit)** |

P can be a few thousand (every distinct product rented across two 15-day windows); `limit ≤ 50`. The heap form is asymptotically better and is what the bonus rewards.

`heapq.nlargest` and the homegrown `push_bounded` from `rental-service/utils/heap.py` are the same algorithm — the analytics service uses the stdlib version because the rest of the file already plays well with `heapq`-style patterns.

---

## Cross-year window — concrete example

`date=2024-01-03`, radius=7:
- `seasonal_anchor` for `years_ago=1`: `2023-01-03`.
- `window_start` = `2023-01-03 - 7d` = `2022-12-27`.
- `window_end`   = `2023-01-03 + 7d` = `2023-01-10`.
- Central API call: `?from=2022-12-27&to=2023-01-10`.

`_shift_year(date(2024,2,29), -1)` returns `date(2023,2,28)` (leap-year fallback). All this works automatically because we're using `date` arithmetic, not string slicing.

---

## Complexity

| Step | Cost |
|------|------|
| Central API rental fetches | 2 × paginated queries (capped at `MAX_RECOMMENDATION_PAGES_PER_WINDOW`) |
| Counting | O(R), R = total rentals in both windows |
| Top-k selection | **O(P log limit)** |
| Batch product lookup | ⌈limit / 50⌉ calls (= 1 since limit ≤ 50) |
| Memory | O(P + limit) |

---

## Edge cases

- **No historical rentals in either window** → `recommendations: []`, 200. Not a 404.
- **`date` lands on a leap day** (`2024-02-29`) → `_shift_year(_, -1)` falls back to `2023-02-28`. Window arithmetic continues from there. No exception.
- **Window crosses Jan 1** (`date=2024-01-03`) → handled by `timedelta`; the Central API call uses ISO dates spanning two years.
- **`limit > distinct products counted`** → `heapq.nlargest` returns however many exist; response length naturally < `limit`.
- **Central API returns rentals outside the requested window** → second range check filters them.
- **Rental missing `rentalStart` or `productId`** → row skipped via `continue`. Defensive.
- **Page budget exceeded for a window** → 502 with `RECOMMENDATIONS_PAGE_BUDGET_DETAIL`. Surfaced explicitly rather than silently truncating.

---

## Cross-references

- **P8 / P9** — same top-k pattern (bounded min-heap), different use of the helper. P9 uses the homegrown `push_bounded`; here we lean on `heapq.nlargest` for the same big-O.
- **P11** — same Central API stats family, different shape (daily counts vs. raw rentals). Recommendations need raw rentals because we want per-product attribution, not per-day totals.
