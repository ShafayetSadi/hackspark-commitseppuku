"use client";

import { useState } from "react";

import {
  BUSY_PERIODS,
  type BusyPeriod,
  type CategoryFilter,
  type PageId,
  PRODUCTS,
  type Product,
  TRENDING,
} from "../data";

import { Badge, Icon, PageHeader, Placeholder } from "./primitives";

type AvailabilityResult = {
  product: Product | undefined;
  busy: BusyPeriod[];
  fromDay: number;
  toDay: number;
  conflicts: BusyPeriod[];
  available: boolean;
};

export function Availability() {
  const [productId, setProductId] = useState("1042");
  const [from, setFrom] = useState("2026-05-08");
  const [to, setTo] = useState("2026-05-15");
  const [result, setResult] = useState<AvailabilityResult | null>(null);
  const [loading, setLoading] = useState(false);

  const check = () => {
    setLoading(true);
    setResult(null);
    setTimeout(() => {
      const id = parseInt(productId, 10);
      const product = PRODUCTS.find((p) => p.id === id);
      const busy =
        BUSY_PERIODS[id] !== undefined ? BUSY_PERIODS[id] : BUSY_PERIODS[1042];
      const fromDay = parseInt(from.split("-")[2] || "0", 10);
      const toDay = parseInt(to.split("-")[2] || "0", 10);
      const conflicts = busy.filter((b) => !(b.end < fromDay || b.start > toDay));
      setResult({
        product,
        busy,
        fromDay,
        toDay,
        conflicts,
        available: conflicts.length === 0,
      });
      setLoading(false);
    }, 700);
  };

  return (
    <div className="content">
      <PageHeader
        title="Availability Checker"
        desc="Enter a product ID and date range to see whether the item is available, including busy periods and free windows."
      />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "380px 1fr",
          gap: 16,
        }}
      >
        <div className="card" style={{ height: "fit-content" }}>
          <h2 className="section-title">Search</h2>
          <div
            style={{ display: "flex", flexDirection: "column", gap: 12 }}
          >
            <div className="field">
              <label className="field-label">Product ID</label>
              <input
                className="input"
                value={productId}
                onChange={(e) => setProductId(e.target.value)}
                placeholder="e.g. 1042"
              />
              <div className="field-help">Try 1042, 1088, or 1156.</div>
            </div>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: 8,
              }}
            >
              <div className="field">
                <label className="field-label">From</label>
                <input
                  className="input"
                  type="date"
                  value={from}
                  onChange={(e) => setFrom(e.target.value)}
                />
              </div>
              <div className="field">
                <label className="field-label">To</label>
                <input
                  className="input"
                  type="date"
                  value={to}
                  onChange={(e) => setTo(e.target.value)}
                />
              </div>
            </div>
            <div className="field-help">
              Choose the exact dates you want to rent the product.
            </div>
            <button
              type="button"
              className="btn btn-accent"
              onClick={check}
              disabled={loading}
            >
              {loading ? "Checking…" : "Check Availability"}
            </button>
          </div>
        </div>

        <div className="card" style={{ minHeight: 320 }}>
          {!result && !loading ? (
            <div
              style={{
                display: "grid",
                placeItems: "center",
                height: "100%",
                minHeight: 280,
                textAlign: "center",
                color: "var(--text-3)",
              }}
            >
              <div>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: 8,
                    background: "var(--surface-2)",
                    display: "inline-grid",
                    placeItems: "center",
                    marginBottom: 12,
                  }}
                >
                  <Icon name="calendar" />
                </div>
                <div
                  style={{
                    fontSize: 14,
                    fontWeight: 500,
                    color: "var(--text-2)",
                    marginBottom: 4,
                  }}
                >
                  Your availability result will appear here
                </div>
                <div style={{ fontSize: 12.5 }}>
                  Enter a product ID and date range, then run a check.
                </div>
              </div>
            </div>
          ) : null}

          {loading ? (
            <div
              style={{
                display: "grid",
                placeItems: "center",
                height: "100%",
                minHeight: 280,
              }}
            >
              <div style={{ textAlign: "center", color: "var(--text-3)" }}>
                <div className="typing-dots" style={{ marginBottom: 8 }}>
                  <span />
                  <span />
                  <span />
                </div>
                <div style={{ fontSize: 13 }}>Checking availability…</div>
              </div>
            </div>
          ) : null}

          {result && !loading ? (
            <>
              <div
                className={result.available ? "result-success" : "result-warn"}
                style={{ marginBottom: 18 }}
              >
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 8,
                    marginBottom: 6,
                  }}
                >
                  {result.available ? (
                    <Icon name="check" />
                  ) : (
                    <Icon name="info" />
                  )}
                  <span style={{ fontSize: 14, fontWeight: 600 }}>
                    {result.available ? "Available" : "Partially unavailable"}
                  </span>
                </div>
                <div style={{ fontSize: 13, color: "var(--text-2)" }}>
                  {result.available
                    ? `${result.product?.name || "This product"} is free for your selected dates.`
                    : `${result.product?.name || "This product"} has bookings during your selected dates.`}
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 18,
                    marginTop: 12,
                    fontSize: 12,
                  }}
                >
                  <div>
                    <div
                      className="mono"
                      style={{
                        fontSize: 10.5,
                        color: "var(--text-3)",
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        marginBottom: 2,
                      }}
                    >
                      Requested
                    </div>
                    <div>
                      {from} → {to}
                    </div>
                  </div>
                  <div>
                    <div
                      className="mono"
                      style={{
                        fontSize: 10.5,
                        color: "var(--text-3)",
                        textTransform: "uppercase",
                        letterSpacing: "0.06em",
                        marginBottom: 2,
                      }}
                    >
                      Product
                    </div>
                    <div>
                      #{productId}
                      {result.product ? ` · ${result.product.name}` : ""}
                    </div>
                  </div>
                </div>
              </div>

              <h3 className="section-title">May 2026 timeline</h3>
              <div style={{ position: "relative", marginBottom: 6 }}>
                <div className="timeline">
                  {result.busy.map((b, i) => (
                    <div
                      key={i}
                      className="timeline-segment timeline-busy"
                      style={{
                        left: `${(b.start / 31) * 100}%`,
                        width: `${((b.end - b.start + 1) / 31) * 100}%`,
                      }}
                      title={`${b.by} · day ${b.start}–${b.end}`}
                    />
                  ))}
                  <div
                    className="timeline-requested"
                    style={{
                      left: `${(result.fromDay / 31) * 100}%`,
                      width: `${((result.toDay - result.fromDay + 1) / 31) * 100}%`,
                    }}
                  />
                </div>
                <div className="timeline-axis">
                  <span>May 1</span>
                  <span>May 8</span>
                  <span>May 15</span>
                  <span>May 22</span>
                  <span>May 31</span>
                </div>
              </div>
              <div
                style={{
                  display: "flex",
                  gap: 14,
                  fontSize: 11,
                  color: "var(--text-3)",
                  fontFamily: "var(--font-mono)",
                  marginTop: 12,
                }}
              >
                <span>
                  <span
                    style={{
                      display: "inline-block",
                      width: 10,
                      height: 10,
                      background: "var(--accent-tint)",
                      borderRadius: 2,
                      verticalAlign: "middle",
                      marginRight: 4,
                    }}
                  />
                  free
                </span>
                <span>
                  <span
                    style={{
                      display: "inline-block",
                      width: 10,
                      height: 10,
                      background: "var(--warn-soft)",
                      borderRadius: 2,
                      verticalAlign: "middle",
                      marginRight: 4,
                    }}
                  />
                  busy
                </span>
                <span>
                  <span
                    style={{
                      display: "inline-block",
                      width: 10,
                      height: 10,
                      border: "1.5px solid var(--text)",
                      borderRadius: 2,
                      verticalAlign: "middle",
                      marginRight: 4,
                    }}
                  />
                  your request
                </span>
              </div>

              {result.conflicts.length > 0 ? (
                <>
                  <h3 className="section-title" style={{ marginTop: 22 }}>
                    Busy periods
                  </h3>
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 6,
                    }}
                  >
                    {result.busy.map((b, i) => (
                      <div
                        key={i}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          padding: "10px 12px",
                          border: "1px solid var(--border)",
                          borderRadius: 8,
                          background: result.conflicts.includes(b)
                            ? "var(--warn-soft)"
                            : "var(--surface)",
                        }}
                      >
                        <div style={{ fontSize: 12.5 }}>
                          May {b.start} → May {b.end}
                        </div>
                        <div
                          className="mono"
                          style={{ fontSize: 11, color: "var(--text-3)" }}
                        >
                          {b.by}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : null}

              <div style={{ marginTop: 20, display: "flex", gap: 8 }}>
                <button type="button" className="btn btn-secondary btn-sm">
                  Continue browsing
                </button>
                <button type="button" className="btn btn-ghost btn-sm">
                  <Icon name="sparkle" size={12} /> Ask assistant about this
                </button>
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
}

