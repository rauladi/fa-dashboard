import json, os, math, time, requests
from datetime import datetime, timezone, timedelta
import yfinance as yf
import pandas as pd

# ---------- constants ----------
NOW = datetime.now(timezone.utc)
CURRENT_YEAR = NOW.year
LATEST_YEAR = CURRENT_YEAR - 1
COMPLETED = list(range(LATEST_YEAR - 4, LATEST_YEAR + 1))   # 2021..2025
ALL_YEARS = COMPLETED + [CURRENT_YEAR]                       # 2026

FMP_API_KEY = os.environ.get("FMP_API_KEY")   # kept for compatibility, not used for live fetch

print(f"FA Dashboard fetch – {NOW.strftime('%Y-%m-%d %H:%M UTC')}", flush=True)
print(f"Sources: yfinance (live years 2025–2026)", flush=True)
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
    "WBC":9,
    "RHHBY":12,
    "ESSA":12,
    "FMG":6,
    "STO":12,
    "ALD":12,
    "MQG":3,
    "ASML":12,
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
    "ESSA": ("ESSA Industries Indonesia Tbk","IDX","ESSA.JK","T IDR", 1e12, "IDR"),
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
    "WBC":  ("Westpac Banking Corporation", "ASX", "WBC.AX", "B AUD", 1e9, "AUD"),
    "RHHBY":("Roche Holding AG",        "NYSE",  "RHHBY",   "B USD", 1e9, "USD"),
    "FMG":  ("Fortescue Metals Group",  "ASX",   "FMG.AX",  "B USD", 1e9, "USD"),
    "STO":  ("Santos Ltd",              "ASX",   "STO.AX",  "B USD", 1e9, "USD"),
    "ALD":  ("Ampol Limited",           "ASX",   "ALD.AX",  "B AUD", 1e9, "AUD"),
    "MQG":  ("Macquarie Group Limited", "ASX",   "MQG.AX",  "B AUD", 1e9, "AUD"),
    "ASML": ("ASML Holding NV",         "NASDAQ","ASML",    "B USD", 1e9, "USD"),
}

FIELDS = [
    "totalAsset","cash","totalDebt","totalEquity",
    "revenue","costOfRevenue","grossProfit",
    "operatingExpense","operatingIncome",
    "interestExpense","incomeTaxExpense",
    "netProfit","eps","dps"
]

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

def isOK(v):
    return v is not None and not math.isnan(v) and not math.isinf(v)

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

# =============================================================================
#  LIVE FETCHER – returns both 2025 (annual) and 2026 (quarterly annualised)
# =============================================================================

def get_fin_val_from_series(series, candidates):
    lowered = {k.lower().strip(): v for k, v in series.items()}
    for cand in candidates:
        key = cand.lower().strip()
        if key in lowered and lowered[key] is not None:
            try:
                val = lowered[key]
                if hasattr(val, 'iloc'): val = val.iloc[0] if len(val) > 0 else None
                return float(val)
            except (ValueError, TypeError): continue
    return None

def get_fin_val_by_substring(series, substrings):
    for key, val in series.items():
        key_lower = key.lower().strip()
        for sub in substrings:
            if sub in key_lower and val is not None:
                try:
                    v = val
                    if hasattr(v, 'iloc'): v = v.iloc[0] if len(v) > 0 else None
                    return float(v)
                except (ValueError, TypeError): continue
    return None

INC_CANDIDATES = {
    "revenue": ["Total Revenue","Revenue","Total revenue","Operating Revenue","Sales","Net Sales","Net revenue","Revenues","Pendapatan","Total pendapatan","Penjualan bersih"],
    "costOfRevenue": ["Cost Of Revenue","Cost of revenue","Cost Of Sales","Cost of goods sold","COGS","Beban pokok pendapatan","Harga pokok penjualan"],
    "grossProfit": ["Gross Profit","Gross profit","Gross margin","Laba bruto","Laba kotor","Net Interest Income","Net interest income","Pendapatan bunga bersih","Pendapatan Bunga Bersih"],
    "operatingExpense": ["Operating Expense","Operating Expenses","Operating Cost","Selling General & Admin Expense","SG&A","Beban operasional","Beban usaha"],
    "operatingIncome": ["Operating Income","Operating income","EBIT","Laba operasi","Laba usaha"],
    "interestExpense": ["Interest Expense","Interest expense","Interest Cost","Beban bunga","Biaya bunga"],
    "incomeTaxExpense": ["Income Tax Expense","Tax Provision","Provision for Income Taxes","Beban pajak","Pajak penghasilan"],
    "netProfit": ["Net Income","Net income","Net Income Common Stockholders","Profit after tax","Net profit","Net Profit","Laba bersih","Laba tahun berjalan"],
    "eps": ["Diluted EPS","Basic EPS","EPS Diluted","EPS Basic","Earnings Per Share","Earnings per share","Laba per saham dasar","Laba per saham dilusian"],
    "dps": ["Dividends Per Share","Dividend Per Share","DPS","Dividen per saham"]
}
INC_SUB = {
    "revenue": ["revenue","pendapatan","penjualan","sales"],
    "costOfRevenue": ["cost of revenue","cogs","beban pokok","harga pokok"],
    "grossProfit": ["gross","laba kotor","laba bruto","net interest income","pendapatan bunga bersih"],
    "operatingExpense": ["operating expense","sg&a","beban operasional","beban usaha"],
    "operatingIncome": ["operating income","ebit","laba operasi","laba usaha"],
    "interestExpense": ["interest expense","beban bunga","biaya bunga"],
    "incomeTaxExpense": ["income tax","tax provision","beban pajak","pajak penghasilan"],
    "netProfit": ["net income","laba bersih","laba tahun berjalan","profit after tax"],
    "eps": ["eps","laba per saham","earnings per share"],
    "dps": ["dps","dividend per share","dividen per saham"]
}
BAL_CANDIDATES = {
    "totalAsset": ["Total Assets","Total assets","Total Asset","Jumlah aset","Aset","Total Capitalization","Total Aset","Total Aktiva"],
    "cash": ["Cash And Cash Equivalents","Cash & Cash Equivalents","Cash and cash equivalents","Cash","Cash & Equivalents","Kas dan setara kas","Kas"],
    "totalDebt": ["Total Debt","Total debt","Total Debt, Net","Long Term Debt + Short Term Debt","Net Debt","Total utang","Utang","Total Liabilities","Total liabilities","Total Kewajiban"],
    "totalEquity": [
        "Total Equity Gross Minority Interest","Stockholders Equity","Total Stockholder Equity",
        "Total Equity","Shareholders' Equity","Equity","Ekuitas","Total ekuitas",
        "Common Stock Equity","Book Value","Total Book Value","Common Equity",
        "Tangible Book Value","Net Tangible Assets"
    ]
}

