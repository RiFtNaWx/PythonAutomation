# Operator UI contract (ate/ui/web)

AI and humans must keep the console shape stable.

## Add a page

1. Add `<button class="tab" data-page="{name}">` inside the single `nav.tabs.glass`.
2. Add `<section id="page-{name}" class="page">` inside `main`.
3. Reuse `glass panel`, `db-grid`, `btn`, `btn accent`, `btn ghost`, `hint`, `row`.
4. Bump `styles.css?v=` cache query in `index.html`.
5. Wire clicks in `app.js` only (no second framework).

## Forbidden

- Second `nav.tabs` (or a parallel top nav)
- Fourth webfont family (keep Barlow / JetBrains Mono / Space Grotesk)
- New design system / CSS reset
- Dumping large inline `style=` blocks for layout (small flex tweaks OK)
- Editing this tree from a regex "auto-improve UI" pass without running `python -m ate.core.check_ui_contract`

## Check

```
python -m ate.core.check_ui_contract
```

Fails if any `data-page` lacks `#page-*`, or if more than one `.tabs` nav, or if a fourth Google Fonts family appears.
