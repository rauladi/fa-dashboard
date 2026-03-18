import json, os, math
from datetime import datetime, timezone

try:
    import yfinance as yf
except Exception:
    os.system("pip install yfinance --quiet")
    import yfinance as yf

NOW          = datetime.now(timezone.utc)
CURRENT_YEAR = NOW.year
LATEST_YEAR  = CURRENT_YEAR - 1
COMPLETED    = list(range(LATEST_YEAR - 4, LATEST_YEAR + 1))
ALL_YEARS    = COMPLETED + [CURRENT_YEAR]

# ── Stock definitions ─────────────────────────────────────────────────
# IMPORTANT: yfinance Python library returns FULL raw numbers (not thousands).
# The Yahoo Finance website shows "All numbers in thousands" — that is a
# website display label only. The API/yfinance returns actual values.
#
# Therefore divisors to reach display units:
#   ASX (USD) : ÷ 1e9  → USD billions → × USD_to_AUD → AUD billions (B AUD)
#   IDX (IDR) : ÷ 1e12 → IDR trillions (T IDR)
#
# EPS: yfinance returns per-share in reporting currency (NOT divided by anything)
#      ASX: USD/share × fx = AUD/share
#      IDX: IDR/share — no conversion
#
# DPS (derived from cashflow): both dividendsPaid and sharesOutstanding are
#      full raw numbers from yfinance, so:
#      DPS = |dividendsPaid| / sharesOutstanding × fx
#
# Format: sym: (name, exchange, yf_ticker, display_currency, divisor, report_cur)

STOCKS = {
    "BHP":  ("BHP Group",               "ASX", "BHP.AX",  "B AUD", 1e9,  "USD"),
    "WDS":  ("Woodside Energy",          "ASX", "WDS.AX",  "B AUD", 1e9,  "USD"),
    "BBRI": ("Bank Rakyat Indonesia",    "IDX", "BBRI.JK", "T IDR", 1e12, "IDR"),
    "ADRO": ("Adaro Energy",             "IDX", "ADRO.JK", "T IDR", 1e12, "IDR"),
    "SMSM": ("Selamat Sempurna",         "IDX", "SMSM.JK", "T IDR", 1e12, "IDR"),
    "UNTR": ("United Tractors",          "IDX", "UNTR.JK", "T IDR", 1e12, "IDR"),
    "ITMG": ("Indo Tambangraya Megah",   "IDX", "ITMG.JK", "T IDR", 1e12, "IDR"),
    "POWR": ("Cikarang Listrindo",       "IDX", "POWR.JK", "T IDR", 1e12, "IDR"),
    "MPMX": ("Mitra Pinasthika Mustika", "IDX", "MPMX.JK", "T IDR", 1e12, "IDR"),
    "BTPS": ("Bank BTPN Syariah",        "IDX", "BTPS.JK", "T IDR", 1e12, "IDR"),
    "DMAS": ("Puradelta Lestari",        "IDX", "DMAS.JK", "T IDR", 1e12, "IDR"),
    "SPTO": ("Surya Toto Indonesia",     "IDX", "SPTO.JK", "T IDR", 1e12, "IDR"),
}

