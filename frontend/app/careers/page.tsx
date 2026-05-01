import type { Metadata } from "next";

import { CompanyPageShell } from "../components/company-page-shell";
import "../company-pages.css";

export const metadata: Metadata = {
  title: "Careers — RentPi",
  description: "Explore career opportunities at RentPi.",
};

export default function CareersPage() {
  return (
    <CompanyPageShell
      title="Careers at RentPi"
      description="This is a placeholder careers page. We are building the full jobs experience and team stories."
      points={[
        "Open roles and hiring tracks will be listed here.",
        "Remote-friendly collaboration with product-minded engineers.",
        "Mission: make renting as easy and trusted as buying.",
      ]}
    />
  );
}