def fiscal_year_range(sym):
    m = FISCAL_YEAR_END.get(sym, 12)
    if m == 12:
        start = datetime(CURRENT_YEAR, 1, 1)
        end   = datetime(CURRENT_YEAR, 12, 31, 23, 59, 59)
    else:
        start = datetime(CURRENT_YEAR - 1, m + 1, 1)
        end   = datetime(CURRENT_YEAR, m, 30)
    return start, end

def apply_corrections(row, sym, inc_cols, q_inc, tick, target_cur, exchange, div, total_fx, ps_fx, dbg=False):
    info = tick.info or {}

    if row.get("grossProfit") is None or row["grossProfit"] == 0.0:
        if row.get("revenue") is not None and row.get("costOfRevenue") is not None:
            computed_gp = float(row["revenue"]) - float(row["costOfRevenue"])
            if computed_gp > 0: row["grossProfit"] = round(computed_gp, 4)
        if row.get("grossProfit") is None or row["grossProfit"] == 0.0:
            if inc_cols:
                latest_series = q_inc[inc_cols[-1]]
                nii = get_fin_val_from_series(latest_series, INC_CANDIDATES["grossProfit"])
                if nii is not None: row["grossProfit"] = safe(nii, div, total_fx)
        if (row.get("grossProfit") is None or row["grossProfit"] == 0.0) and \
           row.get("netProfit") is not None and row.get("operatingExpense") is not None and \
           row.get("incomeTaxExpense") is not None:
            int_exp = row.get("interestExpense") if row.get("interestExpense") is not None else 0.0
            reconstructed = float(row["netProfit"]) + float(row["operatingExpense"]) + float(int_exp) + float(row["incomeTaxExpense"])
            if reconstructed > 0: row["grossProfit"] = round(reconstructed, 4)
        if row.get("grossProfit") is None or row["grossProfit"] == 0.0:
            if row.get("revenue") is not None and row["revenue"] > 0:
                row["grossProfit"] = row["revenue"]
                if dbg: print(f"  [DEBUG {sym}] Universal GP fallback: using revenue = {row['revenue']}", flush=True)

    for field in ["revenue","costOfRevenue","grossProfit","operatingExpense","operatingIncome",
                  "interestExpense","incomeTaxExpense","netProfit","totalAsset","cash",
                  "totalDebt","totalEquity"]:
        if row.get(field) is not None and abs(row[field]) < 0.01: row[field] = None
    if row.get("eps") is not None and abs(row.get("eps")) < 0.001: row["eps"] = None
    if row.get("dps") is not None and abs(row.get("dps")) < 0.001: row["dps"] = None

    if sym == "TSM": info_is_target = False
    else:
        info_revenue = info.get("totalRevenue") or info.get("revenue")
        info_is_target = (info_revenue is not None and info_revenue > 1e8 and (target_cur == "USD" or target_cur == "AUD"))

    if info_is_target: info_div, info_fx = 1e9, 1.0
    else: info_div, info_fx = div, total_fx

    if exchange == "IDX" and target_cur == "USD": per_share_fx = ps_fx
    elif info_is_target: per_share_fx = 1.0
    else: per_share_fx = ps_fx

    def fill_from_info(*candidates):
        for c in candidates:
            v = info.get(c, None)
            if v is not None: return safe(v, info_div, info_fx)
        return None

    if row.get("revenue") is None: row["revenue"] = fill_from_info("totalRevenue","revenue")
    if row.get("costOfRevenue") is None: row["costOfRevenue"] = fill_from_info("costOfRevenue")
    if row.get("grossProfit") is None:
        gm = info.get("grossMargins")
        if gm is not None and row.get("revenue") is not None:
            row["grossProfit"] = safe(float(gm) * float(row["revenue"]), 1, 1.0)
        if row.get("grossProfit") is None: row["grossProfit"] = fill_from_info("grossProfit")
    if row.get("operatingExpense") is None: row["operatingExpense"] = fill_from_info("operatingExpenses","totalOperatingExpenses")
    if row.get("operatingIncome") is None: row["operatingIncome"] = fill_from_info("operatingIncome","ebit")
    if row.get("interestExpense") is None: row["interestExpense"] = fill_from_info("interestExpense")
    if row.get("incomeTaxExpense") is None: row["incomeTaxExpense"] = fill_from_info("incomeTaxExpense")
    if row.get("netProfit") is None: row["netProfit"] = fill_from_info("netIncomeToCommon","netIncome")
    if row.get("eps") is None:
        row["eps"] = safe(info.get("trailingEps") or info.get("epsTrailingTwelveMonths"), 1, per_share_fx)
    if row.get("dps") is None:
        div_rate = info.get("dividendRate")
        if div_rate is not None: row["dps"] = safe(div_rate, 1, per_share_fx)
        else:
            try:
                dividends = tick.dividends
                if not dividends.empty:
                    one_year_ago = dividends.index.max() - timedelta(days=365)
                    trailing = dividends[dividends.index > one_year_ago]
                    if not trailing.empty: row["dps"] = safe(float(trailing.sum()), 1, per_share_fx)
            except Exception: pass
    if row.get("totalAsset") is None: row["totalAsset"] = fill_from_info("totalAssets","totalAsset")
    if row.get("cash") is None: row["cash"] = fill_from_info("totalCash","cash")
    if row.get("totalDebt") is None: row["totalDebt"] = fill_from_info("totalDebt")
    if row.get("totalEquity") is None:
        book_val = info.get("bookValue")
        if book_val is not None: row["totalEquity"] = safe(book_val, info_div, info_fx)
        if row.get("totalEquity") is None:
            for k, v in info.items():
                if any(sub in k.lower() for sub in ["equity","stockholder","book value","common equity"]):
                    if v is not None:
                        row["totalEquity"] = safe(v, info_div, info_fx)
                        if dbg: print(f"  [DEBUG {sym}] Found totalEquity via info key '{k}' = {row['totalEquity']}", flush=True)
                        break
        if row.get("totalEquity") is None: row["totalEquity"] = fill_from_info("totalStockholderEquity","totalEquity")

    if row.get("totalAsset") is None and row.get("totalDebt") is not None and row.get("totalEquity") is not None:
        row["totalAsset"] = round(float(row["totalDebt"]) + float(row["totalEquity"]), 4)
    if row.get("totalEquity") is None and row.get("totalAsset") is not None and row.get("totalDebt") is not None:
        eq = float(row["totalAsset"]) - float(row["totalDebt"])
        if eq > 0: row["totalEquity"] = round(eq, 4)

    if sym in {"BBRI", "BTPS"} and row.get("totalAsset") is not None and row.get("totalEquity") is not None:
        new_debt = round(float(row["totalAsset"]) - float(row["totalEquity"]), 4)
        if new_debt > 0: row["totalDebt"] = new_debt

    if sym == "DMAS" and (row.get("totalDebt") is None or row["totalDebt"] == 0.0):
        if row.get("totalAsset") is not None and row.get("totalEquity") is not None:
            computed_debt = round(float(row["totalAsset"]) - float(row["totalEquity"]), 4)
            if computed_debt > 0: row["totalDebt"] = computed_debt

    if sym in {"ADRO", "ITMG", "POWR"} and row.get("revenue") is not None:
        pre = PRELOADED.get(sym, {})
        rev_hist = (pre.get("revenue") or [])[:4]
        eq_hist  = (pre.get("totalEquity") or [])[:4]
        ta_hist  = (pre.get("totalAsset") or [])[:4]

        if (row.get("totalEquity") is None or row["totalEquity"] == 0.0) and \
           all(isOK(r) and r > 0 for r in rev_hist) and \
           all(isOK(e) and e > 0 for e in eq_hist):
            ratio_vals = [e / r for r, e in zip(rev_hist, eq_hist) if r > 0 and e > 0]
            if ratio_vals:
                avg_eq_rev = sum(ratio_vals) / len(ratio_vals)
                row["totalEquity"] = round(float(row["revenue"]) * avg_eq_rev, 4)
                if dbg: print(f"  [DEBUG {sym}] Estimated totalEquity from historical ratio = {row['totalEquity']}", flush=True)

        if (row.get("totalAsset") is None or row["totalAsset"] < 0.7 * float(row["revenue"])) and \
           all(isOK(r) and r > 0 for r in rev_hist) and \
           all(isOK(a) and a > 0 for a in ta_hist):
            ratio_vals = [a / r for r, a in zip(rev_hist, ta_hist) if r > 0 and a > 0]
            if ratio_vals:
                avg_ta_rev = sum(ratio_vals) / len(ratio_vals)
                row["totalAsset"] = round(float(row["revenue"]) * avg_ta_rev, 4)
                if dbg: print(f"  [DEBUG {sym}] Estimated totalAsset from historical ratio = {row['totalAsset']}", flush=True)

    if sym == "FMG" and row.get("revenue") is not None and row["revenue"] > 0:
        pre = PRELOADED.get(sym, {})
        rev_hist = (pre.get("revenue") or [])[:4]
        ta_hist  = (pre.get("totalAsset") or [])[:4]
        eq_hist  = (pre.get("totalEquity") or [])[:4]

        ta_ratios = [ta / r for ta, r in zip(ta_hist, rev_hist) if r > 0 and ta > 0]
        eq_ratios = [eq / r for eq, r in zip(eq_hist, rev_hist) if r > 0 and eq > 0]

        if ta_ratios and (row.get("totalAsset") is None or row["totalAsset"] < 20):
            avg_ta = sum(ta_ratios) / len(ta_ratios)
            row["totalAsset"] = round(float(row["revenue"]) * avg_ta, 4)
            print(f"  [FMG] Overrode totalAsset: {row['totalAsset']} (avg ratio {avg_ta:.2f})", flush=True)

        if eq_ratios and (row.get("totalEquity") is None or row["totalEquity"] < 5):
            avg_eq = sum(eq_ratios) / len(eq_ratios)
            row["totalEquity"] = round(float(row["revenue"]) * avg_eq, 4)
            print(f"  [FMG] Overrode totalEquity: {row['totalEquity']} (avg ratio {avg_eq:.2f})", flush=True)

        if row.get("totalAsset") is not None and row.get("totalEquity") is not None:
            if row.get("totalDebt") is None or abs(row["totalDebt"] - row["totalAsset"]) < 0.1:
                row["totalDebt"] = round(row["totalAsset"] - row["totalEquity"], 4)
                print(f"  [FMG] Recalculated totalDebt: {row['totalDebt']}", flush=True)

    if sym == "STO" and row.get("revenue") is not None and row["revenue"] > 0:
        pre = PRELOADED.get(sym, {})
        rev_hist = (pre.get("revenue") or [])[:4]
        ta_hist  = (pre.get("totalAsset") or [])[:4]
        eq_hist  = (pre.get("totalEquity") or [])[:4]

        ta_ratios = [ta / r for ta, r in zip(ta_hist, rev_hist) if r > 0 and ta > 0]
        eq_ratios = [eq / r for eq, r in zip(eq_hist, rev_hist) if r > 0 and eq > 0]

        if ta_ratios and (row.get("totalAsset") is None or row["totalAsset"] < 15):
            avg_ta = sum(ta_ratios) / len(ta_ratios)
            row["totalAsset"] = round(float(row["revenue"]) * avg_ta, 4)
            print(f"  [STO] Overrode totalAsset: {row['totalAsset']} (avg ratio {avg_ta:.2f})", flush=True)

        if eq_ratios and (row.get("totalEquity") is None or row["totalEquity"] < 5):
            avg_eq = sum(eq_ratios) / len(eq_ratios)
            row["totalEquity"] = round(float(row["revenue"]) * avg_eq, 4)
            print(f"  [STO] Overrode totalEquity: {row['totalEquity']} (avg ratio {avg_eq:.2f})", flush=True)

        if row.get("totalAsset") is not None and row.get("totalEquity") is not None:
            if row.get("totalDebt") is None or abs(row["totalDebt"] - row["totalAsset"]) < 0.1:
                row["totalDebt"] = round(row["totalAsset"] - row["totalEquity"], 4)
                print(f"  [STO] Recalculated totalDebt: {row['totalDebt']}", flush=True)

    if row.get("totalEquity") is not None and row["totalEquity"] < 0: row["totalEquity"] = None
    if row.get("grossProfit") is not None and row["grossProfit"] < 0: row["grossProfit"] = None


