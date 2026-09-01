---
name: radius-audit
description: Audit border-radius usage for correct corner nesting. Use when the user says "radius audit", "audit corners", "check border-radius", "rounded corners look off", or "/radius-audit". Finds nested rounded elements whose inner radius doesn't match outer radius minus padding/border, and flags ambiguous button radii.
---

# Radius Audit

Audit rounded corners against the nesting principle: a `border-radius` is just a number; what matters is how it *relates* to the element's size and to elements nested inside it.

Based on the "corners are relative" principle from https://shedsgns.me/radius.

## The rule

When a rounded element sits inside another rounded element, concentric corners require:

```
inner radius = outer radius − (padding + border)
```

Both sides of the parent count: a 16px radius card with 8px padding and a 1px border wants an inner radius of `16 − (8 + 1) = 7px`. If the inner radius is hardcoded to the same value as the outer, corners look pinched; if too large, they bulge past the parent.

## What to check

Scan the project's styles (CSS, SCSS, Tailwind classes, styled-components, inline styles — whatever the project uses).

1. **Nested rounded elements** — find a rounded child inside a rounded parent with padding/border between them. Flag when `inner ≠ outer − (padding + border)`. Report the file, the elements, the actual values, and the expected inner radius.
2. **Hardcoded matched radii** — a child reusing the parent's radius token verbatim (e.g. both `rounded-lg`) when there's padding between them. Recommend `calc(outer - padding)` (CSS) or the corrected token.
3. **Ambiguous button radii** — buttons with a middle-ground radius that's neither a clean rectangle nor an intentional pill. Recommend committing to one: small controlled radius, or full pill (`border-radius: 9999px` / `rounded-full`).
4. **Borders ignored in the gap** — the border width is part of the gap; flag formulas that subtract only padding.
5. **`corner-shape` / squircle without fallback** — the subtraction formula is for circular corners and breaks on superellipse curves. Flag `corner-shape` not gated behind `@supports`, and note that squircle nesting needs visual tuning, not the formula.

## Output

One line per finding: `file:line — [issue] outer Xpx / inner Ypx with Zpx gap → expected inner (X−Z)px`.

Prefer `calc()` over hardcoded results so the relationship survives token changes. The formula is the starting point — tell the user to nudge a pixel or two by eye after.