# ── Fallback (display units: B AUD or T IDR) ──────────────────────────
FALLBACK = {
    "BHP":  {"totalAsset":[54.2,51.9,55.7,81.5,None,None],"cash":[14.9,12.4,13.9,13.3,None,None],"totalDebt":[14.5,12.4,14.8,26.7,None,None],"totalEquity":[26.4,28.0,29.7,32.4,None,None],"revenue":[60.8,65.1,53.8,55.7,None,None],"grossProfit":[36.2,40.5,28.3,28.5,None,None],"netProfit":[11.3,30.9,12.9,7.9,None,None],"eps":[2.21,6.05,2.55,1.55,None,None],"dps":[3.01,5.43,1.70,1.09,None,None]},
    "WDS":  {"totalAsset":[40.3,50.5,48.3,48.0,None,None],"cash":[2.8,3.1,2.5,2.2,None,None],"totalDebt":[7.9,15.2,12.8,12.0,None,None],"totalEquity":[18.2,22.4,20.1,20.0,None,None],"revenue":[10.0,13.9,12.3,12.5,None,None],"grossProfit":[5.8,8.6,7.1,7.2,None,None],"netProfit":[2.5,6.0,3.5,1.7,None,None],"eps":[0.80,1.70,1.00,0.48,None,None],"dps":[0.55,1.30,0.90,0.43,None,None]},
    "BBRI": {"totalAsset":[1635,1865,1965,2073,None,None],"cash":[163,186,196,207,None,None],"totalDebt":[1380,1570,1650,1730,None,None],"totalEquity":[255,295,315,343,None,None],"revenue":[135,150,165,187,None,None],"grossProfit":[85,95,104,118,None,None],"netProfit":[25,43,51,60,None,None],"eps":[1019,1753,2086,2443,None,None],"dps":[460,791,940,1100,None,None]},
    "ADRO": {"totalAsset":[80,100,85,92,None,None],"cash":[10,20,15,16,None,None],"totalDebt":[18,25,18,16,None,None],"totalEquity":[58,72,62,68,None,None],"revenue":[65,120,80,85,None,None],"grossProfit":[24,55,35,38,None,None],"netProfit":[8,30,15,16,None,None],"eps":[256,960,480,510,None,None],"dps":[130,480,240,255,None,None]},
    "SMSM": {"totalAsset":[2.6,2.8,3.0,3.2,None,None],"cash":[0.9,1.0,1.1,1.2,None,None],"totalDebt":[0.35,0.30,0.30,0.25,None,None],"totalEquity":[2.0,2.2,2.4,2.6,None,None],"revenue":[2.5,2.8,3.2,3.4,None,None],"grossProfit":[0.82,0.92,1.05,1.12,None,None],"netProfit":[0.43,0.51,0.58,0.62,None,None],"eps":[183,217,247,264,None,None],"dps":[138,164,186,198,None,None]},
    "UNTR": {"totalAsset":[118,130,138,145,None,None],"cash":[16,18,20,22,None,None],"totalDebt":[23,20,18,16,None,None],"totalEquity":[78,88,97,105,None,None],"revenue":[108,125,130,135,None,None],"grossProfit":[25,30,32,33,None,None],"netProfit":[13,16,17,18,None,None],"eps":[3510,4320,4590,4860,None,None],"dps":[1580,1944,2065,2187,None,None]},
    "ITMG": {"totalAsset":[19,26,20,21,None,None],"cash":[6,12,8,7,None,None],"totalDebt":[0.8,1.0,0.8,0.7,None,None],"totalEquity":[16,22,17,18,None,None],"revenue":[36,65,42,45,None,None],"grossProfit":[10,25,14,13,None,None],"netProfit":[5,16,8,7,None,None],"eps":[4530,14493,7246,6344,None,None],"dps":[4000,13000,6500,5710,None,None]},
    "POWR": {"totalAsset":[9.5,10.0,10.5,11.0,None,None],"cash":[1.3,1.4,1.5,1.6,None,None],"totalDebt":[2.0,1.8,1.6,1.4,None,None],"totalEquity":[5.8,6.5,7.2,7.8,None,None],"revenue":[5.0,5.2,5.5,5.8,None,None],"grossProfit":[2.0,2.1,2.2,2.3,None,None],"netProfit":[0.95,1.00,1.10,1.15,None,None],"eps":[95,100,110,115,None,None],"dps":[57,60,66,69,None,None]},
    "MPMX": {"totalAsset":[9.0,9.5,10.0,10.5,None,None],"cash":[1.5,1.6,1.7,1.8,None,None],"totalDebt":[2.4,2.2,2.0,1.8,None,None],"totalEquity":[4.8,5.3,5.8,6.3,None,None],"revenue":[12.5,13.0,13.5,14.0,None,None],"grossProfit":[2.1,2.2,2.3,2.4,None,None],"netProfit":[0.40,0.45,0.50,0.55,None,None],"eps":[93,105,116,128,None,None],"dps":[40,45,50,55,None,None]},
    "BTPS": {"totalAsset":[24,27,30,32,None,None],"cash":[2.4,2.7,3.0,3.2,None,None],"totalDebt":[19,21,23.5,25,None,None],"totalEquity":[5.0,6.0,6.5,7.0,None,None],"revenue":[7.0,8.0,9.0,9.5,None,None],"grossProfit":[4.2,4.8,5.4,5.7,None,None],"netProfit":[1.2,1.8,2.0,2.1,None,None],"eps":[413,557,618,650,None,None],"dps":[124,167,185,195,None,None]},
    "DMAS": {"totalAsset":[7.0,7.5,8.0,8.5,None,None],"cash":[1.8,2.0,2.2,2.4,None,None],"totalDebt":[1.0,0.9,0.8,0.7,None,None],"totalEquity":[5.5,6.0,6.5,7.0,None,None],"revenue":[1.8,2.2,2.8,2.5,None,None],"grossProfit":[1.2,1.6,2.0,1.8,None,None],"netProfit":[0.7,0.9,1.1,1.0,None,None],"eps":[35,45,55,50,None,None],"dps":[24,32,38,35,None,None]},
    "SPTO": {"totalAsset":[2.6,2.7,2.8,2.9,None,None],"cash":[0.32,0.35,0.38,0.40,None,None],"totalDebt":[0.70,0.65,0.60,0.55,None,None],"totalEquity":[1.55,1.70,1.85,1.98,None,None],"revenue":[1.9,2.0,2.1,2.2,None,None],"grossProfit":[0.69,0.73,0.77,0.80,None,None],"netProfit":[0.25,0.27,0.30,0.32,None,None],"eps":[278,300,333,356,None,None],"dps":[139,150,167,178,None,None]},
}

