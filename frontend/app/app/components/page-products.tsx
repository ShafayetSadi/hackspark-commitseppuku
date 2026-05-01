"use client";

import { useMemo, useState } from "react";

import {
  CATEGORIES,
  type CategoryFilter,
  PRODUCTS,
  type Product,
} from "../data";

import { Badge, Icon, PageHeader, Placeholder } from "./primitives";

type ProductsProps = {
  filterCategory: CategoryFilter;
  setFilterCategory: (value: CategoryFilter) => void;
};

const PER_PAGE = 12;

export function Products({ filterCategory, setFilterCategory }: ProductsProps) {
  const [search, setSearch] = useState("");
  const [priceMax, setPriceMax] = useState(2500);
  const [sort, setSort] = useState<"relevance" | "price-asc" | "price-desc" | "name">(
    "relevance",
  );
  const [selected, setSelected] = useState<Product | null>(null);
  const [pageNumber, setPageNumber] = useState(1);

  const filtered = useMemo(() => {
    let result = PRODUCTS.filter((p) => {
      if (
        filterCategory &&
        filterCategory !== "All" &&
        p.category !== filterCategory
      ) {
        return false;
      }
      if (
        search &&
        !p.name.toLowerCase().includes(search.toLowerCase()) &&
        !String(p.id).includes(search)
      ) {
        return false;
      }
      if (p.price > priceMax) return false;
      return true;
    });
    if (sort === "price-asc") result = [...result].sort((a, b) => a.price - b.price);
    if (sort === "price-desc") result = [...result].sort((a, b) => b.price - a.price);
    if (sort === "name")
      result = [...result].sort((a, b) => a.name.localeCompare(b.name));
    return result;
  }, [search, filterCategory, priceMax, sort]);

  // Clamp the page number against the filtered list length without a
  // setState-in-effect (which the React lint rule flags). Whenever filters
  // change, `filtered.length` changes too, so the clamp keeps us in range.
  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const page = Math.min(pageNumber, totalPages);
  const paged = filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  const setPage = (next: number) => {
    setPageNumber(Math.max(1, Math.min(next, totalPages)));
  };

  const resetFilters = () => {
    setSearch("");
    setFilterCategory("All");
    setPriceMax(2500);
    setSort("relevance");
    setPageNumber(1);
  };

  return (
    <div className="content">
      <PageHeader
        title="Product Marketplace"
        desc="Browse rental products by category, compare prices, and open product details before checking availability."
        actions={
          <button type="button" className="btn btn-secondary btn-sm">
            <Icon name="filter" size={13} /> Saved filters
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
          gridTemplateColumns: "1.5fr 1fr 1fr auto auto",
          gap: 10,
          alignItems: "end",
        }}
      >
        <div className="field">
          <label className="field-label">Search</label>
          <div
            className="search-input"
            style={{ background: "var(--surface-2)", maxWidth: "none" }}
          >
            <Icon name="search" size={13} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Product name or ID…"
            />
          </div>
        </div>
        <div className="field">
          <label className="field-label">Max price (৳/day)</label>
          <input
            type="range"
            min={50}
            max={2500}
            step={10}
            value={priceMax}
            onChange={(e) => setPriceMax(Number(e.target.value))}
            style={{ width: "100%" }}
          />
          <div
            className="mono"
            style={{ fontSize: 11, color: "var(--text-3)" }}
          >
            up to ৳{priceMax.toLocaleString()}
          </div>
        </div>
        <div className="field">
          <label className="field-label">Sort by</label>
          <select
            className="select"
            value={sort}
            onChange={(e) =>
              setSort(e.target.value as typeof sort)
            }
          >
            <option value="relevance">Relevance</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
            <option value="name">Name (A–Z)</option>
          </select>
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
          {filtered.length} {filtered.length === 1 ? "product" : "products"}
          {filterCategory && filterCategory !== "All" ? (
            <>
              {" · in "}
              <span style={{ color: "var(--text-2)" }}>{filterCategory}</span>
            </>
          ) : null}
        </div>
      </div>

      {filtered.length === 0 ? (
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
          {paged.map((p) => (
            <div
              key={p.id}
              className="product-card"
              onClick={() => setSelected(p)}
            >
              <Placeholder
                category={p.category}
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
                  {p.desc}
                </div>
                <div className="product-meta">
                  <div className="product-price">
                    ৳{p.price}
                    <small>/day</small>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary btn-sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelected(p);
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
      {filtered.length > PER_PAGE ? (
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
            Page {page} of {totalPages} · showing {paged.length} of{" "}
            {filtered.length}
          </div>
          <div style={{ display: "flex", gap: 6 }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              Previous
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              disabled={page === totalPages}
              onClick={() => setPage(page + 1)}
            >
              Next
            </button>
          </div>
        </div>
      ) : null}

      {/* Drawer */}
      <ProductDrawer
        product={selected}
        onClose={() => setSelected(null)}
      />
    </div>
  );
}

function ProductDrawer({
  product,
  onClose,
}: {
  product: Product | null;
  onClose: () => void;
}) {
  const open = !!product;
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
                category={product.category}
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
                ৳{product.price}
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
                  {product.desc}
                </div>
              </div>

              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 10,
                  marginTop: 16,
                }}
              >
                <DrawerKv label="Owner" value={`#${product.owner}`} />
                <DrawerKv label="Avg. response" value="~ 24 minutes" />
                <DrawerKv label="Min rental" value="1 day" />
                <DrawerKv label="Deposit" value={`৳${product.price * 2}`} />
              </div>

              <h3 className="section-title" style={{ marginTop: 24 }}>
                More in {product.category}
              </h3>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: 8,
                }}
              >
                {PRODUCTS.filter(
                  (p) =>
                    p.category === product.category && p.id !== product.id,
                )
                  .slice(0, 4)
                  .map((p) => (
                    <div
                      key={p.id}
                      style={{
                        padding: 10,
                        border: "1px solid var(--border)",
                        borderRadius: 8,
                      }}
                    >
                      <div
                        style={{
                          fontSize: 12.5,
                          fontWeight: 500,
                          marginBottom: 4,
                        }}
                      >
                        {p.name}
                      </div>
                      <div
                        className="mono"
                        style={{ fontSize: 11, color: "var(--text-3)" }}
                      >
                        ৳{p.price}/day · #{p.id}
                      </div>
                    </div>
                  ))}
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
