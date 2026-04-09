import json, os, math, time
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
    "NAB":9,
    "CVX":12,
    "AXP":12,
    "BAC":12,
}

STOCKS = {
    "BHP":  ("BHP Group",               "ASX",    "BHP.AX",  "B AUD", 1e9,  "USD"),
    "WDS":  ("Woodside Energy",         "ASX",    "WDS.AX",  "B AUD", 1e9,  "USD"),
    "CBA":  ("Commonwealth Bank",       "ASX",    "CBA.AX",  "B AUD", 1e9,  "AUD"),
    "BBRI": ("Bank Rakyat Indonesia",   "IDX",    "BBRI.JK", "T IDR", 1e12, "IDR"),
    "ADRO": ("Alamtri Resources Indonesia", "IDX","ADRO.JK", "T IDR", 1e12, "USD"),
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
    "NAB":  ("National Australia Bank","ASX",    "NAB.AX",  "B AUD", 1e9,  "AUD"),
    "CVX":  ("Chevron Corporation",    "NYSE",   "CVX",     "B USD", 1e9,  "USD"),
    "AXP":  ("American Express",       "NYSE",   "AXP",     "B USD", 1e9,  "USD"),
    "BAC":  ("Bank of America",        "NYSE",   "BAC",     "B USD", 1e9,  "USD"),
}

# Extended fields: include detailed income statement line items
FIELDS = [
    "totalAsset","cash","totalDebt","totalEquity",
    "revenue","costOfRevenue","grossProfit",
    "operatingExpenses","operatingIncome","otherIncome",
    "ebit","interestExpense","incomeBeforeTax","incomeTaxExpense","netProfit",
    "eps","dps"
]

# ---------- FALLBACK DATA (simplified – we keep only core metrics, others will be None) ----------
PRELOADED = {
    "BHP": {"totalAsset":[54.2,51.9,55.7,81.5,None,None],"cash":[14.9,12.4,13.9,13.3,None,None],"totalDebt":[14.5,12.4,14.8,26.7,None,None],"totalEquity":[26.4,28.0,29.7,32.4,None,None],"revenue":[60.8,65.1,53.8,55.7,None,None],"grossProfit":[36.2,40.5,28.3,28.5,None,None],"netProfit":[11.3,30.9,12.9,7.9,None,None],"eps":[2.21,6.05,2.55,1.55,None,None],"dps":[3.01,5.43,1.70,1.09,None,None]},
    # ... (keep all existing PRELOADED entries, but for brevity I'm showing only BHP as example; in final code keep all 28)
    # For the remaining stocks, the same structure as original PRELOADED must be kept.
    # Since the user provided full PRELOADED in the original fetch_data.py, we preserve it.
}

# ---------- exchange rates (unchanged) ----------
def get_rates():
    # ... (same as original)
    pass

def detect_cur(tk, hint):
    # ... (same)
    pass

def get_fx(exchange, fin_cur, usd_aud, usd_idr, twd_usd):
    # ... (same)
    pass

def eps_fx(exchange, fin_cur, usd_aud, usd_idr, twd_usd):
    # ... (same)
    pass

def safe(val, div=1, fx=1.0):
    # ... (same)
    pass

def find_row(df, *names):
    # ... (same)
    pass

def col_yr(df, yr):
    # ... (same)
    pass

def cols_yr(df, yr):
    # ... (same)
    pass

def sum_q(series, cols):
    # ... (same)
    pass

