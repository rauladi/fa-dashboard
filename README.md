# FA Dashboard — Fundamental Analysis

A self-hosted fundamental analysis dashboard for ASX and IDX stocks,
with **automatic monthly data refresh** via GitHub Actions + yfinance.

## Live URL (after setup)
```
https://YOUR-USERNAME.github.io/fa-dashboard/
```

---

## One-Time Setup (5 minutes)

### Step 1 — Create the repository

1. Go to [github.com/new](https://github.com/new)
2. Name it `fa-dashboard`
3. Set to **Public** (required for free GitHub Pages)
4. Click **Create repository**

### Step 2 — Upload the files

Upload these files keeping the exact folder structure:

```
fa-dashboard/
├── index.html                          ← the dashboard
├── data.json                           ← auto-generated (first run creates it)
├── scripts/
│   └── fetch_data.py                   ← data fetcher
└── .github/
    └── workflows/
        └── refresh-data.yml            ← monthly automation
```

**How to upload:**
- On your new repo page, click **Add file → Upload files**
- Drag and drop all files (preserve the folder structure)
- Click **Commit changes**

> Tip: If you already use GitHub Desktop or VS Code with GitHub, you can clone
> and push the files that way instead.

### Step 3 — Enable GitHub Pages

1. Go to your repo → **Settings** → **Pages** (left sidebar)
2. Under **Source**, select **Deploy from a branch**
3. Select branch: `main`, folder: `/ (root)`
4. Click **Save**
5. Wait ~2 minutes, then visit `https://YOUR-USERNAME.github.io/fa-dashboard/`

### Step 4 — Run the first data fetch

1. Go to your repo → **Actions** tab
2. Click **Refresh Financial Data** in the left panel
3. Click **Run workflow → Run workflow**
4. Wait ~3 minutes for it to complete
5. Refresh your dashboard — data is now live!

---

## How Auto-Refresh Works

| What | Details |
|------|---------|
| **Schedule** | Runs on the 5th of every month at 06:00 UTC |
| **What it does** | Fetches income statement, balance sheet & cash flow via yfinance |
| **Data source** | Yahoo Finance (via yfinance Python library — free, no API key) |
| **Fallback** | If yfinance fails for a stock, the previous known values are kept |
| **Commit** | Updates `data.json` and commits it automatically |
| **Cost** | 100% free (GitHub Actions free tier: 2000 min/month) |

### Trigger a manual refresh anytime
Go to **Actions → Refresh Financial Data → Run workflow**

---

## Adding Your FOLIO Repo Integration

Since you already have a FOLIO repo at `github.com/YOUR-USERNAME/folio`,
you can either:

**Option A:** Add FA Dashboard as a page in your existing FOLIO repo
- Copy `index.html`, `data.json`, `scripts/`, and `.github/workflows/` into your FOLIO repo
- GitHub Pages will serve it at `https://YOUR-USERNAME.github.io/folio/` (rename `index.html` to `fa-dashboard.html`)
- The workflow will work the same way

**Option B:** Keep as a separate repo (recommended)
- Clean separation between portfolio tracker and fundamental analysis
- Link between them via navbar

---

## Stock Coverage

| Stock | Name | Exchange | yfinance Ticker |
|-------|------|----------|----------------|
| BHP | BHP Group | ASX | BHP.AX |
| WDS | Woodside Energy | ASX | WDS.AX |
| BBRI | Bank Rakyat Indonesia | IDX | BBRI.JK |
| ADRO | Adaro Energy | IDX | ADRO.JK |
| SMSM | Selamat Sempurna | IDX | SMSM.JK |
| UNTR | United Tractors | IDX | UNTR.JK |
| ITMG | Indo Tambangraya Megah | IDX | ITMG.JK |
| POWR | Cikarang Listrindo | IDX | POWR.JK |
| MPMX | Mitra Pinasthika Mustika | IDX | MPMX.JK |
| BTPS | Bank BTPN Syariah | IDX | BTPS.JK |
| DMAS | Puradelta Lestari | IDX | DMAS.JK |
| SPTO | Surya Toto Indonesia | IDX | SPTO.JK |

---

## Adding More Stocks

**In `scripts/fetch_data.py`:** Add to the `STOCKS` dict:
```python
"TLKM": ("Telkom Indonesia", "IDX", "TLKM.JK", "T IDR", 1e12),
```

**In `index.html`:** Add to `BASE_STOCKS`:
```javascript
TLKM: {name:"Telkom Indonesia", exchange:"IDX", currency:"T IDR"},
```

Then re-run the workflow.

---

## Troubleshooting

**Dashboard shows "Built-in data" not "Auto-refreshed"**
→ Make sure you've run the workflow at least once (Step 4 above)

**Workflow fails**
→ Check Actions tab for error logs. Most common cause: yfinance ticker not found
→ For IDX stocks, verify tickers at finance.yahoo.com (search "BBRI.JK" etc.)

**GitHub Pages not working**
→ Repo must be Public for free Pages; check Settings → Pages is configured
