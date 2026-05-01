import type { Metadata } from "next";

import { CompanyPageShell } from "../components/company-page-shell";
import "../company-pages.css";

export const metadata: Metadata = {
  title: "Contact — RentPi",
  description: "Get in touch with the RentPi team.",
};

export default function ContactPage() {
  return (
    <CompanyPageShell
      title="Contact"
      description="This is a placeholder contact page. Direct support and sales channels will be added soon."
      points={[
        "General inquiries and support contact details.",
        "Partnership and enterprise rental coordination.",
        "Response SLAs and support hours information.",
      ]}
    />
  );
}
