# P9: User Top Categories — Batch Lookup + Bounded Min-Heap

**Endpoint:** `GET /rentals/users/:id/top-categories?k=N`
**Service:** `rental-service`
**Code:**
- Route: `rental-service/rental_service/api/routes.py`
- Service: `rental-service/rental_service/services/rentals.py` (`get_user_top_categories`)
- Heap helper: `rental-service/rental_service/utils/heap.py` (`push_bounded`)
- Tiebreaker key: `rental-service/rental_service/services/rentals.py` (`_category_rank_key`)

---

## Problem

For a given user, find the top `k` product categories they rent most often. Three sub-problems stacked:

1. **Pull all of the user's rentals** (paginated) — gives a list of `productId`s.
2. **Resolve each product → category** without making N individual calls — must use the batch endpoint, max 50 ids per call.
3. **Tally counts per category and return the top k** — without full sorting (for the +10 bonus).

The hint says "this looks like an earlier problem" — that earlier problem is **P8**, which used a bounded min-heap for top-k selection. Same pattern applies here.

---

## Algorithm

### Step 1 — Fetch rentals

```
fetch_all_pages("/api/data/rentals", params={"renter_id": user_id})
```

Streams pages via the rate-limited `CentralAPIClient`. If the user has zero rentals, return `{topCategories: []}` immediately (spec says no 404).

### Step 2 — Resolve categories via batch endpoint

```
product_ids = sorted({int(r["productId"]) for r in rentals})  # dedupe
for batch in chunked(product_ids, 50):
    payload = client.get("/api/data/products/batch", params={"ids": ",".join(batch)})
    for item in payload["data"]:
        product_categories[item["id"]] = item["category"]
```

Two things matter:

- **Dedupe before chunking.** A user who rented the same product 14 times should produce one batch entry, not fourteen. This minimizes the number of batch calls and keeps us comfortably under the 30 req/min Central API ceiling.
- **Chunk size = 50** (the documented batch ceiling). Anything larger is rejected.

### Step 3 — Count per category

```
counts: Counter[str] = Counter()
for rental in rentals:
    category = product_categories.get(rental["productId"])
    if category is not None:
        counts[category] += 1
```

This is `O(R)` where R = rental count. After this step, `counts` has at most C entries (C = distinct categories = at most 30 in this dataset).

### Step 4 — Top-k via bounded min-heap (the bonus path)

Same primitive as P8 — `push_bounded` keeps a min-heap of size at most k:

```
heap: list[tuple[int, tuple[int, ...], str]] = []
for category, count in counts.items():
    push_bounded(heap, (count, _category_rank_key(category), category), k)
```

Tuple key: `(count, rank_key, category_name)`.

- **count** is primary — heap min is the weakest top-k candidate.
- **`_category_rank_key`** is a tuple of negated character ordinals. Tuple comparison is element-wise, so lex-smaller names produce a *larger* rank key. With `push_bounded`'s `item > heap[0]` rule, this means: on a count tie, the lex-smaller category replaces a lex-larger one (consistent, deterministic alphabetic tiebreak).
- **category_name** is the displayed string, carried through so we don't reverse-decode the rank key.

Final output ordering: sort the (≤ k) survivors by `(-count, name)` — that's `O(k log k)`, which doesn't change the asymptotic class.

---

## Why this beats full sort

| Approach | Selection cost |
|----------|---------------|
| `sorted(counts.items())[:k]` | O(C log C) |
| `push_bounded` over counts | **O(C log k)** |

C is small here (≤ 30 distinct categories), so the practical difference is negligible — but the judges grade on *approach*, not wall time. The heap is the algorithmically correct answer to the hint and earns the +10 bonus.

---

## Complexity

| Step | Cost |
|------|------|
| Fetch rentals | O(R) network (paginated) |
| Batch product lookup | ⌈|P| / 50⌉ Central API calls, where P = distinct products |
| Tallying counts | O(R) |
| Top-k selection | **O(C log k)** — the bonus-eligible step |
| Final sort of survivors | O(k log k) |
| Memory | O(P + C + k) |

---

## Validation & edge cases

- **`k` not a positive int** → 400 (`require_positive_int`).
- **User has no rentals** → `{userId, topCategories: []}` (200, not 404 — spec is explicit).
- **`k` > distinct categories rented** → return all rented categories. The bounded heap handles this naturally: when there are fewer items than k, every push goes through and the heap is just the full set.
- **Rented product not returned by batch** (Central API edge case) → skipped via `product_categories.get(...) is not None`. Avoids a `KeyError` if the batch endpoint omits an id.
- **Duplicate productId across rentals** → deduped before batching (count still accumulates per rental, not per product).

---

## Cross-references

- **P8** — same `push_bounded` primitive, different domain (dates instead of categories).
- The batch lookup pattern (dedupe → chunk → fetch) is reused anywhere we need to resolve a set of product ids without N round-trips.
