"use client";

import { useEffect, useState } from "react";

import type { CategoryFilter, PageId } from "./data";
import { Availability, Trending } from "./components/page-availability";
import { Chat } from "./components/page-chat";
import {
  Analytics,
  Dashboard,
  Profile,
} from "./components/page-dashboard";
import { Products } from "./components/page-products";
import { Sidebar, Topbar } from "./components/shell";

type AppUser = {
  id: number;
  email: string;
  full_name: string;
};

type AppShellProps = {
  initialUser: AppUser;
};

const PAGE_CHECKPOINT_KEY = "rentpi:last-page";
const PAGE_IDS: ReadonlySet<PageId> = new Set([
  "dashboard",
  "products",
  "availability",
  "trending",
  "chat",
  "profile",
  "analytics",
]);

function isPageId(value: string): value is PageId {
  return PAGE_IDS.has(value as PageId);
}

function initialsFor(name: string | undefined): string {
  if (!name) return "U";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return "AR";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function AppShell({ initialUser }: AppShellProps) {
  const [page, setPage] = useState<PageId>("dashboard");
  const [filterCategory, setFilterCategory] =
    useState<CategoryFilter>("All");
  const [chatAutoPrompt, setChatAutoPrompt] = useState<string | null>(null);
  const [availabilityPrefillProductId, setAvailabilityPrefillProductId] =
    useState<number | null>(null);

  useEffect(() => {
    try {
      const checkpoint = window.localStorage.getItem(PAGE_CHECKPOINT_KEY);
      if (checkpoint && isPageId(checkpoint)) {
        setPage(checkpoint);
      }
    } catch {
      // Ignore storage errors (e.g., disabled storage).
    }
  }, []);

  useEffect(() => {
    try {
      window.localStorage.setItem(PAGE_CHECKPOINT_KEY, page);
    } catch {
      // Ignore storage errors (e.g., disabled storage).
    }
  }, [page]);

  const userInitials = initialsFor(initialUser?.full_name);
  const userName = initialUser.full_name;
  const userEmail = initialUser.email;

  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <Dashboard setPage={setPage} userName={userName} />;
      case "products":
        return (
          <Products
            filterCategory={filterCategory}
            setFilterCategory={setFilterCategory}
            setPage={setPage}
            setChatAutoPrompt={setChatAutoPrompt}
            setAvailabilityPrefillProductId={setAvailabilityPrefillProductId}
          />
        );
      case "availability":
        return (
          <Availability
            setPage={setPage}
            setChatAutoPrompt={setChatAutoPrompt}
            prefillProductId={availabilityPrefillProductId}
            onPrefillConsumed={() => setAvailabilityPrefillProductId(null)}
          />
        );
      case "trending":
        return (
          <Trending
            setPage={setPage}
            setFilterCategory={setFilterCategory}
            userId={initialUser.id}
          />
        );
      case "chat":
        return (
          <Chat
            autoSendPrompt={chatAutoPrompt}
            onAutoSendConsumed={() => setChatAutoPrompt(null)}
          />
        );
      case "profile":
        return <Profile user={initialUser} />;
      case "analytics":
        return <Analytics />;
      default:
        return <Dashboard setPage={setPage} userName={userName} />;
    }
  };

  return (
    <div className="rentpi-app">
      <div className="app" data-screen-label={page}>
        <Sidebar
          page={page}
          setPage={setPage}
          userInitials={userInitials}
          userName={userName}
          userEmail={userEmail}
        />
        <div className="main">
          <Topbar
            userInitials={userInitials}
            onOpenProfile={() => setPage("profile")}
          />
          {renderPage()}
        </div>
      </div>
    </div>
  );
}
