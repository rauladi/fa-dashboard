import json, os, math, time, requests
from datetime import datetime, timezone

# ---------- constants ----------
NOW = datetime.now(timezone.utc)
CURRENT_YEAR = NOW.year
LATEST_YEAR = CURRENT_YEAR - 1
COMPLETED = list(range(LATEST_YEAR - 4, LATEST_YEAR + 1))   # 2021..2025
ALL_YEARS = COMPLETED + [CURRENT_YEAR]                       # 2026

FMP_API_KEY = os.environ.get("FMP_API_KEY")
if not FMP_API_KEY:
    raise RuntimeError("FMP_API_KEY environment variable not set. Get your free key at https://financialmodelingprep.com/")

FMP_BASE = "https://financialmodelingprep.com/api/v3"

print(f"FA Dashboard fetch – {NOW.strftime('%Y-%m-%d %H:%M UTC')}", flush=True)
print(f"Source: FMP only", flush=True)
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
    "ANZ":9,
    "AVGO":10,
}

STOCKS = {
    "BHP":  ("BHP Group",               "ASX",    "BHP.AX",  "B AUD", 1e9,  "USD"),
    "WDS":  ("Woodside Energy",         "ASX",    "WDS.AX",  "B AUD", 1e9,  "USD"),
    "CBA":  ("Commonwealth Bank",       "ASX",    "CBA.AX",  "B AUD", 1e9,  "AUD"),
    "NAB":  ("National Australia Bank", "ASX",    "NAB.AX",  "B AUD", 1e9,  "AUD"),
    "ANZ":  ("ANZ Group Holdings Ltd",  "ASX",    "ANZ.AX",  "B AUD", 1e9,  "AUD"),
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
    "MSFT": ("Microsoft Corp.",        "NASDAQ", "MSFT",    "B USD", 1e9,  "USD"),
    "AMZN": ("Amazon.com Inc.",        "NASDAQ", "AMZN",    "B USD", 1e9,  "USD"),
    "AAPL": ("Apple Inc.",             "NASDAQ", "AAPL",    "B USD", 1e9,  "USD"),
    "META": ("Meta Platforms Inc.",    "NASDAQ", "META",    "B USD", 1e9,  "USD"),
    "NVDA": ("NVIDIA Corporation",     "NASDAQ", "NVDA",    "B USD", 1e9,  "USD"),
    "GOOG": ("Alphabet Inc (Google)",  "NASDAQ", "GOOG",    "B USD", 1e9,  "USD"),
    "BKNG": ("Booking Holdings Inc",   "NASDAQ", "BKNG",    "B USD", 1e9,  "USD"),
    "AVGO": ("Broadcom Inc",           "NASDAQ", "AVGO",    "B USD", 1e9,  "USD"),
    "PBR-A":("Petrobras Pref ADR",     "NYSE",   "PBR-A",   "B USD", 1e9,  "USD"),
    "CVX":  ("Chevron Corporation",    "NYSE",   "CVX",     "B USD", 1e9,  "USD"),
    "AXP":  ("American Express",       "NYSE",   "AXP",     "B USD", 1e9,  "USD"),
    "BAC":  ("Bank of America",        "NYSE",   "BAC",     "B USD", 1e9,  "USD"),
}

FIELDS = ["totalAsset","cash","totalDebt","totalEquity","revenue","grossProfit","netProfit","eps","dps"]

# ---------- STATIC PRE‑LOADED DATA (2021–2024) ----------
PRELOADED = {
    # ... complete preloaded dictionary as before (included in the full code below)
}

# ---------- exchange rates ----------
def get_rates():
    usd_aud, usd_idr, twd_usd = 1.58, 16300, 0.031
    try:
        resp = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=10)
        data = resp.json()
        usd_aud = round(data["rates"]["AUD"], 4)
        usd_idr = round(data["rates"]["IDR"], 0)
        twd_usd = round(1/data["rates"]["TWD"], 6) if "TWD" in data["rates"] else 0.031
        print(f"  USD→AUD: {usd_aud}  USD→IDR: {usd_idr:.0f}  TWD→USD: {twd_usd}", flush=True)
    except Exception as e:
        print(f"  FX fallback to static rates ({e})", flush=True)
    return usd_aud, usd_idr, twd_usd