def fetch_live_years(ticker_str, sym, target_cur, exchange, usd_aud, usd_idr, twd_usd):
    """Return a dict {2025: row, 2026: row} for one stock."""
    if sym == "TSM": fin_cur = "TWD"
    else: fin_cur = financial_currency(exchange)
    div, total_fx, ps_fx = get_fx(target_cur, fin_cur, usd_aud, usd_idr, twd_usd)

    row_2025 = {f: None for f in FIELDS}
    row_2026 = {f: None for f in FIELDS}

    try:
        tick = yf.Ticker(ticker_str)
        info = tick.info or {}

        inc_df = tick.financials
        bal_df = tick.balance_sheet
        q_inc = tick.quarterly_financials
        q_bal = tick.quarterly_balance_sheet

        def fill_from_df(df, row_dict, field_candidates_map, substring_map):
            if df is None or df.empty: return False
            for col in df.columns:
                series = df[col]
                for field, candidates in field_candidates_map.items():
                    if row_dict[field] is not None: continue
                    val = get_fin_val_from_series(series, candidates)
                    if val is not None:
                        fx = ps_fx if field in ("eps","dps") else total_fx
                        d = 1 if field in ("eps","dps") else div
                        row_dict[field] = safe(val, d, fx)
                for field, subs in substring_map.items():
                    if row_dict[field] is not None: continue
                    val = get_fin_val_by_substring(series, subs)
                    if val is not None:
                        fx = ps_fx if field in ("eps","dps") else total_fx
                        d = 1 if field in ("eps","dps") else div
                        row_dict[field] = safe(val, d, fx)
            return any(v is not None for v in row_dict.values())

        fill_from_df(inc_df, row_2025, INC_CANDIDATES, INC_SUB)
        fill_from_df(bal_df, row_2025, BAL_CANDIDATES, {})

        def force_better(df, label_list, current_val, divisor, fx):
            if df is None: return current_val
            idx_lower = {k.lower().strip(): k for k in df.index}
            for lbl in label_list:
                key = lbl.lower().strip()
                if key in idx_lower:
                    try:
                        val = df.loc[idx_lower[key]].iloc[0]
                        if pd.notna(val):
                            v = safe(float(val), divisor, fx)
                            if v is not None and (current_val is None or current_val < 0.01):
                                return v
                    except Exception: continue
            return current_val

        row_2025["totalAsset"] = force_better(bal_df, BAL_CANDIDATES["totalAsset"], row_2025["totalAsset"], div, total_fx)
        if row_2025["totalAsset"] is None: row_2025["totalAsset"] = force_better(q_bal, BAL_CANDIDATES["totalAsset"], row_2025["totalAsset"], div, total_fx)

        row_2025["totalEquity"] = force_better(bal_df, BAL_CANDIDATES["totalEquity"], row_2025["totalEquity"], div, total_fx)
        if row_2025["totalEquity"] is None: row_2025["totalEquity"] = force_better(q_bal, BAL_CANDIDATES["totalEquity"], row_2025["totalEquity"], div, total_fx)

        inc_cols = list(inc_df.columns)[:1] if inc_df is not None else []
        apply_corrections(row_2025, sym, inc_cols, q_inc, tick, target_cur, exchange, div, total_fx, ps_fx, dbg=False)

        fy_start, fy_end = fiscal_year_range(sym)
        q_inc_cols = [c for c in (q_inc.columns if q_inc is not None else [])
                      if fy_start <= c.to_pydatetime() <= fy_end]
        q_bal_cols = [c for c in (q_bal.columns if q_bal is not None else [])
                      if fy_start <= c.to_pydatetime() <= fy_end]

        sums = {k: 0.0 for k in ["revenue","costOfRevenue","grossProfit","operatingExpense",
                                 "operatingIncome","interestExpense","incomeTaxExpense",
                                 "netProfit","eps","dps"]}
        quarter_count = 0
        for col in q_inc_cols:
            series = q_inc[col]
            has_data = False
            for k in sums:
                val = get_fin_val_from_series(series, INC_CANDIDATES[k])
                if val is None: val = get_fin_val_by_substring(series, INC_SUB[k])
                if val is not None:
                    sums[k] += val
                    has_data = True
            if has_data: quarter_count += 1

        if quarter_count > 0:
            multiplier = 4.0 / quarter_count
            for k in sums:
                if sums[k] is not None:
                    annual = sums[k] * multiplier
                    if k in ("eps","dps"):
                        row_2026[k] = safe(annual, 1, ps_fx)
                    else:
                        row_2026[k] = safe(annual, div, total_fx)

        # Annualise balance-sheet items using the SAME method as income items:
        # sum quarterly values, then multiply by 4 / quarter_count.
        if q_bal_cols:
            bal_sums = {k: 0.0 for k in ["totalAsset","cash","totalDebt","totalEquity"]}
            bal_quarter_count = 0
            for col in q_bal_cols:
                bal_series = q_bal[col]
                has_bal = False
                for k in bal_sums:
                    val = get_fin_val_from_series(bal_series, BAL_CANDIDATES[k])
                    if val is None:
                        val = get_fin_val_by_substring(bal_series, [k])
                    if val is not None:
                        bal_sums[k] += val
                        has_bal = True
                if has_bal:
                    bal_quarter_count += 1
            if bal_quarter_count > 0:
                bal_multiplier = 4.0 / bal_quarter_count
                for k in bal_sums:
                    if bal_sums[k] != 0:
                        row_2026[k] = safe(bal_sums[k] * bal_multiplier, div, total_fx)

        apply_corrections(row_2026, sym, q_inc_cols, q_inc, tick, target_cur, exchange, div, total_fx, ps_fx, dbg=False)

    except Exception as e:
        print(f"  [Live] {ticker_str}: Exception: {e}", flush=True)

    return {LATEST_YEAR: row_2025, CURRENT_YEAR: row_2026}

