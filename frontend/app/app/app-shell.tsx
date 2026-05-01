"use client";

import { useState } from "react";

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
  initialUser: AppUser | null;
};

function initialsFor(name: string | undefined): string {
  if (!name) return "AR";
  const parts = name.trim().split(/\s+/);
  if (parts.length === 0) return "AR";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export default function AppShell({ initialUser }: AppShellProps) {
  const [page, setPage] = useState<PageId>("dashboard");
  const [filterCategory, setFilterCategory] =
    useState<CategoryFilter>("All");

  const userInitials = initialsFor(initialUser?.full_name);
  const userName = initialUser?.full_name ?? "Ayesha R.";
  const userEmail = initialUser?.email ?? "ayesha@rentpi.app";

  const renderPage = () => {
    switch (page) {
      case "dashboard":
        return <Dashboard setPage={setPage} />;
      case "products":
        return (
          <Products
            filterCategory={filterCategory}
            setFilterCategory={setFilterCategory}
          />
        );
      case "availability":
        return <Availability />;
      case "trending":
        return (
          <Trending
            setPage={setPage}
            setFilterCategory={setFilterCategory}
          />
        );
      case "chat":
        return <Chat />;
      case "profile":
        return <Profile />;
      case "analytics":
        return <Analytics />;
      default:
        return <Dashboard setPage={setPage} />;
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
          <Topbar userInitials={userInitials} />
          {renderPage()}
        </div>
      </div>
    </div>
  );
}
