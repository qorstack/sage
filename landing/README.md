# Sage — landing page

A single self-contained `index.html` built as an engineering decision ledger:
paper-blue surfaces, protocol lines, a live decision trace, and IBM Plex type
from Google Fonts. No build step or package dependencies.

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

The site then lives at `https://qorstack.github.io/sage/`. The page is fully
self-contained (inline CSS/JS, CDN fonts, only anchor + absolute links), so it works
unchanged under the `/sage/` sub-path.

## Editing

Everything lives in `index.html` — styles are in the `<style>` block at the top.
The palette is defined by the `--paper`, `--ink`, `--blue`, `--orange`, and
`--green` variables.
