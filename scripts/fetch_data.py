import json, os, math, time, urllib.request, random
from datetime import datetime, timezone

try:
    import yfinance as yf
except Exception:
    os.system("pip install yfinance --quiet")
    import yfinance as yf

# ---------- constants ----------
NOW = datetime.now(timezone.utc)
CURRENT_YEAR = NOW.year
LATEST_YEAR = CURRENT_YEAR - 1
COMPLETED = list(range(LATEST_YEAR - 4, LATEST_YEAR + 1))
ALL_YEARS = COMPLETED + [CURRENT_YEAR]

print(f"FA Dashboard fetch – {NOW.strftime('%Y-%m-%d %H:%M UTC')}", flush=True)
print(f"Years: {ALL_YEARS}", flush=True)

FISCAL_YEAR_END = {
    "BHP":6,"WDS":12,"CBA":6,
    "BBRI":12,"ADRO":12,"SMSM":12,"UNTR":12,
    "ITMG":12,"POWR":12,"MPMX":12,"BTPS":12,"DMAS":12,"SPTO":12,
    "TSM":12,"V":9,"MA":12,
    "MSFT":6,"AMZN":12,"AAPL":9,"META":12,"NVDA":1,
    "GOOG":12,"BKNG":12,
    "PBR-A":12,
}

STOCKS = {
    "BHP":  ("BHP Group",               "ASX",    "BHP.AX",  "B AUD", 1e9,  "USD"),
    "WDS":  ("Woodside Energy",         "ASX",    "WDS.AX",  "B AUD", 1e9,  "USD"),
    "CBA":  ("Commonwealth Bank",       "ASX",    "CBA.AX",  "B AUD", 1e9,  "AUD"),
    "BBRI": ("Bank Rakyat Indonesia",   "IDX",    "BBRI.JK", "T IDR", 1e12, "IDR"),
    "ADRO": ("Adaro Energy",            "IDX",    "ADRO.JK", "T IDR", 1e12, "USD"),
    "SMSM": ("Selamat Sempurna",        "IDX",    "SMSM.JK", "T IDR", 1e12, "IDR"),
    "UNTR": ("United Tractors",         "IDX",    "UNTR.JK", "T IDR", 1e12, "IDR"),
    "ITMG": ("Indo Tambangraya Megah",  "IDX",    "ITMG.JK", "T IDR", 1e12, "USD"),
    "POWR": ("Cikarang Listrindo",      "IDX",    "POWR.JK", "T IDR", 1e12, "USD"),
    "MPMX": ("Mitra Pinasthika Mustika","IDX",    "MPMX.JK", "T IDR", 1e12, "IDR"),
    "BTPS": ("Bank BTPN Syariah",       "IDX",    "BTPS.JK", "T IDR", 1e12, "IDR"),
    "DMAS": ("Puradelta Lestari",       "IDX",    "DMAS.JK", "T IDR", 1e12, "IDR"),
    "SPTO": ("Surya Toto Indonesia",    "IDX",    "SPTO.JK", "T IDR", 1e12, "IDR"),
    "TSM":  ("Taiwan Semiconductor",   "NYSE",   "TSM",     "B USD", 1e9,  "USD"),
    "V":    ("Visa Inc.",              "NYSE",   "V",       "B USD", 1e9,  "USD"),
    "MA":   ("Mastercard Inc.",        "NYSE",   "MA",      "B USD", 1e9,  "USD"),
    "PBR-A":("Petrobras Pref ADR",     "NYSE",   "PBR-A",   "B USD", 1e9,  "USD"),
    "MSFT": ("Microsoft Corp.",        "NASDAQ", "MSFT",    "B USD", 1e9,  "USD"),
    "AMZN": ("Amazon.com Inc.",        "NASDAQ", "AMZN",    "B USD", 1e9,  "USD"),
    "AAPL": ("Apple Inc.",             "NASDAQ", "AAPL",    "B USD", 1e9,  "USD"),
    "META": ("Meta Platforms Inc.",    "NASDAQ", "META",    "B USD", 1e9,  "USD"),
    "NVDA": ("NVIDIA Corporation",     "NASDAQ", "NVDA",    "B USD", 1e9,  "USD"),
    "GOOG": ("Alphabet Inc (Google)",  "NASDAQ", "GOOG",    "B USD", 1e9,  "USD"),
    "BKNG": ("Booking Holdings Inc",   "NASDAQ", "BKNG",    "B USD", 1e9,  "USD"),
}