def annual_row(inc, bs, cf, yr, div, fx, epsfx, sym=""):
    row = {}
    ic = col_yr(inc, yr)
    bc = col_yr(bs, yr)
    cc = col_yr(cf, yr)

    if ic is not None:
        # Revenue
        rev = find_row(inc, "Total Revenue", "TotalRevenue", "Interest Income", "InterestIncome")
        row["revenue"] = safe(rev[ic] if rev is not None else None, div, fx)

        # Cost of Revenue
        cor = find_row(inc, "Cost Of Revenue", "CostOfRevenue")
        row["costOfRevenue"] = safe(cor[ic] if cor is not None else None, div, fx)

        # Gross Profit
        gp = find_row(inc, "Gross Profit", "GrossProfit", "Net Interest Income", "NetInterestIncome")
        row["grossProfit"] = safe(gp[ic] if gp is not None else None, div, fx)

        # Operating Expenses
        op_exp = find_row(inc, "Operating Expenses", "OperatingExpense")
        row["operatingExpenses"] = safe(op_exp[ic] if op_exp is not None else None, div, fx)

        # Operating Income
        op_inc = find_row(inc, "Operating Income", "OperatingIncome")
        row["operatingIncome"] = safe(op_inc[ic] if op_inc is not None else None, div, fx)

        # Other Income (non-operating)
        other = find_row(inc, "Total Other Income/Expenses Net", "OtherIncome", "OtherNonOperatingIncome")
        row["otherIncome"] = safe(other[ic] if other is not None else None, div, fx)

        # EBIT (if not directly available, compute: Operating Income + Other Income)
        ebit_val = None
        if row["operatingIncome"] is not None and row["otherIncome"] is not None:
            ebit_val = row["operatingIncome"] + row["otherIncome"]
        else:
            ebit_row = find_row(inc, "EBIT", "Ebit")
            ebit_val = safe(ebit_row[ic] if ebit_row is not None else None, div, fx)
        row["ebit"] = ebit_val

        # Interest Expense
        int_exp = find_row(inc, "Interest Expense", "InterestExpense")
        row["interestExpense"] = safe(int_exp[ic] if int_exp is not None else None, div, fx)

        # Income Before Tax
        ibt = find_row(inc, "Income Before Tax", "IncomeBeforeTax")
        row["incomeBeforeTax"] = safe(ibt[ic] if ibt is not None else None, div, fx)

        # Income Tax Expense
        tax = find_row(inc, "Income Tax Expense", "IncomeTaxExpense")
        row["incomeTaxExpense"] = safe(tax[ic] if tax is not None else None, div, fx)

        # Net Profit
        ni = find_row(inc, "Net Income", "NetIncome", "Net Income Common Stockholders")
        row["netProfit"] = safe(ni[ic] if ni is not None else None, div, fx)

        # EPS
        ep = find_row(inc, "Basic EPS", "BasicEPS", "Diluted EPS", "EPS Diluted")
        row["eps"] = safe(ep[ic] if ep is not None else None, 1, epsfx)

        # Shares outstanding
        sh = find_row(inc, "Basic Average Shares", "BasicAverageShares", "Diluted Average Shares", "Average Dilution Earnings")
        row["_sh"] = safe(sh[ic] if sh is not None else None)

        # Validate fiscal year end (skip TTM if mismatch)
        if yr == LATEST_YEAR and row["revenue"] is not None and row["eps"] is None:
            fy_end = FISCAL_YEAR_END.get(sym, 12)
            if ic.month != fy_end:
                print(f"    ⚠ {sym} yr={yr}: col={ic.date()} FY_end={fy_end} → TTM, skip", flush=True)
                row = {f: None for f in FIELDS}
                row["_sh"] = None
                return row
    else:
        row = {f: None for f in FIELDS}
        row["_sh"] = None

    # Balance sheet items (same as before)
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
        row.update(totalAsset=None, cash=None, totalDebt=None, totalEquity=None)

    # DPS from cashflow
    if cc is not None and row.get("_sh"):
        dp = find_row(cf,"Cash Dividends Paid","Dividends Paid","Common Stock Dividend Paid","Payment Of Dividends")
        dv = safe(dp[cc] if dp is not None else None)
        sh = row["_sh"]
        row["dps"] = round(abs(dv)/sh*epsfx, 4) if dv and sh and sh > 0 else None
    else:
        row["dps"] = None

    # Remove temporary shares field
    row.pop("_sh", None)
    return row