FIELDS = ["totalAsset","cash","totalDebt","totalEquity","revenue","grossProfit","netProfit","eps","dps"]

# ── Live USD→AUD rate ─────────────────────────────────────────────────
def get_usd_to_aud():
    fallback = 1.58
    try:
        hist = yf.Ticker("AUDUSD=X").history(period="2d")
        if not hist.empty:
            audusd = float(hist["Close"].iloc[-1])
            if 0.50 < audusd < 0.90:
                rate = round(1.0 / audusd, 6)
                print(f"  Live rate: 1 AUD = {audusd:.4f} USD → 1 USD = {rate:.4f} AUD", flush=True)
                return rate
    except Exception as e:
        print(f"  Rate error: {e}", flush=True)
    print(f"  Fallback: 1 USD = {fallback} AUD", flush=True)
    return fallback

# ── Helpers ───────────────────────────────────────────────────────────
def safe(val, div=1, fx=1.0):
    if val is None: return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f): return None
        return round(f / div * fx, 4)
    except Exception: return None

def find_row(df, *names):
    for n in names:
        if n in df.index: return df.loc[n]
    return None

def col_yr(df, yr):
    if df is None or df.empty: return None
    for c in df.columns:
        try:
            if hasattr(c, "year") and c.year == yr: return c
        except Exception: pass
    return None

def cols_yr(df, yr):
    if df is None or df.empty: return []
    out = [c for c in df.columns if hasattr(c, "year") and c.year == yr]
    return sorted(out)

def sum_q(series, cols):
    if series is None: return None
    total = 0.0; found = False
    for c in cols:
        v = safe(series[c])
        if v is not None: total += v; found = True
    return total if found else None

