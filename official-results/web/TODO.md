# Results Dashboard Improvements — TODO

Execution plan for the issues in ANALYSIS.md. Each item is a single focused commit that can be tested in isolation.

Testing protocol: after each change, reload `http://127.0.0.1:8000/results-dashboard.html`, verify the change behaves correctly, then commit.

## Plan

- [ ] 1. **Header cleanup** — drop "1) / 2) / …" wizard numbering; rename page title to "SWE-BuildBench Results Explorer".
- [ ] 2. **Demote Data source** — move file input into a compact "Load local CSV…" control in the header; remove its own card.
- [ ] 3. **Side-by-side layout** — controls on the left, chart sticky on the right; stack on narrow screens.
- [ ] 4. **Make chart fill its container** — let SVG grow with viewport height; remove fixed 620px floor when room is available.
- [ ] 5. **Rename "Percent" axis** — display "Pass rate (%)" where we currently show "Percent".
- [ ] 6. **Hover-only labels + Pareto frontier** — show permanent labels only for points on the Pareto frontier; show other labels via hover/focus.
- [ ] 7. **Interactive legend** — click a legend row to toggle that series' visibility; show greyed-out state when off.
- [ ] 8. **Keyboard-accessible markers** — make each point focusable with `tabindex`, announce via `aria-label`, and show the tooltip on focus.
- [ ] 9. **Deduplicate tooltip rows** — skip Tokens Input / Tokens Output detail lines when Tokens Total stacked split already covers them.
- [ ] 10. **Better default selection** — default `colorMode` to `agent` so the initial view isn't a 14-colour rainbow.
- [ ] 11. **Explain Report type / Error bars** — add hint text under each select.
- [ ] 12. **Language X-axis stays discoverable** — keep the option visible but disabled with a title when fewer than 2 languages are selected.
- [ ] 13. **Collapse "no data" pairs** — list them as a compact footnote instead of taking up grid cells.
- [ ] 14. **Fix file input double-labeling** — hide the native `<input>` chrome; style the label as the single click target.
- [ ] 15. **Status + focus + empty-state polish** — lift status-line contrast, add `:focus-visible` styles for checkboxes and action buttons, hide `#chart-empty` until genuinely empty.
- [ ] 16. **Preserve user state on CSV reload** — don't reset axis/colour/report when a new CSV is loaded.
- [ ] 17. **Code nits** — fix misindented `placedBoxes.push`; drop dead `viewBox` reset in `clearChart()`.

## Cleanup

- [ ] 18. **Remove ANALYSIS.md and TODO.md** once the above are all in.
