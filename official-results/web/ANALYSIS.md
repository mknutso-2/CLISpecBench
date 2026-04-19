# Results Dashboard UI/UX Analysis

Review of the static web dashboard at `results-dashboard.html`. Findings come from driving the live page at `http://127.0.0.1:8000/results-dashboard.html` plus reading the HTML/CSS/JS source.

## Layout / information architecture

- **The chart is below the fold.** On a 1440×900 window, the entire initial viewport is filled by configuration cards; you have to scroll past five panels to see the plot. The chart is the whole point of the page — a left-rail-of-controls + right-side-chart split (or a sticky chart at the top) would let users tweak controls and see the effect without scrolling.
- **"Data source" breaks the numbered sequence.** It sits between "2) Languages" and "3) Eval" but has no number, and it's only useful on `file://`. Demote it to a small "Load different CSV…" link in the header or tuck it into a footer.
- **"1) / 2) / 3) …" wizard numbering is misleading.** Nothing forces an order and you re-tweak these constantly. Drop the numbering and let the section titles stand alone.

## Chart

- **Label collisions in the dense cluster.** With the default "all pairs selected", the lower-left clump (Cost < $10) has several labels drawn on top of markers (`codex-cli / gpt-5.2` label is under its own marker; `codex-cli / gpt-5.1-codex-mini` label sits over other markers; `codex-cli / gpt-5.1-codex-max`, `gpt-5.4`, `gpt-5.4-mini`, and the three Gemini pairs have no visible labels at all because the placer gave up). Options: show labels only on hover/selection, or auto-label only the Pareto frontier; keep the rest as dots with legend lookup.
- **No Pareto frontier highlight.** The chart explicitly exists to compare cost vs. quality but doesn't call out the frontier.
- **Fixed SVG size wastes space.** `viewBox="0 0 980 560"` with `min-height: 620px` means the plot neither grows on wide monitors nor shrinks on laptops — huge empty right half when the data lives in the lower-left.
- **Legend isn't interactive.** No `onclick` on `.legend-item` — can't isolate a series, can't hide one. Legend click → toggle is standard in every charting lib.
- **Markers aren't keyboard-reachable.** Tooltips require a mouse; circles have no `tabindex`, `role="img"`, or `aria-label`, so the chart is invisible to screen readers and keyboard users.
- **Tooltip has duplicated info.** With Tokens Total selected, the tooltip shows "Tokens Total (Mean)", then "Tokens Total split: input X / output Y", then "Tokens Input: X" and "Tokens Output: Y" separately.
- **Y-axis titled just "Percent".** Name what it is — "Pass rate (%)" or "Score (%)" — so the axis reads standalone.

## Controls

- **Default selection is too busy.** Loading the page selects all 14 data-bearing pairs colored by pair. Pre-selecting ~5–6 representative pairs (or coloring by agent, which collapses the 14-color rainbow) would produce a readable first impression.
- **Report-type and error-bar semantics are unlabeled.** "Worst/Best/Median/Mean" — across what? "Range" vs "Std Dev." — of what?
- **"Language" X-axis discoverability.** It silently disappears when you're down to one language. A disabled option with hover-title "Select 2+ languages" is less mysterious than it vanishing.
- **"No data" pairs consume grid cells.** Four grayed cards take up space for pairs with no runs. Collapse them into a tiny footnote.
- **No search/filter in the pair list.** Manageable at 18 pairs, painful once you add more evals and models.
- **Long names wrap to two lines.** `codex-cli / gpt-5.1-codex-mini` wraps inside its cell; combined with the "(no data)" suffix, some cells become taller than others and the grid stairs up/down.
- **File input is double-labeled.** The native "Choose File / No file chosen" button renders alongside "Choose local CSV file" on the `<label>`, giving the user two labels and no clear click target.

## Visual / polish

- **Status line is nearly invisible.** `Loaded 162 runs…` sits directly on the dark gradient at very low contrast.
- **Card accent stripe is decorative only.** Could signal validation state (red stripe on "2) Languages" when you unchecked them all).
- **Focus styles only exist for `<select>`.** Tabbing through checkboxes and "Select all"/"Unselect all" shows no visible focus ring — keyboard navigation is effectively broken.
- **Empty-state message flashes briefly.** `#chart-empty` has text "No data to plot yet." without being hidden initially; fast reloads flash that line before the CSV resolves.
- **Page title is hard-coded "CNCSim XY Results Explorer"** even though the eval select would support other evals.

## Minor code nits

- `results-dashboard.js:1343` has misindented `placedBoxes.push`.
- `clearChart()` re-sets the `viewBox` to the only value it ever uses — dead reassignment.
- `initSelectionDefaults` hard-resets axis/colour/report selections on every CSV reload, dropping the user's current view.

## Top 3 if forced to pick

1. Give the chart real estate — side-by-side layout so the plot is visible on load and stays visible while tweaking.
2. Fix the label collision/scaling in the dense cluster (hover-only labels or a Pareto-only label policy) and let the SVG grow with the container.
3. Make the legend interactive and the markers keyboard/screen-reader reachable.
