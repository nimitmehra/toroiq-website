# toroIQ website

[toroiq.com](https://toroiq.com/) — an independent project exploring financial research graphs for agents and the people behind them.

Static HTML, CSS and JavaScript. No build step, external font dependency, analytics tracker, API keys or backend. The graph diagram is illustrative. The configuration builder runs entirely in the browser; it does not transmit the research question or activate a schedule. Contact buttons use email or public GitHub issues.

## Local preview

```sh
python3 -m http.server 8766 --bind 127.0.0.1
```

Open http://127.0.0.1:8766. The runnable project skeleton and its own MIT license live in [starter/](starter/README.md). Only synthetic, newly authored demo material is included; no private tracker data is exported.

## Structure

- `index.html`, `styles.css`, `app.js`: landing page, responsive layout and configuration builder.
- `projects.json`, `llms.txt`: machine-readable project entrypoints and explicit access boundaries.
- `starter/`: offline Python example, graph schema, tests and extension guide.
- `CNAME`: existing `toroiq.com` custom domain. Do not change without a DNS migration.
- `favicon-*.png`, `apple-touch-icon.png`: existing brand assets.

## Deployment

GitHub Pages publishes the root of the `main` branch in `nimitmehra/toroiq-website`. Test changes before pushing. A push to `main` changes the live site; it does not run any tracker, publish briefs or change repository visibility.

## Release boundaries

NSE and US links point to public research mirrors, not their private code. The macro link points to the related public crisis-intelligence project, not the full Global Macro tracker. Crypto is clearly marked release planned. Update both HTML and `projects.json` when release status changes. Do not announce a hosted API, live data access, auto-scheduling, predictive performance or commercial service before it exists.

The `starter/LICENSE` applies only to that directory. No new license is applied to the site's pre-existing assets, third-party data or linked repositories.