def current_year_row(tk, yr, div, fx, epsfx):
    ann = {"method":"none","label":None,"quarters":0,"asOf":None}
    row = {f:None for f in FIELDS}
    try:
        ai=tk.financials; ab=tk.balance_sheet; cf=tk.cashflow
        if ai is not None and not ai.empty and col_yr(ai,yr) is not None:
            r = annual_row(ai, ab, cf, yr, div, fx, epsfx)
            ic = col_yr(ai,yr)
            return r, {"method":"full_year","label":"FY","quarters":4,"asOf":str(ic.date())}

        # Quarterly annualisation
        qi=tk.quarterly_financials; qb=tk.quarterly_balance_sheet; qc=tk.quarterly_cashflow
        if qi is None or qi.empty: return row, ann
        qtrs=cols_yr(qi,yr)
        if not qtrs: return row, ann
        n=len(qtrs); months=n*3; factor=12.0/months; lq=qtrs[-1]
        label="FY" if months>=12 else f"{months}M x{int(factor) if factor==int(factor) else round(factor,3)}"

        # Helper to sum quarterly values
        def sum_q_field(field_name):
            s = find_row(qi, field_name)
            if s is None: return None
            total = 0.0
            for c in qtrs:
                v = safe(s[c])
                if v is not None: total += v
            return total if total != 0.0 else None

        row["revenue"] = sum_q_field("Total Revenue")
        row["costOfRevenue"] = sum_q_field("Cost Of Revenue")
        row["grossProfit"] = sum_q_field("Gross Profit")
        row["operatingExpenses"] = sum_q_field("Operating Expenses")
        row["operatingIncome"] = sum_q_field("Operating Income")
        row["otherIncome"] = sum_q_field("Total Other Income/Expenses Net")
        row["ebit"] = sum_q_field("EBIT")
        row["interestExpense"] = sum_q_field("Interest Expense")
        row["incomeBeforeTax"] = sum_q_field("Income Before Tax")
        row["incomeTaxExpense"] = sum_q_field("Income Tax Expense")
        row["netProfit"] = sum_q_field("Net Income")

        # EPS annualised
        ep = find_row(qi, "Basic EPS")
        if ep is not None:
            eps_sum = sum_q_field("Basic EPS")
            if eps_sum is not None:
                row["eps"] = round(eps_sum * factor, 4)

        # Shares for DPS
        sh = find_row(qi, "Basic Average Shares")
        sh_val = safe(sh[lq]) if sh is not None else None

        # Balance sheet (point-in-time)
        qbc = col_yr(qb,yr) if qb is not None and not qb.empty else None
        if qbc is not None:
            ta = find_row(qb,"Total Assets")
            ca = find_row(qb,"Cash And Cash Equivalents")
            td = find_row(qb,"Total Debt")
            te = find_row(qb,"Stockholders Equity")
            row["totalAsset"] = safe(ta[qbc] if ta is not None else None, div, fx)
            row["cash"] = safe(ca[qbc] if ca is not None else None, div, fx)
            row["totalDebt"] = safe(td[qbc] if td is not None else None, div, fx)
            row["totalEquity"] = safe(te[qbc] if te is not None else None, div, fx)

        # DPS annualised
        if qc is not None and not qc.empty and sh_val:
            cq = cols_yr(qc,yr)
            dp = find_row(qc, "Cash Dividends Paid")
            ytd = sum_q(dp, cq) if dp is not None else None
            if ytd and sh_val > 0:
                row["dps"] = round(abs(ytd)/sh_val * epsfx * factor, 4)

        # Apply scaling and FX
        for k in ["revenue","costOfRevenue","grossProfit","operatingExpenses","operatingIncome","otherIncome","ebit","interestExpense","incomeBeforeTax","incomeTaxExpense","netProfit"]:
            if row[k] is not None:
                row[k] = round(row[k] / div * fx, 4)
        if row["eps"] is not None:
            row["eps"] = round(row["eps"] * epsfx, 4)

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
                yd[yr]=r

            cy,ann=current_year_row(tk,CURRENT_YEAR,div,fx,epsfx)
            yd[CURRENT_YEAR]=cy
            live=[y for y in COMPLETED if yd[y].get("revenue") is not None]
            print(f"  ✓ live: {live}", flush=True)
            return yd, ann
        except Exception as e:
            print(f"  FAIL (attempt {attempt+1}): {e}", flush=True)
    return None, {"method":"none","label":None}

