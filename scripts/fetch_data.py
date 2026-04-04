import json, os, math, time, random, urllib.request
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

# ---------- FALLBACK DATA (same as your HTML's PRELOADED) ----------
PRELOADED = {
    "BHP": {"totalAsset":[54.2,51.9,55.7,81.5,None,None],"cash":[14.9,12.4,13.9,13.3,None,None],"totalDebt":[14.5,12.4,14.8,26.7,None,None],"totalEquity":[26.4,28.0,29.7,32.4,None,None],"revenue":[60.8,65.1,53.8,55.7,None,None],"grossProfit":[36.2,40.5,28.3,28.5,None,None],"netProfit":[11.3,30.9,12.9,7.9,None,None],"eps":[2.21,6.05,2.55,1.55,None,None],"dps":[3.01,5.43,1.70,1.09,None,None]},
    "WDS": {"totalAsset":[40.3,50.5,48.3,48.0,None,None],"cash":[2.8,3.1,2.5,2.2,None,None],"totalDebt":[7.9,15.2,12.8,12.0,None,None],"totalEquity":[18.2,22.4,20.1,20.0,None,None],"revenue":[10.0,13.9,12.3,12.5,None,None],"grossProfit":[5.8,8.6,7.1,7.2,None,None],"netProfit":[2.5,6.0,3.5,1.7,None,None],"eps":[0.80,1.70,1.00,0.48,None,None],"dps":[0.55,1.30,0.90,0.43,None,None]},
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
    "TSM": {"totalAsset":[133,175,206,209,248,None],"cash":[40,52,54,57,87,None],"totalDebt":[20,30,38,40,33,None],"totalEquity":[71,92,107,134,170,None],"revenue":[57,77,70,91,119,None],"grossProfit":[30,42,37,51,71,None],"netProfit":[22,31,27,37,53,None],"eps":[4.18,6.14,5.07,7.09,10.36,None],"dps":[1.72,1.72,1.76,2.19,2.82,None]},
    "V": {"totalAsset":[82.9,85.5,90.5,94.5,92.6,None],"cash":[15.7,16.3,11.9,11.6,17.2,None],"totalDebt":[22.4,20.5,20.5,20.8,25.2,None],"totalEquity":[35.6,38.7,38.3,38.0,32.9,None],"revenue":[24.1,29.3,32.7,35.9,40.0,None],"grossProfit":[20.1,24.9,28.1,31.4,35.1,None],"netProfit":[12.3,15.0,17.3,19.7,20.1,None],"eps":[5.74,7.12,8.23,9.74,10.22,None],"dps":[1.28,1.50,1.80,2.08,2.34,None]},
    "MA": {"totalAsset":[43.0,46.4,46.8,46.5,47.0,None],"cash":[8.0,7.8,7.4,8.0,8.5,None],"totalDebt":[14.2,15.7,15.8,16.6,17.0,None],"totalEquity":[6.0,5.5,5.3,5.0,5.5,None],"revenue":[18.9,22.2,25.1,28.2,31.0,None],"grossProfit":[13.3,16.0,18.4,21.1,23.5,None],"netProfit":[8.7,10.5,11.2,12.9,14.6,None],"eps":[8.76,10.61,11.44,13.89,15.60,None],"dps":[1.76,2.00,2.28,2.64,2.97,None]},
    "PBR-A": {"totalAsset":[247,280,279,264,None,None],"cash":[11,18,16,15,None,None],"totalDebt":[87,80,69,62,None,None],"totalEquity":[96,124,128,118,None,None],"revenue":[77,115,90,88,None,None],"grossProfit":[38,68,48,44,None,None],"netProfit":[9,37,24,19,None,None],"eps":[1.30,5.35,3.46,2.74,None,None],"dps":[0.60,3.80,2.60,2.10,None,None]},
    "MSFT": {"totalAsset":[333.8,364.8,411.9,484.3,523.0,None],"cash":[130.3,104.8,111.3,80.0,71.6,None],"totalDebt":[67.8,61.3,69.9,97.9,97.2,None],"totalEquity":[141.9,166.5,166.5,233.0,287.0,None],"revenue":[168.1,198.3,211.9,245.1,279.6,None],"grossProfit":[115.9,135.6,146.1,171.0,195.1,None],"netProfit":[61.3,72.7,72.4,88.1,106.0,None],"eps":[8.12,9.65,9.72,11.45,14.16,None],"dps":[2.24,2.48,2.72,3.00,3.32,None]},
    "AMZN": {"totalAsset":[420.5,462.7,527.9,527.5,624.9,None],"cash":[96.1,70.0,73.9,86.8,101.2,None],"totalDebt":[116.4,155.6,161.5,164.8,173.0,None],"totalEquity":[138.2,146.0,143.3,171.3,236.9,None],"revenue":[469.8,514.0,524.9,637.0,760.0,None],"grossProfit":[197.5,226.2,240.6,283.0,351.0,None],"netProfit":[33.4,-2.7,20.1,59.2,64.0,None],"eps":[64.81,-5.36,3.99,11.53,12.10,None],"dps":[None,None,None,None,None,None]},
    "AAPL": {"totalAsset":[351.0,352.8,352.6,353.5,364.9,None],"cash":[69.0,48.3,55.2,65.2,53.8,None],"totalDebt":[136.5,132.5,123.9,128.5,97.3,None],"totalEquity":[63.1,50.7,62.1,74.2,56.9,None],"revenue":[365.8,394.3,383.3,391.0,436.0,None],"grossProfit":[152.8,170.8,169.1,180.7,203.0,None],"netProfit":[94.7,99.8,97.0,101.0,94.0,None],"eps":[5.61,6.11,6.13,6.43,6.08,None],"dps":[0.85,0.91,0.94,0.97,1.00,None]},
    "META": {"totalAsset":[165.9,185.7,185.7,229.6,276.1,None],"cash":[47.9,40.7,31.8,49.3,77.8,None],"totalDebt":[10.2,27.5,18.4,28.8,28.8,None],"totalEquity":[124.9,125.1,128.3,153.2,182.6,None],"revenue":[117.9,116.6,134.9,185.0,235.0,None],"grossProfit":[100.1,97.3,113.0,156.9,200.0,None],"netProfit":[39.4,23.2,39.1,62.4,78.0,None],"eps":[13.77,8.59,14.87,23.86,31.00,None],"dps":[None,None,None,None,2.00,None]},
    "NVDA": {"totalAsset":[28.8,44.2,41.2,65.7,111.6,None],"cash":[11.6,19.3,13.3,25.0,43.2,None],"totalDebt":[6.9,11.7,11.0,10.0,8.5,None],"totalEquity":[16.9,26.1,26.1,42.6,65.7,None],"revenue":[16.7,26.9,27.0,60.9,130.5,None],"grossProfit":[10.4,17.5,15.4,42.0,97.9,None],"netProfit":[4.3,9.8,4.4,29.8,72.9,None],"eps":[1.73,3.85,1.74,11.93,29.24,None],"dps":[0.016,0.016,0.016,0.016,0.01,None]},
    "GOOG": {"totalAsset":[359.3,391.4,402.0,430.3,450.0,None],"cash":[142.0,139.6,115.0,108.1,95.7,None],"totalDebt":[14.8,15.1,14.7,14.7,15.0,None],"totalEquity":[251.6,256.1,272.3,314.1,360.0,None],"revenue":[257.6,282.8,307.4,350.0,385.0,None],"grossProfit":[146.7,156.6,174.1,208.1,237.0,None],"netProfit":[76.0,60.0,73.8,100.1,115.0,None],"eps":[5.61,4.56,5.80,7.79,9.27,None],"dps":[None,None,None,None,None,None]},
    "BKNG": {"totalAsset":[25.5,26.8,30.7,31.8,33.0,None],"cash":[11.2,12.4,15.1,16.8,17.5,None],"totalDebt":[15.4,13.8,14.0,12.0,11.0,None],"totalEquity":[0.5,1.4,4.0,7.0,9.0,None],"revenue":[11.0,17.1,21.4,23.7,26.0,None],"grossProfit":[9.7,15.2,19.0,21.2,23.1,None],"netProfit":[1.1,3.0,4.3,4.8,6.0,None],"eps":[25.0,72.0,110.0,130.0,165.0,None],"dps":[None,None,None,None,None,None]},
}

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
        ai=tk.financials; ab=tk.balance_sheet; cf=tk.cashflow
        if ai is not None and not ai.empty and col_yr(ai,yr) is not None:
            r = annual_row(ai, ab, cf, yr, div, fx, epsfx)
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

