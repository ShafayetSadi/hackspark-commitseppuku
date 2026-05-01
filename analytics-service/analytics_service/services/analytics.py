"""Analytics computations over Central API product data."""

from collections import Counter

from shared.app_core.central_api import CentralAPIClient


async def _fetch_all_products(client: CentralAPIClient) -> list[dict]:
    """Best-effort fetch — returns whatever the Central API provides."""
    try:
        result = await client.get("/api/data/products")
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            for key in ("data", "results", "items", "products"):
                if isinstance(result.get(key), list):
                    return result[key]
        return []
    except Exception:
        return []


async def compute_trends(client: CentralAPIClient, category: str | None) -> dict:
    products = await _fetch_all_products(client)

    if category:
        products = [p for p in products if str(p.get("category", "")).lower() == category.lower()]

    category_counts: Counter = Counter()
    for product in products:
        cat = str(product.get("category", "unknown"))
        category_counts[cat] += 1

    return {
        "total_products": len(products),
        "by_category": dict(category_counts.most_common()),
        "top_categories": [cat for cat, _ in category_counts.most_common(5)],
    }


async def compute_surge(client: CentralAPIClient, category: str | None) -> dict:
    products = await _fetch_all_products(client)

    category_counts: Counter = Counter()
    for product in products:
        cat = str(product.get("category", "unknown"))
        category_counts[cat] += 1

    if not category_counts:
        return {"surge_detected": False, "categories": []}

    avg = sum(category_counts.values()) / len(category_counts)
    threshold = avg * 1.5

    surge_cats = [
        {"category": cat, "count": count, "surge_factor": round(count / avg, 2)}
        for cat, count in category_counts.items()
        if count >= threshold
    ]

    if category:
        surge_cats = [s for s in surge_cats if s["category"].lower() == category.lower()]

    return {
        "surge_detected": len(surge_cats) > 0,
        "average_per_category": round(avg, 2),
        "surge_threshold": round(threshold, 2),
        "categories": sorted(surge_cats, key=lambda x: -x["count"]),
    }


async def compute_recommendations(
    client: CentralAPIClient, category: str | None, limit: int
) -> dict:
    products = await _fetch_all_products(client)

    if category:
        products = [p for p in products if str(p.get("category", "")).lower() == category.lower()]

    # Score products by availability field if present, otherwise by position
    def score(p: dict) -> float:
        avail = p.get("availability", p.get("quantity", p.get("stock", 1)))
        try:
            return float(avail)
        except (TypeError, ValueError):
            return 1.0

    ranked = sorted(products, key=score, reverse=True)
    top = ranked[: max(1, limit)]

    return {
        "total_candidates": len(products),
        "recommendations": top,
    }