FIELDS = ["totalAsset","cash","totalDebt","totalEquity","revenue","grossProfit","netProfit","eps","dps"]

# ---------- exchange rates ----------
def get_rates():
    usd_aud, usd_idr, twd_usd = 1.58, 16300, 0.031
    try:
        h = yf.Ticker("AUDUSD=X").history(period="2d")
        if not h.empty:
            v = float(h["Close"].iloc[-1])
            if 0.50 < v < 0.95: usd_aud = round(1.0/v, 6)
        print(f"  USD→AUD: {usd_aud:.4f}", flush=True)
    except Exception as e:
        print(f"  USD→AUD fallback ({e})", flush=True)
    try:
        h = yf.Ticker("IDR=X").history(period="2d")
        if not h.empty:
            v = float(h["Close"].iloc[-1])
            if 10000 < v < 25000: usd_idr = round(v, 0)
        print(f"  USD→IDR: {usd_idr:.0f}", flush=True)
    except Exception as e:
        print(f"  USD→IDR fallback ({e})", flush=True)
    try:
        h = yf.Ticker("TWDUSD=X").history(period="2d")
        if not h.empty:
            v = float(h["Close"].iloc[-1])
            if 0.01 < v < 0.10: twd_usd = round(v, 6)
        print(f"  TWD→USD: {twd_usd:.5f}", flush=True)
    except Exception as e:
        print(f"  TWD→USD fallback ({e})", flush=True)
    return usd_aud, usd_idr, twd_usd

def detect_cur(tk, hint):
    try:
        info = tk.info
        fc = (info.get("financialCurrency") or info.get("currency") or hint).upper()
        return fc
    except Exception:
        return hint.upper()

def get_fx(exchange, fin_cur, usd_aud, usd_idr, twd_usd):
    if exchange == "ASX":
        return 1e9, (usd_aud if fin_cur == "USD" else 1.0)
    elif exchange == "IDX":
        return 1e12, (usd_idr if fin_cur == "USD" else 1.0)
    else:
        return 1e9, (twd_usd if fin_cur == "TWD" else 1.0)

def eps_fx(exchange, fin_cur, usd_aud, usd_idr, twd_usd):
    if exchange == "ASX": return usd_aud if fin_cur == "USD" else 1.0
    if exchange == "IDX": return usd_idr if fin_cur == "USD" else 1.0
    return twd_usd if fin_cur == "TWD" else 1.0

def safe(val, div=1, fx=1.0):
    if val is None: return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f): return None
        return round(f/div*fx, 4)
    except Exception: return None

def find_row(df, *names):
    for n in names:
        if n in df.index: return df.loc[n]
    return None

def col_yr(df, yr):
    if df is None or df.empty: return None
    best = None
    for c in df.columns:
        try:
            if hasattr(c, "year") and c.year == yr:
                if best is None or c > best: best = c
        except Exception: pass
    return best

def cols_yr(df, yr):
    if df is None or df.empty: return []
    return sorted([c for c in df.columns if hasattr(c,"year") and c.year==yr])

def sum_q(series, cols):
    if series is None: return None
    total=0.0; found=False
    for c in cols:
        v=safe(series[c])
        if v is not None: total+=v; found=True
    return total if found else None

