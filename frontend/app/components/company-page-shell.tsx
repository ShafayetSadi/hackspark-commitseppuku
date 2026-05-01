import Link from "next/link";

import { CompanyLogoLockup } from "./company-logo";

type CompanyPageShellProps = {
  title: string;
  description: string;
  points: string[];
};

export function CompanyPageShell({
  title,
  description,
  points,
}: CompanyPageShellProps) {
  return (
    <div className="rentpi-company-page">
      <header className="company-header">
        <div className="company-header-inner">
          <Link href="/" aria-label="Go to RentPi home">
            <CompanyLogoLockup className="company-logo" markClassName="logo-mark" />
          </Link>
          <Link href="/" className="company-link">
            Back to home
          </Link>
        </div>
      </header>

      <main className="company-main">
        <section className="company-card">
          <p className="company-eyebrow">RentPi Company</p>
          <h1>{title}</h1>
          <p>{description}</p>

          <ul className="company-points">
            {points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>

          <div className="company-actions">
            <Link href="/app" className="company-btn company-btn-primary">
              Open marketplace
            </Link>
            <Link href="/login" className="company-btn company-btn-secondary">
              Sign in
            </Link>
          </div>
        </section>
      </main>
    </div>
  );
}
