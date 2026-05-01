"use client";

import { useEffect, useState } from "react";

import {
  CATEGORIES,
  type Category,
  type CategoryFilter,
  type PageId,
} from "../data";

import { Badge, Icon, PageHeader, Placeholder } from "./primitives";

type AvailabilityResult = {
  productId: number;
  from: string;
  to: string;
  available: boolean;
  busyPeriods: Array<{ start: string; end: string }>;
  freeWindows: Array<{ start: string; end: string }>;
  freeStreak: { from: string; to: string; days: number } | null;
};

function availabilityErrorMessage(status: number): string {
  if (status === 400) return "Please choose a valid date range.";
  if (status === 404) return "This product could not be found.";
  if (status === 503) return "Availability data is unavailable right now.";
  return "Could not check availability right now.";
}

function getYearFromDate(value: string): number {
  const parsed = Number(value.slice(0, 4));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : new Date().getFullYear();
}

function dateLabel(value: string): string {
  if (!value) return value;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function toTimelineValue(value: string): number {
  if (!value) return 0;
  const dayPart = value.split("-")[2];
  return Number(dayPart ?? 0);
}

function timelineWidth(from: string, to: string): string {
  const start = toTimelineValue(from);
  const end = toTimelineValue(to);
  if (start <= 0 || end <= 0 || end < start) return "0%";
  return `${((end - start + 1) / 31) * 100}%`;
}

function timelineLeft(from: string): string {
  const start = toTimelineValue(from);
  if (start <= 0) return "0%";
  return `${(start / 31) * 100}%`;
}

function normalizePeriods(
  periods: Array<{ start?: unknown; end?: unknown }> | undefined,
): Array<{ start: string; end: string }> {
  if (!Array.isArray(periods)) return [];
  return periods
    .map((p) => ({
      start: String(p.start ?? ""),
      end: String(p.end ?? ""),
    }))
    .filter((p) => p.start.length > 0 && p.end.length > 0);
}

type AvailabilityPayload = {
  productId?: number;
  from?: string;
  to?: string;
  available: boolean;
};

export function Availability() {
  const [productId, setProductId] = useState("1042");
  const [from, setFrom] = useState("2026-05-08");
  const [to, setTo] = useState("2026-05-15");
  const [result, setResult] = useState<AvailabilityResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const check = async () => {
    setLoading(true);
    setErrorMessage(null);
    setResult(null);
    try {
      const id = Number.parseInt(productId, 10);
      if (!Number.isFinite(id) || id <= 0) {
        setErrorMessage("Please enter a valid product ID.");
        return;
      }
      const response = await fetch(
        `/api/rentals/products/${id}/availability?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`,
        { cache: "no-store" },
      );
      if (!response.ok) {
        setErrorMessage(availabilityErrorMessage(response.status));
        return;
      }
      const payload = (await response.json()) as AvailabilityPayload & {
        busyPeriods?: Array<{ start?: unknown; end?: unknown }>;
        freeWindows?: Array<{ start?: unknown; end?: unknown }>;
      };

      let freeStreak: AvailabilityResult["freeStreak"] = null;
      const streakResp = await fetch(
        `/api/rentals/products/${id}/free-streak?year=${getYearFromDate(from)}`,
        { cache: "no-store" },
      );
      if (streakResp.ok) {
        const streakPayload = (await streakResp.json()) as {
          longestFreeStreak?: { from?: string; to?: string; days?: number };
        };
        if (streakPayload.longestFreeStreak) {
          freeStreak = {
            from: String(streakPayload.longestFreeStreak.from ?? ""),
            to: String(streakPayload.longestFreeStreak.to ?? ""),
            days: Number(streakPayload.longestFreeStreak.days ?? 0),
          };
        }
      }

      setResult({
        productId: Number(payload.productId ?? id),
        from: String(payload.from ?? from),
        to: String(payload.to ?? to),
        available: Boolean(payload.available),
        busyPeriods: normalizePeriods(payload.busyPeriods),
        freeWindows: normalizePeriods(payload.freeWindows),
        freeStreak,
      });
    } catch {
      setErrorMessage("Availability data is unavailable right now.");
    } finally {
      setLoading(false);
    }
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
              <div className="field-help">Enter the product ID you want to check.</div>
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
              onClick={() => void check()}
              disabled={loading}
            >
              {loading ? "Checking…" : "Check Availability"}
            </button>
          </div>
        </div>

        <div className="card" style={{ minHeight: 320 }}>
          {errorMessage ? (
            <div className="result-warn" style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 13 }}>{errorMessage}</div>
            </div>
          ) : null}
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
                    ? "This product is free for your selected dates."
                    : "This product has bookings during your selected dates."}
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
                      {dateLabel(result.from)} → {dateLabel(result.to)}
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
                      #{result.productId}
                    </div>
                  </div>
                </div>
              </div>

              <h3 className="section-title">Timeline</h3>
              <div style={{ position: "relative", marginBottom: 6 }}>
                <div className="timeline">
                  {result.busyPeriods.map((b, i) => (
                    <div
                      key={i}
                      className="timeline-segment timeline-busy"
                      style={{
                        left: timelineLeft(b.start),
                        width: timelineWidth(b.start, b.end),
                      }}
                      title={`${dateLabel(b.start)} → ${dateLabel(b.end)}`}
                    />
                  ))}
                  <div
                    className="timeline-requested"
                    style={{
                      left: timelineLeft(result.from),
                      width: timelineWidth(result.from, result.to),
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

              {result.busyPeriods.length > 0 ? (
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
                    {result.busyPeriods.map((b, i) => (
                      <div
                        key={i}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          padding: "10px 12px",
                          border: "1px solid var(--border)",
                          borderRadius: 8,
                          background: "var(--warn-soft)",
                        }}
                      >
                        <div style={{ fontSize: 12.5 }}>
                          {dateLabel(b.start)} → {dateLabel(b.end)}
                        </div>
                        <div className="mono" style={{ fontSize: 11, color: "var(--text-3)" }}>
                          Busy
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : null}

              {result.freeWindows.length > 0 ? (
                <>
                  <h3 className="section-title" style={{ marginTop: 16 }}>
                    Free windows
                  </h3>
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    {result.freeWindows.map((w, i) => (
                      <div
                        key={i}
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          padding: "10px 12px",
                          border: "1px solid var(--border)",
                          borderRadius: 8,
                          background: "var(--surface)",
                        }}
                      >
                        <div style={{ fontSize: 12.5 }}>
                          {dateLabel(w.start)} → {dateLabel(w.end)}
                        </div>
                        <div className="mono" style={{ fontSize: 11, color: "var(--text-3)" }}>
                          Free
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              ) : null}

              {result.freeStreak ? (
                <div className="card" style={{ marginTop: 16, padding: 12 }}>
                  <div className="mono" style={{ fontSize: 10.5, color: "var(--text-3)" }}>
                    LONGEST FREE STREAK (YEAR)
                  </div>
                  <div style={{ fontSize: 13, marginTop: 4 }}>
                    {dateLabel(result.freeStreak.from)} → {dateLabel(result.freeStreak.to)} (
                    {result.freeStreak.days} days)
                  </div>
                </div>
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
  const toKnownCategory = (value: string): Category => {
    const matched = CATEGORIES.find(
      (category) => category.toLowerCase() === value.toLowerCase(),
    );
    return matched ?? "Electronics";
  };

  const [recommendations, setRecommendations] = useState<
    Array<{ productId: number; name: string; score: number; category: string }>
  >([]);
  const [refreshing, setRefreshing] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const refresh = async () => {
    setRefreshing(true);
    setErrorMessage(null);
    try {
      const response = await fetch("/api/analytics/recommendations?limit=6", {
        cache: "no-store",
      });
      if (!response.ok) {
        setErrorMessage("Recommendations are unavailable right now.");
        return;
      }
      const payload = (await response.json()) as {
        category?: string;
        recommendations?: Array<{
          productId?: number;
          id?: number;
          name?: string;
          title?: string;
          score?: number;
          recommendationScore?: number;
          category?: string;
        }>;
      };
      const fallbackCategory = String(payload.category ?? "GENERAL");
      setRecommendations(
        (payload.recommendations ?? []).map((item) => ({
          productId: Number(item.productId ?? item.id ?? 0),
          name: String(item.name ?? item.title ?? "Recommended product"),
          score: Number(item.score ?? item.recommendationScore ?? 0),
          category: String(item.category ?? fallbackCategory),
        })),
      );
    } catch {
      setErrorMessage("Recommendations are unavailable right now.");
    } finally {
      setRefreshing(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <div className="content">
      <PageHeader
        title="Trending Today"
        desc="Discover products that are seasonally popular right now based on historical rental demand."
        actions={
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => void refresh()}
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
      {errorMessage ? <div className="result-warn" style={{ marginBottom: 12 }}>{errorMessage}</div> : null}
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
          : recommendations.map((t, i) => (
              <div key={`${t.productId}-${i}`} className="product-card">
                <Placeholder
                  category={toKnownCategory(t.category)}
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
                    <Badge variant="accent">Score {t.score.toFixed(2)}</Badge>
                  </div>
                  <div className="product-title">{t.name}</div>
                  <div style={{ fontSize: 12, color: "var(--text-3)" }}>
                    Product #{t.productId} recommended from analytics.
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
                        setFilterCategory(toKnownCategory(t.category));
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