# ── Build one annual year's data row ─────────────────────────────────
def annual_row(inc, bs, cf, yr, div, fx):
    """
    div: 1e9 for ASX (USD→B USD), 1e12 for IDX (IDR→T IDR)
    fx : USD_to_AUD for ASX, 1.0 for IDX
    Financial statement line items: raw full numbers → ÷div → ×fx = display units
    EPS: already per-share in report currency → ×fx only (no ÷div)
    DPS: |cashDividendsPaid_raw| ÷ sharesOutstanding_raw → ×fx (both are full numbers, cancel)
    """
    row = {}
    ic = col_yr(inc, yr); bc = col_yr(bs, yr); cc = col_yr(cf, yr)

    if ic is not None:
        rv = find_row(inc, "Total Revenue", "TotalRevenue")
        gp = find_row(inc, "Gross Profit", "GrossProfit")
        ni = find_row(inc, "Net Income", "NetIncome",
                      "Net Income Common Stockholders",
                      "Net Income Including Noncontrolling Interests")
        ep = find_row(inc, "Basic EPS", "BasicEPS", "Diluted EPS", "EPS Diluted")
        sh = find_row(inc, "Basic Average Shares", "BasicAverageShares",
                      "Diluted Average Shares", "Average Dilution Earnings")
        row["revenue"]     = safe(rv[ic] if rv is not None else None, div, fx)
        row["grossProfit"] = safe(gp[ic] if gp is not None else None, div, fx)
        row["netProfit"]   = safe(ni[ic] if ni is not None else None, div, fx)
        row["eps"]         = safe(ep[ic] if ep is not None else None, 1, fx)   # per share, no div
        row["_sh"]         = safe(sh[ic] if sh is not None else None, 1, 1.0) # raw share count
    else:
        row.update(revenue=None, grossProfit=None, netProfit=None, eps=None, _sh=None)

    if bc is not None:
        ta = find_row(bs, "Total Assets", "TotalAssets")
        ca = find_row(bs, "Cash And Cash Equivalents", "Cash",
                      "CashAndCashEquivalents", "Cash And Short Term Investments")
        td = find_row(bs, "Total Debt", "TotalDebt",
                      "Long Term Debt And Capital Lease Obligation", "Long Term Debt")
        te = find_row(bs, "Stockholders Equity", "Total Stockholder Equity",
                      "Common Stock Equity", "Total Equity Gross Minority Interest")
        row["totalAsset"]  = safe(ta[bc] if ta is not None else None, div, fx)
        row["cash"]        = safe(ca[bc] if ca is not None else None, div, fx)
        row["totalDebt"]   = safe(td[bc] if td is not None else None, div, fx)
        row["totalEquity"] = safe(te[bc] if te is not None else None, div, fx)
    else:
        row.update(totalAsset=None, cash=None, totalDebt=None, totalEquity=None)

    # DPS: dividendsPaid (full raw) / shares (full raw) × fx
    if cc is not None and row.get("_sh"):
        dp = find_row(cf, "Cash Dividends Paid", "Dividends Paid",
                      "Common Stock Dividend Paid", "Payment Of Dividends")
        dv = safe(dp[cc] if dp is not None else None, 1, 1.0)  # raw
        sh = row["_sh"]
        row["dps"] = round(abs(dv) / sh * fx, 4) if dv and sh and sh > 0 else None
    else:
        row["dps"] = None
    return row