# ---------- Gemini API with retries ----------
def call_gemini_with_retry(prompt, api_key, max_tokens=2500, retries=3):
    import urllib.request, json as jsonlib
    model = "gemini-2.0-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    body = jsonlib.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.2}
    }).encode()

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = jsonlib.loads(resp.read())
                parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                return "".join(p.get("text","") for p in parts) or None
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 10 * (2 ** attempt)  # 10, 20, 40 seconds
                print(f"  Rate limit (429), retrying in {wait}s...", flush=True)
                time.sleep(wait)
                continue
            else:
                print(f"  Gemini API HTTP error {e.code}: {e.reason}", flush=True)
                return None
        except Exception as e:
            print(f"  Gemini API error: {e}", flush=True)
            return None
    print("  Max retries exceeded, giving up.", flush=True)
    return None

def build_ai_prompt(sym, name, exchange, ticker, metrics):
    return f"""You are a professional equity analyst. Write a comprehensive, deep-dive investment analysis for {name} ({ticker}, {exchange}).

First, here are the company's key financial metrics (based on actual data):
- Revenue CAGR (last {metrics['years']} years): {metrics['rev_cagr']}
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

    if not api_key.startswith("AIza"):
        print("API key does not start with AIza – Gemini requires that prefix.", flush=True)
        return

    print(f"\n{'='*50}\nGenerating AI profiles via Gemini 2.0 Flash for {len(all_stocks)} stocks...\n{'='*50}", flush=True)

    for sym, (name, exchange, ticker, *_) in all_stocks.items():
        metrics = all_metrics.get(sym)
        if not metrics:
            print(f"  [{sym}] No metrics available, skipping", flush=True)
            continue

        prompt = build_ai_prompt(sym, name, exchange, ticker, metrics)
        print(f"  [{sym}] generating analysis...", flush=True)

        profile = call_gemini_with_retry(prompt, api_key, max_tokens=3000, retries=3)
        if profile:
            out["stocks"][sym]["profile"] = profile
            out["stocks"][sym]["profileDate"] = NOW.isoformat()
            print(f"  [{sym}] profile generated ({len(profile)} chars)", flush=True)
        else:
            print(f"  [!] No profile for {sym}", flush=True)
            out["stocks"][sym]["profile"] = generate_fallback_analysis(sym, name, exchange, metrics)
            out["stocks"][sym]["profileDate"] = NOW.isoformat()

        time.sleep(8)  # stay under rate limits

        news_prompt = f"""Summarize the 5 most recent important fundamental business developments for {name} ({ticker}, {exchange}).

