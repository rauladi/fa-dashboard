#!/usr/bin/env python3
"""
FA Dashboard Data Fetcher — runs via GitHub Actions monthly.

For COMPLETED years: uses full-year annual data.
For CURRENT year (in-progress): uses YTD quarterly data, annualised:
    3M YTD  ÷ 3  × 12  = ×4      (Q1 only)
    6M YTD  ÷ 6  × 12  = ×2      (Q1+Q2)
    9M YTD  ÷ 9  × 12  = ×1.333  (Q1+Q2+Q3)
    FY      (all 4 Q's or annual exists) → use actual, no annualisation

Balance-sheet items (totalAsset, cash, totalDebt, totalEquity) are
point-in-time, so they're taken directly from the most recent quarter
without any annualisation factor.

DPS for the current year is annualised the same way as flow items.
EPS is taken directly from the income statement if available; otherwise
annualised from quarterly netProfit ÷ shares.
"""

import json, os, math
from datetime import datetime, timezone

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    os.system("pip install yfinance pandas --quiet")
    import yfinance as yf
    import pandas as pd

# ── Constants ────────────────────────────────────────────────────────
NOW         = datetime.now(timezone.utc)
CURRENT_YEAR = NOW.year
LATEST_YEAR  = CURRENT_YEAR - 1          # last fully completed year
YEARS        = list(range(LATEST_YEAR - 4, LATEST_YEAR + 1))   # 5 completed years
CURRENT_DATA_YEAR = CURRENT_YEAR         # slot we populate with annualised estimate

ALL_YEARS    = YEARS + [CURRENT_DATA_YEAR]   # 6 slots in output arrays

STOCKS = {
    "BHP":  ("BHP Group",               "ASX", "BHP.AX",  "B AUD", 1e9),
    "WDS":  ("Woodside Energy",          "ASX", "WDS.AX",  "B AUD", 1e9),
    "BBRI": ("Bank Rakyat Indonesia",    "IDX", "BBRI.JK", "T IDR", 1e12),
    "ADRO": ("Adaro Energy",             "IDX", "ADRO.JK", "T IDR", 1e12),
    "SMSM": ("Selamat Sempurna",         "IDX", "SMSM.JK", "T IDR", 1e12),
    "UNTR": ("United Tractors",          "IDX", "UNTR.JK", "T IDR", 1e12),
    "ITMG": ("Indo Tambangraya Megah",   "IDX", "ITMG.JK", "T IDR", 1e12),
    "POWR": ("Cikarang Listrindo",       "IDX", "POWR.JK", "T IDR", 1e12),
    "MPMX": ("Mitra Pinasthika Mustika", "IDX", "MPMX.JK", "T IDR", 1e12),
    "BTPS": ("Bank BTPN Syariah",        "IDX", "BTPS.JK", "T IDR", 1e12),
    "DMAS": ("Puradelta Lestari",        "IDX", "DMAS.JK", "T IDR", 1e12),
    "SPTO": ("Surya Toto Indonesia",     "IDX", "SPTO.JK", "T IDR", 1e12),
}

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

# ── Helpers ──────────────────────────────────────────────────────────
def safe_val(val, divisor=1):
    if val is None: return None
    try:
        f = float(val)
        return None if (math.isnan(f) or math.isinf(f)) else round(f / divisor, 6)
    except (TypeError, ValueError):
        return None

def get_row(df, *names):
    """Return the first matching row from a DataFrame by index name."""
    for n in names:
        if n in df.index:
            return df.loc[n]
    return None

def cols_for_year(df, yr):
    """Return all columns whose timestamp year == yr, sorted oldest→newest."""
    if df is None or df.empty: return []
    cols = [c for c in df.columns if hasattr(c, 'year') and c.year == yr]
    return sorted(cols)

def latest_col_for_year(df, yr):
    cols = cols_for_year(df, yr)
    return cols[-1] if cols else None