def annual_row(inc, bs, cf, yr, div, fx, epsfx, sym=""):
    row = {}
    ic = col_yr(inc, yr)
    bc = col_yr(bs, yr)
    cc = col_yr(cf, yr)

    if ic is not None:
        rv = find_row(inc,"Total Revenue","TotalRevenue","Interest Income","InterestIncome")
        gp = find_row(inc,"Gross Profit","GrossProfit","Net Interest Income","NetInterestIncome")
        ni = find_row(inc,"Net Income","NetIncome","Net Income Common Stockholders")
        ep = find_row(inc,"Basic EPS","BasicEPS","Diluted EPS","EPS Diluted")
        sh = find_row(inc,"Basic Average Shares","BasicAverageShares","Diluted Average Shares","Average Dilution Earnings")

        rev_val = safe(rv[ic] if rv is not None else None, div, fx)
        eps_val = safe(ep[ic] if ep is not None else None, 1, epsfx)

        if yr == LATEST_YEAR and rev_val is not None and eps_val is None:
            fy_end = FISCAL_YEAR_END.get(sym, 12)
            if ic.month != fy_end:
                print(f"    ⚠ {sym} yr={yr}: col={ic.date()} FY_end={fy_end} → TTM, skip", flush=True)
                row.update(revenue=None,grossProfit=None,netProfit=None,eps=None,_sh=None,
                           totalAsset=None,cash=None,totalDebt=None,totalEquity=None,dps=None)
                return row

        row["revenue"]     = rev_val
        row["grossProfit"] = safe(gp[ic] if gp is not None else None, div, fx)
        row["netProfit"]   = safe(ni[ic] if ni is not None else None, div, fx)
        row["eps"]         = eps_val
        row["_sh"]         = safe(sh[ic] if sh is not None else None)
    else:
        row.update(revenue=None,grossProfit=None,netProfit=None,eps=None,_sh=None)

    if bc is not None:
        ta = find_row(bs,"Total Assets","TotalAssets")
        ca = find_row(bs,"Cash And Cash Equivalents","Cash","CashAndCashEquivalents","Cash And Short Term Investments")
        td = find_row(bs,"Total Debt","TotalDebt","Long Term Debt And Capital Lease Obligation","Long Term Debt")
        te = find_row(bs,"Stockholders Equity","Total Stockholder Equity","Common Stock Equity","Total Equity Gross Minority Interest")
        row["totalAsset"]  = safe(ta[bc] if ta is not None else None, div, fx)
        row["cash"]        = safe(ca[bc] if ca is not None else None, div, fx)
        row["totalDebt"]   = safe(td[bc] if td is not None else None, div, fx)
        row["totalEquity"] = safe(te[bc] if te is not None else None, div, fx)
    else:
        row.update(totalAsset=None,cash=None,totalDebt=None,totalEquity=None)

    if cc is not None and row.get("_sh"):
        dp = find_row(cf,"Cash Dividends Paid","Dividends Paid","Common Stock Dividend Paid","Payment Of Dividends")
        dv = safe(dp[cc] if dp is not None else None)
        sh = row["_sh"]
        row["dps"] = round(abs(dv)/sh*epsfx, 4) if dv and sh and sh > 0 else None
    else:
        row["dps"] = None
    return row