For each, use exactly:
## [Headline]
**Date:** [period]  **Relevance:** [Bullish/Bearish/Neutral]
[2-3 sentences on what happened and why it matters for long-term investors]

Focus on: earnings, revenue changes, strategy, acquisitions, dividends, regulations. Skip pure price news."""
        print(f"  [{sym}] news...", flush=True)
        news = call_gemini_with_retry(news_prompt, api_key, max_tokens=1500, retries=3)
        if news:
            out["stocks"][sym]["news"] = news
            out["stocks"][sym]["newsDate"] = NOW.isoformat()
            print(f"  [{sym}] news generated ({len(news)} chars)", flush=True)
        else:
            out["stocks"][sym]["news"] = f"Recent news for {name} could not be retrieved. Please check company announcements."
            out["stocks"][sym]["newsDate"] = NOW.isoformat()

        time.sleep(8)

    print("AI content generation complete.", flush=True)

def generate_fallback_analysis(sym, name, exchange, metrics):
    return f"""## Business Model Canvas
**Key Partners:** Suppliers, distributors, and strategic partners in the {exchange} market.
**Key Activities:** Core operations including production, sales, and service delivery.
**Key Resources:** Financial capital, intellectual property, physical assets, and human resources.
**Value Proposition:** Delivering quality products/services to customers. Revenue CAGR {metrics['rev_cagr']}, net margin {metrics['npm_avg']}.
**Customer Relationships:** Long-term contracts, dedicated account management, after-sales support.
**Channels:** Direct sales, distributor network, online platforms.
**Customer Segments:** Diverse customer base across domestic and international markets.
**Cost Structure:** Raw materials, labour, overheads, R&D. Debt/equity {metrics['de_avg']}.
**Revenue Streams:** Product sales, service fees, recurring revenue.

