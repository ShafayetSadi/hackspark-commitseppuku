import type { Metadata } from "next";

import { CompanyPageShell } from "../components/company-page-shell";
import "../company-pages.css";

export const metadata: Metadata = {
  title: "About — RentPi",
  description: "Learn about RentPi and why we built a real-time rental marketplace.",
};

export default function AboutPage() {
  return (
    <CompanyPageShell
      title="About RentPi"
      description="RentPi is a rental marketplace focused on reliable availability, transparent pricing, and faster decisions for renters."
      points={[
        "Built around real-time inventory and booking confidence.",
        "Designed to help renters discover better alternatives quickly.",
        "Backed by an assistant that stays grounded in catalog data.",
      ]}
    />
  );
}