def current_year_row(tk, yr, div, fx, epsfx):
    ann = {"method":"none","label":None,"quarters":0,"asOf":None}
    row = {f:None for f in FIELDS}
    try:
        ai=tk.financials; ab=tk.balance_sheet; ac=tk.cashflow
        if ai is not None and not ai.empty and col_yr(ai,yr) is not None:
            r = annual_row(ai, ab, ac, yr, div, fx, epsfx)
            r.pop("_sh",None)
            ic = col_yr(ai,yr)
            return r, {"method":"full_year","label":"FY","quarters":4,"asOf":str(ic.date())}

        qi=tk.quarterly_financials; qb=tk.quarterly_balance_sheet; qc=tk.quarterly_cashflow
        if qi is None or qi.empty: return row, ann
        qtrs=cols_yr(qi,yr)
        if not qtrs: return row, ann
        n=len(qtrs); months=n*3; factor=12.0/months; lq=qtrs[-1]
        label="FY" if months>=12 else f"{months}M x{int(factor) if factor==int(factor) else round(factor,3)}"

        rv=find_row(qi,"Total Revenue","TotalRevenue","Interest Income","InterestIncome")
        gp=find_row(qi,"Gross Profit","GrossProfit","Net Interest Income","NetInterestIncome")
        ni=find_row(qi,"Net Income","NetIncome","Net Income Common Stockholders")
        ep=find_row(qi,"Basic EPS","BasicEPS","Diluted EPS","EPS Diluted")
        sh=find_row(qi,"Basic Average Shares","BasicAverageShares","Diluted Average Shares","Average Dilution Earnings")

        af=lambda s: round(sum_q(s,qtrs)/div*fx*factor,4) if sum_q(s,qtrs) is not None else None
        ae=lambda s: round(sum_q(s,qtrs)*epsfx*factor,4) if sum_q(s,qtrs) is not None else None

        row["revenue"]=af(rv); row["grossProfit"]=af(gp); row["netProfit"]=af(ni); row["eps"]=ae(ep)
        sh_val=safe(sh[lq]) if sh is not None else None

        qbc=col_yr(qb,yr) if qb is not None and not qb.empty else None
        if qbc is not None:
            ta=find_row(qb,"Total Assets","TotalAssets")
            ca=find_row(qb,"Cash And Cash Equivalents","Cash","CashAndCashEquivalents","Cash And Short Term Investments")
            td=find_row(qb,"Total Debt","TotalDebt","Long Term Debt And Capital Lease Obligation","Long Term Debt")
            te=find_row(qb,"Stockholders Equity","Total Stockholder Equity","Common Stock Equity","Total Equity Gross Minority Interest")
            row["totalAsset"]=safe(ta[qbc] if ta is not None else None,div,fx)
            row["cash"]=safe(ca[qbc] if ca is not None else None,div,fx)
            row["totalDebt"]=safe(td[qbc] if td is not None else None,div,fx)
            row["totalEquity"]=safe(te[qbc] if te is not None else None,div,fx)

        if qc is not None and not qc.empty and sh_val:
            cq=cols_yr(qc,yr)
            dp=find_row(qc,"Cash Dividends Paid","Dividends Paid","Common Stock Dividend Paid","Payment Of Dividends")
            ytd=sum_q(dp,cq)
            row["dps"]=round(abs(ytd)/sh_val*epsfx*factor,4) if ytd and sh_val>0 else None

        ann={"method":"annualised","label":label,"quarters":n,"months":months,"factor":round(factor,4),"asOf":str(lq.date())}
        print(f"      CY{yr}: {n}Q → {label} as of {lq.date()}", flush=True)
    except Exception as e:
        print(f"      CY{yr} error: {e}", flush=True)
    return row, ann

def fetch_one(sym, exchange, ticker_str, hint_cur, usd_aud, usd_idr, twd_usd):
    print(f"\n[{sym}] {ticker_str}", flush=True)
    for attempt in range(2):
        try:
            if attempt > 0:
                print(f"  Retry {attempt}...", flush=True)
                time.sleep(5)
            tk = yf.Ticker(ticker_str)
            fin_cur = detect_cur(tk, hint_cur)
            div, fx = get_fx(exchange, fin_cur, usd_aud, usd_idr, twd_usd)
            epsfx   = eps_fx(exchange, fin_cur, usd_aud, usd_idr, twd_usd)
            print(f"  cur={fin_cur} fx={fx:.6f} epsfx={epsfx:.6f}", flush=True)

            inc=tk.financials; bs=tk.balance_sheet; cf=tk.cashflow
            if inc is None or inc.empty: raise ValueError("no annual data")

            yd={}
            for yr in COMPLETED:
                r=annual_row(inc,bs,cf,yr,div,fx,epsfx,sym)
                r.pop("_sh",None); yd[yr]=r

            cy,ann=current_year_row(tk,CURRENT_YEAR,div,fx,epsfx)
            yd[CURRENT_YEAR]=cy
            live=[y for y in COMPLETED if yd[y].get("revenue") is not None]
            print(f"  ✓ live: {live}", flush=True)
            return yd, ann
        except Exception as e:
            print(f"  FAIL (attempt {attempt+1}): {e}", flush=True)
    return None, {"method":"none","label":None}

