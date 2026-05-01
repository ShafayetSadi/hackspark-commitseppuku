import Link from "next/link";

import { CompanyLogoLockup } from "./components/company-logo";
import "./landing.css";

// Landing page implementation of the RentPi design (Landing.html).
// Pure server component — no client-side interactivity needed for this view.

const APP_HREF = "/app";
const SIGN_IN_HREF = "/login";

function ArrowRightIcon({ size = 13 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M5 12h14M13 6l6 6-6 6" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      width={16}
      height={16}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d="M5 12l5 5L20 7" />
    </svg>
  );
}

function NavBar() {
  return (
    <nav className="lp-nav">
      <div className="lp-nav-inner">
        <CompanyLogoLockup className="lp-logo" markClassName="logo-mark" />
        <div className="lp-nav-links">
          <a href="#features">Features</a>
          <a href="#categories">Categories</a>
          <a href="#how">How it works</a>
          <a href="#ai">Assistant</a>
        </div>
        <div className="lp-nav-cta">
          <Link href={SIGN_IN_HREF} className="btn btn-ghost btn-sm">
            Sign in
          </Link>
          <Link href={APP_HREF} className="btn btn-primary btn-sm">
            Open app <ArrowRightIcon size={12} />
          </Link>
        </div>
      </div>
    </nav>
  );
}

function PreviewSidebarItem({
  active = false,
  icon,
  label,
}: {
  active?: boolean;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <div className={`lp-preview-nav${active ? " active" : ""}`}>
      {icon}
      {label}
    </div>
  );
}

