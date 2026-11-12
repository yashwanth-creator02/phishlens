import type { CSSProperties } from "react";

export interface LogoProps {
  size?: number;
  className?: string;
  style?: CSSProperties;
}

export function Logo({ size = 20, className, style }: LogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      role="img"
      aria-label="PhishLens logo"
      className={className}
      style={style}
    >
      <path d="M12 2L3 6v6c0 5.25 3.75 10.15 9 11.5 5.25-1.35 9-6.25 9-11.5V6l-9-4z" />
      <circle cx="12" cy="11" r="3.5" stroke="var(--accent)" />
      <circle cx="12" cy="11" r="1" fill="var(--accent)" />
    </svg>
  );
}
