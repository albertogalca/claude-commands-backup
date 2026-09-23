---
name: interface-review
description: Review UI code against the Interfaces cheat sheet (interfaces.dev/cheat-sheet). Use when asked to review, audit or polish an interface, a component, CSS, or a frontend diff, or when the user says the UI "feels off", or runs /interface-review. Checks radius, alignment, shadows, animation, typography, color tokens, accessibility, layout and UI copy. Reports file:line findings, it does not redesign.
---

# Interface review

Checklist review of UI code. Source: the Interface Cheat Sheet, interfaces.dev/cheat-sheet.
Rules restated here; credit the source if the user publishes the output.

## Procedure

1. Scope. A diff if there is one (`git diff`), else the files the user names. Never the whole repo unless asked.
2. Read the files. Walk the checklist once per file. Skip whole sections that do not apply (no animation code, skip Animation).
3. Report only what you can point at. One line per finding:
   `path:line — [section] what is wrong → the fix`
4. Order by severity: accessibility first, then correctness, then polish.
5. Do not edit unless asked. If asked, apply the smallest diff.

Rules are defaults, not law. A deliberate choice against a rule is fine. Say so and move on.

## User interface

- Nested radius is concentric: outer radius = inner radius + padding between them.
- Optical alignment over geometric alignment.
- Button with an icon: slightly less padding on the icon side.
- Depth comes from a layered `box-shadow`, not a border.
- Images get a 1px outline offset by -1px: black 8% in light mode, white 8% in dark.
- Icon stroke width matches the weight of the text beside it.

## Animation

- Animate from the trigger. Set `transform-origin` to the trigger position, not the center.
- Menus opened often: no open animation, animate the close only.
- Exit is more subtle than entrance: shorter distance, fade opacity, 4px blur.
- Name the properties in a transition. Never `transition: all`.
- Buttons scale to 0.95-0.98 when pressed, `transition: scale 200ms ease-out`.
- Icon swap: crossfade. New icon scale 0.25 to 1, opacity 0 to 1, blur 4px to 0. Old icon reversed.
- CSS transitions for interactions, so motion can reverse mid-flight. Keyframes for one-shot sequences.
- Disable every transition while switching light and dark mode.
- 1-2px jitter during animation: add `will-change: transform`. Common in Safari on iOS.
- Entrances animate in small groups with a short delay between groups, not one block, not one item at a time.
- Nothing animates on page load unless that is the intent.
- Frequent interactions (hover color, list highlight) are instant or very fast.

## Typography

- `.woff2` only on the web. Never `.ttf` or `.otf`.
- `font-variant-numeric: tabular-nums` in timers, counters, prices, tables. Not needed in monospace.
- Long text: 60-75 characters per line.
- `text-wrap: balance` on headings, `text-wrap: pretty` on descriptions, neither on long text.
- `overflow-wrap: break-word` for long words, links and IDs. `white-space: nowrap` for labels and badges.
- Root layout sets `-webkit-font-smoothing: antialiased` and `-moz-osx-font-smoothing: grayscale`.
- Store text in normal capitalization. Change the case with `text-transform`.
- Smart punctuation: curly quotes, en dash for ranges, em dash for asides, a real ellipsis.
- Underlines clear the descenders: `text-underline-position: from-font` plus `text-decoration-skip-ink: auto`.
- Truncated text stays readable somewhere: a tooltip or an expanded view.

## Colors

- Every step in a palette has a job: page background, component hover, border, solid fill, body text. No unused steps.
- Components reference semantic tokens (`--color-text-secondary`), never primitives (`--blue-500`).
- Token names say purpose, not color and not location. `--color-accent-solid`, not `--color-blue-button`.
- `accent` is the brand color. `primary` must not mean both the brand and the body text.
- Measure contrast against the surface directly behind the element, not the page.
- Dark mode gets its own palette. Do not invert the light one.
- One theming mechanism: `prefers-color-scheme` or a `.dark` class. Never both.
- Gradient interpolation: `in oklab` for even brightness, `in oklch` for vivid midpoints, `in srgb` for muted ones.

## Accessibility

- Native elements: `<button>` for buttons, `<a href>` for links. A `div` with a click handler is a finding.
- Style `:focus-visible`, not `:focus`. Never remove the outline without a replacement.
- `tabindex` is 0 or -1 only. Positive values break the order.
- Icon-only buttons need an `aria-label`. Never `aria-hidden="true"` on anything focusable.
- Alt text says what the image shows and why it is there. Decorative images get `alt=""`.
- Every input has a visible `<label>`. `type` and `inputmode` match the expected content.
- Never block paste.
- Submit stays enabled until the request starts. Validate on submit, mark fields `aria-invalid="true"`, link errors with `aria-describedby`, move focus to the first invalid field.
- Hit areas: 24x24px minimum, 44x44px on touch, 40x40px on desktop. They never overlap.
- Decorative glows and gradients get `pointer-events: none`.
- Hover styles live inside `@media (hover: hover)`.
- Animations live inside `@media (prefers-reduced-motion: no-preference)`.
- `role="status"` for routine updates, `role="alert"` for urgent errors only.
- Color alone never carries a status. Add an icon, a label or an underline.
- The skip-to-content link is the first tab stop.

## Layout

- `scroll-margin-top` on headings that are link targets.
- Space between groups is at least twice the space inside a group. 8px inside, 16px or more between.

## Writing

- Button labels start with a verb. "Save draft", not "OK!".
- Confirmation buttons name the action: "Delete project" beside "Cancel".
- One label for the next step across a whole flow. "Continue" everywhere, or "Next" everywhere.
- Links say where they go. Not "click here".
- Capitalization is consistent. Sentence case is the safe default.
- Toggles are labelled by what happens when on: "Send read receipts", not "Disable read receipts".
- Empty states say what belongs there and give one action.
- Address the reader as "you", not "the user".

## Output

Findings list, then one closing line with the count. No redesign proposals, no essays.
If nothing fails, say so in one line.