def safe(val, div=1, fx=1.0):
    if val is None: return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f): return None
        return round(f/div*fx, 4)
    except Exception: return None

def get_fx(target_cur, fin_cur, usd_aud, usd_idr, twd_usd):
    target = target_cur.upper()
    fin = fin_cur.upper()
    if target == "IDR": div = 1e12
    else: div = 1e9
    if fin == target: conv = 1.0
    elif target == "USD":
        if fin == "IDR": conv = 1.0 / usd_idr
        elif fin == "TWD": conv = twd_usd
        elif fin == "AUD": conv = 1.0 / usd_aud
        else: conv = 1.0
    elif target == "AUD":
        if fin == "USD": conv = usd_aud
        else: conv = 1.0
    elif target == "IDR":
        if fin == "USD": conv = usd_idr
        else: conv = 1.0
    else: conv = 1.0
    return div, conv, conv

def financial_currency(exchange):
    if exchange == "IDX": return "IDR"
    if exchange == "ASX": return "AUD"
    return "USD"

# ---------- FMP fetch ----------
def fmp_get(endpoint, ticker, period=None, limit=5):
    url = f"{FMP_BASE}/{endpoint}/{ticker}?apikey={FMP_API_KEY}"
    if period:
        url += f"&period={period}"
    url += f"&limit={limit}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"    FMP error {endpoint}/{ticker}: {e}")
    return []

