"use client";

import { useEffect, useMemo, useState } from "react";

import {
  type Category,
  CATEGORIES,
  type CategoryFilter,
} from "../data";

import { Badge, Icon, PageHeader, Placeholder } from "./primitives";

type ProductsProps = {
  filterCategory: CategoryFilter;
  setFilterCategory: (value: CategoryFilter) => void;
};

const PER_PAGE = 12;

type Product = {
  id: number;
  name: string;
  category: string;
  pricePerDay: number;
  ownerId: number;
  description?: string;
};

function mapProduct(raw: Record<string, unknown>): Product {
  return {
    id: Number(raw.id ?? 0),
    name: String(raw.name ?? "Unnamed product"),
    category: String(raw.category ?? "UNKNOWN"),
    pricePerDay: Number(raw.pricePerDay ?? raw.price ?? 0),
    ownerId: Number(raw.ownerId ?? raw.owner ?? 0),
    description:
      typeof raw.description === "string"
        ? raw.description
        : typeof raw.desc === "string"
          ? raw.desc
          : undefined,
  };
}

function friendlyProductsError(status: number): string {
  if (status === 400) return "Please choose a valid category.";
  if (status === 429) return "Too many requests. Please wait a moment and try again.";
  if (status === 503) return "Products are unavailable right now. Try again soon.";
  return "Could not load products right now.";
}

function toKnownCategory(value: string): Category {
  const matched = CATEGORIES.find(
    (category) => category.toLowerCase() === value.toLowerCase(),
  );
  return matched ?? "Electronics";
}