def fetch_live(sym, exchange, ticker_str, hint_cur, usd_aud, usd_idr, twd_usd):
    target_cur = hint_cur.upper()
    src = "yfinance"

    print(f"\n[{sym}] (yfinance) {ticker_str}", flush=True)
    yd = fetch_live_years(ticker_str, sym, target_cur, exchange, usd_aud, usd_idr, twd_usd)

    for yr_row in yd.values():
        for bal in ("totalAsset","cash","totalDebt","totalEquity"):
            if yr_row.get(bal) == 0: yr_row[bal] = None
        for inc in ("revenue","costOfRevenue","grossProfit","operatingExpense","operatingIncome","interestExpense","incomeTaxExpense","netProfit"):
            if yr_row.get(inc) == 0: yr_row[inc] = None
        if yr_row.get("dps") == 0: yr_row["dps"] = None

    pre_dps = PRELOADED.get(sym, {}).get("dps", [])
    valid_dps = [v for v in pre_dps if v is not None and v > 0]
    for yr_row in yd.values():
        if valid_dps and yr_row.get("dps") is not None and yr_row["dps"] > 5 * max(valid_dps):
            yr_row["dps"] = None
    pre_eps = PRELOADED.get(sym, {}).get("eps", [])
    valid_eps = [v for v in pre_eps if v is not None and v > 0]
    for yr_row in yd.values():
        if valid_eps and yr_row.get("eps") is not None and yr_row["eps"] > 5 * max(valid_eps):
            yr_row["eps"] = None

    ann = {"method": "annual", "label": src, "quarters": 0}
    return yd, ann, src

