/** Static company mark — file lives in `/public/company-logo.svg`. */

export const COMPANY_LOGO_SRC = "/company-logo.svg";

type CompanyLogoMarkProps = {
  width?: number;
  height?: number;
  className?: string;
};

export function CompanyLogoMark({
  width = 28,
  height = 28,
  className,
}: CompanyLogoMarkProps) {
  return (
    <img
      src={COMPANY_LOGO_SRC}
      alt=""
      width={width}
      height={height}
      className={className}
      draggable={false}
    />
  );
}

type CompanyLogoLockupProps = {
  className?: string;
  markClassName?: string;
  name?: string;
};

export function CompanyLogoLockup({
  className,
  markClassName,
  name = "RentPi",
}: CompanyLogoLockupProps) {
  return (
    <div className={className}>
      <span className={markClassName}>
        <CompanyLogoMark width={28} height={28} />
      </span>
      <span>{name}</span>
    </div>
  );
}