## SWOT Analysis
**Strengths:** Revenue growth {metrics['rev_cagr']}, ROE {metrics['roe_avg']}, gross margin {metrics['gpm_avg']}.
**Weaknesses:** Net margin {metrics['npm_avg']}, debt/equity {metrics['de_avg']}.
**Opportunities:** Market expansion, operational efficiency, product innovation.
**Threats:** Competition, regulatory changes, economic cycles.

## PESTLE Analysis
Political, economic, social, technological, legal, and environmental factors all influence the company's operating environment. Specific risks vary by jurisdiction and sector.

## Porter's Five Forces
Competitive rivalry, threat of new entrants, supplier power, buyer power, and threat of substitutes are all factors that shape the industry's profitability.

## Management & Decision Making
Capital allocation focuses on shareholder returns and reinvestment. Buffett test score: {metrics['buffett']}.

## Future Outlook
The company's outlook depends on its ability to maintain growth, manage costs, and adapt to industry trends. Watch revenue growth, margin stability, and capital allocation."""

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
    all_metrics = {}

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

        # Compute metrics for AI prompt
        rev_arr = arrs["revenue"]
        np_arr = arrs["netProfit"]
        gp_arr = arrs["grossProfit"]
        ep_arr = arrs["eps"]
        ta_arr = arrs["totalAsset"]
        ca_arr = arrs["cash"]
        te_arr = arrs["totalEquity"]
        td_arr = arrs["totalDebt"]
        dp_arr = arrs["dps"]

        valid = lambda arr: [v for v in arr if v is not None and v != 0]
        rev_valid = valid(rev_arr)
        np_valid = valid(np_arr)

        def cagr(arr):
            if len(arr) < 2:
                return "N/A"
            start = arr[0]
            end = arr[-1]
            years = len(arr) - 1
            if start <= 0 or end <= 0:
                return "N/A"
            return f"{(pow(end/start, 1/years)-1)*100:.1f}%"

        def avg_ratio(num_arr, den_arr):
            ratios = []
            for n, d in zip(num_arr, den_arr):
                if n is not None and d is not None and d != 0:
                    ratios.append(n/d * 100)
            if not ratios:
                return "N/A"
            return f"{sum(ratios)/len(ratios):.1f}%"

        buffett = "N/A"
        if len(ep_arr) >= 2:
            eps_start = ep_arr[0]
            eps_end = ep_arr[-1]
            if eps_start is not None and eps_end is not None and eps_start != 0:
                eps_inc = eps_end - eps_start
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

    # Try multiple possible secret names
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY", "")

    if api_key:
        generate_ai_content(all_stocks, out, api_key, all_metrics)
    else:
        print("No API key found in environment (tried ANTHROPIC_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY).", flush=True)
        print("Skipping AI generation. Financial data only.", flush=True)

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n{'='*50}\nWritten: {path}\nLive yfinance: {ok}/{len(all_stocks)}\n{'='*50}", flush=True)

if __name__ == "__main__":
    main()