# ── Current year from quarterly data ─────────────────────────────────
def current_year_row(tk, yr, div, fx):
    ann = {"method": "none", "label": None, "quarters": 0, "asOf": None}
    row = {f: None for f in FIELDS}
    try:
        # Check if full annual already exists for current year
        ai = tk.financials; ab = tk.balance_sheet; ac = tk.cashflow
        if ai is not None and not ai.empty and col_yr(ai, yr) is not None:
            r = annual_row(ai, ab, ac, yr, div, fx); r.pop("_sh", None)
            ic = col_yr(ai, yr)
            return r, {"method":"full_year","label":"FY","quarters":4,"asOf":str(ic.date())}

        qi = tk.quarterly_financials
        qb = tk.quarterly_balance_sheet
        qc = tk.quarterly_cashflow
        if qi is None or qi.empty: return row, ann

        qtrs = cols_yr(qi, yr)
        if not qtrs: return row, ann

        n = len(qtrs); months = n * 3; factor = 12.0 / months; lq = qtrs[-1]
        label = "FY" if months >= 12 else \
                f"{months}M x{int(factor) if factor == int(factor) else round(factor, 3)}"

        rv = find_row(qi, "Total Revenue", "TotalRevenue")
        gp = find_row(qi, "Gross Profit", "GrossProfit")
        ni = find_row(qi, "Net Income", "NetIncome",
                      "Net Income Common Stockholders",
                      "Net Income Including Noncontrolling Interests")
        ep = find_row(qi, "Basic EPS", "BasicEPS", "Diluted EPS", "EPS Diluted")
        sh = find_row(qi, "Basic Average Shares", "BasicAverageShares",
                      "Diluted Average Shares", "Average Dilution Earnings")

        # Flow items: sum YTD (raw), ÷div ×fx ×annualisation factor
        def ann_flow(s):
            ytd = sum_q(s, qtrs)
            return round(ytd / div * fx * factor, 4) if ytd is not None else None
        # EPS: per share, sum YTD ×fx ×factor
        def ann_eps(s):
            ytd = sum_q(s, qtrs)
            return round(ytd * fx * factor, 4) if ytd is not None else None

        row["revenue"]     = ann_flow(rv)
        row["grossProfit"] = ann_flow(gp)
        row["netProfit"]   = ann_flow(ni)
        row["eps"]         = ann_eps(ep)
        sh_val = safe(sh[lq], 1, 1.0) if sh is not None else None  # raw shares

        # Balance sheet: point-in-time latest quarter, no annualisation
        qbc = col_yr(qb, yr) if qb is not None and not qb.empty else None
        if qbc is not None:
            ta = find_row(qb, "Total Assets", "TotalAssets")
            ca = find_row(qb, "Cash And Cash Equivalents", "Cash",
                          "CashAndCashEquivalents", "Cash And Short Term Investments")
            td = find_row(qb, "Total Debt", "TotalDebt",
                          "Long Term Debt And Capital Lease Obligation", "Long Term Debt")
            te = find_row(qb, "Stockholders Equity", "Total Stockholder Equity",
                          "Common Stock Equity", "Total Equity Gross Minority Interest")
            row["totalAsset"]  = safe(ta[qbc] if ta is not None else None, div, fx)
            row["cash"]        = safe(ca[qbc] if ca is not None else None, div, fx)
            row["totalDebt"]   = safe(td[qbc] if td is not None else None, div, fx)
            row["totalEquity"] = safe(te[qbc] if te is not None else None, div, fx)

        # DPS annualised: sum YTD dividends paid / shares × fx × factor
        if qc is not None and not qc.empty and sh_val:
            cq  = cols_yr(qc, yr)
            dp  = find_row(qc, "Cash Dividends Paid", "Dividends Paid",
                           "Common Stock Dividend Paid", "Payment Of Dividends")
            ytd = sum_q(dp, cq)  # raw
            row["dps"] = round(abs(ytd) / sh_val * fx * factor, 4) \
                         if ytd is not None and sh_val > 0 else None

        ann = {"method":"annualised","label":label,"quarters":n,
               "months":months,"factor":round(factor,4),"asOf":str(lq.date())}
        print(f"      CY{yr}: {n}Q → {label} (as of {lq.date()})", flush=True)

    except Exception as e:
        print(f"      CY{yr} error: {e}", flush=True)
    return row, ann

