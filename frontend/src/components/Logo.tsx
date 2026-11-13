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
      role="img"
      aria-label="PhishLens logo"
      className={className}
      style={style}
    >
      {/* Outer Defensive Shield Structure */}
      <path
        d="M12 2.2L3.8 5.8V12c0 5.4 3.5 10.1 8.2 11.4 4.7-1.3 8.2-6 8.2-11.4V5.8L12 2.2z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Upper Envelope / Facet Chevron */}
      <path
        d="M5.5 7.5L12 12l6.5-4.5"
        stroke="currentColor"
        strokeWidth="1.25"
        strokeLinecap="round"
        strokeLinejoin="round"
        opacity="0.35"
      />
      {/* Central Inspection Lens Element */}
      <circle
        cx="12"
        cy="12"
        r="4.5"
        stroke="var(--accent)"
        strokeWidth="1.75"
        strokeLinecap="round"
      />
      {/* Precision Reticle Axis Points */}
      <path
        d="M12 5.5v2M12 16.5v2M5.5 12h2M16.5 12h2"
        stroke="var(--accent)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      {/* Core Optical Focal Diamond */}
      <rect
        x="10.4"
        y="10.4"
        width="3.2"
        height="3.2"
        rx="0.6"
        transform="rotate(45 12 12)"
        fill="var(--accent)"
      />
    </svg>
  );
}