export function Products({ filterCategory, setFilterCategory }: ProductsProps) {
  const [ownerId, setOwnerId] = useState("");
  const [selected, setSelected] = useState<Product | null>(null);
  const [pageNumber, setPageNumber] = useState(1);
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDetailsLoading, setIsDetailsLoading] = useState(false);

  const normalizedCategory = useMemo(() => {
    if (!filterCategory || filterCategory === "All") return "";
    return String(filterCategory).toUpperCase();
  }, [filterCategory]);

  useEffect(() => {
    const controller = new AbortController();
    const loadProducts = async () => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const query = new URLSearchParams({
          page: String(pageNumber),
          limit: String(PER_PAGE),
        });
        if (normalizedCategory) query.set("category", normalizedCategory);
        if (ownerId.trim()) query.set("owner_id", ownerId.trim());

        const response = await fetch(`/api/rentals/products?${query.toString()}`, {
          cache: "no-store",
          signal: controller.signal,
        });
        if (!response.ok) {
          setErrorMessage(friendlyProductsError(response.status));
          setProducts([]);
          setTotal(0);
          setTotalPages(1);
          return;
        }

        const payload = (await response.json()) as {
          data?: Record<string, unknown>[];
          total?: number;
          totalPages?: number;
        };
        const next = Array.isArray(payload.data) ? payload.data.map(mapProduct) : [];
        setProducts(next);
        setTotal(Number(payload.total ?? next.length));
        setTotalPages(Math.max(1, Number(payload.totalPages ?? 1)));
      } catch {
        if (!controller.signal.aborted) {
          setErrorMessage("Could not load products right now.");
          setProducts([]);
          setTotal(0);
          setTotalPages(1);
        }
      } finally {
        if (!controller.signal.aborted) setIsLoading(false);
      }
    };
    void loadProducts();
    return () => controller.abort();
  }, [normalizedCategory, ownerId, pageNumber]);

  const setPage = (next: number) => {
    setPageNumber(Math.max(1, Math.min(next, totalPages)));
  };

  const resetFilters = () => {
    setFilterCategory("All");
    setOwnerId("");
    setPageNumber(1);
  };

  const loadProductDetails = async (id: number) => {
    setIsDetailsLoading(true);
    try {
      const response = await fetch(`/api/rentals/products/${id}`, { cache: "no-store" });
      if (!response.ok) return;
      const payload = (await response.json()) as Record<string, unknown>;
      setSelected(mapProduct(payload));
    } catch {
      // Keep previous selected state on failure.
    } finally {
      setIsDetailsLoading(false);
    }
  };

  return (
    <div className="content">
      <PageHeader
        title="Product Marketplace"
        desc="Browse rental products by category, compare prices, and open product details before checking availability."
        actions={
          <button type="button" className="btn btn-secondary btn-sm">
            <Icon name="filter" size={13} /> API-powered filters
          </button>
        }
      />

      {/* Category chips */}
      <div
        style={{
          display: "flex",
          gap: 6,
          marginBottom: 16,
          flexWrap: "wrap",
        }}
      >
        <button
          type="button"
          className={`chip ${
            !filterCategory || filterCategory === "All" ? "active" : ""
          }`}
          onClick={() => setFilterCategory("All")}
        >
          All
        </button>
        {CATEGORIES.map((c) => (
          <button
            key={c}
            type="button"
            className={`chip ${filterCategory === c ? "active" : ""}`}
            onClick={() => setFilterCategory(c)}
          >
            {c}
          </button>
        ))}
      </div>

      {/* Filter bar */}
      <div
        className="card"
        style={{
          padding: 14,
          marginBottom: 18,
          display: "grid",
          gridTemplateColumns: "1fr 1fr auto",
          gap: 10,
          alignItems: "end",
        }}
      >
        <div className="field">
          <label className="field-label">Owner ID (optional)</label>
          <input
            className="input"
            inputMode="numeric"
            value={ownerId}
            onChange={(e) => {
              setOwnerId(e.target.value);
              setPageNumber(1);
            }}
            placeholder="e.g. 5021"
          />
        </div>
        <div className="field">
          <label className="field-label">Items per page</label>
          <div className="mono" style={{ fontSize: 12, color: "var(--text-3)", paddingBottom: 8 }}>
            {PER_PAGE}
          </div>
        </div>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={resetFilters}
        >
          Reset
        </button>
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 12,
        }}
      >
        <div className="mono" style={{ fontSize: 12, color: "var(--text-3)" }}>
          {total} {total === 1 ? "product" : "products"}
          {filterCategory && filterCategory !== "All" ? (
            <>
              {" · in "}
              <span style={{ color: "var(--text-2)" }}>{filterCategory}</span>
            </>
          ) : null}
        </div>
      </div>

      {errorMessage ? (
        <div className="card" style={{ padding: 20, marginBottom: 18 }}>
          <div style={{ fontSize: 13, color: "var(--warn)" }}>{errorMessage}</div>
        </div>
      ) : null}

      {isLoading ? (
        <div className="product-grid">
          {Array.from({ length: 6 }).map((_, idx) => (
            <div key={idx} className="product-card">
              <div className="skel" style={{ aspectRatio: "4/3" }} />
              <div className="product-body">
                <div className="skel" style={{ height: 12, width: "35%", marginBottom: 8 }} />
                <div className="skel" style={{ height: 16, width: "70%", marginBottom: 8 }} />
                <div className="skel" style={{ height: 11, width: "100%", marginBottom: 6 }} />
                <div className="skel" style={{ height: 11, width: "75%" }} />
              </div>
            </div>
          ))}
        </div>
      ) : products.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <div
            style={{
              width: 40,
              height: 40,
              borderRadius: 8,
              background: "var(--surface-2)",
              display: "inline-grid",
              placeItems: "center",
              marginBottom: 12,
              color: "var(--text-3)",
            }}
          >
            <Icon name="search" />
          </div>
          <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
            No products found
          </div>
          <div
            style={{
              fontSize: 12.5,
              color: "var(--text-3)",
              marginBottom: 14,
            }}
          >
            Try changing your filters or search query.
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={resetFilters}
          >
            Reset filters
          </button>
        </div>
      ) : (
        <div className="product-grid">
          {products.map((p) => (
            <div
              key={p.id}
              className="product-card"
              onClick={() => void loadProductDetails(p.id)}
            >
              <Placeholder
                category={toKnownCategory(p.category)}
                label={`${p.category.toLowerCase()}.jpg`}
              />
              <div className="product-body">
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "flex-start",
                    gap: 8,
                  }}
                >
                  <Badge variant="default">{p.category}</Badge>
                  <span
                    className="mono"
                    style={{ fontSize: 10.5, color: "var(--text-4)" }}
                  >
                    #{p.id}
                  </span>
                </div>
                <div className="product-title">{p.name}</div>
                <div
                  style={{
                    fontSize: 12,
                    color: "var(--text-3)",
                    overflow: "hidden",
                    display: "-webkit-box",
                    WebkitLineClamp: 2,
                    WebkitBoxOrient: "vertical",
                  }}
                >
                  {p.description ?? "View details for complete product information."}
                </div>
                <div className="product-meta">
                  <div className="product-price">
                    ৳{p.pricePerDay}
                    <small>/day</small>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      void loadProductDetails(p.id);
                    }}
                  >
                    View
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 ? (
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: 20,
          }}
        >
          <div
            className="mono"
            style={{ fontSize: 12, color: "var(--text-3)" }}
          >
            Page {pageNumber} of {totalPages} · showing {products.length} of {total}
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={pageNumber === 1}
              onClick={() => setPage(pageNumber - 1)}
            >
              Previous
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={pageNumber === totalPages}
              onClick={() => setPage(pageNumber + 1)}
            >
              Next
            </button>
          </div>
        </div>
      ) : null}

      {/* Drawer */}
      <ProductDrawer
        product={selected}
        isLoading={isDetailsLoading}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