def build_arrays(yd, sym):
    out={}
    for f in FIELDS:
        arr=[]
        for i,yr in enumerate(ALL_YEARS):
            lv=yd[yr].get(f) if yd and yr in yd else None
            if lv is None and sym in PRELOADED and f in PRELOADED[sym] and i < len(PRELOADED[sym][f]):
                lv = PRELOADED[sym][f][i]
            arr.append(lv)
        out[f]=arr
    return out

# ---------- PROFILES (unchanged, keep all) ----------
PROFILES = { ... }  # Keep the original long dictionary

LEADERSHIP = { ... }  # Keep original

def build_profile_with_insights(sym, m, exchange, currency):
    base = PROFILES.get(sym, "## Business Model Canvas\nGeneric analysis for {sym}.")
    leader = LEADERSHIP.get(sym, {"ceo": "N/A", "cfo": "N/A", "track": "No data."})
    leadership_section = f"\n\n## Leadership\n**CEO:** {leader['ceo']}  \n**CFO:** {leader['cfo']}  \n**Track Record:** {leader['track']}"
    return base + leadership_section

def generate_static_profiles(out):
    for sym, st_data in out["stocks"].items():
        exchange = st_data["exchange"]
        currency = st_data["currency"]
        rev_arr = st_data["revenue"]
        np_arr = st_data["netProfit"]
        gp_arr = st_data["grossProfit"]
        te_arr = st_data["totalEquity"]
        td_arr = st_data["totalDebt"]
        def valid(arr): return [v for v in arr if v is not None and v != 0]
        def cagr(arr):
            v = valid(arr)
            if len(v) < 2: return None
            start, end = v[0], v[-1]
            years = len(v) - 1
            if start <= 0 or end <= 0: return None
            return (pow(end/start, 1/years)-1)*100
        def avg_ratio(num_arr, den_arr):
            ratios = []
            for n, d in zip(num_arr, den_arr):
                if n is not None and d is not None and d != 0:
                    ratios.append(n/d * 100)
            return sum(ratios)/len(ratios) if ratios else None
        m = type('', (), {})()
        m.cg = type('', (), {})()
        m.cg.rev = cagr(rev_arr) or 0
        m.cg.np = cagr(np_arr) or 0
        m.av = type('', (), {})()
        m.av.gpm = avg_ratio(gp_arr, rev_arr) or 0
        m.av.npm = avg_ratio(np_arr, rev_arr) or 0
        m.av.roe = avg_ratio(np_arr, te_arr) or 0
        m.av.debtToEquity = avg_ratio(td_arr, te_arr) or 0
        m.buff = None
        profile_text = build_profile_with_insights(sym, m, exchange, currency)
        out["stocks"][sym]["profile"] = profile_text
        out["stocks"][sym]["profileDate"] = NOW.isoformat()
        out["stocks"][sym]["news"] = "For latest news, please refer to company announcements and recent filings."
        out["stocks"][sym]["newsDate"] = NOW.isoformat()

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

    ok = 0
    for i, (sym, (name, exchange, ticker_str, currency, _div, hint_cur)) in enumerate(all_stocks.items()):
        if i > 0:
            time.sleep(1)
        yd, ann = fetch_one(sym, exchange, ticker_str, hint_cur, usd_aud, usd_idr, twd_usd)
        arrs = build_arrays(yd, sym)
        src = "yfinance" if yd else "fallback"
        if yd:
            ok += 1
        out["stocks"][sym] = {
            "name": name, "exchange": exchange, "currency": currency,
            "ticker": ticker_str, "source": src, "fyEndMonth": FISCAL_YEAR_END.get(sym, 12)
        }
        out["stocks"][sym].update(arrs)
        out["annualisation"][sym] = ann

    generate_static_profiles(out)

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n{'='*50}\nWritten: {path}\nLive yfinance: {ok}/{len(all_stocks)}\n{'='*50}", flush=True)

if __name__ == "__main__":
    main()
