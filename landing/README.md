# Precept — landing page

A single self-contained `index.html` (dark theme, heavy-blue brand accent,
Google Fonts via CDN). No build step, no dependencies.

## Preview locally

Just open the file:

```bash
# any of these
open index.html               # macOS
start index.html              # Windows
python -m http.server 3000    # then visit http://localhost:3000
```

## Deploy to GitHub Pages

The repo ships a workflow at [`.github/workflows/pages.yml`](../.github/workflows/pages.yml)
that publishes this `landing/` folder to GitHub Pages on every push to `main`.

One-time setup (repo owner):

1. GitHub → **Settings → Pages → Build and deployment → Source** = **GitHub Actions**.
2. Merge to `main` (or run the workflow manually from the **Actions** tab → *Deploy
   landing page to GitHub Pages* → **Run workflow**).

The site then lives at `https://qorstack.github.io/preceptai/`. The page is fully
self-contained (inline CSS/JS, CDN fonts, only anchor + absolute links), so it works
unchanged under the `/preceptai/` sub-path.

## Editing

Everything lives in `index.html` — styles are in the `<style>` block at the top.
Brand color is the `--primary` / `--primary-bright` CSS variables; swap those to
re-theme the whole page.