def sum_cols(series, cols):
    """Sum a pandas Series across the given column labels, ignoring NaN."""
    total = 0.0
    found = False
    for c in cols:
        v = safe_val(series[c] if series is not None else None)
        if v is not None:
            total += v
            found = True
    return total if found else None

# ── Annualisation factor based on months of data ──────────────────────
def annualise_factor(months_of_data):
    """
    months_of_data: 3, 6, 9, or 12
    Returns (factor, label) e.g. (4.0, "3M×4") or (1.0, "FY")
    """
    if months_of_data <= 0:
        return None, None
    factor = 12.0 / months_of_data
    if months_of_data >= 12:
        return 1.0, "FY"
    months_label = f"{months_of_data}M"
    # Format factor nicely
    if factor == int(factor):
        factor_label = f"×{int(factor)}"
    else:
        factor_label = f"×{factor:.3f}"
    return factor, f"{months_label}{factor_label}"

def detect_months_covered(qtrs_in_year):
    """
    Given a sorted list of quarterly column timestamps for the current year,
    estimate how many months of data we have.
    Each quarter = 3 months. Yahoo quarters end roughly Mar/Jun/Sep/Dec.
    """
    return len(qtrs_in_year) * 3  # 1 qtr=3M, 2=6M, 3=9M, 4=12M