function HeroSection() {
  return (
    <section className="lp-hero">
      <div className="lp-eyebrow">
        <span className="dot"></span>
        Now live in Dhaka — 487K+ products
      </div>
      <h1 className="lp-h1">
        Rent anything. <em>Anytime.</em>
        <br />
        Without the guesswork.
      </h1>
      <p className="lp-sub">
        RentPi is a real-time rental marketplace with availability you can trust,
        seasonal trend data, and an AI assistant that actually knows the catalog.
        From cameras to camping gear — see what&apos;s free, what&apos;s hot, and
        what fits your budget before you book.
      </p>
      <div className="lp-cta-row">
        <Link href={APP_HREF} className="btn btn-accent btn-lg">
          Start renting <ArrowRightIcon />
        </Link>
        <a href="#features" className="btn btn-secondary btn-lg">
          See how it works
        </a>
        <span className="meta">No credit card · 30s sign-up</span>
      </div>

      {/* Hero preview card */}
      <div className="lp-hero-card">
        <div className="lp-hero-card-inner">
          <div className="lp-hero-preview">
            <div className="lp-preview-sidebar">
              <div className="lp-preview-section-label">Marketplace</div>
              <PreviewSidebarItem
                active
                label="Products"
                icon={
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 8L12 3 3 8v8l9 5 9-5V8z" />
                    <path d="M3 8l9 5 9-5" />
                  </svg>
                }
              />
              <PreviewSidebarItem
                label="Availability"
                icon={
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <rect x="3" y="5" width="18" height="16" rx="2" />
                    <path d="M3 10h18M8 3v4M16 3v4" />
                  </svg>
                }
              />
              <PreviewSidebarItem
                label="Trending"
                icon={
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M3 17l6-6 4 4 8-8" />
                    <path d="M14 7h7v7" />
                  </svg>
                }
              />
              <PreviewSidebarItem
                label="Chat"
                icon={
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M21 12a8 8 0 1 1-3.5-6.6L21 4l-1 4.5A7.95 7.95 0 0 1 21 12z" />
                  </svg>
                }
              />
            </div>
            <div className="lp-preview-main">
              <div className="lp-preview-header">
                <div>
                  <div className="lp-preview-title">Product Marketplace</div>
                  <div className="lp-preview-subtitle">
                    487 results · sorted by relevance
                  </div>
                </div>
                <span className="badge badge-accent">Live</span>
              </div>
              <div className="lp-preview-chips">
                <span className="chip active">All</span>
                <span className="chip">Cameras</span>
                <span className="chip">Outdoor</span>
                <span className="chip">Tools</span>
                <span className="chip">Vehicles</span>
              </div>
              <div className="lp-preview-grid">
                {[
                  { title: "Premium Camera Kit", meta: "৳450/day · #1042", h: 200 },
                  { title: "Camping Tent", meta: "৳300/day · #1088", h: 145 },
                  { title: "Mountain Bike", meta: "৳540/day · #1233", h: 25 },
                ].map((card) => (
                  <div key={card.title} className="lp-preview-card">
                    <div
                      className="lp-preview-img"
                      style={{ ["--h" as string]: card.h } as React.CSSProperties}
                    />
                    <div className="lp-preview-body">
                      <div className="lp-preview-body-title">{card.title}</div>
                      <div className="lp-preview-body-meta">{card.meta}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

function StatsSection() {
  const stats = [
    { num: "487K+", label: "Products listed" },
    { num: "10.2M", label: "Rental records" },
    { num: "30", label: "Categories" },
    { num: "1.2s", label: "Avg. AI response" },
  ];
  return (
    <section className="lp-stats">
      <div className="lp-section">
        <div className="lp-stats-grid">
          {stats.map((s) => (
            <div key={s.label}>
              <div className="lp-stat-num">{s.num}</div>
              <div className="lp-stat-label">{s.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function FeaturesSection() {
  return (
    <section className="lp-features" id="features">
      <div className="lp-section-eyebrow">FEATURES</div>
      <h2 className="lp-section-title">
        Everything a rental marketplace should have. Nothing it shouldn&apos;t.
      </h2>
      <p className="lp-section-sub">
        Built for the way people actually rent — from quick weekend pickups to
        multi-week pro gear bookings.
      </p>

      <div className="lp-feat-grid">
        {/* Feature 1 — Marketplace */}
        <div className="lp-feat">
          <div className="lp-feat-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 8L12 3 3 8v8l9 5 9-5V8z" />
              <path d="M3 8l9 5 9-5" />
              <path d="M12 13v8" />
            </svg>
          </div>
          <h3>Marketplace browsing</h3>
          <p>
            Filter by category, price range, owner, and date. Drawer details,
            related items, and one-click availability checks.
          </p>
          <div className="lp-feat-visual">
            <div className="lp-feat-visual-grid">
              <div className="lp-feat-tile lp-feat-tile-1" />
              <div className="lp-feat-tile lp-feat-tile-2" />
              <div className="lp-feat-tile lp-feat-tile-3" />
            </div>
          </div>
        </div>

        {/* Feature 2 — Availability */}
        <div className="lp-feat">
          <div className="lp-feat-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="3" y="5" width="18" height="16" rx="2" />
              <path d="M3 10h18M8 3v4M16 3v4" />
            </svg>
          </div>
          <h3>Real-time availability</h3>
          <p>
            Pick a date range — see free windows, busy periods, and conflicts on
            a clean horizontal timeline before you commit.
          </p>
          <div className="lp-feat-visual">
            <div className="lp-timeline">
              <div
                className="lp-timeline-busy"
                style={{ left: "20%", width: "18%" }}
              />
              <div
                className="lp-timeline-busy"
                style={{ left: "62%", width: "14%" }}
              />
              <div
                className="lp-timeline-pick"
                style={{ left: "38%", width: "22%" }}
              />
            </div>
            <div className="lp-timeline-axis">
              <span>May 1</span>
              <span>May 15</span>
              <span>May 31</span>
            </div>
          </div>
        </div>

        {/* Feature 3 — Trends */}
        <div className="lp-feat">
          <div className="lp-feat-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M3 17l6-6 4 4 8-8" />
              <path d="M14 7h7v7" />
            </svg>
          </div>
          <h3>Seasonal trends</h3>
          <p>
            See what&apos;s hot around today&apos;s date based on years of rental
            history. Don&apos;t compete for the same gear everyone else is
            grabbing.
          </p>
          <div className="lp-feat-visual">
            <div className="lp-bars">
              {[
                { h: 30, o: 0.3 },
                { h: 45, o: 0.45 },
                { h: 55, o: 0.55 },
                { h: 42, o: 0.5 },
                { h: 75, o: 0.7 },
                { h: 88, o: 0.85 },
                { h: 100, o: 1 },
                { h: 92, o: 0.9 },
              ].map((b, i) => (
                <div
                  key={i}
                  style={{ height: `${b.h}%`, opacity: b.o }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Feature 4 — Assistant */}
        <div className="lp-feat">
          <div className="lp-feat-icon">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M21 12a8 8 0 1 1-3.5-6.6L21 4l-1 4.5A7.95 7.95 0 0 1 21 12z" />
            </svg>
          </div>
          <h3>RentPi Assistant</h3>
          <p>
            An AI that knows the catalog. Ask &ldquo;is product 1042 free next
            week?&rdquo; or &ldquo;what&apos;s trending in cameras?&rdquo; and get
            grounded answers.
          </p>
          <div className="lp-feat-visual">
            <div className="lp-mini-chat">
              <div className="lp-mini-chat-user">
                Is the camera kit free next week?
              </div>
              <div className="lp-mini-chat-bot">
                Yes — #1042 is open May 8–14. ৳450/day.
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

type Category = {
  name: string;
  count: string;
  icon: React.ReactNode;
  imageSrc?: string;
  cta?: boolean;
};

function CategoriesSection() {
  const categories: Category[] = [
    {
      name: "Electronics",
      count: "82K listings",
      imageSrc: "/categories/electronics.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="3" y="5" width="18" height="14" rx="2" />
          <path d="M9 19v2M15 19v2" />
        </svg>
      ),
    },
    {
      name: "Vehicles",
      count: "14K listings",
      imageSrc: "/categories/vehicles.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="9" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      ),
    },
    {
      name: "Tools",
      count: "61K listings",
      imageSrc: "/categories/tools.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M14.7 6.3a4 4 0 0 0-5.4 5.4L4 17l3 3 5.3-5.3a4 4 0 0 0 5.4-5.4L15 12l-3-3z" />
        </svg>
      ),
    },
    {
      name: "Outdoor",
      count: "47K listings",
      imageSrc: "/categories/outdoor.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 20l9-16 9 16zM12 4v16" />
        </svg>
      ),
    },
    {
      name: "Sports",
      count: "38K listings",
      imageSrc: "/categories/sports.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" />
        </svg>
      ),
    },
    {
      name: "Music",
      count: "22K listings",
      imageSrc: "/categories/music.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M9 18V5l12-2v13" />
          <circle cx="6" cy="18" r="3" />
          <circle cx="18" cy="16" r="3" />
        </svg>
      ),
    },
    {
      name: "Furniture",
      count: "29K listings",
      imageSrc: "/categories/furniture.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 10h18M5 10v10h14V10M7 10V6a3 3 0 0 1 3-3h4a3 3 0 0 1 3 3v4" />
        </svg>
      ),
    },
    {
      name: "Cameras",
      count: "19K listings",
      imageSrc: "/categories/cameras.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="3" y="6" width="18" height="13" rx="2" />
          <circle cx="12" cy="12.5" r="3.5" />
          <path d="M8 6l1.5-3h5L16 6" />
        </svg>
      ),
    },
    {
      name: "Office",
      count: "17K listings",
      imageSrc: "/categories/office.png",
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <rect x="3" y="4" width="18" height="14" rx="1" />
          <path d="M3 18l3 3h12l3-3M9 9h6M9 13h4" />
        </svg>
      ),
    },
    {
      name: "Browse all →",
      count: "487K total",
      cta: true,
      icon: (
        <svg
          className="lp-cat-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M5 12h14M13 6l6 6-6 6" />
        </svg>
      ),
    },
  ];

  return (
    <section className="lp-cats" id="categories">
      <div className="lp-cats-inner">
        <h2>Nine categories. Thirty subcategories.</h2>
        <p>
          From a tripod for the weekend to a 7-seater for the family trip —
          chances are someone near you already owns it.
        </p>
        <div className="lp-cats-grid">
          {categories.map((c) => (
            <Link
              key={c.name}
              href={APP_HREF}
              className={`lp-cat${c.cta ? " lp-cat-cta" : ""}`}
            >
              {c.imageSrc ? (
                <div className="lp-cat-media">
                  <img src={c.imageSrc} alt={c.name} />
                </div>
              ) : (
                c.icon
              )}
              <div>
                <div className="lp-cat-name">{c.name}</div>
                <div className="lp-cat-count">{c.count}</div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorksSection() {
  const steps = [
    {
      n: "STEP 01",
      title: "Browse with confidence",
      desc: "Filter by category, price, dates, and location. Every listing shows live availability — so what you see is what you can actually book.",
    },
    {
      n: "STEP 02",
      title: "Check, ask, decide",
      desc: "Lock in your dates with the timeline view, or ask the assistant for trending alternatives in your budget.",
    },
    {
      n: "STEP 03",
      title: "Rent — and earn trust",
      desc: "Complete rentals build your trust score. Higher score, bigger discounts. Up to 20% off for Elite tier renters.",
    },
  ];

  return (
    <section className="lp-how" id="how">
      <div className="lp-section-eyebrow">HOW IT WORKS</div>
      <h2 className="lp-section-title">Three steps from idea to in-hand.</h2>
      <p className="lp-section-sub">
        No back-and-forth, no &ldquo;is it still available?&rdquo; texts. The
        catalog tells you everything upfront.
      </p>

      <div className="lp-steps">
        {steps.map((s) => (
          <div key={s.n} className="lp-step">
            <div className="lp-step-num">{s.n}</div>
            <h3>{s.title}</h3>
            <p>{s.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function AISection() {
  return (
    <section className="lp-ai" id="ai">
      <div className="lp-ai-inner">
        <div>
          <div className="lp-section-eyebrow">RENTPI ASSISTANT</div>
          <h2 className="lp-section-title" style={{ fontSize: 36 }}>
            Ask the catalog directly.
          </h2>
          <p className="lp-ai-copy">
            The assistant is grounded in real rental data — products, prices,
            owners, availability, and trends. It won&apos;t hallucinate inventory
            or answer off-topic. Just rentals, done well.
          </p>
          <ul className="lp-ai-list">
            <li>
              <span className="check">
                <CheckIcon />
              </span>
              <span>
                <strong>Specific & cited</strong> — references product IDs,
                prices in ৳, and exact dates.
              </span>
            </li>
            <li>
              <span className="check">
                <CheckIcon />
              </span>
              <span>
                <strong>Stays on topic</strong> — politely declines off-platform
                questions.
              </span>
            </li>
            <li>
              <span className="check">
                <CheckIcon />
              </span>
              <span>
                <strong>Saved sessions</strong> — pick up where you left off
                across devices.
              </span>
            </li>
          </ul>
          <Link href={APP_HREF} className="btn btn-primary">
            Try the assistant <ArrowRightIcon />
          </Link>
        </div>

        <div className="lp-chat-mock">
          <div className="lp-chat-bubble user">
            Which cameras are trending this week?
          </div>
          <div className="lp-chat-bubble bot">
            <strong>3 picks for cameras this week:</strong>
            <br />
            • Pro Camera Lens 70-200 (#1421) · ৳520/day · score 19
            <br />
            • Premium Camera Kit (#1042) · ৳450/day · score 14
            <br />
            • Drone with 4K (#1305) · ৳780/day · score 11
            <br />
            Want me to check availability for one?
          </div>
          <div className="lp-chat-bubble user">
            Is the Pro Lens free May 8–14?
          </div>
          <div className="lp-chat-bubble bot lp-chat-typing">
            <span className="lp-chat-typing-dots">
              <span />
              <span />
              <span />
            </span>
            <span className="lp-chat-typing-text">Checking rental data…</span>
          </div>
        </div>
      </div>
    </section>
  );
}

function TestimonialSection() {
  return (
    <section className="lp-quote">
      <blockquote>
        &ldquo;RentPi turned &lsquo;maybe I&apos;ll borrow one&rsquo; into a
        real Saturday plan. Found a tent, a stove, and a portable speaker —
        all available, all booked in five minutes.&rdquo;
      </blockquote>
      <div className="lp-quote-meta">
        <div className="avatar">RH</div>
        <div>
          <div className="name">Rafi H.</div>
          <div>Elite Trust tier · 23 rentals</div>
        </div>
      </div>
    </section>
  );
}

function CtaSection() {
  return (
    <section className="lp-cta">
      <div className="lp-cta-card">
        <h2>Stop owning. Start renting smart.</h2>
        <p>
          Open the app — no card needed to browse, check availability, or ask
          the assistant.
        </p>
        <Link href={APP_HREF} className="btn btn-accent btn-lg">
          Open RentPi <ArrowRightIcon />
        </Link>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="lp-footer">
      <div className="lp-footer-inner">
        <div>
          <div style={{ marginBottom: 12 }}>
            <CompanyLogoLockup className="lp-logo" markClassName="logo-mark" />
          </div>
          <p className="lp-footer-tagline">
            A rental marketplace built for real-time availability, seasonal
            trends, and AI-powered help.
          </p>
          <div className="lp-footer-status">
            <span className="status-pill">
              <span className="status-dot" />
              Platform Online
            </span>
          </div>
        </div>
        <div className="lp-foot-col">
          <h4>Product</h4>
          <Link href={APP_HREF}>Marketplace</Link>
          <Link href={APP_HREF}>Availability</Link>
          <Link href={APP_HREF}>Trending</Link>
          <Link href={APP_HREF}>Assistant</Link>
        </div>
        <div className="lp-foot-col">
          <h4>Company</h4>
          <Link href="/about">About</Link>
          <Link href="/careers">Careers</Link>
          <Link href="/press">Press</Link>
          <Link href="/contact">Contact</Link>
        </div>
      </div>
      <div className="lp-foot-bottom">
        <span>© 2026 RentPi · Dhaka</span>
        <span>v1.0.0 · Built for the hackathon</span>
      </div>
    </footer>
  );
}

export const metadata = {
  title: "RentPi — Rent smarter.",
  description:
    "RentPi is a real-time rental marketplace with availability you can trust, seasonal trend data, and an AI assistant that actually knows the catalog.",
};

export default function Home() {
  return (
    <div className="rentpi-landing">
      <NavBar />
      <HeroSection />
      <StatsSection />
      <FeaturesSection />
      <CategoriesSection />
      <HowItWorksSection />
      <AISection />
      <TestimonialSection />
      <CtaSection />
      <Footer />
    </div>
  );
}
