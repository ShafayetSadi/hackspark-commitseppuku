"use client";

import type { CSSProperties, ReactNode } from "react";

import { CATEGORY_HUE, type Category } from "../data";

export type IconName =
  | "dashboard"
  | "box"
  | "calendar"
  | "trending"
  | "chat"
  | "user"
  | "chart"
  | "search"
  | "bell"
  | "plus"
  | "close"
  | "arrow"
  | "check"
  | "sparkle"
  | "filter"
  | "menu"
  | "sort"
  | "location"
  | "refresh"
  | "send"
  | "paperclip"
  | "trash"
  | "info"
  | "star"
  | "shield";

const ICON_PATHS: Record<IconName, ReactNode> = {
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="9" rx="1.5" />
      <rect x="14" y="3" width="7" height="5" rx="1.5" />
      <rect x="14" y="12" width="7" height="9" rx="1.5" />
      <rect x="3" y="16" width="7" height="5" rx="1.5" />
    </>
  ),
  box: (
    <>
      <path d="M21 8L12 3 3 8v8l9 5 9-5V8z" />
      <path d="M3 8l9 5 9-5" />
      <path d="M12 13v8" />
    </>
  ),
  calendar: (
    <>
      <rect x="3" y="5" width="18" height="16" rx="2" />
      <path d="M3 10h18M8 3v4M16 3v4" />
    </>
  ),
  trending: (
    <>
      <path d="M3 17l6-6 4 4 8-8" />
      <path d="M14 7h7v7" />
    </>
  ),
  chat: <path d="M21 12a8 8 0 1 1-3.5-6.6L21 4l-1 4.5A7.95 7.95 0 0 1 21 12z" />,
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
  chart: (
    <>
      <path d="M3 3v18h18" />
      <path d="M7 14l4-4 4 4 5-5" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="M21 21l-4.3-4.3" />
    </>
  ),
  bell: (
    <>
      <path d="M18 16v-5a6 6 0 1 0-12 0v5l-2 2h16z" />
      <path d="M10 20a2 2 0 0 0 4 0" />
    </>
  ),
  plus: <path d="M12 5v14M5 12h14" />,
  close: <path d="M18 6L6 18M6 6l12 12" />,
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  check: <path d="M5 12l5 5L20 7" />,
  sparkle: (
    <>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M5.6 18.4l2.8-2.8M15.6 8.4l2.8-2.8" />
    </>
  ),
  filter: <path d="M3 5h18M6 12h12M10 19h4" />,
  menu: <path d="M3 6h18M3 12h18M3 18h18" />,
  sort: <path d="M3 6h13M3 12h9M3 18h5M17 8V20M17 20l4-4M17 20l-4-4" />,
  location: (
    <>
      <path d="M12 22s8-7.5 8-13a8 8 0 1 0-16 0c0 5.5 8 13 8 13z" />
      <circle cx="12" cy="9" r="3" />
    </>
  ),
  refresh: (
    <>
      <path d="M21 12a9 9 0 1 1-3-6.7L21 8" />
      <path d="M21 3v5h-5" />
    </>
  ),
  send: (
    <>
      <path d="M22 2L11 13" />
      <path d="M22 2l-7 20-4-9-9-4 20-7z" />
    </>
  ),
  paperclip: (
    <path d="M21 11l-9 9a5 5 0 0 1-7-7l9-9a3 3 0 0 1 4 4l-9 9a1 1 0 0 1-2-2l8-8" />
  ),
  trash: (
    <>
      <path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
    </>
  ),
  info: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 8v.01M12 11v5" />
    </>
  ),
  star: (
    <path d="M12 3l2.6 6 6.4.6-4.8 4.4 1.4 6.4L12 17l-5.6 3.4 1.4-6.4L3 9.6 9.4 9z" />
  ),
  shield: (
    <>
      <path d="M12 3l8 3v7c0 4.5-3.5 8-8 9-4.5-1-8-4.5-8-9V6z" />
      <path d="M9 12l2 2 4-4" />
    </>
  ),
};

export function Icon({ name, size = 16 }: { name: IconName; size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {ICON_PATHS[name]}
    </svg>
  );
}

export function Placeholder({
  category,
  label,
}: {
  category: Category;
  label?: string;
}) {
  const hue = CATEGORY_HUE[category] ?? 200;
  const style: CSSProperties = {
    background: `linear-gradient(135deg, oklch(0.95 0.02 ${hue}), oklch(0.92 0.03 ${hue}))`,
  };
  return (
    <div className="product-image" style={style}>
      <div className="stripes" />
      <div className="product-image-label">{label || category}</div>
    </div>
  );
}

export type BadgeVariant =
  | "default"
  | "accent"
  | "warn"
  | "danger"
  | "info"
  | "solid";

export function Badge({
  children,
  variant = "default",
}: {
  children: ReactNode;
  variant?: BadgeVariant;
}) {
  const className =
    variant === "default" ? "badge" : `badge badge-${variant}`;
  return <span className={className}>{children}</span>;
}

export function PageHeader({
  title,
  desc,
  actions,
}: {
  title: string;
  desc?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <h1>{title}</h1>
        {desc ? <div className="desc">{desc}</div> : null}
      </div>
      {actions ? <div className="page-header-actions">{actions}</div> : null}
    </div>
  );
}

export function Stat({
  label,
  value,
  meta,
}: {
  label: string;
  value: string;
  meta?: string;
}) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">{value}</div>
      {meta ? <div className="stat-meta">{meta}</div> : null}
    </div>
  );
}