# ── Main per-stock fetch ──────────────────────────────────────────────
def fetch_one(symbol, ticker_str, divisor):
    print(f"  [{symbol}] {ticker_str} ...", flush=True)
    try:
        tk = yf.Ticker(ticker_str)

        # ── Annual statements ──────────────────────────────────────
        ann_inc = tk.financials          # annual income
        ann_bs  = tk.balance_sheet       # annual balance sheet
        ann_cf  = tk.cashflow            # annual cash flow

        if ann_inc is None or ann_inc.empty:
            raise ValueError("No annual income statement")

        # ── Quarterly statements ───────────────────────────────────
        try:
            q_inc = tk.quarterly_financials
            q_bs  = tk.quarterly_balance_sheet
            q_cf  = tk.quarterly_cashflow
        except Exception:
            q_inc = q_bs = q_cf = None

        result      = {}
        annual_info = {}   # per-year metadata for current year annualisation

        # ═══ COMPLETED YEARS (use annual data) ════════════════════
        for yr in YEARS:
            ic = latest_col_for_year(ann_inc, yr)
            bc = latest_col_for_year(ann_bs,  yr)
            cc = latest_col_for_year(ann_cf,  yr)
            row = {}

            if ic is not None:
                rv = get_row(ann_inc,"Total Revenue","TotalRevenue")
                gp = get_row(ann_inc,"Gross Profit","GrossProfit")
                ni = get_row(ann_inc,"Net Income","NetIncome",
                             "Net Income Common Stockholders",
                             "Net Income Including Noncontrolling Interests")
                ep = get_row(ann_inc,"Basic EPS","BasicEPS","Diluted EPS","EPS Diluted")
                sh = get_row(ann_inc,"Basic Average Shares","BasicAverageShares",
                             "Diluted Average Shares","Average Dilution Earnings")
                row["revenue"]     = safe_val(rv[ic] if rv is not None else None, divisor)
                row["grossProfit"] = safe_val(gp[ic] if gp is not None else None, divisor)
                row["netProfit"]   = safe_val(ni[ic] if ni is not None else None, divisor)
                row["eps"]         = safe_val(ep[ic] if ep is not None else None, 1)
                row["_sh"]         = safe_val(sh[ic] if sh is not None else None, 1)
            else:
                row.update(revenue=None,grossProfit=None,netProfit=None,eps=None,_sh=None)

            if bc is not None:
                ta = get_row(ann_bs,"Total Assets","TotalAssets")
                ca = get_row(ann_bs,"Cash And Cash Equivalents","Cash",
                             "CashAndCashEquivalents","Cash And Short Term Investments")
                td = get_row(ann_bs,"Total Debt","TotalDebt",
                             "Long Term Debt And Capital Lease Obligation","Long Term Debt")
                te = get_row(ann_bs,"Stockholders Equity","Total Stockholder Equity",
                             "Common Stock Equity","Total Equity Gross Minority Interest")
                row["totalAsset"]  = safe_val(ta[bc] if ta is not None else None, divisor)
                row["cash"]        = safe_val(ca[bc] if ca is not None else None, divisor)
                row["totalDebt"]   = safe_val(td[bc] if td is not None else None, divisor)
                row["totalEquity"] = safe_val(te[bc] if te is not None else None, divisor)
            else:
                row.update(totalAsset=None,cash=None,totalDebt=None,totalEquity=None)

            if cc is not None and row.get("_sh"):
                dp = get_row(ann_cf,"Cash Dividends Paid","Dividends Paid",
                             "Common Stock Dividend Paid","Payment Of Dividends")
                dv = safe_val(dp[cc] if dp is not None else None, 1)
                sh = row["_sh"]
                row["dps"] = round(abs(dv)/sh, 6) if dv is not None and sh and sh > 0 else None
            else:
                row["dps"] = None

            result[yr] = row

        # ═══ CURRENT YEAR — quarterly annualised estimate ══════════
        yr = CURRENT_DATA_YEAR
        row = {}
        annual_info[yr] = {"method": "none", "label": None, "quarters": 0, "months": 0, "asOf": None}

        # First check: does annual data already exist for this year?
        # (happens if full-year results published before script runs)
        ann_ic = latest_col_for_year(ann_inc, yr)
        if ann_ic is not None:
            # Full year results already published — use them directly
            ic, bc, cc = ann_ic, latest_col_for_year(ann_bs, yr), latest_col_for_year(ann_cf, yr)
            rv = get_row(ann_inc,"Total Revenue","TotalRevenue")
            gp = get_row(ann_inc,"Gross Profit","GrossProfit")
            ni = get_row(ann_inc,"Net Income","NetIncome","Net Income Common Stockholders","Net Income Including Noncontrolling Interests")
            ep = get_row(ann_inc,"Basic EPS","BasicEPS","Diluted EPS","EPS Diluted")
            sh = get_row(ann_inc,"Basic Average Shares","BasicAverageShares","Diluted Average Shares","Average Dilution Earnings")
            row["revenue"]     = safe_val(rv[ic] if rv is not None else None, divisor)
            row["grossProfit"] = safe_val(gp[ic] if gp is not None else None, divisor)
            row["netProfit"]   = safe_val(ni[ic] if ni is not None else None, divisor)
            row["eps"]         = safe_val(ep[ic] if ep is not None else None, 1)
            row["_sh"]         = safe_val(sh[ic] if sh is not None else None, 1)
            if bc is not None:
                ta = get_row(ann_bs,"Total Assets","TotalAssets")
                ca = get_row(ann_bs,"Cash And Cash Equivalents","Cash","CashAndCashEquivalents","Cash And Short Term Investments")
                td = get_row(ann_bs,"Total Debt","TotalDebt","Long Term Debt And Capital Lease Obligation","Long Term Debt")
                te = get_row(ann_bs,"Stockholders Equity","Total Stockholder Equity","Common Stock Equity","Total Equity Gross Minority Interest")
                row["totalAsset"]  = safe_val(ta[bc] if ta is not None else None, divisor)
                row["cash"]        = safe_val(ca[bc] if ca is not None else None, divisor)
                row["totalDebt"]   = safe_val(td[bc] if td is not None else None, divisor)
                row["totalEquity"] = safe_val(te[bc] if te is not None else None, divisor)
            else:
                row.update(totalAsset=None,cash=None,totalDebt=None,totalEquity=None)
            if cc is not None and row.get("_sh"):
                dp = get_row(ann_cf,"Cash Dividends Paid","Dividends Paid","Common Stock Dividend Paid","Payment Of Dividends")
                dv = safe_val(dp[cc] if dp is not None else None, 1)
                sh = row["_sh"]
                row["dps"] = round(abs(dv)/sh, 6) if dv is not None and sh and sh > 0 else None
            else:
                row["dps"] = None
            annual_info[yr] = {"method":"full_year","label":"FY","quarters":4,"months":12,"asOf":str(ann_ic.date())}
            print(f"    CY {yr}: Full year results available", flush=True)

        elif q_inc is not None and not q_inc.empty:
            # Use quarterly data — find all quarters reported for this year
            qtrs = cols_for_year(q_inc, yr)

            if not qtrs:
                # No quarters yet for current year
                row.update(revenue=None,grossProfit=None,netProfit=None,eps=None,_sh=None,
                           totalAsset=None,cash=None,totalDebt=None,totalEquity=None,dps=None)
                annual_info[yr] = {"method":"none","label":None,"quarters":0,"months":0,"asOf":None}
                print(f"    CY {yr}: No quarterly data yet", flush=True)
            else:
                n_qtrs  = len(qtrs)
                months  = detect_months_covered(qtrs)
                factor, label = annualise_factor(months)
                latest_q = qtrs[-1]   # most recent quarter end date

                # ── Flow items: sum all YTD quarters then annualise ──
                rv = get_row(q_inc,"Total Revenue","TotalRevenue")
                gp = get_row(q_inc,"Gross Profit","GrossProfit")
                ni = get_row(q_inc,"Net Income","NetIncome","Net Income Common Stockholders","Net Income Including Noncontrolling Interests")
                ep = get_row(q_inc,"Basic EPS","BasicEPS","Diluted EPS","EPS Diluted")
                sh = get_row(q_inc,"Basic Average Shares","BasicAverageShares","Diluted Average Shares","Average Dilution Earnings")

                def annualise_flow(series):
                    ytd = sum_cols(series, qtrs)
                    if ytd is None: return None
                    return round(ytd / divisor * factor, 6)

                def annualise_eps(series):
                    ytd = sum_cols(series, qtrs)
                    if ytd is None: return None
                    return round(ytd * factor, 6)

                row["revenue"]     = annualise_flow(rv)
                row["grossProfit"] = annualise_flow(gp)
                row["netProfit"]   = annualise_flow(ni)
                row["eps"]         = annualise_eps(ep)
                row["_sh"]         = safe_val(sh[latest_q] if sh is not None else None, 1)

                # ── Balance sheet: point-in-time, use latest quarter only ──
                latest_bs_q = latest_col_for_year(q_bs, yr) if q_bs is not None and not q_bs.empty else None
                if latest_bs_q is not None:
                    ta = get_row(q_bs,"Total Assets","TotalAssets")
                    ca = get_row(q_bs,"Cash And Cash Equivalents","Cash","CashAndCashEquivalents","Cash And Short Term Investments")
                    td = get_row(q_bs,"Total Debt","TotalDebt","Long Term Debt And Capital Lease Obligation","Long Term Debt")
                    te = get_row(q_bs,"Stockholders Equity","Total Stockholder Equity","Common Stock Equity","Total Equity Gross Minority Interest")
                    row["totalAsset"]  = safe_val(ta[latest_bs_q] if ta is not None else None, divisor)
                    row["cash"]        = safe_val(ca[latest_bs_q] if ca is not None else None, divisor)
                    row["totalDebt"]   = safe_val(td[latest_bs_q] if td is not None else None, divisor)
                    row["totalEquity"] = safe_val(te[latest_bs_q] if te is not None else None, divisor)
                else:
                    row.update(totalAsset=None,cash=None,totalDebt=None,totalEquity=None)

                # ── DPS: annualise dividends paid YTD ──────────────────
                latest_cf_q = latest_col_for_year(q_cf, yr) if q_cf is not None and not q_cf.empty else None
                cf_qtrs = cols_for_year(q_cf, yr) if q_cf is not None and not q_cf.empty else []
                sh_val = row.get("_sh")
                if cf_qtrs and sh_val:
                    dp = get_row(q_cf,"Cash Dividends Paid","Dividends Paid","Common Stock Dividend Paid","Payment Of Dividends")
                    ytd_div = sum_cols(dp, cf_qtrs)
                    if ytd_div is not None and sh_val > 0:
                        row["dps"] = round(abs(ytd_div) / sh_val * factor, 6)
                    else:
                        row["dps"] = None
                else:
                    row["dps"] = None

                annual_info[yr] = {
                    "method":   "annualised",
                    "label":    label,
                    "quarters": n_qtrs,
                    "months":   months,
                    "factor":   round(factor, 6),
                    "asOf":     str(latest_q.date()),
                }
                print(f"    CY {yr}: {n_qtrs} quarter(s) → {label} (factor ×{factor:.4f}, as of {latest_q.date()})", flush=True)
        else:
            row.update(revenue=None,grossProfit=None,netProfit=None,eps=None,_sh=None,
                       totalAsset=None,cash=None,totalDebt=None,totalEquity=None,dps=None)
            print(f"    CY {yr}: No quarterly data available", flush=True)

        result[yr] = row

        live_completed = [y for y in YEARS if result[y].get("revenue") is not None]
        print(f"    Completed years with data: {live_completed}", flush=True)
        return result, annual_info

    except Exception as e:
        print(f"    FAIL: {e}", flush=True)
        return None, {}