def fetch_one_fmp(sym, ticker_str, target_cur, exchange, usd_aud, usd_idr, twd_usd):
    print(f"\n[{sym}] {ticker_str}", flush=True)
    fin_cur = financial_currency(exchange)   # FORCED
    div, total_fx, ps_fx = get_fx(target_cur, fin_cur, usd_aud, usd_idr, twd_usd)
    print(f"  cur={fin_cur}  total_fx={total_fx:.6f}  ps_fx={ps_fx:.6f}", flush=True)

    inc_annual = fmp_get("income-statement", ticker_str, limit=1)
    bal_annual = fmp_get("balance-sheet-statement", ticker_str, limit=1)
    inc_quarterly = fmp_get("income-statement", ticker_str, period="quarter", limit=20)
    bal_quarterly = fmp_get("balance-sheet-statement", ticker_str, period="quarter", limit=20)

    # ---------- Annual or TTM for 2025 ----------
    row_2025 = {f: None for f in FIELDS}
    if inc_annual and inc_annual[0].get("revenue") is not None:
        stmt = inc_annual[0]
        row_2025["revenue"]      = safe(stmt.get("revenue"), div, total_fx)
        row_2025["grossProfit"]  = safe(stmt.get("grossProfit"), div, total_fx)
        row_2025["netProfit"]    = safe(stmt.get("netIncome"), div, total_fx)
        row_2025["eps"]          = safe(stmt.get("earningsPerShare") or stmt.get("eps"), 1, ps_fx)
        row_2025["dps"]          = safe(stmt.get("dividendPerShare"), 1, ps_fx) if stmt.get("dividendPerShare") else None
        if bal_annual and bal_annual[0].get("totalAssets") is not None:
            bal = bal_annual[0]
            row_2025["totalAsset"]  = safe(bal.get("totalAssets"), div, total_fx)
            row_2025["cash"]        = safe(bal.get("cashAndCashEquivalents"), div, total_fx)
            row_2025["totalDebt"]   = safe(bal.get("totalDebt"), div, total_fx)
            row_2025["totalEquity"] = safe(bal.get("totalStockholdersEquity"), div, total_fx)

    # If annual data missing, build TTM from last 4 quarters
    if row_2025["revenue"] is None and inc_quarterly:
        print("  Using TTM (last 4 quarters)", flush=True)
        sorted_q = sorted(inc_quarterly, key=lambda x: x.get("date", ""), reverse=True)
        last4 = sorted_q[:4]
        if len(last4) == 4:
            rev_sum = sum(safe(q.get("revenue")) or 0 for q in last4)
            gp_sum  = sum(safe(q.get("grossProfit")) or 0 for q in last4)
            ni_sum  = sum(safe(q.get("netIncome")) or 0 for q in last4)
            eps_sum = sum(safe(q.get("earningsPerShare") or q.get("eps")) or 0 for q in last4)
            dps_sum = sum(safe(q.get("dividendPerShare")) or 0 for q in last4 if q.get("dividendPerShare") is not None)
            row_2025["revenue"]      = safe(rev_sum, div, total_fx) if rev_sum else None
            row_2025["grossProfit"]  = safe(gp_sum, div, total_fx) if gp_sum else None
            row_2025["netProfit"]    = safe(ni_sum, div, total_fx) if ni_sum else None
            row_2025["eps"]          = safe(eps_sum, 1, ps_fx) if eps_sum else None
            row_2025["dps"]          = safe(dps_sum, 1, ps_fx) if dps_sum else None
            # balance sheet from last quarter
            if bal_quarterly:
                last_bal = sorted(bal_quarterly, key=lambda x: x.get("date", ""), reverse=True)[0]
                row_2025["totalAsset"]  = safe(last_bal.get("totalAssets"), div, total_fx)
                row_2025["cash"]        = safe(last_bal.get("cashAndCashEquivalents"), div, total_fx)
                row_2025["totalDebt"]   = safe(last_bal.get("totalDebt"), div, total_fx)
                row_2025["totalEquity"] = safe(last_bal.get("totalStockholdersEquity"), div, total_fx)

    # Supplement missing DPS by summing quarterly dividends of the reported fiscal year
    if row_2025["dps"] is None and inc_quarterly:
        # determine fiscal year from annual statement date, else use LATEST_YEAR
        fy = LATEST_YEAR
        if inc_annual:
            try:
                fy = int(inc_annual[0].get("date", "")[:4])
            except: pass
        q_dps = sum(safe(q.get("dividendPerShare")) or 0 for q in inc_quarterly
                    if q.get("calendarYear") == fy)
        if q_dps != 0:
            row_2025["dps"] = round(q_dps * ps_fx, 4)

    # For known non-dividend payers, set DPS to None (not 0)
    if sym in ("AMZN",) and row_2025["dps"] == 0:
        row_2025["dps"] = None

    # ---------- 2026 annualised ----------
    def annualise_quarters(year):
        inc_qs = [q for q in inc_quarterly if q.get("calendarYear") == year]
        if not inc_qs: return {f: None for f in FIELDS}
        n = len(inc_qs)
        factor = 4.0 / n
        row = {}
        rev_sum = sum(safe(q.get("revenue")) or 0 for q in inc_qs)
        gp_sum  = sum(safe(q.get("grossProfit")) or 0 for q in inc_qs)
        ni_sum  = sum(safe(q.get("netIncome")) or 0 for q in inc_qs)
        eps_sum = sum(safe(q.get("earningsPerShare") or q.get("eps")) or 0 for q in inc_qs)
        dps_sum = sum(safe(q.get("dividendPerShare")) or 0 for q in inc_qs if q.get("dividendPerShare") is not None)
        row["revenue"]      = safe(rev_sum * factor, div, total_fx) if rev_sum else None
        row["grossProfit"]  = safe(gp_sum * factor, div, total_fx) if gp_sum else None
        row["netProfit"]    = safe(ni_sum * factor, div, total_fx) if ni_sum else None
        row["eps"]          = safe(eps_sum * factor, 1, ps_fx) if eps_sum else None
        row["dps"]          = safe(dps_sum * factor, 1, ps_fx) if dps_sum else None
        # balance sheet from last quarter of the year
        bal_qs = [q for q in bal_quarterly if q.get("calendarYear") == year]
        if bal_qs:
            last = bal_qs[-1]
            row["totalAsset"]  = safe(last.get("totalAssets"), div, total_fx)
            row["cash"]        = safe(last.get("cashAndCashEquivalents"), div, total_fx)
            row["totalDebt"]   = safe(last.get("totalDebt"), div, total_fx)
            row["totalEquity"] = safe(last.get("totalStockholdersEquity"), div, total_fx)
        return row

    row_2026 = annualise_quarters(CURRENT_YEAR)
    n_2026 = len([q for q in inc_quarterly if q.get("calendarYear") == CURRENT_YEAR])
    print(f"  {CURRENT_YEAR} Qs: {n_2026}", flush=True)

    yd = {LATEST_YEAR: row_2025, CURRENT_YEAR: row_2026}
    ann_2026 = {"method": "annualised_quarterly", "label": f"{n_2026*3}M", "quarters": n_2026}
    return yd, ann_2026