def build_arrays(yd, fb):
    out={}
    for f in FIELDS:
        arr=[]
        for i,yr in enumerate(ALL_YEARS):
            lv=yd[yr].get(f) if yd and yr in yd else None
            fv=fb[f][i] if fb and f in fb and i<len(fb[f]) else None
            arr.append(lv if lv is not None else fv)
        out[f]=arr
    return out

# ---------- AI generation (Gemini / Anthropic) with rich financial context ----------
def call_anthropic(prompt, api_key, max_tokens=2500):
    try:
        import urllib.request, json as jsonlib
        body = jsonlib.dumps({
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = jsonlib.loads(resp.read())
            return data["content"][0]["text"]
    except Exception as e:
        print(f"  Anthropic API error: {e}", flush=True)
        return None

def call_gemini(prompt, api_key, max_tokens=2500):
    try:
        import urllib.request, json as jsonlib
        model = "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        body = jsonlib.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.2}
        }).encode()
        req = urllib.request.Request(url, data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = jsonlib.loads(resp.read())
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            return "".join(p.get("text","") for p in parts) or None
    except Exception as e:
        print(f"  Gemini API error: {e}", flush=True)
        return None

def build_ai_prompt(sym, name, exchange, ticker, metrics):
    """Build a detailed prompt with company-specific financial metrics."""
    return f"""You are a professional equity analyst. Write a comprehensive, deep-dive investment analysis for {name} ({ticker}, {exchange}).

First, here are the company's key financial metrics (based on actual data):
- Revenue CAGR (last {len(metrics['years'])} years): {metrics['rev_cagr']}
- Net profit CAGR: {metrics['np_cagr']}
- Average gross margin: {metrics['gpm_avg']}
- Average net margin: {metrics['npm_avg']}
- Average ROE: {metrics['roe_avg']}
- Average debt/equity: {metrics['de_avg']}
- Average cash/assets: {metrics['cash_asset_avg']}
- Buffett $1 test score: {metrics['buffett']}
- Dividend payout ratio (avg): {metrics['payout_avg']}

Use the above numbers as the basis for your analysis. Also incorporate your knowledge of the company's business model, industry trends, recent news, and strategic moves.

Your analysis must contain the following sections with clear headings. Be specific, detailed, and factual. Avoid generic statements.

## Business Model Canvas
Fill all nine blocks with concrete, company-specific information:
- Key Partners
- Key Activities
- Key Resources
- Value Proposition
- Customer Relationships
- Channels
- Customer Segments
- Cost Structure
- Revenue Streams

## SWOT Analysis
List at least 4 points for each category (Strengths, Weaknesses, Opportunities, Threats). Base strengths/weaknesses on the financial metrics above and known operational factors. Opportunities/threats should be industry and company-specific.

## PESTLE Analysis
Write a detailed paragraph for each letter (Political, Economic, Social, Technological, Legal, Environmental). Connect each factor to the company's operations and outlook.

## Porter's Five Forces
Analyse each force in depth:
- Competitive Rivalry (main competitors, industry concentration)
- Threat of New Entrants (barriers to entry)
- Supplier Power (key inputs, bargaining power)
- Buyer Power (customer concentration, switching costs)
- Threat of Substitutes (alternative products/services)

## Management & Decision Making
Discuss:
- Capital allocation philosophy (dividends, buybacks, debt, M&A)
- Recent strategic decisions (major projects, acquisitions, divestments)
- Quality of management (based on track record and Buffett test score)

## Future Outlook
Provide a 3-5 year outlook including:
- Key growth drivers
- Major risks
- What investors should watch

Write in a professional, analytical tone. Use specific numbers from the metrics above where relevant. The analysis should be tailored to {name} and its sector ({exchange})."""

def generate_ai_content(all_stocks, out, api_key, all_metrics):
    if not api_key:
        print("\nNo API key found — skipping AI content.", flush=True)
        return

    is_gemini = api_key.startswith("AIza")
    provider = "Gemini" if is_gemini else "Anthropic Claude Haiku"
    call_fn = call_gemini if is_gemini else call_anthropic
    print(f"\n{'='*50}\nGenerating AI profiles & news via {provider} ({len(all_stocks)} stocks)...\n{'='*50}", flush=True)

    for sym, (name, exchange, ticker, *_) in all_stocks.items():
        metrics = all_metrics.get(sym)
        if not metrics:
            print(f"  [{sym}] No metrics available, skipping", flush=True)
            continue

        prompt = build_ai_prompt(sym, name, exchange, ticker, metrics)
        print(f"  [{sym}] generating analysis...", flush=True)

        # Call AI once for the entire analysis (profile)
        profile = call_fn(prompt, api_key, max_tokens=3000)
        if profile:
            out["stocks"][sym]["profile"] = profile
            out["stocks"][sym]["profileDate"] = NOW.isoformat()
        else:
            print(f"  [!] No profile for {sym}", flush=True)

        # Small delay to avoid rate limits
        time.sleep(random.uniform(0.8, 1.5))

        # Also generate a news summary (shorter prompt)
        news_prompt = f"""Summarize the 5 most recent important fundamental business developments for {name} ({ticker}, {exchange}).

For each, use exactly:
## [Headline]
**Date:** [period]  **Relevance:** [Bullish/Bearish/Neutral]
[2-3 sentences on what happened and why it matters for long-term investors]

Focus on: earnings, revenue changes, strategy, acquisitions, dividends, regulations. Skip pure price news."""
        print(f"  [{sym}] news...", flush=True)
        news = call_fn(news_prompt, api_key, max_tokens=1500)
        if news:
            out["stocks"][sym]["news"] = news
            out["stocks"][sym]["newsDate"] = NOW.isoformat()
        else:
            print(f"  [!] No news for {sym}", flush=True)

        time.sleep(random.uniform(0.8, 1.5))

    print(f"AI content generation complete via {provider}.", flush=True)

# ---------- main ----------
def main():
    usd_aud, usd_idr, twd_usd = get_rates()
    all_stocks = {**STOCKS}
    print(f"\nTotal stocks: {len(all_stocks)}\n{'='*50}", flush=True)

    out = {
        "generated": NOW.isoformat(),
        "years": ALL_YEARS, "completedYears": COMPLETED,
        "currentYear": CURRENT_YEAR, "latestYear": LATEST_YEAR,
        "rates": {"usdToAud":usd_aud,"usdToIdr":usd_idr,"twdToUsd":twd_usd,
                  "audToUsd":round(1.0/usd_aud,6),"idrToUsd":round(1.0/usd_idr,9)},
        "fiscalYearEnd": FISCAL_YEAR_END,
        "annualisation": {}, "stocks": {}
    }

    # First fetch financial data and store metrics
    ok = 0
    all_metrics = {}
    for i, (sym, (name, exchange, ticker_str, currency, _div, hint_cur)) in enumerate(all_stocks.items()):
        if i > 0:
            time.sleep(1)
        yd, ann = fetch_one(sym, exchange, ticker_str, hint_cur, usd_aud, usd_idr, twd_usd)
        # Fallback data to fill missing years (especially 2021)
        fb = {}
        # We'll use a simple fallback: if revenue for 2021 is missing, we keep None (dashboard will show N/A)
        # The user has preloaded data in the HTML, so it's fine.
        arrs = build_arrays(yd, fb)
        src = "yfinance" if yd else "fallback"
        if yd:
            ok += 1
        out["stocks"][sym] = {
            "name": name, "exchange": exchange, "currency": currency,
            "ticker": ticker_str, "source": src, "fyEndMonth": FISCAL_YEAR_END.get(sym, 12)
        }
        out["stocks"][sym].update(arrs)
        out["annualisation"][sym] = ann

        # Compute metrics for AI prompt
        # We need to compute CAGR and averages from the arrays
        rev_arr = arrs.get("revenue", [])
        np_arr = arrs.get("netProfit", [])
        gp_arr = arrs.get("grossProfit", [])
        ep_arr = arrs.get("eps", [])
        ta_arr = arrs.get("totalAsset", [])
        ca_arr = arrs.get("cash", [])
        te_arr = arrs.get("totalEquity", [])
        td_arr = arrs.get("totalDebt", [])
        dp_arr = arrs.get("dps", [])

        # Helper to filter valid numbers
        valid = lambda arr: [v for v in arr if v is not None and v != 0]
        rev_valid = valid(rev_arr)
        np_valid = valid(np_arr)
        gp_valid = valid(gp_arr)
        ep_valid = valid(ep_arr)

        def cagr(arr):
            if len(arr) < 2:
                return "N/A"
            start = arr[0]
            end = arr[-1]
            years = len(arr) - 1
            if start <= 0 or end <= 0:
                return "N/A"
            return f"{(pow(end/start, 1/years)-1)*100:.1f}%"

        def avg(arr):
            if not arr:
                return "N/A"
            return f"{sum(arr)/len(arr):.1f}%"

        def avg_ratio(arr_num, arr_den):
            ratios = []
            for n, d in zip(arr_num, arr_den):
                if n is not None and d is not None and d != 0:
                    ratios.append(n/d * 100)
            if not ratios:
                return "N/A"
            return f"{sum(ratios)/len(ratios):.1f}%"

        # Buffett test: we already have it from calcM, but we don't have calcM here.
        # We'll compute a simple version: total retained EPS / EPS increase
        # For simplicity, we'll skip if not available.
        buffett = "N/A"
        # We'll compute from eps and dps arrays
        if len(ep_valid) >= 2:
            eps_start = ep_valid[0]
            eps_end = ep_valid[-1]
            eps_inc = eps_end - eps_start
            # Sum of retained EPS (EPS - DPS) over the period
            # We need aligned arrays
            ret_sum = 0
            count = 0
            for e, d in zip(ep_arr, dp_arr):
                if e is not None and d is not None:
                    ret_sum += (e - d)
                    count += 1
            if count > 0 and ret_sum != 0:
                buffett = f"{(eps_inc / ret_sum * 100):.1f}%"

        metrics = {
            "years": len(rev_valid),
            "rev_cagr": cagr(rev_valid),
            "np_cagr": cagr(np_valid),
            "gpm_avg": avg_ratio(gp_arr, rev_arr),
            "npm_avg": avg_ratio(np_arr, rev_arr),
            "roe_avg": avg_ratio(np_arr, te_arr),
            "de_avg": avg_ratio(td_arr, te_arr),
            "cash_asset_avg": avg_ratio(ca_arr, ta_arr),
            "payout_avg": avg_ratio(dp_arr, ep_arr),
            "buffett": buffett
        }
        all_metrics[sym] = metrics

    # Now generate AI content using the collected metrics
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if api_key:
        generate_ai_content(all_stocks, out, api_key, all_metrics)
    else:
        print("No API key found – skipping AI generation.", flush=True)

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n{'='*50}\nWritten: {path}\nLive yfinance: {ok}/{len(all_stocks)}\n{'='*50}", flush=True)

if __name__ == "__main__":
    main()
