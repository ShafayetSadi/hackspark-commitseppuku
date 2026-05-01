"use client";

import { useEffect, useState } from "react";

import type { PageId } from "../data";

import { Badge, Icon, type IconName, PageHeader, Stat } from "./primitives";

type DashboardProps = {
  setPage: (page: PageId) => void;
  userName: string;
};

type ProfileUser = {
  id: number;
  email: string;
  full_name: string;
};

function initialsFor(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "U";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

type FeatureCard = {
  id: PageId;
  icon: IconName;
  title: string;
  desc: string;
};

const FEATURE_CARDS: FeatureCard[] = [
  {
    id: "products",
    icon: "box",
    title: "Product Marketplace",
    desc: "Browse rentable products across categories with clean filters and product details.",
  },
  {
    id: "availability",
    icon: "calendar",
    title: "Availability Checker",
    desc: "Find out whether a product is free for your selected dates.",
  },
  {
    id: "trending",
    icon: "trending",
    title: "Trending Today",
    desc: "See seasonal products that people are renting around this time.",
  },
  {
    id: "chat",
    icon: "sparkle",
    title: "RentPi Assistant",
    desc: "Ask rental-related questions and get helpful, data-focused answers.",
  },
];

export function Dashboard({ setPage, userName }: DashboardProps) {
  return (
    <div className="content">
      <div style={{ marginBottom: 32 }}>
        <div
          style={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius-lg)",
            padding: "36px 36px 32px",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: -100,
              right: -100,
              width: 320,
              height: 320,
              background:
                "radial-gradient(circle, var(--accent-tint), transparent 70%)",
              pointerEvents: "none",
            }}
          />
          <div
            className="mono"
            style={{
              fontSize: 11,
              color: "var(--text-3)",
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              marginBottom: 12,
            }}
          >
            Welcome back, {userName}
          </div>
          <h1
            style={{
              fontSize: 32,
              fontWeight: 600,
              letterSpacing: "-0.03em",
              margin: "0 0 8px",
              maxWidth: 640,
            }}
          >
            Rent smarter with real-time availability and seasonal trends.
          </h1>
          <div
            style={{
              color: "var(--text-3)",
              fontSize: 14,
              maxWidth: 580,
              marginBottom: 22,
            }}
          >
            Browse rental products, check availability, discover what&apos;s
            trending around you, and get AI-powered rental support — all from
            one place.
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              type="button"
              className="btn btn-accent btn-lg"
              onClick={() => setPage("products")}
            >
              Explore Products <Icon name="arrow" size={14} />
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-lg"
              onClick={() => setPage("availability")}
            >
              Check Availability
            </button>
          </div>
        </div>
      </div>

      <div className="stat-grid" style={{ marginBottom: 28 }}>
        <Stat label="Products API" value="Connected" meta="Live listing + detail + availability" />
        <Stat label="Analytics API" value="Connected" meta="Trends, surge, recommendations, peak window" />
        <Stat label="Chat API" value="Connected" meta="Sessions, history, and delete wired" />
        <Stat label="Auth" value="Protected" meta="JWT session required for /app routes" />
      </div>

      <h2 className="section-title">What you can do</h2>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          gap: 12,
        }}
      >
        {FEATURE_CARDS.map((card) => (
          <button
            key={card.id}
            type="button"
            className="card card-hover"
            style={{ textAlign: "left", cursor: "pointer" }}
            onClick={() => setPage(card.id)}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 8,
                background: "var(--accent-tint)",
                color: "var(--accent-deep)",
                display: "grid",
                placeItems: "center",
                marginBottom: 14,
              }}
            >
              <Icon name={card.icon} size={16} />
            </div>
            <div style={{ fontSize: 14, fontWeight: 500, marginBottom: 4 }}>
              {card.title}
            </div>
            <div
              style={{
                color: "var(--text-3)",
                fontSize: 12.5,
                lineHeight: 1.5,
              }}
            >
              {card.desc}
            </div>
            <div
              style={{
                marginTop: 16,
                color: "var(--accent-deep)",
                fontSize: 12,
                fontWeight: 500,
                display: "inline-flex",
                alignItems: "center",
                gap: 4,
              }}
            >
              Open <Icon name="arrow" size={12} />
            </div>
          </button>
        ))}
      </div>

      <div style={{ marginTop: 36 }}>
        <div
          className="card"
          style={{
            background: "var(--surface-2)",
            border: "1px solid var(--border)",
          }}
        >
          <h2 className="section-title">
            <Icon name="sparkle" size={14} /> Tip of the day
          </h2>
          <div
            style={{
              fontSize: 13,
              color: "var(--text-2)",
              lineHeight: 1.55,
              marginBottom: 14,
            }}
          >
            Camping gear demand peaks Friday–Sunday. Booking on a Wednesday
            gives you the best chance of locking in popular tents and bikes.
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setPage("trending")}
          >
            See trending now <Icon name="arrow" size={12} />
          </button>
        </div>
      </div>
    </div>
  );
}

