# toroIQ website

[toroiq.com](https://toroiq.com/) — an independent project exploring financial research graphs for agents and the people behind them.

Static HTML, CSS and JavaScript. No build step, external font dependency, analytics tracker, API keys or backend. The graph diagram is illustrative. The configuration builder runs entirely in the browser; it does not transmit the research question or activate a schedule. Contact buttons use email or public GitHub issues.

`.nojekyll` keeps the documentation and JSON files available at their exact paths without a Jekyll transformation.

## Local preview

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open http://127.0.0.1:8766. The [starter](starter/README.md) includes five source-linked structural seeds and a local workspace initializer. Original code, topology and summaries are MIT-licensed; linked source documents are not included or relicensed. No private tracker data is exported. The old fictional demo remains separately available.

## Worked research example

[example.html](example.html) follows Microsoft’s changing AI-capacity expectations across three 2025 disclosures. It is a historical, manually reviewed example with CSV and JSON downloads, separate from the structural seeds.

Edit `examples/management-expectations.json` after checking primary sources, then run `python3 scripts/build_example.py`. The script validates and renders reviewed records; it does not fetch new disclosures, perform research, or publish. No private tracker exports are used.

## Structure

- `index.html`, `styles.css`, `app.js`: landing page, responsive layout and configuration builder.
- `motion.js`, `motion.css`: illustrative 14-second research cycle with pause, reduced-motion and offscreen controls; no live agent activity.
- `projects.json`, `llms.txt`: machine-readable project entrypoints and explicit access boundaries.
- `starter/seeds/`: five downloadable packs and their machine-readable catalog.
- `starter/seed.py`, `starter/seed.schema.json`: initializer and structural seed schema; the older `run.py` uses its separate demo schema.
- `tests/browser_check.py`: optional Playwright/Firefox integration checks against localhost or a supplied deployment URL.
- `CNAME`: existing `toroiq.com` custom domain. Do not change without a DNS migration.
- `favicon-*.png`, `apple-touch-icon.png`: existing brand assets.

## Deployment

GitHub Pages publishes the root of the `main` branch in `nimitmehra/toroiq-website`. Test changes before pushing. A push to `main` changes the live site; it does not run any tracker, publish briefs or change repository visibility.

## Release boundaries

All five small seed packs are public. Existing NSE and US viewers still point to research mirrors, not private code. The macro viewer is the related public crisis project, not the full Global Macro tracker. Full private tracker releases remain separate. Keep HTML, `projects.json`, the seed catalog and agent guide consistent. Do not announce live data, automatic monitoring or predictive performance before it exists.

The `starter/LICENSE` applies only to that directory. No new license is applied to the site's pre-existing assets, third-party data or linked repositories.
