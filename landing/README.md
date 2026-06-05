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

## Deploy to Vercel

**Option A — CLI (fastest):**

```bash
cd landing
npx vercel        # first run links/creates the project
npx vercel --prod # promote to production
```

Vercel auto-detects it as a static site (an `index.html` with no framework),
so there is nothing to configure.

**Option B — Git import:**

1. Push this repo to GitHub.
2. In Vercel → *New Project* → import the repo.
3. Set **Root Directory** to `landing`. Framework preset: **Other**. Deploy.

## Editing

Everything lives in `index.html` — styles are in the `<style>` block at the top.
Brand color is the `--primary` / `--primary-bright` CSS variables; swap those to
re-theme the whole page.