type TrendingProps = {
  setPage: (page: PageId) => void;
  setFilterCategory: (value: CategoryFilter) => void;
};

export function Trending({ setPage, setFilterCategory }: TrendingProps) {
  const [refreshing, setRefreshing] = useState(false);
  const refresh = () => {
    setRefreshing(true);
    setTimeout(() => setRefreshing(false), 800);
  };

  return (
    <div className="content">
      <PageHeader
        title="Trending Today"
        desc="Discover products that are seasonally popular right now based on historical rental demand."
        actions={
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={refresh}
            disabled={refreshing}
          >
            <span
              style={{ display: "inline-flex" }}
              className={refreshing ? "spin" : ""}
            >
              <Icon name="refresh" size={13} />
            </span>
            {refreshing ? "Refreshing…" : "Refresh"}
          </button>
        }
      />

      <div
        className="card"
        style={{
          background:
            "linear-gradient(135deg, var(--accent-tint), var(--surface) 60%)",
          marginBottom: 20,
          padding: 28,
          position: "relative",
          overflow: "hidden",
        }}
      >
        <Badge variant="accent">Updated 2 min ago</Badge>
        <h2
          style={{
            fontSize: 22,
            fontWeight: 600,
            letterSpacing: "-0.025em",
            margin: "12px 0 6px",
          }}
        >
          What should you rent right now?
        </h2>
        <div
          style={{
            color: "var(--text-2)",
            fontSize: 13.5,
            maxWidth: 540,
            marginBottom: 14,
          }}
        >
          RentPi highlights products that people often rent around this time
          of year — based on patterns across{" "}
          <span className="mono">10.2M</span> rental records.
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <span
            className="mono"
            style={{ fontSize: 11, color: "var(--text-3)" }}
          >
            📍 Dhaka · Today, May 1
          </span>
        </div>
      </div>

      <h2 className="section-title">Top picks for today</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
          gap: 12,
          marginBottom: 28,
        }}
      >
        {refreshing
          ? Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="card" style={{ padding: 0 }}>
                <div
                  className="skel"
                  style={{
                    aspectRatio: "4/3",
                    borderRadius: "14px 14px 0 0",
                  }}
                />
                <div style={{ padding: 14 }}>
                  <div
                    className="skel"
                    style={{ height: 14, width: "70%", marginBottom: 8 }}
                  />
                  <div
                    className="skel"
                    style={{ height: 11, width: "40%" }}
                  />
                </div>
              </div>
            ))
          : TRENDING.map((t, i) => (
              <div key={t.id} className="product-card">
                <Placeholder
                  category={t.category}
                  label={`#${i + 1} trending`}
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
                    <Badge variant="default">{t.category}</Badge>
                    <Badge variant="accent">Score {t.score}</Badge>
                  </div>
                  <div className="product-title">{t.name}</div>
                  <div style={{ fontSize: 12, color: "var(--text-3)" }}>
                    {t.note}
                  </div>
                  <div className="product-meta">
                    <div
                      style={{
                        display: "flex",
                        gap: 3,
                        alignItems: "flex-end",
                        height: 22,
                      }}
                    >
                      {[3, 5, 4, 7, 6, 9, 8].map((v, k) => (
                        <div
                          key={k}
                          style={{
                            width: 4,
                            height: `${(v / 9) * 100}%`,
                            background: "var(--accent)",
                            borderRadius: 1,
                            opacity: 0.4 + (k / 7) * 0.6,
                          }}
                        />
                      ))}
                    </div>
                    <button
                      type="button"
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        setFilterCategory(t.category);
                        setPage("products");
                      }}
                    >
                      Browse {t.category}
                    </button>
                  </div>
                </div>
              </div>
            ))}
      </div>

      <div className="card" style={{ background: "var(--surface-2)" }}>
        <div
          style={{
            display: "flex",
            gap: 14,
            alignItems: "flex-start",
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 8,
              background: "var(--surface)",
              border: "1px solid var(--border)",
              display: "grid",
              placeItems: "center",
              flexShrink: 0,
            }}
          >
            <Icon name="info" />
          </div>
          <div>
            <h3
              style={{
                fontSize: 13,
                fontWeight: 600,
                margin: "0 0 4px",
              }}
            >
              How recommendations work
            </h3>
            <div
              style={{
                fontSize: 12.5,
                color: "var(--text-2)",
                lineHeight: 1.55,
                maxWidth: 600,
              }}
            >
              RentPi looks at seasonal rental patterns across the past 24
              months and highlights products with strong demand around
              today&apos;s date. Scores compare each item to its own
              baseline — so you see what&apos;s hot right now, not just
              what&apos;s always popular.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