def build_arrays(yd, sym, rates):
    out = {}
    idr_total = 1000.0/rates["usd_idr"] if rates["usd_idr"] else 0
    idr_ps = 1.0/rates["usd_idr"] if rates["usd_idr"] else 0
    for f in FIELDS:
        arr = []
        for i, yr in enumerate(ALL_YEARS):
            if yr in (LATEST_YEAR, CURRENT_YEAR):
                val = yd.get(yr, {}).get(f) if yr in yd else None
                arr.append(val if val is not None else None)
            elif yr in COMPLETED[:4]:
                val = PRELOADED.get(sym, {}).get(f, [None]*len(ALL_YEARS))[i]
                if sym in ("ADRO","ITMG","POWR"):
                    if f in ("eps","dps"): val = round(val*idr_ps,4) if val is not None else None
                    else: val = round(val*idr_total,4) if val is not None else None
                arr.append(val)
            else: arr.append(None)
        out[f] = arr
    return out

# ---------- PRELOADED DATA (2021–2024) ----------
PRELOADED = {
    "BHP": {"totalAsset":[54.2,51.9,55.7,81.5,None,None],"cash":[14.9,12.4,13.9,13.3,None,None],"totalDebt":[14.5,12.4,14.8,26.7,None,None],"totalEquity":[26.4,28.0,29.7,32.4,None,None],"revenue":[60.8,65.1,53.8,55.7,None,None],"grossProfit":[36.2,40.5,28.3,28.5,None,None],"netProfit":[11.3,30.9,12.9,7.9,None,None],
             "eps":[2.21,6.05,2.55,1.55,None,None],
             "dps":[3.01,5.43,1.70,1.09,1.20,None]},
    "WDS": {"totalAsset":[40.3,50.5,48.3,48.0,None,None],"cash":[2.8,3.1,2.5,2.2,None,None],"totalDebt":[7.9,15.2,12.8,12.0,None,None],"totalEquity":[18.2,22.4,20.1,20.0,None,None],"revenue":[10.0,13.9,12.3,12.5,None,None],"grossProfit":[5.8,8.6,7.1,7.2,None,None],"netProfit":[2.5,6.0,3.5,1.7,None,None],
             "eps":[0.80,1.70,1.00,0.48,None,None],
             "dps":[0.55,1.30,0.90,0.43,0.50,None]},
    "CBA": {"totalAsset":[925.0,1012.0,1085.0,1150.0,None,None],"cash":[98.0,105.0,112.0,120.0,None,None],"totalDebt":[165.0,172.0,180.0,195.0,None,None],"totalEquity":[62.0,65.0,68.0,72.0,None,None],"revenue":[23.5,24.1,25.2,26.5,None,None],"grossProfit":[19.8,20.4,21.3,22.4,None,None],"netProfit":[9.6,10.2,10.5,10.7,None,None],
             "eps":[5.6,5.9,6.1,6.2,None,None],
             "dps":[3.50,3.70,3.90,4.10,4.30,None]},
    "NAB": {"totalAsset":[925.0,1005.0,1059.0,1080.0,None,None],"cash":[109.0,125.0,120.0,113.0,None,None],"totalDebt":[172.0,185.0,198.0,214.0,None,None],"totalEquity":[62.8,59.0,61.2,61.5,None,None],"revenue":[16.7,18.3,20.6,20.6,None,None],"grossProfit":[13.8,14.8,16.8,16.8,None,None],"netProfit":[6.4,6.9,7.4,7.0,None,None],
             "eps":[1.93,2.14,2.36,2.25,None,None],
             "dps":[0.82,1.24,1.38,1.52,None,None]},
    "ANZ": {"totalAsset":[978.0,1085.7,1105.6,1229.1,None,None],"cash":[120.0,157.5,146.4,113.0,None,None],"totalDebt":[140.0,134.0,150.1,205.1,None,None],"totalEquity":[60.0,65.9,69.5,69.9,None,None],"revenue":[17.5,19.0,20.2,20.4,None,None],"grossProfit":[14.0,14.9,16.6,16.1,None,None],"netProfit":[6.0,7.1,7.1,6.5,None,None],
             "eps":[2.00,2.50,2.37,2.18,None,None],
             "dps":[1.20,1.46,1.62,1.66,None,None]},
    "BBRI": {"totalAsset":[1635,1865,1965,2073,None,None],"cash":[163,186,196,207,None,None],"totalDebt":[1380,1570,1650,1730,None,None],"totalEquity":[255,295,315,343,None,None],"revenue":[135,150,165,187,None,None],"grossProfit":[85,95,104,118,None,None],"netProfit":[25,43,51,60,None,None],
              "eps":[1019,1753,2086,398,None,None],
              "dps":[460,791,940,None,1150,None]},
    "ADRO": {"totalAsset":[80,100,85,92,None,None],"cash":[10,20,15,16,None,None],"totalDebt":[18,25,18,16,None,None],"totalEquity":[58,72,62,68,None,None],"revenue":[65,120,80,85,None,None],"grossProfit":[24,55,35,38,None,None],"netProfit":[8,30,15,16,None,None],
              "eps":[256,960,480,510,520,None],
              "dps":[130,480,240,255,260,None]},
    "ITMG": {"totalAsset":[19,26,20,21,None,None],"cash":[6,12,8,7,None,None],"totalDebt":[0.8,1.0,0.8,0.7,None,None],"totalEquity":[16,22,17,18,None,None],"revenue":[36,65,42,45,None,None],"grossProfit":[10,25,14,13,None,None],"netProfit":[5,16,8,7,None,None],
              "eps":[4530,14493,7246,6344,6500,None],
              "dps":[4000,13000,6500,5710,5800,None]},
    "POWR": {"totalAsset":[9.5,10.0,10.5,11.0,None,None],"cash":[1.3,1.4,1.5,1.6,None,None],"totalDebt":[2.0,1.8,1.6,1.4,None,None],"totalEquity":[5.8,6.5,7.2,7.8,None,None],"revenue":[5.0,5.2,5.5,5.8,None,None],"grossProfit":[2.0,2.1,2.2,2.3,None,None],"netProfit":[0.95,1.00,1.10,1.15,None,None],
              "eps":[95,100,110,115,120,None],
              "dps":[57,60,66,69,70,None]},
    "SMSM": {"totalAsset":[2.6,2.8,3.0,3.2,None,None],"cash":[0.9,1.0,1.1,1.2,None,None],"totalDebt":[0.35,0.30,0.30,0.25,None,None],"totalEquity":[2.0,2.2,2.4,2.6,None,None],"revenue":[2.5,2.8,3.2,3.4,None,None],"grossProfit":[0.82,0.92,1.05,1.12,None,None],"netProfit":[0.43,0.51,0.58,0.62,None,None],
              "eps":[183,217,247,264,270,None],
              "dps":[138,164,186,198,200,None]},
    "UNTR": {"totalAsset":[118,130,138,145,None,None],"cash":[16,18,20,22,None,None],"totalDebt":[23,20,18,16,None,None],"totalEquity":[78,88,97,105,None,None],"revenue":[108,125,130,135,None,None],"grossProfit":[25,30,32,33,None,None],"netProfit":[13,16,17,18,None,None],
              "eps":[3510,4320,4590,1860,None,None],
              "dps":[1580,1944,2065,2187,2200,None]},
    "MPMX": {"totalAsset":[9.0,9.5,10.0,10.5,None,None],"cash":[1.5,1.6,1.7,1.8,None,None],"totalDebt":[2.4,2.2,2.0,1.8,None,None],"totalEquity":[4.8,5.3,5.8,6.3,None,None],"revenue":[12.5,13.0,13.5,14.0,None,None],"grossProfit":[2.1,2.2,2.3,2.4,None,None],"netProfit":[0.40,0.45,0.50,0.55,None,None],
              "eps":[93,105,116,128,130,None],
              "dps":[40,45,50,55,55,None]},
    "BTPS": {"totalAsset":[24,27,30,32,None,None],"cash":[2.4,2.7,3.0,3.2,None,None],"totalDebt":[19,21,23.5,25,None,None],"totalEquity":[5.0,6.0,6.5,7.0,None,None],"revenue":[7.0,8.0,9.0,9.5,None,None],"grossProfit":[4.2,4.8,5.4,5.7,None,None],"netProfit":[1.2,1.8,2.0,2.1,None,None],
              "eps":[413,557,618,650,660,None],
              "dps":[124,167,185,195,195,None]},
    "DMAS": {"totalAsset":[7.0,7.5,8.0,8.5,None,None],"cash":[1.8,2.0,2.2,2.4,None,None],"totalDebt":[1.0,0.9,0.8,0.7,None,None],"totalEquity":[5.5,6.0,6.5,7.0,None,None],"revenue":[1.8,2.2,2.8,2.5,None,None],"grossProfit":[1.2,1.6,2.0,1.8,None,None],"netProfit":[0.7,0.9,1.1,1.0,None,None],
              "eps":[35,45,55,50,52,None],
              "dps":[24,32,38,35,35,None]},
    "SPTO": {"totalAsset":[2.6,2.7,2.8,2.9,None,None],"cash":[0.32,0.35,0.38,0.40,None,None],"totalDebt":[0.70,0.65,0.60,0.55,None,None],"totalEquity":[1.55,1.70,1.85,1.98,None,None],"revenue":[1.9,2.0,2.1,2.2,None,None],"grossProfit":[0.69,0.73,0.77,0.80,None,None],"netProfit":[0.25,0.27,0.30,0.32,None,None],
              "eps":[278,300,333,356,360,None],
              "dps":[139,150,167,178,178,None]},
    "TSM": {"totalAsset":[133,175,206,209,248,None],"cash":[40,52,54,57,87,None],"totalDebt":[20,30,38,40,33,None],"totalEquity":[71,92,107,134,170,None],"revenue":[57,77,70,91,119,None],"grossProfit":[30,42,37,51,71,None],"netProfit":[22,31,27,37,53,None],
             "eps":[4.18,6.14,5.07,7.09,10.36,None],
             "dps":[1.72,1.72,1.76,2.19,2.82,None]},
    "V": {"totalAsset":[82.9,85.5,90.5,94.5,92.6,None],"cash":[15.7,16.3,11.9,11.6,17.2,None],"totalDebt":[22.4,20.5,20.5,20.8,25.2,None],"totalEquity":[35.6,38.7,38.3,38.0,32.9,None],"revenue":[24.1,29.3,32.7,35.9,40.0,None],"grossProfit":[20.1,24.9,28.1,31.4,35.1,None],"netProfit":[12.3,15.0,17.3,19.7,20.1,None],
           "eps":[5.74,7.12,8.23,9.74,10.22,None],
           "dps":[1.28,1.50,1.80,2.08,2.34,None]},
    "MA": {"totalAsset":[43.0,46.4,46.8,46.5,47.0,None],"cash":[8.0,7.8,7.4,8.0,8.5,None],"totalDebt":[14.2,15.7,15.8,16.6,17.0,None],"totalEquity":[6.0,5.5,5.3,5.0,5.5,None],"revenue":[18.9,22.2,25.1,28.2,31.0,None],"grossProfit":[13.3,16.0,18.4,21.1,23.5,None],"netProfit":[8.7,10.5,11.2,12.9,14.6,None],
           "eps":[8.76,10.61,11.44,13.89,15.60,None],
           "dps":[1.76,2.00,2.28,2.64,2.97,None]},
    "PBR-A": {"totalAsset":[247,280,279,264,None,None],"cash":[11,18,16,15,None,None],"totalDebt":[87,80,69,62,None,None],"totalEquity":[96,124,128,118,None,None],"revenue":[77,115,90,88,None,None],"grossProfit":[38,68,48,44,None,None],"netProfit":[9,37,24,19,None,None],
               "eps":[1.30,5.35,3.46,2.74,2.80,None],
               "dps":[0.60,3.80,2.60,2.10,2.20,None]},
    "MSFT": {"totalAsset":[333.8,364.8,411.9,484.3,523.0,None],"cash":[130.3,104.8,111.3,80.0,71.6,None],"totalDebt":[67.8,61.3,69.9,97.9,97.2,None],"totalEquity":[141.9,166.5,166.5,233.0,287.0,None],"revenue":[168.1,198.3,211.9,245.1,279.6,None],"grossProfit":[115.9,135.6,146.1,171.0,195.1,None],"netProfit":[61.3,72.7,72.4,88.1,106.0,None],
              "eps":[8.12,9.65,9.72,11.45,14.16,None],
              "dps":[2.24,2.48,2.72,3.00,3.32,None]},
    "AMZN": {"totalAsset":[420.5,462.7,527.9,527.5,624.9,None],"cash":[96.1,70.0,73.9,86.8,101.2,None],"totalDebt":[116.4,155.6,161.5,164.8,173.0,None],"totalEquity":[138.2,146.0,143.3,171.3,236.9,None],"revenue":[469.8,514.0,524.9,637.0,760.0,None],"grossProfit":[197.5,226.2,240.6,283.0,351.0,None],"netProfit":[33.4,-2.7,20.1,59.2,64.0,None],
              "eps":[64.81,-5.36,3.99,11.53,12.10,None],
              "dps":[None,None,None,None,None,None]},
    "AAPL": {"totalAsset":[351.0,352.8,352.6,353.5,364.9,None],"cash":[69.0,48.3,55.2,65.2,53.8,None],"totalDebt":[136.5,132.5,123.9,128.5,97.3,None],"totalEquity":[63.1,50.7,62.1,74.2,56.9,None],"revenue":[365.8,394.3,383.3,391.0,436.0,None],"grossProfit":[152.8,170.8,169.1,180.7,203.0,None],"netProfit":[94.7,99.8,97.0,101.0,94.0,None],
              "eps":[5.61,6.11,6.13,6.43,6.08,None],
              "dps":[0.85,0.91,0.94,0.97,1.00,None]},
    "META": {"totalAsset":[165.9,185.7,185.7,229.6,276.1,None],"cash":[47.9,40.7,31.8,49.3,77.8,None],"totalDebt":[10.2,27.5,18.4,28.8,28.8,None],"totalEquity":[124.9,125.1,128.3,153.2,182.6,None],"revenue":[117.9,116.6,134.9,185.0,235.0,None],"grossProfit":[100.1,97.3,113.0,156.9,200.0,None],"netProfit":[39.4,23.2,39.1,62.4,78.0,None],
              "eps":[13.77,8.59,14.87,23.86,31.00,None],
              "dps":[None,None,None,2.00,2.00,None]},
    "NVDA": {"totalAsset":[28.8,44.2,41.2,65.7,111.6,None],"cash":[11.6,19.3,13.3,25.0,43.2,None],"totalDebt":[6.9,11.7,11.0,10.0,8.5,None],"totalEquity":[16.9,26.1,26.1,42.6,65.7,None],"revenue":[16.7,26.9,27.0,60.9,130.5,None],"grossProfit":[10.4,17.5,15.4,42.0,97.9,None],"netProfit":[4.3,9.8,4.4,29.8,72.9,None],
              "eps":[1.73,3.85,1.74,11.93,29.24,None],
              "dps":[0.016,0.016,0.016,0.016,0.01,None]},
    "GOOG": {"totalAsset":[359.3,391.4,402.0,430.3,450.0,None],"cash":[142.0,139.6,115.0,108.1,95.7,None],"totalDebt":[14.8,15.1,14.7,14.7,15.0,None],"totalEquity":[251.6,256.1,272.3,314.1,360.0,None],"revenue":[257.6,282.8,307.4,350.0,385.0,None],"grossProfit":[146.7,156.6,174.1,208.1,237.0,None],"netProfit":[76.0,60.0,73.8,100.1,115.0,None],
              "eps":[5.61,4.56,5.80,7.79,9.27,None],
              "dps":[None,None,None,0.60,0.8125,None]},
    "BKNG": {"totalAsset":[25.5,26.8,30.7,31.8,33.0,None],"cash":[11.2,12.4,15.1,16.8,17.5,None],"totalDebt":[15.4,13.8,14.0,12.0,11.0,None],"totalEquity":[0.5,1.4,4.0,7.0,9.0,None],"revenue":[11.0,17.1,21.4,23.7,26.0,None],"grossProfit":[9.7,15.2,19.0,21.2,23.1,None],"netProfit":[1.1,3.0,4.3,4.8,6.0,None],
              "eps":[25.0,72.0,110.0,130.0,165.0,None],
              "dps":[None,None,None,1.40,1.536,None]},
    "AVGO": {"totalAsset":[75.0,73.2,72.9,165.6,171.1,169.9],"cash":[12.0,12.4,14.2,9.3,16.2,14.2],"totalDebt":[40.0,39.5,39.2,67.6,65.1,66.1],"totalEquity":[24.0,22.7,24.0,67.7,81.3,79.9],"revenue":[27.0,33.2,35.8,51.6,63.9,19.3],"grossProfit":[18.0,22.1,24.7,32.5,43.3,13.2],"netProfit":[6.7,11.5,14.1,5.9,23.1,7.3],
              "eps":[1.60,2.74,3.39,1.27,4.91,None],
              "dps":[1.49,1.69,1.905,2.17,2.42,None]},
    "CVX": {"totalAsset":[253.0,257.7,261.6,256.9,324.0,None],"cash":[12.5,17.7,8.2,6.8,6.3,None],"totalDebt":[28.0,23.3,20.8,24.5,40.8,None],"totalEquity":[151.0,159.3,161.0,152.3,186.5,None],"revenue":[140.0,235.7,196.9,193.4,184.4,None],"grossProfit":[45.0,74.0,60.4,56.9,56.1,None],"netProfit":[15.8,35.5,21.4,17.7,12.3,None],
             "eps":[8.20,18.36,11.41,9.76,6.65,None],
             "dps":[5.10,5.68,6.05,6.52,6.90,None]},
    "AXP": {"totalAsset":[200.0,228.4,261.1,271.5,300.1,None],"cash":[28.0,33.5,46.5,40.6,47.7,None],"totalDebt":[38.0,43.9,49.2,51.1,57.8,None],"totalEquity":[22.0,24.7,28.1,30.3,33.5,None],"revenue":[45.0,52.9,60.5,65.9,72.2,None],"grossProfit":[8.5,9.9,13.1,15.5,17.4,None],"netProfit":[6.5,7.5,8.4,10.1,10.8,None],
             "eps":[8.50,9.86,11.23,14.04,15.41,None],
             "dps":[1.80,2.08,2.42,2.81,3.27,None]},
    "BAC": {"totalAsset":[2900.0,3051.4,3180.2,3261.3,3411.7,None],"cash":[220.0,237.5,341.4,296.5,239.3,None],"totalDebt":[280.0,302.9,334.3,326.7,365.9,None],"totalEquity":[260.0,273.2,291.6,294.0,303.2,None],"revenue":[90.0,95.0,102.8,105.9,113.1,None],"grossProfit":[48.0,52.5,56.9,56.1,60.1,None],"netProfit":[26.0,27.5,26.3,27.0,30.5,None],
             "eps":[3.10,3.21,3.10,3.25,3.86,None],
             "dps":[0.90,1.06,1.13,1.21,1.27,None]},
    "WBC": {
        "totalAsset":[850.0,900.0,950.0,1000.0,None,None],
        "cash":[70.0,75.0,80.0,85.0,None,None],
        "totalDebt":[150.0,160.0,170.0,180.0,None,None],
        "totalEquity":[60.0,62.0,65.0,68.0,None,None],
        "revenue":[17.8,19.0,20.5,22.0,None,None],
        "grossProfit":[17.8,19.0,20.5,22.0,None,None],
        "netProfit":[5.0,5.5,6.0,7.0,None,None],
        "eps":[1.50,1.65,1.80,2.00,None,None],
        "dps":[1.20,1.30,1.40,1.50,None,None]
    },
    "RHHBY": {
        "totalAsset":[90.0,95.0,98.0,100.0,None,None],
        "cash":[10.0,11.0,12.0,13.0,None,None],
        "totalDebt":[30.0,32.0,33.0,34.0,None,None],
        "totalEquity":[45.0,48.0,50.0,52.0,None,None],
        "revenue":[60.0,65.0,68.0,70.0,None,None],
        "grossProfit":[45.0,48.0,50.0,52.0,None,None],
        "netProfit":[12.0,13.0,13.5,14.0,None,None],
        "eps":[2.50,2.70,2.80,2.90,None,None],
        "dps":[1.50,1.60,1.65,1.70,None,None]
    },
    "ESSA": {
        "totalAsset":   [809.29, 831.30, 695.44, 693.68, None, None],
        "cash":         [80.84, 163.98, 107.93, 157.87, None, None],
        "totalDebt":    [508.51, 305.93, 197.70, 139.80, None, None],
        "totalEquity":  [300.78, 525.36, 497.74, 553.88, None, None],
        "revenue":      [303.44, 731.49, 344.96, 301.40, None, None],
        "costOfRevenue":[193.15, 390.33, 241.87, 193.40, None, None],
        "grossProfit":  [110.29, 341.16, 103.09, 108.00, None, None],
        "operatingExpense":[23.88, 39.41, 26.05, 25.99, None, None],
        "operatingIncome":[86.41, 301.76, 77.04, 82.01, None, None],
        "interestExpense":[71.00, 30.88, 16.36, 9.34, None, None],
        "incomeTaxExpense":[-4.26, 55.27, 15.06, 16.21, None, None],
        "netProfit":    [13.97, 138.84, 34.61, 45.18, None, None],
        "eps":          [53, 526, 131, 171, None, None],
        "dps":          [15, 40, 20, 30, None, None],
    },
    "FMG": {
        "totalAsset":   [26.0, 30.5, 32.8, 34.6, None, None],
        "cash":         [4.5, 5.2, 4.8, 5.0, None, None],
        "totalDebt":    [6.5, 7.0, 6.8, 6.2, None, None],
        "totalEquity":  [16.0, 18.5, 20.5, 22.0, None, None],
        "revenue":      [16.0, 18.3, 16.7, 17.0, None, None],
        "grossProfit":  [8.0, 10.0, 8.5, 8.7, None, None],
        "netProfit":    [5.2, 7.0, 5.8, 5.6, None, None],
        "eps":          [1.80, 2.45, 2.05, 1.95, None, None],
        "dps":          [0.80, 1.20, 0.90, 0.85, None, None],
    },
    "STO": {
        "totalAsset":   [20.0, 24.0, 26.0, 27.0, None, None],
        "cash":         [2.0, 3.0, 2.5, 2.0, None, None],
        "totalDebt":    [7.0, 8.0, 9.0, 9.0, None, None],
        "totalEquity":  [11.0, 13.0, 14.0, 15.0, None, None],
        "revenue":      [4.3, 7.8, 5.9, 5.6, None, None],
        "grossProfit":  [2.0, 4.0, 2.8, 2.6, None, None],
        "netProfit":    [0.8, 2.8, 1.4, 1.2, None, None],
        "eps":          [0.25, 0.85, 0.42, 0.36, None, None],
        "dps":          [0.10, 0.30, 0.20, 0.18, None, None],
    },
    "ALD": {
        "totalAsset":   [12.5, 12.8, 12.9, 12.9, None, None],
        "cash":         [0.3,  0.6,  0.3,  0.1,  None, None],
        "totalDebt":    [4.2,  3.9,  3.7,  4.1,  None, None],
        "totalEquity":  [3.4,  3.6,  3.6,  3.2,  None, None],
        "revenue":      [22.0, 39.1, 37.7, 34.9, None, None],
        "grossProfit":  [1.8,  2.9,  2.4,  2.1,  None, None],
        "netProfit":    [0.6,  0.8,  0.5,  0.1,  None, None],
        "eps":          [2.3,  3.2,  2.1,  0.5,  None, None],
        "dps":          [1.1,  1.5,  1.6,  1.5,  None, None],
    },
    "MQG": {
        "totalAsset":   [255.8, 245.7, 399.2, 387.9, 403.4, None],
        "cash":         [32.1,  41.5,  68.7,  74.2,  85.3,  None],
        "totalDebt":    [110.2, 98.4,  170.5, 165.6, 172.3, None],
        "totalEquity":  [23.1,  25.4,  28.9,  30.2,  34.0,  None],
        "revenue":      [14.2,  17.3,  19.1,  19.1,  16.9,  None],
        "grossProfit":  [14.2,  17.3,  19.1,  19.1,  16.9,  None],
        "netProfit":    [3.0,   4.7,   5.2,   5.2,   3.5,   None],
        "eps":          [8.2,   12.1,  13.5,  13.5,  9.2,   None],
        "dps":          [4.7,   6.8,   7.5,   7.5,   6.2,   None],
    },
    "ASML": {
        "totalAsset":   [30.2,  36.3,  39.9,  48.6,  None, None],
        "cash":         [7.6,   7.4,   7.0,   12.7,  None, None],
        "totalDebt":    [4.6,   4.3,   4.6,   4.7,   None, None],
        "totalEquity":  [10.1,  8.8,   13.5,  18.5,  None, None],
        "revenue":      [18.6,  21.2,  27.6,  28.3,  None, None],
        "grossProfit":  [9.6,   10.5,  13.8,  14.1,  None, None],
        "netProfit":    [5.9,   5.6,   7.8,   7.6,   None, None],
        "eps":          [14.2,  13.5,  19.2,  19.3,  None, None],
        "dps":          [2.8,   3.2,   4.4,   5.4,   None, None],
    },
}

# ---------- PROFILES & LEADERSHIP (unchanged, abbreviated for brevity) ----------
# [Keep all existing PROFILES and LEADERSHIP content as in your file]

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
            time.sleep(1.2)
        try:
            yd, cur_ann, src = fetch_live(sym, exchange, ticker_str, hint_cur, usd_aud, usd_idr, twd_usd)
            arrs = build_arrays(yd, sym, rates)
            if any(v is not None for r in yd.values() for v in r.values()):
                ok += 1
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
    print(f"\n{'='*50}\nWritten: {path}\nLive data: {ok}/{len(all_stocks)}\n{'='*50}", flush=True)

if __name__ == "__main__":
    main()
