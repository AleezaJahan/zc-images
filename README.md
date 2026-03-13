# Zero Collective Image Pipeline

This repo contains:

- `scrape_zc.py` to scrape product data into `zero_collective_products.csv`
- `generate_bag_images.py` to generate lifestyle/editorial bag images with Gemini
- `generate_batches.py` to process batches and sync status to Supabase
- `dashboard/index.html` as the lightweight review dashboard for Vercel

## Environment variables

Create a local `.env` file with:

```bash
GEMINI_API_KEY=...
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
```

## Install

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install
```

## Deploy dashboard to Vercel

Set the Vercel project root to `dashboard/` so it serves `index.html` as a static site.
