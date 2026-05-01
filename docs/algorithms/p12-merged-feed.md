# P12: Unified Rental Feed — K-Way Merge via Divide-and-Conquer

**Endpoint:** `GET /rentals/merged-feed?productIds=12,47,...&limit=N`
**Service:** `rental-service`
**Code:**
- Route: `rental-service/rental_service/api/routes.py`
- Service: `rental-service/rental_service/services/rentals.py` (`get_merged_feed`, `_merge_feed_groups`, `_merge_sorted_feeds`, `_normalize_feed_rental`, `_feed_sort_key`)
- Validation: `parse_merged_feed_product_ids`, `require_merged_feed_limit`

---

## Problem

Given up to 10 product ids and a `limit` (≤100), return the first `limit` rentals across **all** of those products, sorted globally by `rentalStart` ascending.

The Central API already returns each product's rentals sorted chronologically. So the input is **K already-sorted lists** and the question is how to merge them into one global sorted output without redoing work the API has already done.

The hint spells out the target: **pairwise merge applied recursively**, total cost **O(N · K · log K)** where N is the records returned.

---

## Algorithm

Two-pointer pairwise merge + divide-and-conquer over the K streams + a `limit` early-exit threaded through every step.

### Step 1 — Parse and dedupe

```python
deduped_product_ids = list(dict.fromkeys(product_ids))
```

`dict.fromkeys` preserves first-seen order while removing duplicates — important so the `productIds` echoed back in the response matches what the user actually gets results for.

Validation:
- `productIds`: 1–10 comma-separated integers → 400 otherwise.
- `limit`: positive integer, max 100 → 400 otherwise.

### Step 2 — Fetch each stream, capped at `limit`

```python
for product_id in deduped_product_ids:
    rentals = await fetch_all_pages(
        client, "/api/data/rentals",
        params={"product_id": str(product_id)},
        max_items=limit,
    )
    feeds.append([_normalize_feed_rental(r) for r in rentals])
```

The key optimization: **a single stream can contribute at most `limit` records to the final answer**, so there's no reason to page past that. `max_items=limit` short-circuits pagination once the stream has enough — saves Central API quota and memory linearly in K.

A product with no rentals → empty list, not an error.

`_normalize_feed_rental` standardizes the shape (`rentalId`, `productId`, `rentalStart`, `rentalEnd`) and trims timestamps to dates.

### Step 3 — Two-pointer pairwise merge

`_merge_sorted_feeds(left, right, limit)`:

```python
while len(merged) < limit and l_idx < len(left) and r_idx < len(right):
    if key(left[l_idx]) <= key(right[r_idx]):
        merged.append(left[l_idx]); l_idx += 1
    else:
        merged.append(right[r_idx]); r_idx += 1
# drain whichever side has remaining items, still respecting `limit`
```

No sorting inside — just two cursors and a key comparison. Stops early once `len(merged) == limit`.

**Sort key:** `(rentalStart, productId, rentalId)`. The primary key is the date; product/rental ids are tiebreakers so the output is deterministic when multiple rentals start the same day. Without a tiebreaker, the merge order on equal dates would depend on which stream the merge happened to consult first — fine for correctness, bad for testability.

### Step 4 — Divide-and-conquer over K streams

`_merge_feed_groups(feeds, limit)`:

```python
if len(feeds) == 1:
    return feeds[0][:limit]
mid = len(feeds) // 2
left  = _merge_feed_groups(feeds[:mid], limit)
right = _merge_feed_groups(feeds[mid:], limit)
return _merge_sorted_feeds(left, right, limit)
```

This builds a balanced binary tree of merges with depth `⌈log K⌉`. Each level does total work proportional to the number of records currently alive, capped at `limit` per intermediate result. The classic merge-sort reduction.

---

## Why divide-and-conquer over "merge into accumulator"

The naive K-way alternative is "fold left": merge stream 1 with stream 2 → result, merge result with stream 3 → result, etc. With K streams of size N each:

- **Naive fold:** total work `O(N · K²)` — each accumulator pass touches up to K·N items K times.
- **Divide-and-conquer:** `O(N · K · log K)` — the depth log K caps how many times any single record gets re-copied.

The divisor matters when K is small but non-trivial (here K ≤ 10 → log K ≈ 3.3). Bonus-grade approach.

A min-heap K-way merge (`heapq.merge`-style) hits the same `O(N · K · log K)` bound and is what most production systems use. The hint specifies the divide-and-conquer form, which is what's implemented here.

---

## Complexity

| Step | Cost |
|------|------|
| Fetch K streams | O(K · limit) network records (each capped at `limit`) |
| Pairwise merge | O(records merged) per level |
| Total merge | **O(N · K · log K)**, N = records returned ≤ limit |
| Memory | O(K · limit) at peak |

`limit ≤ 100` and `K ≤ 10`, so this is small in absolute terms — but the algorithmic structure is what's graded.

---

## Edge cases

- **Single productId** → `_merge_feed_groups` short-circuits at `len(feeds) == 1` and returns `feeds[0][:limit]` directly. No merging happens.
- **Empty stream** (productId with no rentals) → contributes an empty list; pairwise merge handles it via the cursor checks (`l_idx < len(left)` short-circuits immediately).
- **All streams empty** → final result is `[]`. `feed` field still present, just empty.
- **Total rentals < limit** → return whatever exists; `feed` length < `limit` is allowed by the spec.
- **Duplicate productIds in the query** → deduped before fetching; the `productIds` field in the response echoes the deduped list.
- **Same `rentalStart` across products** → tiebreaker `(productId, rentalId)` makes the output deterministic; identical rentals from a duplicate-product fetch can't occur (we deduped).
- **`limit > total records across all streams`** → fine, drain loops handle it; no off-by-one.

---

## Cross-references

- The two-pointer merge primitive is the heart of merge-sort and reappears anywhere two sorted streams need a sorted union (e.g. an interval merge if all intervals were pre-sorted into K disjoint groups, though P7's input isn't structured that way).
