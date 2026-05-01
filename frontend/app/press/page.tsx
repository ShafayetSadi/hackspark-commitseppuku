import type { Metadata } from "next";

import { CompanyPageShell } from "../components/company-page-shell";
import "../company-pages.css";

export const metadata: Metadata = {
  title: "Press — RentPi",
  description: "Press resources and announcements for RentPi.",
};

export default function PressPage() {
  return (
    <CompanyPageShell
      title="Press"
      description="This is a placeholder press page for media kits, announcements, and brand resources."
      points={[
        "Upcoming product and partnership announcements.",
        "Brand assets and company boilerplate for media coverage.",
        "Contact channel for interviews and press inquiries.",
      ]}
    />
  );
}
