"use client";

import type { PageId } from "../data";

import { CompanyLogoMark } from "../../components/company-logo";
import { Icon, type IconName } from "./primitives";

type NavItem = { id: PageId; label: string; icon: IconName };

const NAV_ITEMS: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: "dashboard" },
  { id: "products", label: "Products", icon: "box" },
  { id: "availability", label: "Availability", icon: "calendar" },
  { id: "trending", label: "Trending", icon: "trending" },
  { id: "chat", label: "Chat Assistant", icon: "chat" },
];

const SECONDARY_NAV: NavItem[] = [
  { id: "profile", label: "Profile", icon: "user" },
  { id: "analytics", label: "Analytics", icon: "chart" },
];

type SidebarProps = {
  page: PageId;
  setPage: (page: PageId) => void;
  userInitials: string;
  userName: string;
  userEmail: string;
};

export function Sidebar({
  page,
  setPage,
  userInitials,
  userName,
  userEmail,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <CompanyLogoMark width={26} height={26} />
        </div>
        <div>RentPi</div>
      </div>

      <div className="nav-section">Marketplace</div>
      {NAV_ITEMS.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`nav-item ${page === item.id ? "active" : ""}`}
          onClick={() => setPage(item.id)}
        >
          <span className="nav-icon">
            <Icon name={item.icon} />
          </span>
          <span>{item.label}</span>
        </button>
      ))}

      <div className="nav-section">Account</div>
      {SECONDARY_NAV.map((item) => (
        <button
          key={item.id}
          type="button"
          className={`nav-item ${page === item.id ? "active" : ""}`}
          onClick={() => setPage(item.id)}
        >
          <span className="nav-icon">
            <Icon name={item.icon} />
          </span>
          <span>{item.label}</span>
        </button>
      ))}

      <div className="sidebar-footer">
        <div className="avatar">{userInitials}</div>
        <div className="sidebar-footer-text">
          <div className="name">{userName}</div>
          <div className="email">{userEmail}</div>
        </div>
      </div>
    </aside>
  );
}

type TopbarProps = {
  onSearch?: (value: string) => void;
  userInitials: string;
};

export function Topbar({ onSearch, userInitials }: TopbarProps) {
  return (
    <div className="topbar">
      <div className="search-input">
        <Icon name="search" size={14} />
        <input
          placeholder="Search products, categories, rentals…"
          onChange={(event) => onSearch?.(event.target.value)}
        />
        <span className="search-kbd">⌘K</span>
      </div>
      <div style={{ flex: 1 }} />
      <div className="status-pill">
        <span className="status-dot" />
        Platform Online
      </div>
      <button type="button" className="icon-btn" title="Notifications">
        <Icon name="bell" />
        <span className="badge-dot" />
      </button>
      <div style={{ width: 1, height: 22, background: "var(--border)" }} />
      <div className="avatar" style={{ width: 30, height: 30 }}>
        {userInitials}
      </div>
    </div>
  );
}