# ── Per-stock fetch ───────────────────────────────────────────────────
def fetch_one(sym, ticker_str, div, report_cur, usd_to_aud):
    print(f"\n  [{sym}] {ticker_str}", flush=True)
    fx = usd_to_aud if report_cur == "USD" else 1.0
    print(f"    yfinance returns: raw full {report_cur} values", flush=True)
    print(f"    Conversion: ÷{div:.0e} ×{fx:.4f} → display units", flush=True)
    try:
        tk  = yf.Ticker(ticker_str)
        inc = tk.financials; bs = tk.balance_sheet; cf = tk.cashflow
        if inc is None or inc.empty: raise ValueError("no annual data")

        yd = {}
        for yr in COMPLETED:
            r = annual_row(inc, bs, cf, yr, div, fx)
            r.pop("_sh", None)
            yd[yr] = r

        # Spot-check printout for last 2 completed years
        for yr in COMPLETED[-2:]:
            ta = yd[yr].get("totalAsset")
            rv = yd[yr].get("revenue")
            ep = yd[yr].get("eps")
            dp = yd[yr].get("dps")
            if ta is not None:
                print(f"      {yr}: asset={ta:.2f}  rev={rv}  eps={ep}  dps={dp}", flush=True)

        cy, ann = current_year_row(tk, CURRENT_YEAR, div, fx)
        yd[CURRENT_YEAR] = cy
        live = [y for y in COMPLETED if yd[y].get("revenue") is not None]
        print(f"    ✓ Completed years with data: {live}", flush=True)
        return yd, ann

    except Exception as e:
        print(f"    FAIL: {e}", flush=True)
        return None, {"method":"none","label":None}

def build_arrays(yd, fb):
    out = {}
    for f in FIELDS:
        arr = []
        for i, yr in enumerate(ALL_YEARS):
            lv = yd[yr].get(f) if yd and yr in yd else None
            fv = fb[f][i] if fb and i < len(fb.get(f, [])) else None
            arr.append(lv if lv is not None else fv)
        out[f] = arr
    return out

def main():
    print(f"\n{'='*60}")
    print(f"FA Dashboard Data Fetch")
    print(f"Run: {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Years: {ALL_YEARS}")
    print(f"")
    print(f"Conversion rules (yfinance returns FULL raw numbers, not thousands):")
    print(f"  ASX: raw USD ÷ 1e9 × USD→AUD = B AUD")
    print(f"  IDX: raw IDR ÷ 1e12          = T IDR")
    print(f"  EPS: raw per-share × fx       = display currency/share")
    print(f"  DPS: |divPaid_raw|/shares_raw × fx")
    print(f"{'='*60}")

    usd_to_aud = get_usd_to_aud()

    out = {
        "generated":      NOW.isoformat(),
        "years":          ALL_YEARS,
        "completedYears": COMPLETED,
        "currentYear":    CURRENT_YEAR,
        "latestYear":     LATEST_YEAR,
        "usdToAud":       usd_to_aud,
        "annualisation":  {},
        "stocks":         {},
    }

    ok = 0
    for sym, (name, exchange, ticker_str, currency, div, report_cur) in STOCKS.items():
        yd, ann = fetch_one(sym, ticker_str, div, report_cur, usd_to_aud)
        fb   = FALLBACK.get(sym, {})
        arrs = build_arrays(yd, fb)
        src  = "yfinance" if yd else "fallback"
        if yd: ok += 1
        out["stocks"][sym] = {
            "name": name, "exchange": exchange, "currency": currency,
            "ticker": ticker_str, "source": src,
        }
        out["stocks"][sym].update(arrs)
        out["annualisation"][sym] = ann

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Written: {path}")
    print(f"Live: {ok}/{len(STOCKS)}  Fallback: {len(STOCKS)-ok}/{len(STOCKS)}")
    print(f"\n--- Spot check (2 most recent completed years) ---")
    for sym in list(STOCKS.keys()):
        s  = out["stocks"].get(sym, {})
        ta = s.get("totalAsset", [])
        rv = s.get("revenue",    [])
        ep = s.get("eps",        [])
        cur= s.get("currency",   "")
        # indices -3 and -2 are the 4th and 5th completed years
        print(f"  {sym:6s} ({cur}): asset {ta[-3]}/{ta[-2]}  rev {rv[-3]}/{rv[-2]}  eps {ep[-3]}/{ep[-2]}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