function ProductDrawer({
  product,
  isLoading,
  onClose,
}: {
  product: Product | null;
  isLoading: boolean;
  onClose: () => void;
}) {
  const open = !!product || isLoading;
  const [freeStreak, setFreeStreak] = useState<{
    from: string;
    to: string;
    days: number;
  } | null>(null);

  useEffect(() => {
    const loadFreeStreak = async () => {
      if (!product) {
        setFreeStreak(null);
        return;
      }
      try {
        const year = new Date().getFullYear();
        const response = await fetch(
          `/api/rentals/products/${product.id}/free-streak?year=${year}`,
          { cache: "no-store" },
        );
        if (!response.ok) {
          setFreeStreak(null);
          return;
        }
        const payload = (await response.json()) as {
          longestFreeStreak?: { from?: string; to?: string; days?: number };
        };
        const streak = payload.longestFreeStreak;
        if (!streak) {
          setFreeStreak(null);
          return;
        }
        setFreeStreak({
          from: streak.from ?? "",
          to: streak.to ?? "",
          days: Number(streak.days ?? 0),
        });
      } catch {
        setFreeStreak(null);
      }
    };
    void loadFreeStreak();
  }, [product]);
  return (
    <>
      <div
        className={`drawer-backdrop ${open ? "open" : ""}`}
        onClick={onClose}
      />
      <div className={`drawer ${open ? "open" : ""}`}>
        {product ? (
          <>
            <div className="drawer-header">
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Badge variant="default">{product.category}</Badge>
                <span
                  className="mono"
                  style={{ fontSize: 11, color: "var(--text-3)" }}
                >
                  #{product.id}
                </span>
              </div>
              <button type="button" className="icon-btn" onClick={onClose}>
                <Icon name="close" />
              </button>
            </div>
            <div className="drawer-body">
              <Placeholder
                category={toKnownCategory(product.category)}
                label={`${product.category.toLowerCase()}.jpg`}
              />
              <h2
                style={{
                  fontSize: 22,
                  fontWeight: 600,
                  letterSpacing: "-0.025em",
                  margin: "18px 0 4px",
                }}
              >
                {product.name}
              </h2>
              <div
                style={{
                  fontSize: 18,
                  fontWeight: 600,
                  color: "var(--accent-deep)",
                }}
              >
                ৳{product.pricePerDay}
                <span
                  style={{
                    fontSize: 13,
                    color: "var(--text-3)",
                    fontWeight: 400,
                  }}
                >
                  /day
                </span>
              </div>

              <div
                style={{
                  marginTop: 20,
                  padding: 14,
                  background: "var(--surface-2)",
                  borderRadius: 10,
                }}
              >
                <div
                  style={{
                    fontSize: 12.5,
                    color: "var(--text-2)",
                    lineHeight: 1.55,
                  }}
                >
                  {product.description ?? "No description provided."}
                </div>
              </div>

              {freeStreak ? (
                <div
                  style={{
                    marginTop: 12,
                    padding: 12,
                    borderRadius: 10,
                    background: "var(--surface-2)",
                  }}
                >
                  <div className="mono" style={{ fontSize: 11, color: "var(--text-3)" }}>
                    LONGEST FREE STREAK
                  </div>
                  <div style={{ fontSize: 13, marginTop: 4 }}>
                    {freeStreak.from} → {freeStreak.to} ({freeStreak.days} days)
                  </div>
                </div>
              ) : null}

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 10,
                  marginTop: 16,
                }}
              >
                <DrawerKv label="Owner" value={`#${product.ownerId}`} />
                <DrawerKv label="Avg. response" value="~ 24 minutes" />
                <DrawerKv label="Min rental" value="1 day" />
                <DrawerKv label="Deposit" value={`৳${product.pricePerDay * 2}`} />
              </div>
            </div>
            <div className="drawer-footer">
              <button type="button" className="btn btn-ghost">
                <Icon name="sparkle" size={13} /> Ask assistant
              </button>
              <div style={{ flex: 1 }} />
              <button type="button" className="btn btn-secondary">
                Check availability
              </button>
              <button type="button" className="btn btn-accent">
                Request rental
              </button>
            </div>
          </>
        ) : isLoading ? (
          <div className="drawer-body">
            <div className="skel" style={{ height: 220, borderRadius: 12 }} />
            <div className="skel" style={{ height: 22, width: "60%", marginTop: 12 }} />
            <div className="skel" style={{ height: 12, width: "35%", marginTop: 8 }} />
          </div>
        ) : null}
      </div>
    </>
  );
}

function DrawerKv({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div
        className="mono"
        style={{
          fontSize: 10.5,
          color: "var(--text-3)",
          textTransform: "uppercase",
          letterSpacing: "0.06em",
          marginBottom: 4,
        }}
      >
        {label}
      </div>
      <div style={{ fontSize: 13 }}>{value}</div>
    </div>
  );
}