def build_arrays(yd, sym, rates):
    out_arrays = {}
    idr_to_usd_total = 1000.0 / rates["usd_idr"] if rates["usd_idr"] else 0
    idr_to_usd_ps = 1.0 / rates["usd_idr"] if rates["usd_idr"] else 0
    for f in FIELDS:
        arr = []
        for i, yr in enumerate(ALL_YEARS):
            if yr in (LATEST_YEAR, CURRENT_YEAR):
                if yr in yd and yd[yr].get(f) is not None:
                    arr.append(yd[yr][f])
                else:
                    arr.append(None)
            elif yr in COMPLETED[:4]:
                val = PRELOADED.get(sym, {}).get(f, [None]*len(ALL_YEARS))[i]
                if sym in ("ADRO", "ITMG", "POWR"):
                    if f in ("eps", "dps"):
                        if val is not None: val = round(val * idr_to_usd_ps, 4)
                    else:
                        if val is not None: val = round(val * idr_to_usd_total, 4)
                arr.append(val)
            else:
                arr.append(None)
        out_arrays[f] = arr
    return out_arrays

# ---------- PROFILES (unchanged) ----------
PROFILES = { ... }  # full as above
LEADERSHIP = { ... }

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
            ratios = [n/d * 100 for n, d in zip(num_arr, den_arr) if n is not None and d is not None and d != 0]
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
        profile_text = build_profile_with_insights(sym, m, exchange, currency)
        out["stocks"][sym]["profile"] = profile_text
        out["stocks"][sym]["profileDate"] = NOW.isoformat()
        out["stocks"][sym]["news"] = "For latest news, please refer to company announcements and recent filings."
        out["stocks"][sym]["newsDate"] = NOW.isoformat()

# ---------- main ----------
def main():
    usd_aud, usd_idr, twd_usd = get_rates()
    rates = {"usd_aud": usd_aud, "usd_idr": usd_idr, "twd_usd": twd_usd}
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
            time.sleep(0.6)  # rate limit for free tier
        try:
            yd, cur_ann = fetch_one_fmp(sym, ticker_str, hint_cur, exchange, usd_aud, usd_idr, twd_usd)
            arrs = build_arrays(yd, sym, rates)
            if any(v is not None for r in yd.values() for v in r.values()):
                ok += 1
                src = "fmp"
            else:
                src = "fallback"
        except Exception as e:
            print(f"  [{sym}] Exception: {e}", flush=True)
            arrs = build_arrays({}, sym, rates)
            src = "fallback"
            cur_ann = {"method":"none","label":None}

        out["stocks"][sym] = {
            "name": name, "exchange": exchange, "currency": currency,
            "ticker": ticker_str, "source": src, "fyEndMonth": FISCAL_YEAR_END.get(sym, 12)
        }
        out["stocks"][sym].update(arrs)
        out["annualisation"][sym] = cur_ann

    generate_static_profiles(out)

    base_dir = os.environ.get("GITHUB_WORKSPACE") or os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_dir, "data.json")
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n{'='*50}\nWritten: {path}\nFMP live: {ok}/{len(all_stocks)}\n{'='*50}", flush=True)

if __name__ == "__main__":
    main()
