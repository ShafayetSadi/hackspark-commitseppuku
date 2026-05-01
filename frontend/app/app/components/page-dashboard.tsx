"use client";

import type { PageId } from "../data";

import { Badge, Icon, type IconName, PageHeader, Stat } from "./primitives";

type DashboardProps = {
  setPage: (page: PageId) => void;
};

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

const RECENT_ACTIVITY = [
  {
    t: "Inquiry on Premium Camera Kit",
    m: "Asked about 3-day weekend availability",
    time: "14m",
  },
  {
    t: "Saved: Outdoor Camping Tent",
    m: "Added to your watchlist",
    time: "2h",
  },
  {
    t: "Discount tier updated",
    m: "Security score 82 → 85, now Elite Trust",
    time: "Yesterday",
  },
  {
    t: "Trending refresh",
    m: "New seasonal recommendations available",
    time: "Yesterday",
  },
];

export function Dashboard({ setPage }: DashboardProps) {
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
            Welcome back, Ayesha
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
        <Stat label="Products" value="487,201" meta="↑ 2.4% this week" />
        <Stat label="Categories" value="30" meta="across 9 verticals" />
        <Stat label="Rental records" value="10.2M" meta="last 24 months" />
        <Stat label="Assistant" value="Online" meta="avg. 1.2s response" />
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

      <div
        style={{
          marginTop: 36,
          display: "grid",
          gridTemplateColumns: "2fr 1fr",
          gap: 12,
        }}
      >
        <div className="card">
          <h2 className="section-title">Recent activity</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
            {RECENT_ACTIVITY.map((row, i) => (
              <div
                key={row.t}
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "11px 0",
                  borderTop: i === 0 ? "none" : "1px solid var(--border)",
                }}
              >
                <div>
                  <div style={{ fontSize: 13, fontWeight: 500 }}>{row.t}</div>
                  <div style={{ fontSize: 12, color: "var(--text-3)" }}>
                    {row.m}
                  </div>
                </div>
                <div
                  className="mono"
                  style={{ fontSize: 11, color: "var(--text-3)" }}
                >
                  {row.time}
                </div>
              </div>
            ))}
          </div>
        </div>
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

export function Profile() {
  const score = 85;
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
              AR
            </div>
            <div>
              <div style={{ fontSize: 16, fontWeight: 600 }}>
                Ayesha Rahman
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-3)" }}>
                ayesha@rentpi.app
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
              #R-49281
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
                Total rentals
              </div>
              47
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

const SURGE_HIGH = new Set([3, 8, 14, 15, 16, 22, 23, 24, 29]);
const SURGE_MED = new Set([5, 11, 12, 17, 25]);

const CATEGORY_DEMAND = [
  { cat: "Electronics", count: 4821, trend: [3, 5, 4, 7, 6, 8, 9] },
  { cat: "Outdoor", count: 3902, trend: [4, 6, 5, 7, 8, 9, 11] },
  { cat: "Tools", count: 2104, trend: [5, 4, 6, 5, 5, 6, 5] },
  { cat: "Vehicles", count: 1788, trend: [3, 3, 4, 5, 4, 5, 6] },
  { cat: "Cameras", count: 2553, trend: [2, 4, 5, 6, 7, 7, 8] },
];