const DISCOUNT_TIERS = [
  { range: "0–19", d: "No discount", active: false },
  { range: "20–39", d: "5% off", active: false },
  { range: "40–59", d: "10% off", active: false },
  { range: "60–79", d: "15% off", active: false },
  { range: "80–100", d: "20% off", active: true },
];

export function Profile({ user }: { user: ProfileUser }) {
  const score = 85;
  const displayName = user.full_name || user.email;
  const avatarInitials = initialsFor(displayName);
  const [topCategories, setTopCategories] = useState<
    Array<{ category: string; rentalCount: number }>
  >([]);
  const [topCategoriesError, setTopCategoriesError] = useState<string | null>(null);

  useEffect(() => {
    const loadTopCategories = async () => {
      try {
        setTopCategoriesError(null);
        const response = await fetch(
          `/api/rentals/users/${user.id}/top-categories?k=5`,
          { cache: "no-store" },
        );
        if (!response.ok) {
          setTopCategoriesError("Top categories are unavailable right now.");
          return;
        }
        const payload = (await response.json()) as {
          topCategories?: Array<{ category?: string; rentalCount?: number }>;
        };
        setTopCategories(
          (payload.topCategories ?? []).map((item) => ({
            category: String(item.category ?? "UNKNOWN"),
            rentalCount: Number(item.rentalCount ?? 0),
          })),
        );
      } catch {
        setTopCategoriesError("Top categories are unavailable right now.");
      }
    };
    void loadTopCategories();
  }, [user.id]);
  return (
    <div className="content">
      <PageHeader
        title="My Rental Profile"
        desc="View your account details, trust score, and rental discount eligibility."
      />
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1.4fr",
          gap: 16,
        }}
      >
        <div className="card">
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              marginBottom: 18,
            }}
          >
            <div
              className="avatar"
              style={{ width: 56, height: 56, fontSize: 18 }}
            >
              {avatarInitials}
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600 }}>
                {displayName}
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-3)" }}>
                {user.email}
              </div>
            </div>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: 10,
              fontSize: 12.5,
            }}
          >
            <div>
              <div
                className="muted mono"
                style={{
                  fontSize: 10.5,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  marginBottom: 4,
                }}
              >
                User ID
              </div>
              {user.id}
            </div>
            <div>
              <div
                className="muted mono"
                style={{
                  fontSize: 10.5,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  marginBottom: 4,
                }}
              >
                Status
              </div>
              <Badge variant="accent">Active</Badge>
            </div>
            <div>
              <div
                className="muted mono"
                style={{
                  fontSize: 10.5,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  marginBottom: 4,
                }}
              >
                Member since
              </div>
              Mar 2024
            </div>
            <div>
              <div
                className="muted mono"
                style={{
                  fontSize: 10.5,
                  textTransform: "uppercase",
                  letterSpacing: "0.06em",
                  marginBottom: 4,
                }}
              >
                Top category
              </div>
              {topCategories[0]?.category ?? "-"}
            </div>
          </div>
        </div>

        <div className="card">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-start",
              marginBottom: 14,
            }}
          >
            <div>
              <div
                style={{
                  fontSize: 12,
                  color: "var(--text-3)",
                  marginBottom: 4,
                }}
              >
                Security score
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  letterSpacing: "-0.025em",
                }}
              >
                {score}
                <span
                  style={{
                    fontSize: 14,
                    color: "var(--text-3)",
                    fontWeight: 400,
                  }}
                >
                  /100
                </span>
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div
                style={{
                  fontSize: 12,
                  color: "var(--text-3)",
                  marginBottom: 4,
                }}
              >
                Discount
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  color: "var(--accent-deep)",
                  letterSpacing: "-0.025em",
                }}
              >
                20%
              </div>
            </div>
          </div>
          <div className="progress" style={{ marginBottom: 8 }}>
            <div
              className="progress-fill"
              style={{ width: `${score}%` }}
            />
          </div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 11,
              color: "var(--text-3)",
              fontFamily: "var(--font-mono)",
              marginBottom: 18,
            }}
          >
            <span>0</span>
            <span>20</span>
            <span>40</span>
            <span>60</span>
            <span>80</span>
            <span>100</span>
          </div>
          <Badge variant="accent">
            <Icon name="shield" size={11} /> Elite Trust Tier
          </Badge>
        </div>
      </div>

      <div style={{ marginTop: 16 }} className="card">
        <h2 className="section-title">Top rental categories</h2>
        {topCategoriesError ? (
          <div className="result-warn" style={{ marginBottom: 12 }}>
            {topCategoriesError}
          </div>
        ) : null}
        {topCategories.length === 0 && !topCategoriesError ? (
          <div style={{ fontSize: 12.5, color: "var(--text-3)", marginBottom: 12 }}>
            No category history yet.
          </div>
        ) : null}
        {topCategories.length > 0 ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(5, 1fr)",
              gap: 8,
              marginBottom: 14,
            }}
          >
            {topCategories.map((item) => (
              <div
                key={item.category}
                style={{
                  padding: 12,
                  border: "1px solid var(--border)",
                  borderRadius: 10,
                  background: "var(--surface)",
                }}
              >
                <div className="mono" style={{ fontSize: 10.5, color: "var(--text-3)" }}>
                  {item.category}
                </div>
                <div style={{ fontSize: 14, fontWeight: 600, marginTop: 4 }}>
                  {item.rentalCount}
                </div>
              </div>
            ))}
          </div>
        ) : null}

        <h2 className="section-title">Discount tiers</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: 8,
          }}
        >
          {DISCOUNT_TIERS.map((tier) => (
            <div
              key={tier.range}
              style={{
                padding: 14,
                border: tier.active
                  ? "1px solid var(--accent)"
                  : "1px solid var(--border)",
                borderRadius: 10,
                background: tier.active
                  ? "var(--accent-tint)"
                  : "var(--surface)",
              }}
            >
              <div
                className="mono"
                style={{
                  fontSize: 11,
                  color: tier.active
                    ? "var(--accent-deep)"
                    : "var(--text-3)",
                  marginBottom: 4,
                }}
              >
                {tier.range}
              </div>
              <div style={{ fontSize: 13, fontWeight: 500 }}>{tier.d}</div>
              {tier.active ? (
                <div
                  style={{
                    fontSize: 10.5,
                    color: "var(--accent-deep)",
                    marginTop: 6,
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  YOUR TIER
                </div>
              ) : null}
            </div>
          ))}
        </div>
        <div
          style={{
            marginTop: 14,
            padding: 12,
            background: "var(--surface-2)",
            borderRadius: 8,
            fontSize: 12.5,
            color: "var(--text-2)",
            display: "flex",
            gap: 8,
            alignItems: "flex-start",
          }}
        >
          <Icon name="info" size={14} />
          <span>
            Your security score reflects rental trust based on completed
            rentals, on-time returns, and verification status. Higher scores
            unlock better discounts.
          </span>
        </div>
      </div>
    </div>
  );
}

