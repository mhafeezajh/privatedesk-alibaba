"use client";
import { useId } from "react";

/**
 * PrivateDesk mark: two memory "nodes" separated by a wall — the product's whole
 * idea (isolated, private memory) in one glyph. One node bright, the other dimmed,
 * because from any principal's side the other simply isn't reachable.
 */
export default function Logo({ size = 28, className = "" }: { size?: number; className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" fill="none" className={className}
         role="img" aria-label="PrivateDesk">
      <defs>
        <linearGradient id={`g-${id}`} x1="4" y1="2" x2="44" y2="46" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6366F1" />
          <stop offset="0.55" stopColor="#7C3AED" />
          <stop offset="1" stopColor="#8B5CF6" />
        </linearGradient>
        <linearGradient id={`sheen-${id}`} x1="8" y1="4" x2="24" y2="26" gradientUnits="userSpaceOnUse">
          <stop stopColor="#fff" stopOpacity="0.28" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* vault / desk body */}
      <rect x="2" y="2" width="44" height="44" rx="13" fill={`url(#g-${id})`} />
      <rect x="2" y="2" width="44" height="44" rx="13" fill={`url(#sheen-${id})`} />

      {/* the wall — a crisp vertical divider down the middle */}
      <path d="M24 9.5 L24 38.5" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" opacity="0.95" />

      {/* two private memory nodes, walled apart. Short stubs point at the wall but never cross it. */}
      <circle cx="14" cy="24" r="5.7" stroke="#fff" strokeWidth="2.4" />
      <circle cx="14" cy="24" r="1.9" fill="#fff" />
      <path d="M20 24 H21.6" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" opacity="0.85" />

      <circle cx="34" cy="24" r="5.7" stroke="#fff" strokeWidth="2.4" />
      <circle cx="34" cy="24" r="1.9" fill="#fff" />
      <path d="M28 24 H26.4" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" opacity="0.85" />
    </svg>
  );
}