def build_arrays(year_data, annul_info, fb):
    """
    Build output arrays for ALL_YEARS (completed + current year).
    For each field, prefer live year_data, fall back to FALLBACK.
    """
    fields = ["totalAsset","cash","totalDebt","totalEquity",
              "revenue","grossProfit","netProfit","eps","dps"]
    out = {}
    for field in fields:
        arr = []
        for i, yr in enumerate(ALL_YEARS):
            lv = year_data[yr].get(field) if year_data and yr in year_data else None
            fv = fb[field][i] if fb and i < len(fb.get(field, [])) else None
            arr.append(lv if lv is not None else fv)
        out[field] = arr
    return out


# ── Main ─────────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"FA Dashboard Data Fetch")
    print(f"Run time     : {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"Completed yrs: {YEARS}")
    print(f"Current year : {CURRENT_DATA_YEAR} (annualised from quarterly data)")
    print(f"{'='*60}")

    out = {
        "generated":       NOW.isoformat(),
        "years":           ALL_YEARS,
        "completedYears":  YEARS,
        "currentYear":     CURRENT_DATA_YEAR,
        "latestYear":      LATEST_YEAR,
        "annualisation":   {},   # per-symbol current-year metadata
        "stocks":          {}
    }

    ok = 0
    for sym, (name, exchange, ticker_str, currency, divisor) in STOCKS.items():
        print(f"\n{'─'*40}\n[{sym}] {name}", flush=True)
        year_data, ann_info = fetch_one(sym, ticker_str, divisor)
        fb   = FALLBACK.get(sym, {})
        arrs = build_arrays(year_data, ann_info, fb)
        src  = "yfinance" if year_data else "fallback"
        if year_data:
            ok += 1

        out["stocks"][sym] = {
            "name":     name,
            "exchange": exchange,
            "currency": currency,
            "ticker":   ticker_str,
            "source":   src,
            **arrs
        }
        # Store current-year annualisation metadata per symbol
        if CURRENT_DATA_YEAR in ann_info:
            out["annualisation"][sym] = ann_info[CURRENT_DATA_YEAR]

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Written  : {path}")
    print(f"Live data: {ok}/{len(STOCKS)} stocks")
    print(f"Fallback : {len(STOCKS)-ok}/{len(STOCKS)} stocks")
    print(f"Current year annualisation summary:")
    for sym, info in out["annualisation"].items():
        label = info.get("label") or "none"
        asof  = info.get("asOf") or "—"
        print(f"  {sym:6s}: {label:10s}  as of {asof}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
