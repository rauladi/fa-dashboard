import json, os, math, time, requests
from datetime import datetime, timezone
import yfinance as yf

# ---------- constants ----------
NOW = datetime.now(timezone.utc)
CURRENT_YEAR = NOW.year
LATEST_YEAR = CURRENT_YEAR - 1
COMPLETED = list(range(LATEST_YEAR - 4, LATEST_YEAR + 1))   # 2021..2025
ALL_YEARS = COMPLETED + [CURRENT_YEAR]                       # 2026

FMP_API_KEY = os.environ.get("FMP_API_KEY")
USE_FMP = bool(FMP_API_KEY)

FMP_BASE = "https://financialmodelingprep.com/api/v3"

print(f"FA Dashboard fetch – {NOW.strftime('%Y-%m-%d %H:%M UTC')}", flush=True)
print(f"Source: {'FMP + Yahoo fallback' if USE_FMP else 'Yahoo only'}", flush=True)
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
              "dps":[460,791,940,1100,1150,None]},
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

# ---------- Yahoo Finance fetch (fallback) ----------
def fetch_one_yahoo(sym, exchange, ticker_str, hint_cur, usd_aud, usd_idr, twd_usd):
    print(f"\n[{sym}] (Yahoo) {ticker_str}", flush=True)
    target_cur = hint_cur.upper()
    for attempt in range(2):
        try:
            if attempt > 0:
                time.sleep(5)
            tk = yf.Ticker(ticker_str)
            fin_cur = financial_currency(exchange)
            div, total_fx, ps_fx = get_fx(target_cur, fin_cur, usd_aud, usd_idr, twd_usd)
            print(f"  cur={fin_cur}  target={target_cur}  total_fx={total_fx:.6f}  ps_fx={ps_fx:.6f}", flush=True)

            inc = tk.financials
            bs = tk.balance_sheet
            qi = tk.quarterly_financials
            qb = tk.quarterly_balance_sheet

            def find_row(df, *names):
                if df is None or df.empty: return None
                lower_idx = {str(idx).strip().lower(): idx for idx in df.index}
                for n in names:
                    key = n.strip().lower()
                    if key in lower_idx: return df.loc[lower_idx[key]]
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

            def get_ttm_col(df):
                if df is None or df.empty: return None
                for c in df.columns:
                    col_str = str(c).strip().lower()
                    if col_str == "ttm": return c
                for c in df.columns:
                    if "ttm" in str(c).lower(): return c
                return None

            def annual_row(ic_col=None, bc_col=None):
                row = {f: None for f in FIELDS}
                if inc is not None and ic_co