export function Analytics() {
  const [fromMonth, setFromMonth] = useState("2024-01");
  const [toMonth, setToMonth] = useState("2024-06");
  const [rank, setRank] = useState("3");
  const [isLoadingKth, setIsLoadingKth] = useState(false);
  const [kthError, setKthError] = useState<string | null>(null);
  const [kthResult, setKthResult] = useState<{
    from: string;
    to: string;
    k: number;
    date: string;
    rentalCount: number;
  } | null>(null);
  const [mergedIds, setMergedIds] = useState("12,47,88");
  const [mergedLimit, setMergedLimit] = useState("30");
  const [mergedError, setMergedError] = useState<string | null>(null);
  const [isLoadingMerged, setIsLoadingMerged] = useState(false);
  const [mergedFeed, setMergedFeed] = useState<
    Array<{ rentalId: number; productId: number; rentalStart: string; rentalEnd: string }>
  >([]);
  const [analyticsFrom, setAnalyticsFrom] = useState("2024-01");
  const [analyticsTo, setAnalyticsTo] = useState("2024-06");
  const [analyticsCategory, setAnalyticsCategory] = useState("");
  const [trendsData, setTrendsData] = useState<Array<{ month: string; rentalCount: number }>>([]);
  const [surgeData, setSurgeData] = useState<
    Array<{
      period: string;
      surgeMultiplier: number;
      baselineRentals: number;
      actualRentals: number;
    }>
  >([]);
  const [recommendationLimit, setRecommendationLimit] = useState("5");
  const [recommendationsData, setRecommendationsData] = useState<
    Array<{ productId: number; name: string; score: number }>
  >([]);
  const [peakWindow, setPeakWindow] = useState<{
    from: string;
    to: string;
    peakWindow: { start: string; end: string; totalRentals: number };
  } | null>(null);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);
  const [isLoadingAnalytics, setIsLoadingAnalytics] = useState(false);

  const runKthBusiest = async () => {
    setIsLoadingKth(true);
    setKthError(null);
    setKthResult(null);
    try {
      const response = await fetch(
        `/api/rentals/kth-busiest-date?from=${encodeURIComponent(fromMonth)}&to=${encodeURIComponent(
          toMonth,
        )}&k=${encodeURIComponent(rank)}`,
        { cache: "no-store" },
      );
      if (!response.ok) {
        if (response.status === 400) {
          setKthError("Please choose a valid month range and rank.");
          return;
        }
        if (response.status === 404) {
          setKthError("Not enough rental dates found for this rank.");
          return;
        }
        setKthError("Could not load Kth busiest date right now.");
        return;
      }
      const payload = (await response.json()) as {
        from: string;
        to: string;
        k: number;
        date: string;
        rentalCount: number;
      };
      setKthResult(payload);
    } catch {
      setKthError("Could not load Kth busiest date right now.");
    } finally {
      setIsLoadingKth(false);
    }
  };

  const loadMergedFeed = async () => {
    setIsLoadingMerged(true);
    setMergedError(null);
    setMergedFeed([]);
    try {
      const response = await fetch(
        `/api/rentals/merged-feed?productIds=${encodeURIComponent(mergedIds)}&limit=${encodeURIComponent(
          mergedLimit,
        )}`,
        { cache: "no-store" },
      );
      if (!response.ok) {
        if (response.status === 404) {
          setMergedError("Merged feed API is not available on the backend yet.");
          return;
        }
        setMergedError("Could not load merged feed right now.");
        return;
      }
      const payload = (await response.json()) as {
        feed?: Array<{
          rentalId?: number;
          productId?: number;
          rentalStart?: string;
          rentalEnd?: string;
        }>;
      };
      setMergedFeed(
        (payload.feed ?? []).map((item) => ({
          rentalId: Number(item.rentalId ?? 0),
          productId: Number(item.productId ?? 0),
          rentalStart: String(item.rentalStart ?? ""),
          rentalEnd: String(item.rentalEnd ?? ""),
        })),
      );
    } catch {
      setMergedError("Could not load merged feed right now.");
    } finally {
      setIsLoadingMerged(false);
    }
  };

  const loadAnalyticsEndpoints = async () => {
    setIsLoadingAnalytics(true);
    setAnalyticsError(null);
    setTrendsData([]);
    setSurgeData([]);
    setRecommendationsData([]);
    setPeakWindow(null);
    try {
      const categoryParam = analyticsCategory.trim();
      const trendsQuery = categoryParam
        ? `?category=${encodeURIComponent(categoryParam)}`
        : "";
      const surgeQuery = categoryParam
        ? `?category=${encodeURIComponent(categoryParam)}`
        : "";
      const recommendationQuery = new URLSearchParams({
        limit: recommendationLimit || "5",
      });
      if (categoryParam) recommendationQuery.set("category", categoryParam);

      const [trendsResp, surgeResp, recommendationsResp, peakWindowResp] =
        await Promise.all([
          fetch(`/api/analytics/trends${trendsQuery}`, { cache: "no-store" }),
          fetch(`/api/analytics/surge${surgeQuery}`, { cache: "no-store" }),
          fetch(`/api/analytics/recommendations?${recommendationQuery.toString()}`, {
            cache: "no-store",
          }),
          fetch(
            `/api/analytics/peak-window?from=${encodeURIComponent(analyticsFrom)}&to=${encodeURIComponent(analyticsTo)}`,
            { cache: "no-store" },
          ),
        ]);

      if (!trendsResp.ok || !surgeResp.ok || !recommendationsResp.ok || !peakWindowResp.ok) {
        setAnalyticsError("Could not load analytics endpoints right now.");
        return;
      }

      const trendsPayload = (await trendsResp.json()) as {
        trends?: Array<{ month?: string; rentalCount?: number }>;
      };
      const surgePayload = (await surgeResp.json()) as {
        surges?: Array<{
          period?: string;
          surgeMultiplier?: number;
          baselineRentals?: number;
          actualRentals?: number;
        }>;
      };
      const recommendationsPayload = (await recommendationsResp.json()) as {
        recommendations?: Array<{ productId?: number; name?: string; score?: number }>;
      };
      const peakWindowPayload = (await peakWindowResp.json()) as {
        from?: string;
        to?: string;
        peakWindow?: { start?: string; end?: string; totalRentals?: number };
      };

      setTrendsData(
        (trendsPayload.trends ?? []).map((item) => ({
          month: String(item.month ?? ""),
          rentalCount: Number(item.rentalCount ?? 0),
        })),
      );
      setSurgeData(
        (surgePayload.surges ?? []).map((item) => ({
          period: String(item.period ?? ""),
          surgeMultiplier: Number(item.surgeMultiplier ?? 0),
          baselineRentals: Number(item.baselineRentals ?? 0),
          actualRentals: Number(item.actualRentals ?? 0),
        })),
      );
      setRecommendationsData(
        (recommendationsPayload.recommendations ?? []).map((item) => ({
          productId: Number(item.productId ?? 0),
          name: String(item.name ?? "Recommended product"),
          score: Number(item.score ?? 0),
        })),
      );
      if (peakWindowPayload.peakWindow) {
        setPeakWindow({
          from: String(peakWindowPayload.from ?? analyticsFrom),
          to: String(peakWindowPayload.to ?? analyticsTo),
          peakWindow: {
            start: String(peakWindowPayload.peakWindow.start ?? ""),
            end: String(peakWindowPayload.peakWindow.end ?? ""),
            totalRentals: Number(peakWindowPayload.peakWindow.totalRentals ?? 0),
          },
        });
      }
    } catch {
      setAnalyticsError("Could not load analytics endpoints right now.");
    } finally {
      setIsLoadingAnalytics(false);
    }
  };

  const hasAnalyticsData =
    peakWindow !== null ||
    trendsData.length > 0 ||
    surgeData.length > 0 ||
    recommendationsData.length > 0;

  const trendMax = trendsData.length > 0 ? Math.max(...trendsData.map((d) => d.rentalCount)) : 1;

  return (
    <div className="content">
      <PageHeader
        title="Rental Analytics"
        desc="Explore rentals and analytics service endpoints from one workspace."
      />

      {/* ── Analytics service endpoints ─────────────────────────────── */}
      <div className="card" style={{ marginBottom: 14 }}>
        <h2 className="section-title">
          <Icon name="chart" size={14} /> Analytics service endpoints
        </h2>

        {/* Controls */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr 100px auto",
            gap: 8,
            marginBottom: 16,
          }}
        >
          <div className="field">
            <label className="field-label">From (YYYY-MM)</label>
            <input
              className="input"
              value={analyticsFrom}
              onChange={(e) => setAnalyticsFrom(e.target.value)}
              placeholder="2024-01"
            />
          </div>
          <div className="field">
            <label className="field-label">To (YYYY-MM)</label>
            <input
              className="input"
              value={analyticsTo}
              onChange={(e) => setAnalyticsTo(e.target.value)}
              placeholder="2024-06"
            />
          </div>
          <div className="field">
            <label className="field-label">Category (optional)</label>
            <input
              className="input"
              value={analyticsCategory}
              onChange={(e) => setAnalyticsCategory(e.target.value)}
              placeholder="TOOLS"
            />
          </div>
          <div className="field">
            <label className="field-label">Rec. limit</label>
            <input
              className="input"
              value={recommendationLimit}
              onChange={(e) => setRecommendationLimit(e.target.value)}
              placeholder="5"
              inputMode="numeric"
            />
          </div>
          <div className="field">
            <label className="field-label">&nbsp;</label>
            <button
              type="button"
              className="btn btn-accent"
              onClick={() => void loadAnalyticsEndpoints()}
              disabled={isLoadingAnalytics}
            >
              {isLoadingAnalytics ? "Loading…" : "Load analytics"}
            </button>
          </div>
        </div>

        {analyticsError ? (
          <div className="result-warn">{analyticsError}</div>
        ) : null}

        {/* Empty state */}
        {!isLoadingAnalytics && !analyticsError && !hasAnalyticsData ? (
          <div
            style={{
              padding: "28px 0",
              textAlign: "center",
              color: "var(--text-3)",
              fontSize: 13,
            }}
          >
            Set filters above and click{" "}
            <strong style={{ color: "var(--text-2)" }}>Load analytics</strong> to see
            trends, surge periods, and recommendations.
          </div>
        ) : null}

        {/* Peak Window — full-width highlighted banner */}
        {peakWindow ? (
          <div
            className="result-success"
            style={{
              marginBottom: 14,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              gap: 16,
            }}
          >
            <div>
              <div
                className="mono"
                style={{
                  fontSize: 10.5,
                  color: "var(--accent-deep)",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  marginBottom: 6,
                }}
              >
                Peak rental window
              </div>
              <div
                style={{
                  fontSize: 20,
                  fontWeight: 600,
                  letterSpacing: "-0.02em",
                  color: "var(--text)",
                }}
              >
                {peakWindow.peakWindow.start} → {peakWindow.peakWindow.end}
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-2)", marginTop: 4 }}>
                Query range: {peakWindow.from} → {peakWindow.to}
              </div>
            </div>
            <div style={{ textAlign: "right", flexShrink: 0 }}>
              <div
                className="mono"
                style={{
                  fontSize: 10.5,
                  color: "var(--accent-deep)",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  marginBottom: 6,
                }}
              >
                Total rentals
              </div>
              <div
                style={{
                  fontSize: 32,
                  fontWeight: 600,
                  letterSpacing: "-0.03em",
                  color: "var(--accent-deep)",
                  lineHeight: 1,
                }}
              >
                {peakWindow.peakWindow.totalRentals.toLocaleString()}
              </div>
            </div>
          </div>
        ) : null}

        {/* 3-column results grid */}
        {hasAnalyticsData ? (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 12,
            }}
          >
            {/* Trends */}
            <div
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 10,
                padding: 14,
              }}
            >
              <div
                className="mono"
                style={{
                  fontSize: 10.5,
                  color: "var(--text-3)",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  marginBottom: 10,
                }}
              >
                Trends
              </div>
              {trendsData.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                  {trendsData.map((item) => (
                    <div key={item.month}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          fontSize: 12,
                          marginBottom: 3,
                        }}
                      >
                        <span>{item.month}</span>
                        <span className="mono" style={{ fontSize: 11, color: "var(--text-3)" }}>
                          {item.rentalCount.toLocaleString()}
                        </span>
                      </div>
                      <div
                        style={{
                          height: 4,
                          background: "var(--border)",
                          borderRadius: 2,
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            height: "100%",
                            width: `${(item.rentalCount / trendMax) * 100}%`,
                            background: "var(--accent)",
                            borderRadius: 2,
                            transition: "width 0.3s ease",
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "var(--text-3)" }}>No trend data</div>
              )}
            </div>

            {/* Surge */}
            <div
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 10,
                padding: 14,
              }}
            >
              <div
                className="mono"
                style={{
                  fontSize: 10.5,
                  color: "var(--text-3)",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  marginBottom: 10,
                }}
              >
                Surge periods
              </div>
              {surgeData.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                  {surgeData.map((item) => (
                    <div
                      key={`${item.period}-${item.actualRentals}`}
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "flex-start",
                        gap: 8,
                      }}
                    >
                      <div>
                        <div style={{ fontSize: 12, fontWeight: 500 }}>{item.period}</div>
                        <div
                          className="mono"
                          style={{ fontSize: 11, color: "var(--text-3)", marginTop: 1 }}
                        >
                          {item.actualRentals} / {item.baselineRentals} baseline
                        </div>
                      </div>
                      <span
                        className={`badge ${item.surgeMultiplier >= 2 ? "badge-warn" : "badge-accent"}`}
                        style={{ flexShrink: 0 }}
                      >
                        ×{item.surgeMultiplier}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "var(--text-3)" }}>No surge data</div>
              )}
            </div>

            {/* Recommendations */}
            <div
              style={{
                background: "var(--surface-2)",
                border: "1px solid var(--border)",
                borderRadius: 10,
                padding: 14,
              }}
            >
              <div
                className="mono"
                style={{
                  fontSize: 10.5,
                  color: "var(--text-3)",
                  textTransform: "uppercase",
                  letterSpacing: "0.07em",
                  marginBottom: 10,
                }}
              >
                Recommendations
              </div>
              {recommendationsData.length > 0 ? (
                <div style={{ display: "flex", flexDirection: "column", gap: 7 }}>
                  {recommendationsData.map((item, i) => (
                    <div
                      key={`${item.productId}-${item.name}`}
                      style={{ display: "flex", alignItems: "center", gap: 8 }}
                    >
                      <div
                        className="mono"
                        style={{
                          width: 20,
                          height: 20,
                          borderRadius: 4,
                          background: "var(--border)",
                          display: "grid",
                          placeItems: "center",
                          fontSize: 10,
                          color: "var(--text-3)",
                          flexShrink: 0,
                        }}
                      >
                        {i + 1}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div
                          style={{
                            fontSize: 12,
                            fontWeight: 500,
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                            whiteSpace: "nowrap",
                          }}
                        >
                          {item.name}
                        </div>
                        <div
                          className="mono"
                          style={{ fontSize: 11, color: "var(--text-3)", marginTop: 1 }}
                        >
                          #{item.productId}
                        </div>
                      </div>
                      <span className="badge" style={{ flexShrink: 0 }}>
                        {item.score.toFixed(2)}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12, color: "var(--text-3)" }}>No recommendations</div>
              )}
            </div>
          </div>
        ) : null}
      </div>

      {/* ── Kth busiest  +  Merged feed  ────────────────────────────── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>

        {/* Kth busiest date */}
        <div className="card">
          <h2 className="section-title">
            <Icon name="trending" size={14} /> Kth busiest date
          </h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 80px",
              gap: 8,
              marginBottom: 10,
            }}
          >
            <div className="field">
              <label className="field-label">From (YYYY-MM)</label>
              <input
                className="input"
                value={fromMonth}
                onChange={(e) => setFromMonth(e.target.value)}
                placeholder="2024-01"
              />
            </div>
            <div className="field">
              <label className="field-label">To (YYYY-MM)</label>
              <input
                className="input"
                value={toMonth}
                onChange={(e) => setToMonth(e.target.value)}
                placeholder="2024-06"
              />
            </div>
            <div className="field">
              <label className="field-label">K</label>
              <input
                className="input"
                value={rank}
                onChange={(e) => setRank(e.target.value)}
                placeholder="3"
                inputMode="numeric"
              />
            </div>
          </div>
          <button
            type="button"
            className="btn btn-accent"
            style={{ width: "100%" }}
            onClick={() => void runKthBusiest()}
            disabled={isLoadingKth}
          >
            {isLoadingKth ? "Checking…" : "Find kth busiest date"}
          </button>
          {kthError ? (
            <div className="result-warn" style={{ marginTop: 10 }}>
              {kthError}
            </div>
          ) : null}
          {kthResult ? (
            <div className="result-success" style={{ marginTop: 10 }}>
              <div style={{ fontSize: 14, fontWeight: 600 }}>
                #{kthResult.k} busiest date: {kthResult.date}
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-2)", marginTop: 4 }}>
                {kthResult.from} → {kthResult.to} · {kthResult.rentalCount} rentals
              </div>
            </div>
          ) : null}
        </div>

        {/* Merged product rental feed */}
        <div className="card">
          <h2 className="section-title">
            <Icon name="sort" size={14} /> Merged product rental feed
          </h2>
          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 80px", gap: 8, marginBottom: 10 }}
          >
            <div className="field">
              <label className="field-label">Product IDs (comma-separated)</label>
              <input
                className="input"
                value={mergedIds}
                onChange={(e) => setMergedIds(e.target.value)}
                placeholder="12,47,88"
              />
            </div>
            <div className="field">
              <label className="field-label">Limit</label>
              <input
                className="input"
                value={mergedLimit}
                onChange={(e) => setMergedLimit(e.target.value)}
                placeholder="30"
                inputMode="numeric"
              />
            </div>
          </div>
          <button
            type="button"
            className="btn btn-accent"
            style={{ width: "100%" }}
            onClick={() => void loadMergedFeed()}
            disabled={isLoadingMerged}
          >
            {isLoadingMerged ? "Loading…" : "Load feed"}
          </button>
          {mergedError ? (
            <div className="result-warn" style={{ marginTop: 10 }}>
              {mergedError}
            </div>
          ) : null}
          {mergedFeed.length > 0 ? (
            <div
              style={{
                marginTop: 10,
                display: "flex",
                flexDirection: "column",
                gap: 5,
                maxHeight: 280,
                overflowY: "auto",
              }}
            >
              {mergedFeed.map((item) => (
                <div
                  key={`${item.rentalId}-${item.productId}`}
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "8px 10px",
                    border: "1px solid var(--border)",
                    borderRadius: 7,
                  }}
                >
                  <div style={{ fontSize: 12.5 }}>
                    Rental #{item.rentalId} · Product #{item.productId}
                  </div>
                  <div className="mono" style={{ fontSize: 11, color: "var(--text-3)" }}>
                    {item.rentalStart} → {item.rentalEnd}
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>

      </div>
    </div>
  );
}