export function Analytics() {
  return (
    <div className="content">
      <PageHeader
        title="Rental Analytics"
        desc="Explore demand patterns, peak rental windows, and surge days across RentPi."
      />
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
        <div className="card">
          <h2 className="section-title">Peak window</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr auto",
              gap: 8,
              marginBottom: 14,
            }}
          >
            <div className="field">
              <label className="field-label">From</label>
              <select className="select" defaultValue="Jan 2026">
                <option>Jan 2026</option>
                <option>Feb 2026</option>
                <option>Mar 2026</option>
              </select>
            </div>
            <div className="field">
              <label className="field-label">To</label>
              <select className="select" defaultValue="Apr 2026">
                <option>Apr 2026</option>
                <option>May 2026</option>
                <option>Jun 2026</option>
              </select>
            </div>
            <div className="field">
              <label className="field-label">&nbsp;</label>
              <button type="button" className="btn btn-primary">
                Analyze
              </button>
            </div>
          </div>
          <div className="result-success">
            <div
              className="mono"
              style={{
                fontSize: 10.5,
                color: "var(--accent-deep)",
                textTransform: "uppercase",
                letterSpacing: "0.06em",
                marginBottom: 6,
              }}
            >
              Strongest 7-day window
            </div>
            <div
              style={{
                fontSize: 22,
                fontWeight: 600,
                letterSpacing: "-0.02em",
              }}
            >
              Mar 10 — Mar 16
            </div>
            <div
              style={{ fontSize: 12.5, color: "var(--text-2)", marginTop: 4 }}
            >
              2,847 rentals · 41% above weekly average
            </div>
          </div>
        </div>

        <div className="card">
          <h2 className="section-title">Surge days — March</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(7, 1fr)",
              gap: 4,
            }}
          >
            {Array.from({ length: 31 }, (_, i) => {
              const intensity = SURGE_HIGH.has(i)
                ? "high"
                : SURGE_MED.has(i)
                  ? "med"
                  : "low";
              const c =
                intensity === "high"
                  ? "var(--accent)"
                  : intensity === "med"
                    ? "var(--accent-soft)"
                    : "var(--surface-2)";
              const txt = intensity === "high" ? "white" : "var(--text-3)";
              return (
                <div
                  key={i}
                  style={{
                    aspectRatio: "1",
                    background: c,
                    color: txt,
                    borderRadius: 4,
                    display: "grid",
                    placeItems: "center",
                    fontSize: 10.5,
                    fontFamily: "var(--font-mono)",
                  }}
                >
                  {i + 1}
                </div>
              );
            })}
          </div>
          <div
            style={{
              display: "flex",
              gap: 12,
              marginTop: 12,
              fontSize: 11,
              color: "var(--text-3)",
              fontFamily: "var(--font-mono)",
            }}
          >
            <span>
              <span
                style={{
                  display: "inline-block",
                  width: 10,
                  height: 10,
                  background: "var(--surface-2)",
                  borderRadius: 2,
                  verticalAlign: "middle",
                  marginRight: 4,
                }}
              />
              low
            </span>
            <span>
              <span
                style={{
                  display: "inline-block",
                  width: 10,
                  height: 10,
                  background: "var(--accent-soft)",
                  borderRadius: 2,
                  verticalAlign: "middle",
                  marginRight: 4,
                }}
              />
              medium
            </span>
            <span>
              <span
                style={{
                  display: "inline-block",
                  width: 10,
                  height: 10,
                  background: "var(--accent)",
                  borderRadius: 2,
                  verticalAlign: "middle",
                  marginRight: 4,
                }}
              />
              surge
            </span>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h2 className="section-title">Category demand</h2>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(5, 1fr)",
            gap: 12,
          }}
        >
          {CATEGORY_DEMAND.map((c) => {
            const max = Math.max(...c.trend);
            return (
              <div
                key={c.cat}
                style={{
                  padding: 14,
                  border: "1px solid var(--border)",
                  borderRadius: 10,
                }}
              >
                <div
                  style={{ fontSize: 12.5, fontWeight: 500, marginBottom: 4 }}
                >
                  {c.cat}
                </div>
                <div
                  style={{
                    fontSize: 18,
                    fontWeight: 600,
                    letterSpacing: "-0.02em",
                    marginBottom: 10,
                  }}
                >
                  {c.count.toLocaleString()}
                </div>
                <div
                  style={{
                    display: "flex",
                    gap: 3,
                    alignItems: "flex-end",
                    height: 30,
                  }}
                >
                  {c.trend.map((v, i) => (
                    <div
                      key={i}
                      style={{
                        flex: 1,
                        height: `${(v / max) * 100}%`,
                        background: "var(--accent)",
                        borderRadius: 2,
                        opacity: 0.4 + (i / c.trend.length) * 0.6,
                      }}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
