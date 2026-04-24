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

# ---------- FALLBACK DATA ----------
PRELOADED = {
    "BHP": {"totalAsset":[54.2,51.9,55.7,81.5,None,None],"cash":[14.9,12.4,13.9,13.3,None,None],"totalDebt":[14.5,12.4,14.8,26.7,None,None],"totalEquity":[26.4,28.0,29.7,32.4,None,None],"revenue":[60.8,65.1,53.8,55.7,None,None],"grossProfit":[36.2,40.5,28.3,28.5,None,None],"netProfit":[11.3,30.9,12.9,7.9,None,None],"eps":[2.21,6.05,2.55,1.55,None,None],"dps":[3.01,5.43,1.70,1.09,1.20,None]},
    "WDS": {"totalAsset":[40.3,50.5,48.3,48.0,None,None],"cash":[2.8,3.1,2.5,2.2,None,None],"totalDebt":[7.9,15.2,12.8,12.0,None,None],"totalEquity":[18.2,22.4,20.1,20.0,None,None],"revenue":[10.0,13.9,12.3,12.5,None,None],"grossProfit":[5.8,8.6,7.1,7.2,None,None],"netProfit":[2.5,6.0,3.5,1.7,None,None],"eps":[0.80,1.70,1.00,0.48,None,None],"dps":[0.55,1.30,0.90,0.43,0.50,None]},
    "CBA": {"totalAsset":[925.0,1012.0,1085.0,1150.0,None,None],"cash":[98.0,105.0,112.0,120.0,None,None],"totalDebt":[165.0,172.0,180.0,195.0,None,None],"totalEquity":[62.0,65.0,68.0,72.0,None,None],"revenue":[23.5,24.1,25.2,26.5,None,None],"grossProfit":[19.8,20.4,21.3,22.4,None,None],"netProfit":[9.6,10.2,10.5,10.7,None,None],"eps":[5.6,5.9,6.1,6.2,None,None],"dps":[3.50,3.70,3.90,4.10,4.30,None]},
    "NAB": {"totalAsset":[925.0,1005.0,1059.0,1080.0,None,None],"cash":[109.0,125.0,120.0,113.0,None,None],"totalDebt":[172.0,185.0,198.0,214.0,None,None],"totalEquity":[62.8,59.0,61.2,61.5,None,None],"revenue":[16.7,18.3,20.6,20.6,None,None],"grossProfit":[13.8,14.8,16.8,16.8,None,None],"netProfit":[6.4,6.9,7.4,7.0,None,None],"eps":[1.93,2.14,2.36,2.25,None,None],"dps":[0.82,1.24,1.38,1.52,None,None]},
    "ANZ": {"totalAsset":[978.0,1085.7,1105.6,1229.1,None,None],"cash":[120.0,157.5,146.4,113.0,None,None],"totalDebt":[140.0,134.0,150.1,205.1,None,None],"totalEquity":[60.0,65.9,69.5,69.9,None,None],"revenue":[17.5,19.0,20.2,20.4,None,None],"grossProfit":[14.0,14.9,16.6,16.1,None,None],"netProfit":[6.0,7.1,7.1,6.5,None,None],"eps":[2.00,2.50,2.37,2.18,None,None],"dps":[1.20,1.46,1.62,1.66,None,None]},
    "BBRI": {"totalAsset":[1635,1865,1965,2073,None,None],"cash":[163,186,196,207,None,None],"totalDebt":[1380,1570,1650,1730,None,None],"totalEquity":[255,295,315,343,None,None],"revenue":[135,150,165,187,None,None],"grossProfit":[85,95,104,118,None,None],"netProfit":[25,43,51,60,None,None],"eps":[1019,1753,2086,2443,2650,None],"dps":[460,791,940,1100,1150,None]},
    "ADRO": {"totalAsset":[80,100,85,92,None,None],"cash":[10,20,15,16,None,None],"totalDebt":[18,25,18,16,None,None],"totalEquity":[58,72,62,68,None,None],"revenue":[65,120,80,85,None,None],"grossProfit":[24,55,35,38,None,None],"netProfit":[8,30,15,16,None,None],"eps":[256,960,480,510,520,None],"dps":[130,480,240,255,260,None]},
    "SMSM": {"totalAsset":[2.6,2.8,3.0,3.2,None,None],"cash":[0.9,1.0,1.1,1.2,None,None],"totalDebt":[0.35,0.30,0.30,0.25,None,None],"totalEquity":[2.0,2.2,2.4,2.6,None,None],"revenue":[2.5,2.8,3.2,3.4,None,None],"grossProfit":[0.82,0.92,1.05,1.12,None,None],"netProfit":[0.43,0.51,0.58,0.62,None,None],"eps":[183,217,247,264,270,None],"dps":[138,164,186,198,200,None]},
    "UNTR": {"totalAsset":[118,130,138,145,None,None],"cash":[16,18,20,22,None,None],"totalDebt":[23,20,18,16,None,None],"totalEquity":[78,88,97,105,None,None],"revenue":[108,125,130,135,None,None],"grossProfit":[25,30,32,33,None,None],"netProfit":[13,16,17,18,None,None],"eps":[3510,4320,4590,4860,4950,None],"dps":[1580,1944,2065,2187,2200,None]},
    "ITMG": {"totalAsset":[19,26,20,21,None,None],"cash":[6,12,8,7,None,None],"totalDebt":[0.8,1.0,0.8,0.7,None,None],"totalEquity":[16,22,17,18,None,None],"revenue":[36,65,42,45,None,None],"grossProfit":[10,25,14,13,None,None],"netProfit":[5,16,8,7,None,None],"eps":[4530,14493,7246,6344,6500,None],"dps":[4000,13000,6500,5710,5800,None]},
    "POWR": {"totalAsset":[9.5,10.0,10.5,11.0,None,None],"cash":[1.3,1.4,1.5,1.6,None,None],"totalDebt":[2.0,1.8,1.6,1.4,None,None],"totalEquity":[5.8,6.5,7.2,7.8,None,None],"revenue":[5.0,5.2,5.5,5.8,None,None],"grossProfit":[2.0,2.1,2.2,2.3,None,None],"netProfit":[0.95,1.00,1.10,1.15,None,None],"eps":[95,100,110,115,120,None],"dps":[57,60,66,69,70,None]},
    "MPMX": {"totalAsset":[9.0,9.5,10.0,10.5,None,None],"cash":[1.5,1.6,1.7,1.8,None,None],"totalDebt":[2.4,2.2,2.0,1.8,None,None],"totalEquity":[4.8,5.3,5.8,6.3,None,None],"revenue":[12.5,13.0,13.5,14.0,None,None],"grossProfit":[2.1,2.2,2.3,2.4,None,None],"netProfit":[0.40,0.45,0.50,0.55,None,None],"eps":[93,105,116,128,130,None],"dps":[40,45,50,55,55,None]},
    "BTPS": {"totalAsset":[24,27,30,32,None,None],"cash":[2.4,2.7,3.0,3.2,None,None],"totalDebt":[19,21,23.5,25,None,None],"totalEquity":[5.0,6.0,6.5,7.0,None,None],"revenue":[7.0,8.0,9.0,9.5,None,None],"grossProfit":[4.2,4.8,5.4,5.7,None,None],"netProfit":[1.2,1.8,2.0,2.1,None,None],"eps":[413,557,618,650,660,None],"dps":[124,167,185,195,195,None]},
    "DMAS": {"totalAsset":[7.0,7.5,8.0,8.5,None,None],"cash":[1.8,2.0,2.2,2.4,None,None],"totalDebt":[1.0,0.9,0.8,0.7,None,None],"totalEquity":[5.5,6.0,6.5,7.0,None,None],"revenue":[1.8,2.2,2.8,2.5,None,None],"grossProfit":[1.2,1.6,2.0,1.8,None,None],"netProfit":[0.7,0.9,1.1,1.0,None,None],"eps":[35,45,55,50,52,None],"dps":[24,32,38,35,35,None]},
    "SPTO": {"totalAsset":[2.6,2.7,2.8,2.9,None,None],"cash":[0.32,0.35,0.38,0.40,None,None],"totalDebt":[0.70,0.65,0.60,0.55,None,None],"totalEquity":[1.55,1.70,1.85,1.98,None,None],"revenue":[1.9,2.0,2.1,2.2,None,None],"grossProfit":[0.69,0.73,0.77,0.80,None,None],"netProfit":[0.25,0.27,0.30,0.32,None,None],"eps":[278,300,333,356,360,None],"dps":[139,150,167,178,178,None]},
    "TSM": {"totalAsset":[133,175,206,209,248,None],"cash":[40,52,54,57,87,None],"totalDebt":[20,30,38,40,33,None],"totalEquity":[71,92,107,134,170,None],"revenue":[57,77,70,91,119,None],"grossProfit":[30,42,37,51,71,None],"netProfit":[22,31,27,37,53,None],"eps":[4.18,6.14,5.07,7.09,10.36,None],"dps":[1.72,1.72,1.76,2.19,2.82,None]},
    "V": {"totalAsset":[82.9,85.5,90.5,94.5,92.6,None],"cash":[15.7,16.3,11.9,11.6,17.2,None],"totalDebt":[22.4,20.5,20.5,20.8,25.2,None],"totalEquity":[35.6,38.7,38.3,38.0,32.9,None],"revenue":[24.1,29.3,32.7,35.9,40.0,None],"grossProfit":[20.1,24.9,28.1,31.4,35.1,None],"netProfit":[12.3,15.0,17.3,19.7,20.1,None],"eps":[5.74,7.12,8.23,9.74,10.22,None],"dps":[1.28,1.50,1.80,2.08,2.34,None]},
    "MA": {"totalAsset":[43.0,46.4,46.8,46.5,47.0,None],"cash":[8.0,7.8,7.4,8.0,8.5,None],"totalDebt":[14.2,15.7,15.8,16.6,17.0,None],"totalEquity":[6.0,5.5,5.3,5.0,5.5,None],"revenue":[18.9,22.2,25.1,28.2,31.0,None],"grossProfit":[13.3,16.0,18.4,21.1,23.5,None],"netProfit":[8.7,10.5,11.2,12.9,14.6,None],"eps":[8.76,10.61,11.44,13.89,15.60,None],"dps":[1.76,2.00,2.28,2.64,2.97,None]},
    "PBR-A": {"totalAsset":[247,280,279,264,None,None],"cash":[11,18,16,15,None,None],"totalDebt":[87,80,69,62,None,None],"totalEquity":[96,124,128,118,None,None],"revenue":[77,115,90,88,None,None],"grossProfit":[38,68,48,44,None,None],"netProfit":[9,37,24,19,None,None],"eps":[1.30,5.35,3.46,2.74,2.80,None],"dps":[0.60,3.80,2.60,2.10,2.20,None]},
    "MSFT": {"totalAsset":[333.8,364.8,411.9,484.3,523.0,None],"cash":[130.3,104.8,111.3,80.0,71.6,None],"totalDebt":[67.8,61.3,69.9,97.9,97.2,None],"totalEquity":[141.9,166.5,166.5,233.0,287.0,None],"revenue":[168.1,198.3,211.9,245.1,279.6,None],"grossProfit":[115.9,135.6,146.1,171.0,195.1,None],"netProfit":[61.3,72.7,72.4,88.1,106.0,None],"eps":[8.12,9.65,9.72,11.45,14.16,None],"dps":[2.24,2.48,2.72,3.00,3.32,None]},
    "AMZN": {"totalAsset":[420.5,462.7,527.9,527.5,624.9,None],"cash":[96.1,70.0,73.9,86.8,101.2,None],"totalDebt":[116.4,155.6,161.5,164.8,173.0,None],"totalEquity":[138.2,146.0,143.3,171.3,236.9,None],"revenue":[469.8,514.0,524.9,637.0,760.0,None],"grossProfit":[197.5,226.2,240.6,283.0,351.0,None],"netProfit":[33.4,-2.7,20.1,59.2,64.0,None],"eps":[64.81,-5.36,3.99,11.53,12.10,None],"dps":[None,None,None,None,None,None]},
    "AAPL": {"totalAsset":[351.0,352.8,352.6,353.5,364.9,None],"cash":[69.0,48.3,55.2,65.2,53.8,None],"totalDebt":[136.5,132.5,123.9,128.5,97.3,None],"totalEquity":[63.1,50.7,62.1,74.2,56.9,None],"revenue":[365.8,394.3,383.3,391.0,436.0,None],"grossProfit":[152.8,170.8,169.1,180.7,203.0,None],"netProfit":[94.7,99.8,97.0,101.0,94.0,None],"eps":[5.61,6.11,6.13,6.43,6.08,None],"dps":[0.85,0.91,0.94,0.97,1.00,None]},
    "META": {"totalAsset":[165.9,185.7,185.7,229.6,276.1,None],"cash":[47.9,40.7,31.8,49.3,77.8,None],"totalDebt":[10.2,27.5,18.4,28.8,28.8,None],"totalEquity":[124.9,125.1,128.3,153.2,182.6,None],"revenue":[117.9,116.6,134.9,185.0,235.0,None],"grossProfit":[100.1,97.3,113.0,156.9,200.0,None],"netProfit":[39.4,23.2,39.1,62.4,78.0,None],"eps":[13.77,8.59,14.87,23.86,31.00,None],"dps":[None,None,None,2.00,2.00,None]},
    "NVDA": {"totalAsset":[28.8,44.2,41.2,65.7,111.6,None],"cash":[11.6,19.3,13.3,25.0,43.2,None],"totalDebt":[6.9,11.7,11.0,10.0,8.5,None],"totalEquity":[16.9,26.1,26.1,42.6,65.7,None],"revenue":[16.7,26.9,27.0,60.9,130.5,None],"grossProfit":[10.4,17.5,15.4,42.0,97.9,None],"netProfit":[4.3,9.8,4.4,29.8,72.9,None],"eps":[1.73,3.85,1.74,11.93,29.24,None],"dps":[0.016,0.016,0.016,0.016,0.01,None]},
    "GOOG": {"totalAsset":[359.3,391.4,402.0,430.3,450.0,None],"cash":[142.0,139.6,115.0,108.1,95.7,None],"totalDebt":[14.8,15.1,14.7,14.7,15.0,None],"totalEquity":[251.6,256.1,272.3,314.1,360.0,None],"revenue":[257.6,282.8,307.4,350.0,385.0,None],"grossProfit":[146.7,156.6,174.1,208.1,237.0,None],"netProfit":[76.0,60.0,73.8,100.1,115.0,None],"eps":[5.61,4.56,5.80,7.79,9.27,None],"dps":[None,None,None,0.60,0.8125,None]},
    "BKNG": {"totalAsset":[25.5,26.8,30.7,31.8,33.0,None],"cash":[11.2,12.4,15.1,16.8,17.5,None],"totalDebt":[15.4,13.8,14.0,12.0,11.0,None],"totalEquity":[0.5,1.4,4.0,7.0,9.0,None],"revenue":[11.0,17.1,21.4,23.7,26.0,None],"grossProfit":[9.7,15.2,19.0,21.2,23.1,None],"netProfit":[1.1,3.0,4.3,4.8,6.0,None],"eps":[25.0,72.0,110.0,130.0,165.0,None],"dps":[None,None,None,1.40,1.536,None]},
    "AVGO": {"totalAsset":[75.0,73.2,72.9,165.6,171.1,169.9],"cash":[12.0,12.4,14.2,9.3,16.2,14.2],"totalDebt":[40.0,39.5,39.2,67.6,65.1,66.1],"totalEquity":[24.0,22.7,24.0,67.7,81.3,79.9],"revenue":[27.0,33.2,35.8,51.6,63.9,19.3],"grossProfit":[18.0,22.1,24.7,32.5,43.3,13.2],"netProfit":[6.7,11.5,14.1,5.9,23.1,7.3],"eps":[1.60,2.74,3.39,1.27,4.91,None],"dps":[1.49,1.69,1.905,2.17,2.42,None]},
    "CVX": {"totalAsset":[253.0,257.7,261.6,256.9,324.0,None],"cash":[12.5,17.7,8.2,6.8,6.3,None],"totalDebt":[28.0,23.3,20.8,24.5,40.8,None],"totalEquity":[151.0,159.3,161.0,152.3,186.5,None],"revenue":[140.0,235.7,196.9,193.4,184.4,None],"grossProfit":[45.0,74.0,60.4,56.9,56.1,None],"netProfit":[15.8,35.5,21.4,17.7,12.3,None],"eps":[8.20,18.36,11.41,9.76,6.65,None],"dps":[5.10,5.68,6.05,6.52,6.90,None]},
    "AXP": {"totalAsset":[200.0,228.4,261.1,271.5,300.1,None],"cash":[28.0,33.5,46.5,40.6,47.7,None],"totalDebt":[38.0,43.9,49.2,51.1,57.8,None],"totalEquity":[22.0,24.7,28.1,30.3,33.5,None],"revenue":[45.0,52.9,60.5,65.9,72.2,None],"grossProfit":[8.5,9.9,13.1,15.5,17.4,None],"netProfit":[6.5,7.5,8.4,10.1,10.8,None],"eps":[8.50,9.86,11.23,14.04,15.41,None],"dps":[1.80,2.08,2.42,2.81,3.27,None]},
    "BAC": {"totalAsset":[2900.0,3051.4,3180.2,3261.3,3411.7,None],"cash":[220.0,237.5,341.4,296.5,239.3,None],"totalDebt":[280.0,302.9,334.3,326.7,365.9,None],"totalEquity":[260.0,273.2,291.6,294.0,303.2,None],"revenue":[90.0,95.0,102.8,105.9,113.1,None],"grossProfit":[48.0,52.5,56.9,56.1,60.1,None],"netProfit":[26.0,27.5,26.3,27.0,30.5,None],"eps":[3.10,3.21,3.10,3.25,3.86,None],"dps":[0.90,1.06,1.13,1.21,1.27,None]},
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

def annual_row(inc, bs, cf, yr, div, fx, sym):
    row = {}
    ic = col_yr(inc, yr)
    bc = col_yr(bs, yr)

    if ic is not None:
        rv = find_row(inc,"Total Revenue","TotalRevenue","Interest Income","InterestIncome")
        gp = find_row(inc,"Gross Profit","GrossProfit","Net Interest Income","NetInterestIncome")
        ni = find_row(inc,"Net Income","NetIncome","Net Income Common Stockholders")
        ep = find_row(inc,"Basic EPS","BasicEPS","Diluted EPS","EPS Diluted")

        rev_raw = safe(rv[ic] if rv is not None else None, 1, 1)
        gp_raw  = safe(gp[ic] if gp is not None else None, 1, 1)
        np_raw  = safe(ni[ic] if ni is not None else None, 1, 1)
        eps_raw = safe(ep[ic] if ep is not None else None, 1, 1)

        row["revenue"]     = safe(rev_raw, div, fx)
        row["grossProfit"] = safe(gp_raw, div, fx)
        row["netProfit"]   = safe(np_raw, div, fx)
        row["eps"] = eps_raw
    else:
        row.update(revenue=None,grossProfit=None,netProfit=None,eps=None)

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

    row["dps"] = None
    return row

def annualise_year(tk, yr, div, fx, sym):
    inc = tk.financials
    bs = tk.balance_sheet
    row = None
    ic = None

    # 1) Try full fiscal year from annual financials
    if inc is not None and not inc.empty:
        ic = col_yr(inc, yr)
        if ic is not None:
            row = annual_row(inc, bs, None, yr, div, fx, sym)
            if row.get("revenue") is not None:
                return row, {"method":"full_year","label":"FY","quarters":4,"asOf":str(ic.date())}

    # 2) For LATEST_YEAR, attempt fiscal-year TTM; if that fails, fall back to generic quarterly
    if yr == LATEST_YEAR:
        qi = tk.quarterly_financials
        qb = tk.quarterly_balance_sheet
        if qi is not None and not qi.empty:
            all_qtrs = sorted(qi.columns, reverse=True)
            if all_qtrs:
                fy_end_month = FISCAL_YEAR_END.get(sym, 12)
                # Try to get quarters belonging to the exact fiscal year
                target_qtrs = []
                for q in all_qtrs:
                    q_year = q.year
                    q_month = q.month
                    fiscal_year = q_year if q_month <= fy_end_month else q_year + 1
                    if fiscal_year == yr:
                        target_qtrs.append(q)
                # If no quarters found for this fiscal year, use the most recent 4 quarters as fallback
                if not target_qtrs:
                    target_qtrs = all_qtrs[:4]
                if target_qtrs:
                    target_qtrs = sorted(target_qtrs, reverse=True)[:4]
                    n = len(target_qtrs)
                    months = n * 3
                    factor = 12.0 / months
                    lq = target_qtrs[0]
                    label = "FY" if months >= 12 else f"{months}M x{int(factor) if factor==int(factor) else round(factor,3)}"

                    def sum_q_field(field_name):
                        s = find_row(qi, field_name)
                        if s is None: return None
                        total = 0.0
                        for c in target_qtrs:
                            v = safe(s[c])
                            if v is not None: total += v
                        return total if total != 0.0 else None

                    row = {f: None for f in FIELDS}
                    row["revenue"] = sum_q_field("Total Revenue")
                    row["grossProfit"] = sum_q_field("Gross Profit")
                    row["netProfit"] = sum_q_field("Net Income")
                    eps_field = find_row(qi, "Basic EPS", "Diluted EPS", "EPS Diluted", "BasicEPS")
                    row["eps"] = None
                    if eps_field is not None:
                        total_eps = 0.0
                        for c in target_qtrs:
                            v = safe(eps_field[c])
                            if v is not None: total_eps += v
                        row["eps"] = total_eps if total_eps != 0.0 else None
                    row["dps"] = None

                    # Only return TTM row if we actually got some revenue data
                    if row["revenue"] is not None:
                        qbc = target_qtrs[0]
                        if qb is not None and not qb.empty and qbc in qb.columns:
                            ta = find_row(qb, "Total Assets")
                            ca = find_row(qb, "Cash And Cash Equivalents")
                            td = find_row(qb, "Total Debt")
                            te = find_row(qb, "Stockholders Equity")
                            row["totalAsset"] = safe(ta[qbc] if ta is not None else None, div, fx)
                            row["cash"] = safe(ca[qbc] if ca is not None else None, div, fx)
                            row["totalDebt"] = safe(td[qbc] if td is not None else None, div, fx)
                            row["totalEquity"] = safe(te[qbc] if te is not None else None, div, fx)

                        for k in ["revenue","grossProfit","netProfit","eps"]:
                            if row[k] is not None:
                                row[k] = round(row[k] / div * fx, 4)

                        ann = {"method":"annualised","label":label,"quarters":n,"months":months,"factor":round(factor,4),"asOf":str(lq.date())}
                        print(f"      {yr}: {n}Q → {label} as of {lq.date()}", flush=True)
                        return row, ann

    # 3) Fallback to generic quarterly (for years before LATEST_YEAR, or if TTM failed)
    qi = tk.quarterly_financials
    qb = tk.quarterly_balance_sheet
    if qi is None or qi.empty:
        return {f: None for f in FIELDS}, {"method":"none","label":None}
    qtrs = cols_yr(qi, yr)
    if not qtrs:
        return {f: None for f in FIELDS}, {"method":"none","label":None}
    n = len(qtrs)
    months = n * 3
    factor = 12.0 / months
    lq = qtrs[-1]
    label = "FY" if months >= 12 else f"{months}M x{int(factor) if factor==int(factor) else round(factor,3)}"

    def sum_q_field(field_name):
        s = find_row(qi, field_name)
        if s is None: return None
        total = 0.0
        for c in qtrs:
            v = safe(s[c])
            if v is not None: total += v
        return total if total != 0.0 else None

    row = {f: None for f in FIELDS}
    row["revenue"] = sum_q_field("Total Revenue")
    row["grossProfit"] = sum_q_field("Gross Profit")
    row["netProfit"] = sum_q_field("Net Income")
    row["eps"] = None
    row["dps"] = None

    qbc = col_yr(qb, yr) if qb is not None and not qb.empty else None
    if qbc is not None:
        ta = find_row(qb, "Total Assets")
        ca = find_row(qb, "Cash And Cash Equivalents")
        td = find_row(qb, "Total Debt")
        te = find_row(qb, "Stockholders Equity")
        row["totalAsset"] = safe(ta[qbc] if ta is not None else None, div, fx)
        row["cash"] = safe(ca[qbc] if ca is not None else None, div, fx)
        row["totalDebt"] = safe(td[qbc] if td is not None else None, div, fx)
        row["totalEquity"] = safe(te[qbc] if te is not None else None, div, fx)

    for k in ["revenue","grossProfit","netProfit"]:
        if row[k] is not None:
            row[k] = round(row[k] / div * fx, 4)

    ann = {"method":"annualised","label":label,"quarters":n,"months":months,"factor":round(factor,4),"asOf":str(lq.date())}
    print(f"      {yr}: {n}Q → {label} as of {lq.date()}", flush=True)
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
            print(f"  cur={fin_cur} fx={fx:.6f}", flush=True)

            yd = {}
            ann = {}
            for yr in ALL_YEARS:
                row, ann_yr = annualise_year(tk, yr, div, fx, sym)
                yd[yr] = row
                if ann_yr["method"] != "none":
                    ann[yr] = ann_yr

            # ----- EPS and DPS fallback logic (apply only when live value is None) -----
            if exchange == "IDX":
                for i, yr in enumerate(ALL_YEARS):
                    if yr in COMPLETED:
                        # For years before LATEST_YEAR, always use PRELOADED EPS/DPS
                        if yr < LATEST_YEAR:
                            if sym in PRELOADED and "eps" in PRELOADED[sym]:
                                if i < len(PRELOADED[sym]["eps"]):
                                    fb_eps = PRELOADED[sym]["eps"][i]
                                    if fb_eps is not None:
                                        yd[yr]["eps"] = fb_eps
                                        print(f"      using fallback EPS for {yr}: {fb_eps}", flush=True)
                            if sym in PRELOADED and "dps" in PRELOADED[sym]:
                                if i < len(PRELOADED[sym]["dps"]):
                                    fb_dps = PRELOADED[sym]["dps"][i]
                                    if fb_dps is not None:
                                        yd[yr]["dps"] = fb_dps
                                        print(f"      using fallback DPS for {yr}: {fb_dps}", flush=True)
                        else:  # LATEST_YEAR: use fallback only if live data is None
                            if yd[yr].get("eps") is None and sym in PRELOADED and "eps" in PRELOADED[sym]:
                                if i < len(PRELOADED[sym]["eps"]):
                                    fb_eps = PRELOADED[sym]["eps"][i]
                                    if fb_eps is not None:
                                        yd[yr]["eps"] = fb_eps
                                        print(f"      using fallback EPS for {yr}: {fb_eps}", flush=True)
                            if yd[yr].get("dps") is None and sym in PRELOADED and "dps" in PRELOADED[sym]:
                                if i < len(PRELOADED[sym]["dps"]):
                                    fb_dps = PRELOADED[sym]["dps"][i]
                                    if fb_dps is not None:
                                        yd[yr]["dps"] = fb_dps
                                        print(f"      using fallback DPS for {yr}: {fb_dps}", flush=True)
            else:
                for i, yr in enumerate(ALL_YEARS):
                    if yr in COMPLETED:
                        if yd[yr].get("dps") is None and sym in PRELOADED and "dps" in PRELOADED[sym]:
                            if i < len(PRELOADED[sym]["dps"]):
                                fb_dps = PRELOADED[sym]["dps"][i]
                                if fb_dps is not None:
                                    yd[yr]["dps"] = fb_dps
                                    print(f"      using fallback DPS for {yr}: {fb_dps}", flush=True)

            live = [y for y in COMPLETED if yd[y].get("revenue") is not None]
            print(f"  ✓ live: {live}", flush=True)
            final_ann = ann.get(CURRENT_YEAR) if ann.get(CURRENT_YEAR) else {"method":"none","label":None}
            return yd, final_ann
        except Exception as e:
            print(f"  FAIL (attempt {attempt+1}): {e}", flush=True)
    return None, {"method":"none","label":None}

def build_arrays(yd, sym):
    out = {}
    first_live = None
    if yd:
        for yr in ALL_YEARS:
            if yr in yd and yd[yr].get("revenue") is not None:
                first_live = yr
                break
    for f in FIELDS:
        arr = []
        for i, yr in enumerate(ALL_YEARS):
            lv = yd[yr].get(f) if yd and yr in yd else None
            if lv is None and sym in PRELOADED and f in PRELOADED[sym]:
                if first_live is None or yr < first_live:
                    if i < len(PRELOADED[sym][f]):
                        lv = PRELOADED[sym][f][i]
            arr.append(lv)
        out[f] = arr
    return out

# ---------- FULL PROFILES ----------
PROFILES = {
    "BHP": """## Business Model Canvas
**Key Partners:** Mitsubishi (BMA coal JV 50/50), Lundin Mining (Filo Corp 50/50), JESCO (Jansen potash JV), Vale (Samarco JV), BlackRock GIP (iron ore network), Bechtel, Thiess (EPC contractors), Commonwealth Bank, HSBC.
**Key Activities:** Large-scale open-cut & underground mining; iron ore extraction & export (Pilbara 263Mt record); copper production (Escondida highest in 17 years); potash development (Jansen); steelmaking coal (Queensland); commodity marketing & trading; exploration & reserve development; mine automation & digital innovation.
**Key Resources:** WAIO (Western Australia Iron Ore); Escondida (world's largest copper mine); Olympic Dam, Carrapateena; Jansen Potash mine ($7.6B capex); BMA coal assets; ~$55B revenue base; EBITDA margin 51%; strong balance sheet.
**Value Proposition:** World's lowest-cost major iron ore producer (6+ years); record copper output (2Mt FY2025); EBITDA margin 51% for 8+ years; Jansen potash – future-facing food security play; consistent shareholder returns (~$7.1B dividends FY2025).
**Customer Relationships:** Long-term supply agreements (iron ore, copper); annual benchmark pricing with steel mills; strategic marketing in Singapore & Houston; direct sales to Chinese/Japanese steel mills; ESG/sustainability reporting.
**Channels:** Port Hedland (world's largest bulk export port); BHP Marketing offices (Singapore, Houston); direct long-term contracts; spot market/commodity exchanges; Escondida copper concentrates (pipelines & ships).
**Customer Segments:** Steel producers (~50%: China Baowu, HBIS, Japan Nippon Steel, South Korea); copper buyers (~29%: wire mills, EV manufacturers); fertiliser/potash buyers (global agriculture); energy & coal buyers (power utilities, Asia/Europe).
**Cost Structure:** Mining & processing opex: WAIO C1 cash cost ~$18/t iron ore, Escondida ~$1.5/lb copper; Jansen Potash capex $7.6B; sustaining capex ~$6B/yr; royalties & taxes ~41.7%; ESG & decarbonisation $4B plan.
**Revenue Streams:** Iron Ore (~47%): WAIO export sales, $23B segment revenue; Copper (~29%): Escondida + Olympic Dam + Carrapateena, $18.6B segment revenue, record 2Mt; Coal & Other (~24%): steelmaking coal, exploration income.

## SWOT Analysis
**Strengths:** Lowest-cost iron ore producer globally; record copper output; 51% EBITDA margin for 8+ years; Jansen potash new revenue stream; strong balance sheet; $7.1B dividends.
**Weaknesses:** Exposure to China steel demand (80% of iron ore); commodity price cyclicality; high effective tax rate (41.7%); nickel business mothballed; ESG risks in Chile/Australia.
**Opportunities:** Jansen potash first production 2026; copper demand from electrification; automation/AI productivity gains; potential M&A in copper/potash; green steel partnerships.
**Threats:** Commodity price volatility; Chinese economic slowdown; carbon taxes; resource nationalism in Chile; competition from Rio Tinto and Glencore; potash market oversupply risk.

## PESTLE Analysis
**Political:** Australian & Chilean govt relations, resource nationalism. **Economic:** China GDP growth, commodity prices. **Social:** ESG investor pressure, community relations. **Technological:** Automation, AI in mining, carbon capture. **Legal:** Mining permits, tax laws. **Environmental:** Decarbonisation targets, water management.

## Porter's Five Forces
**Rivalry:** Oligopoly with Rio, Vale, Glencore – volume competition. **New Entrants:** High barriers (capex, permits). **Supplier Power:** Low (commoditised). **Buyer Power:** High for iron ore (China concentration). **Substitutes:** Limited for iron ore/copper, but steel scrap recycling reduces ore demand.

## Management & Decision Making
Capital allocation disciplined: returned $7.1B dividends, avoided overpaying for Anglo American. Recent decisions: Jansen potash on track, abandoned Anglo bid. Management quality: industry-leading margins and returns.

## Future Outlook
Jansen potash 2026 first production. Copper demand from electrification. China stimulus potential. Watch commodity prices, China demand, and project execution.""",
    "WDS": """## Business Model Canvas
**Key Partners:** Stonepeak (40% stake in Louisiana LNG, $5.7B), Williams (LNG pipeline), OCI Global (Beaumont ammonia), Japanese and Korean LNG offtakers, Santos (industry peer), government regulators.
**Key Activities:** LNG production & liquefaction (North West Shelf, Pluto, Wheatstone, Louisiana); oil production (Sangomar); low-carbon ammonia production (Beaumont Texas); exploration & development (Scarborough, Browse); marketing & trading; carbon capture development.
**Key Resources:** Record 2025 production 198.8 MMboe; Louisiana LNG FID 2025, 22% complete; Beaumont ammonia plant (110ktpa operational Dec 2025); Sangomar oil field; strong balance sheet $2.7B net profit FY2025.
**Value Proposition:** Record production exceeding guidance; 15% reduction in GHG emissions; Louisiana LNG with Stonepeak partnership; low-carbon ammonia production; resilient operating performance.
**Customer Relationships:** Long-term LNG SPAs with Asian utilities; spot LNG sales; crude offtake contracts; ammonia supply agreements; direct marketing teams.
**Channels:** LNG carriers; North West Shelf, Pluto, Wheatstone facilities; Louisiana Gulf Coast; Beaumont ammonia terminal; crude lifting and sales.
**Customer Segments:** Asian LNG buyers (Japan, Korea, China, India); European LNG buyers; oil refiners; agricultural/industrial ammonia buyers; power utilities.
**Cost Structure:** LNG liquefaction opex; upstream production costs; shipping & logistics; Louisiana LNG capex; Beaumont integration; carbon management.
**Revenue Streams:** LNG (~60% of revenue); oil and condensate (~25%); ammonia and other (~10%); marketing income (~5%).

## SWOT Analysis
**Strengths:** Record production; Louisiana LNG progressing; Beaumont ammonia operational; Sangomar delivering oil; 15% emissions reduction.
**Weaknesses:** LNG price sensitivity; high capex requirements; project execution risk; still oil & gas focused despite transition pivot.
**Opportunities:** Louisiana LNG 2026-27 production; low-carbon ammonia demand; LNG as transition fuel; carbon capture development.
**Threats:** Oil & gas price volatility; energy transition policy; competition from Qatar, US LNG; carbon taxes.

## PESTLE Analysis
**Political:** Australian and US regulatory support for LNG. **Economic:** LNG prices, oil prices. **Social:** Community acceptance of LNG projects. **Technological:** Carbon capture, low-carbon ammonia. **Legal:** Environmental permits. **Environmental:** Net zero targets.

## Porter's Five Forces
**Rivalry:** Intense among global LNG players (Qatar, US, Russia). **New Entrants:** High barriers (capex, long-term contracts). **Supplier Power:** Moderate (equipment, contractors). **Buyer Power:** High (Asian utilities have long-term contracts but can switch). **Substitutes:** Renewables, coal.

## Management & Decision Making
Management committed to shareholder returns, Louisiana LNG de-risked via Stonepeak partnership. Acquisition of OCI Clean Ammonia shows pivot to low-carbon fuels.

## Future Outlook
Louisiana LNG 2026-27. Beaumont low-carbon ammonia. LNG as transition fuel. Watch project execution, gas prices, and energy transition policies.""",
    "CBA": """## Business Model Canvas
**Key Partners:** AWS (core banking cloud migration), OpenAI (ChatGPT Enterprise partner), Microsoft, Visa/Mastercard, financial advisers, fintech partners (IPSI eCommerce), regulators.
**Key Activities:** Retail, business and institutional banking; home lending; digital banking (CommBank app, CommBiz); wealth management; AI-driven fraud detection; core banking on AWS.
**Key Resources:** Statutory NPAT $10.13B FY2025; AWS core banking; CommBiz mobile; OpenAI partnership; largest mortgage book in Australia.
**Value Proposition:** #1 retail bank brand; leading digital platform; AI-powered scam detection; AWS cloud scalability; OpenAI genAI banking solutions.
**Customer Relationships:** Digital-first via CommBank app; branch network; relationship managers; OpenAI innovation.
**Channels:** CommBank app; CommBiz mobile; branches; call centres; X15 Ventures.
**Customer Segments:** Retail consumers; SMEs; corporate & institutional; wealth clients; government.
**Cost Structure:** Technology & digital (AWS, AI); staff; branches; compliance; loan impairment expenses.
**Revenue Streams:** Net interest income (home loans, business); non-interest income (fees, wealth); digital transaction fees; corporate banking; insurance.

## SWOT Analysis
**Strengths:** #1 retail bank; leading digital platform; OpenAI partnership; AWS cloud migration complete; strong capital.
**Weaknesses:** Mortgage book concentration; AI offshoring controversy; digital competition.
**Opportunities:** AI-powered banking products; cloud innovation; interest rate cuts boosting mortgage demand.
**Threats:** Digital bank competition (Sea Bank, Jago); NIM compression; regulatory scrutiny.

## PESTLE Analysis
**Political:** Banking regulation, open banking. **Economic:** Interest rates, housing market. **Social:** Digital adoption, trust. **Technological:** AI, cloud, cybersecurity. **Legal:** Capital requirements, AML. **Environmental:** Green finance, climate risk.

## Porter's Five Forces
**Rivalry:** High – Big 4 banks plus digital natives. **New Entrants:** Moderate – digital bank licences easier but scale hard. **Supplier Power:** Low – technology vendors have some power. **Buyer Power:** High – customers can switch banks easily. **Substitutes:** Fintech lenders, neobanks.

## Management & Decision Making
Completed AWS migration – largest system-of-record migration in 114 years. OpenAI partnership for AI banking. Appointed Chief AI Officer. Acquired IPSI eCommerce. Capital allocation disciplined.

## Future Outlook
AWS cloud enables faster AI integration. OpenAI partnership driving AI products. Interest rate cuts risk NIM compression but boost mortgage demand. Watch tech execution, competition, and credit quality.""",
    "BBRI": """## Business Model Canvas
**Key Partners:** Indonesian government (53% ownership, KUR program), Bank Raya, Pegadaian, PNM (ultra-micro), Mastercard, BRILink agents (1.2M+), fintech partners, ASEAN Development Bank.
**Key Activities:** Micro & SME lending (KUR); consumer banking (BRImo); corporate lending; treasury; digital banking via Bank Raya; ultra-micro via PNM; bancassurance; wealth management.
**Key Resources:** BRImo: 45.9M users, Rp7,077T transaction value; 1.2M+ BRILink agents; 53% govt ownership; lowest cost of funds (CASA 70.6%); NIM 7.8%.
**Value Proposition:** World's largest microfinance institution (60M+ micro customers); unrivalled rural network; 'BRIvolution Re-ignite' transformation; digital acceleration; sovereign backing.
**Customer Relationships:** BRImo app; BRILink agents; branches; KUR program; relationship managers.
**Channels:** BRImo app; BRILink agents (1.2M); 10,000+ branches; Bank Raya; call centre.
**Customer Segments:** Micro entrepreneurs (60M+); SMEs; ultra-micro via PNM; corporate; mass retail; government.
**Cost Structure:** Branch network; BRILink commissions; technology; staff; credit provisions; marketing.
**Revenue Streams:** Interest income (micro, SME, corporate); KUR subsidy income; non-interest income (fees, bancassurance); treasury; investments.

## SWOT Analysis
**Strengths:** World's largest microfinance institution; unrivalled rural network; government backing; BRImo super-app; lowest funding cost.
**Weaknesses:** Asset quality (NPL 3.0%); KUR dependency; digital competition; high cost-to-income; branch network expensive.
**Opportunities:** Ultra-micro (30M addressable); digital lending AI credit scoring; MSME formalisation; bancassurance; wealth management; green finance.
**Threats:** Digital-native banks (Sea Bank, Jago); OJK consolidation; rising NPL risk; political risk; rate cuts compressing NIM; fintech lending.

## PESTLE Analysis
**Political:** Government ownership, KUR program, Bank Indonesia rate policy, OJK regulation. **Economic:** Indonesia GDP growth, rupiah, inflation, interest rate cuts. **Social:** Financial inclusion, micro-entrepreneur culture, digital adoption. **Technological:** BRImo AI, open banking, biometric KYC. **Legal:** Banking law, AML/KYC, data protection. **Environmental:** Sustainable finance, green bonds, climate risk.

## Porter's Five Forces
**Rivalry:** High – Big 4 SOE banks plus digital natives. **New Entrants:** Moderate – digital bank licences easier but scale hard. **Supplier Power:** Low – depositors atomised. **Buyer Power:** Micro borrowers captive; urban SMEs can switch. **Substitutes:** Mobile wallets, BNPL, cooperatives.

## Management & Decision Making
'BRIvolution Re-ignite' transformation. Digital acceleration via BRImo. Ultra-micro integration (PNM, Pegadaian). Management focused on sustainable growth.

## Future Outlook
Ultra-micro expansion. Digital lending reduces cost-to-serve. Bancassurance cross-selling. Watch NPL, digital competition, and KUR policy changes.""",
    "ADRO": """## Business Model Canvas
**Key Partners:** PT Adaro Minerals Indonesia (ADMR 83.8%), PT SIS (mining contractor), aluminum smelter JV partners, PLTA Mentarang hydro JV, Japanese trading houses, Chinese steel mills, KIPI, Indonesian government.
**Key Activities:** Metallurgical coal mining (ADMR 158Mt reserves, 5.6Mt FY2024); mining contracting (SIS 64.8Mt OB); aluminum smelter construction (500kt, North Kalimantan); renewable energy (Adaro Green); PLTA Mentarang hydropower; coal logistics.
**Key Resources:** ADMR metcoal reserves 158Mt; SIS contractor fleet; 15% stake in AADI; aluminum smelter capex $475-525M; PLTA Mentarang concession; strong balance sheet.
**Value Proposition:** Indonesia's largest metcoal miner; vertically integrated mining contractor; aluminum downstream from 2026; green pivot (hydro, Adaro Green); ESG repositioning.
**Customer Relationships:** Long-term metcoal supply contracts (Japan, S. Korea); spot sales to China; mining service contracts; aluminum offtake under negotiation.
**Channels:** Dedicated coal port; barge transport; SIS fleet; Singapore trading desk; IDX-listed subsidiaries.
**Customer Segments:** Asian steelmakers (Japan, Korea, China); mining contractors; aluminum offtakers; power utilities.
**Cost Structure:** ADMR metcoal cash cost <$80/t; SIS fuel & labour ~$0.57/bcm; aluminum smelter capex; royalties; ESG.
**Revenue Streams:** Metcoal (ADMR ~55%): $1.2B revenue; Mining Services (SIS ~41%): $849M revenue; Other/New Energy (~4%): AADI equity, aluminum from 2026F, hydro.

## SWOT Analysis
**Strengths:** Largest metcoal miner (158Mt reserves); vertical integration; aluminum smelter from 2026; green pivot; strong balance sheet.
**Weaknesses:** Thermal coal legacy; metcoal price sensitivity; smelter execution risk; regulatory dependence; ESG exclusion.
**Opportunities:** Aluminum smelter ramp; hydropower; India metcoal demand growth; carbon credits; battery minerals.
**Threats:** Metcoal price collapse; energy transition; Indonesian mining law changes; Australian metcoal competition; dry well risk.

## PESTLE Analysis
**Political:** RKAB quotas, mining law reform, downstream processing mandate. **Economic:** Metcoal prices, Indian steel demand, rupiah. **Social:** Local hiring, community development. **Technological:** Smelter technology, hydropower, mine automation. **Legal:** Mining law, environmental AMDAL, export regulations. **Environmental:** Net zero aspiration, reforestation, carbon offsets.

## Porter's Five Forces
**Rivalry:** Moderate – few large Indonesian metcoal miners. **New Entrants:** High barriers (capex, concessions). **Supplier Power:** Low – own barging fleet reduces dependency. **Buyer Power:** Moderate – Indian and Japanese steel mills price-sensitive. **Substitutes:** Metcoal substitutes limited in blast furnace steelmaking.

## Management & Decision Making
Strategic pivot from thermal to metcoal + aluminum + renewables (rebranded Alamtri Resources). Smelter construction on track. Hydro development. Management committed to ESG repositioning.

## Future Outlook
Aluminum smelter ramping to 500kt by 2026/27. Hydropower for low-cost energy. India metcoal demand growth. Watch metcoal prices, smelter execution, and energy transition policies.""",
    "SMSM": """## Business Model Canvas
**Key Partners:** PT Adrindo Intiperkasa (parent ADR Group); Toyota, Honda, Mitsubishi, Isuzu (OEM); Yanmar Diesel; Astra International; raw material suppliers; export logistics partners; ISO/SNI bodies; Gaikindo.
**Key Activities:** Filter manufacturing (SAKURA); radiator & cooling (ADR); body & chassis parts; quality control (zero-defect OEM); R&D for EV thermal management; export development.
**Key Resources:** SAKURA Filter brand – #1 in Indonesia; ADR Radiator brand; 5 manufacturing facilities; automated lines; 45+ years expertise; export network to 45+ countries; net income Rp1.2T FY2025.
**Value Proposition:** Indonesia's #1 filter and radiator brand; >90% aftermarket revenue; OEM certified supplier to Toyota, Honda, Mitsubishi, Isuzu; export to 45+ countries; debt-free; high dividends.
**Customer Relationships:** OEM supply contracts; aftermarket brand loyalty; dealer/workshop network; B2B export relationships; e-commerce.
**Channels:** OEM direct supply; aftermarket via workshops (10,000+); Astra distribution; export via international distributors; e-commerce (Tokopedia, Shopee).
**Customer Segments:** Automotive OEMs (~30%); aftermarket (>60%: car owners, workshops); heavy equipment/industrial; export markets (~30% revenue).
**Cost Structure:** Raw materials (steel, rubber, aluminium); manufacturing opex; R&D; distribution & export logistics.
**Revenue Streams:** Filtration (~50%+): SAKURA filters; Radiator/Cooling (~30%): ADR radiators; Body Maker & Other (~20%): dump hoists, brake pipes, exhaust.

## SWOT Analysis
**Strengths:** #1 filter and radiator brand; >90% aftermarket revenue; OEM certified; export to 45+ countries; debt-free; high dividends.
**Weaknesses:** Concentration in Indonesia; limited EV product exposure; raw material cost sensitivity; brand dependency.
**Opportunities:** EV thermal management; ASEAN automotive growth; Indonesia-Europe CEPA; industrial air filtration; e-commerce growth.
**Threats:** EV transition reducing traditional volumes; Chinese competition; JPY/IDR FX risk; property slowdown; counterfeits.

## PESTLE Analysis
**Political:** TKDN local content, EV policy, trade policy. **Economic:** Auto sales, motorcycle market, USD/IDR FX, commodity prices. **Social:** Low car ownership (9% vs Thailand 30%), aftermarket culture, brand loyalty. **Technological:** EV product development, filter manufacturing tech, automation. **Legal:** SNI certification, product liability, OEM warranty. **Environmental:** ISO 14001, filter disposal, carbon footprint.

## Porter's Five Forces
**Rivalry:** Moderate – few large auto parts makers in Indonesia. **New Entrants:** Moderate – brand and OEM relationships hard to replicate. **Supplier Power:** Moderate – raw materials global prices. **Buyer Power:** OEMs have power but SMSM certified; aftermarket atomised. **Substitutes:** Chinese imports, EV removing some parts.

## Management & Decision Making
Export growth to 45+ countries. EV thermal management R&D. Maintained debt-free balance sheet. High dividend payout policy.

## Future Outlook
Export growth continues. EV thermal management products. Indonesian auto penetration still low (9%) – long secular growth. Watch EV transition, raw material costs, and export demand.""",
    "UNTR": """## Business Model Canvas
**Key Partners:** PT Astra International Tbk (59.5% parent); Komatsu Ltd Japan (exclusive distributor); UD Trucks, Scania, Bomag, Tadano; PT Pamapersada Nusantara (PAMA); PT Agincourt Resources (Martabe gold); Nickel Industries (19.99% stake); PT Acset Indonusa; PT Energia Prima Nusantara; PT Arkora Hydro; Indonesian Govt/ESDM.
**Key Activities:** Heavy equipment distribution (Komatsu, UD Trucks, etc.); after-sales parts, service, reconditioning (REMAN); mining contracting via PAMA; coal mining; gold mining (Martabe); nickel mining; construction; renewable energy (solar, mini-hydro).
**Key Resources:** Komatsu exclusive license; PAMA – Indonesia's largest mining contractor (829M bcm OB removal H1 2025); Martabe gold mine (2.5Moz Au + 26Moz Ag); coal assets; nickel ore; ~Rp130T revenue; Astra backing.
**Value Proposition:** Largest heavy equipment company – sole Komatsu distributor; PAMA largest mining contractor; diversified beyond coal (gold, nickel, renewables); energy transition play; Astra Group backing.
**Customer Relationships:** Long-term equipment supply + service contracts (PAMA); Komatsu warranty & REMAN loyalty; coal offtake contracts; gold bullion spot & term; government/PLN.
**Channels:** National Komatsu dealer network; PAMA direct contract; coal barge & shipping; gold to international hubs; construction bidding.
**Customer Segments:** Mining companies (~50%); coal buyers (PLN, Asian importers); gold/commodity buyers; construction clients.
**Cost Structure:** Equipment procurement; PAMA fleet management; coal production opex; gold mine cash costs; reconditioning low-cost advantage; capex ~US$1B annual.
**Revenue Streams:** Construction Machinery (~38%): Komatsu sales, after-sales; Mining Contracting (~28%): PAMA OB removal; Mining & Energy (~34%): coal, gold, nickel, RE.

## SWOT Analysis
**Strengths:** Sole Komatsu distributor; PAMA largest contractor; diversified 5 pillars; Martabe gold low cost; Astra backing; EBITDA margin 25-28%.
**Weaknesses:** Komatsu single-brand; coal cycle exposure; heavy equipment cyclical; gold single asset; renewables early stage.
**Opportunities:** Battery minerals (nickel, copper) contracts; data centre equipment demand; renewable energy target 150MW; Martabe brownfield; Komatsu electric machinery.
**Threats:** Coal transition; Komatsu competition (Caterpillar, Sany); nickel price crash; labour shortage; flood risk; EV policy.

## PESTLE Analysis
**Political:** Mining permits, downstream policy, infrastructure spending. **Economic:** Coal prices, gold prices, rupiah, interest rates. **Social:** Local employment, community relations. **Technological:** Komatsu AHS, renewable energy tech. **Legal:** Mining law, environmental permits. **Environmental:** ESG pressure, reclamation, emissions.

## Porter's Five Forces
**Rivalry:** High – competition from Caterpillar, Hitachi, Sany. **New Entrants:** Moderate – capital intensive, but Chinese brands entering. **Supplier Power:** Low – Komatsu exclusive but limited alternatives. **Buyer Power:** Moderate – mining clients can choose contractors. **Substitutes:** Chinese equipment, electric machinery.

## Management & Decision Making
Komatsu 4,500 units target. PAMA still largest contractor. Martabe gold ~250koz/yr. Investing in renewables. Astra Group backing ensures governance.

## Future Outlook
Battery minerals service contracts. Gold price ~$3,000/oz supports Martabe. Renewable energy investments. Watch coal transition, Komatsu competition, and gold prices.""",
    "ITMG": """## Business Model Canvas
**Key Partners:** Banpu Minerals Singapore (60% owner); PT Thiess Indonesia; China coal importers (40% of exports); Japan/S. Korea utility buyers (17%); PLN (22% of sales); Bontang port operators; Komatsu, Caterpillar; Indonesian Govt/ESDM.
**Key Activities:** Open-cut thermal coal mining (6 mines, Kalimantan); coal blending; terminal operations (BoCT); logistics (barging, port loading); power plant operations; solar hybrid PV; mining contracting.
**Key Resources:** Coal reserves 375Mt (+30% in 2024); resources 2.13Bt; 6 concessions; Bontang Coal Terminal; 3 loading ports; cash $877M (mid-2024).
**Value Proposition:** Wide calorific range (3,400-7,300 kcal/kg); expert blending; integrated logistics; strong cash & high dividends; green expansion.
**Customer Relationships:** Annual supply agreements with utilities; spot & short-term contracts; China spot buying; blending to spec.
**Channels:** Bontang Coal Terminal (BoCT); 3 additional ports; barge transport; commodity desk; domestic direct to PLN.
**Customer Segments:** China importers (~40%); domestic market (~22% PLN); Japan (~17%); rest of Asia (India, Thailand, Bangladesh, S. Korea, Philippines).
**Cost Structure:** Mining opex ~$67/t; royalties $260M FY2024 (22% of HBA); logistics; capex for new mines & solar.
**Revenue Streams:** Thermal coal sales (~93%): 24Mt sold, ASP $125-130/t; Energy services (~5%): BoCT terminal, mining contracting; Other/RE (~2%): solar hybrid, internal electricity.

## SWOT Analysis
**Strengths:** 375Mt reserves; Banpu parent; 24Mt sales +15% YoY; wide calorific range; own terminal; net cash; high dividends.
**Weaknesses:** 100% thermal coal; Banpu majority; single geography; high payout limits reinvestment; no non-coal business.
**Opportunities:** India demand growth; BoCT terminal expansion; Banpu clean energy JVs; spot premiums; production optimisation.
**Threats:** Coal price below $100/t risk; ESG divestment; RKAB quotas; China domestic coal; La Niña flooding.

## PESTLE Analysis
**Political:** RKAB quotas, mining law, Indonesia energy policy. **Economic:** Coal prices, India/China demand, rupiah. **Social:** Local communities, ESG investor pressure. **Technological:** Coal blending, solar hybrid. **Legal:** Mining permits, environmental. **Environmental:** Energy transition, reclamation.

## Porter's Five Forces
**Rivalry:** Moderate – several Indonesian thermal coal miners. **New Entrants:** High – concession barriers. **Supplier Power:** Low – multiple equipment suppliers. **Buyer Power:** High – China and India price-sensitive. **Substitutes:** High – renewables, gas.

## Management & Decision Making
High dividend payout (80-90%) rewards shareholders. Banpu parent may extract dividends. Limited reinvestment for diversification.

## Future Outlook
India import demand growing. BoCT terminal expansion. Solar hybrid projects. Watch coal prices, energy transition policies, and Banpu parent strategy.""",
    "POWR": """## Business Model Canvas
**Key Partners:** PGN/Pertamina (gas supply); PLN (grid backstop); industrial tenants (2,650 customers); GE/Siemens (turbines); Bechtel/Technip (EPC); government (PPU licence).
**Key Activities:** Electricity generation (gas, coal); distribution to industrial estates; grid maintenance; capacity expansion; power purchase agreements.
**Key Resources:** PPU licence for 5 Cikarang estates; 2,650 industrial customers; 30-year exclusive incumbency; long-term supply contracts; strong cash flow.
**Value Proposition:** Sole private power supplier in Cikarang industrial estates; reliable dedicated grid; long-term contracts; captive customer base.
**Customer Relationships:** Multi-year supply agreements; dedicated account management; ESG reporting for multinationals.
**Channels:** Direct distribution network; PLN grid as backstop; direct billing.
**Customer Segments:** Industrial tenants (Toyota, Samsung, data centres); PLN (wholesale); data centre operators.
**Cost Structure:** Gas/coal fuel; maintenance; capex for capacity expansion; staff.
**Revenue Streams:** Electricity sales (tariff-based); capacity charges; connection fees.

## SWOT Analysis
**Strengths:** Captive monopoly in Cikarang; 30-year incumbency; long-term contracts; stable cash flow.
**Weaknesses:** Single customer concentration (PLN 18% but industrial atomised); fuel price sensitivity; no growth without new estates.
**Opportunities:** Data centre power demand; industrial estate expansion; solar/battery integration; green PPAs.
**Threats:** PLN grid connection; rooftop solar + BESS; diesel generators for baseload too expensive; regulatory changes.

## PESTLE Analysis
**Political:** PPU licence protection, energy policy. **Economic:** Industrial growth, data centre demand. **Social:** ESG expectations from multinational tenants. **Technological:** Solar, BESS, grid modernisation. **Legal:** PPU licence, environmental permits. **Environmental:** Emissions, renewable integration.

## Porter's Five Forces
**Rivalry:** Very low – sole private supplier in zone. **New Entrants:** Extremely unlikely – only one PPU licence per zone. **Supplier Power:** Moderate – gas from PGN, turbines from GE/Siemens. **Buyer Power:** Low – switching cost high, but large buyers have some leverage. **Substitutes:** PLN grid (inferior reliability), rooftop solar (limited by roof space).

## Management & Decision Making
Conservative management, focused on contract renewals and grid reliability. Slow to adopt renewables.

## Future Outlook
Data centre power demand. Industrial estate expansion. Watch PLN grid connection, solar adoption, and industrial tenant growth.""",
    "MPMX": """## Business Model Canvas
**Key Partners:** AHM (Honda sole distributor); Carro JV; insurance reinsurers; banks (MPM Finance funding); AHM spare parts supply.
**Key Activities:** Honda motorcycle distribution (East Java); automotive financing (MPM Finance); insurance (non-life); vehicle rental (MPMRent); used car digital (Carro JV).
**Key Resources:** Honda exclusive distribution rights (East Java); 280 dealers; MPM Finance lending book; MPMRent fleet; strong brand.
**Value Proposition:** Exclusive Honda distributor in East Java; integrated financing, insurance, rental; one-stop automotive ecosystem.
**Customer Relationships:** Dealer network; direct financing; rental contracts; insurance policies.
**Channels:** 280 dealers; MPM Finance branches; MPMRent fleet; Carro digital platform.
**Customer Segments:** Motorcycle buyers (individual, corporate); financing customers; rental customers; insurance buyers.
**Cost Structure:** Inventory (Honda units); dealer commissions; financing cost of funds; fleet maintenance; insurance claims.
**Revenue Streams:** Motorcycle sales; financing interest; insurance premiums; rental income; used car fees.

## SWOT Analysis
**Strengths:** Honda exclusive East Java; integrated ecosystem; strong dealer network.
**Weaknesses:** Single brand (Honda); geography concentration; financing book credit risk.
**Opportunities:** EV motorcycle transition; digital rental (MPMRent); used car platform; insurance cross-sell.
**Threats:** AHM direct-to-consumer; Yamaha competition; interest rate sensitivity; EV brands (Niu, Volta).

## PESTLE Analysis
**Political:** EV policy, local content rules. **Economic:** Motorcycle market 6.5M units/yr, GDP East Java 5.2%, BI rate cuts. **Social:** Motorcycle culture, digital mobility, financial inclusion. **Technological:** EV technology, telematics, InsurTech. **Legal:** Multi-finance regulation, insurance law, consumer protection. **Environmental:** EV transition, carbon reporting.

## Porter's Five Forces
**Rivalry:** Moderate – Yamaha competes at retail level. **New Entrants:** Low – AHM would need to grant new licence. **Supplier Power:** High – AHM sole supplier. **Buyer Power:** Individual buyers price-sensitive but Honda brand loyal. **Substitutes:** Public transport, ride-hailing, car ownership.

## Management & Decision Making
Management focuses on Honda distribution, financing, and rental. Investing in EV transition and digital.

## Future Outlook
EV motorcycle rollout. MPMRent EV fleet transition. Digital used car platform. Watch Honda EV strategy, interest rates, and competition.""",
    "BTPS": """## Business Model Canvas
**Key Partners:** PT Bank SMBC Indonesia (70% parent); SMFG; Baznas; government ultra-micro programs (UMI); community groups (Tunas).
**Key Activities:** Sharia microfinance (murabahah); group lending (Tunas solidarity model); field officer network; digital group meetings (Bestee).
**Key Resources:** 100% sharia-compliant; group solidarity model (lowest NPL); 26 branches + field officers; SMBC AAA rating; murabahah margin 89% of revenue.
**Value Proposition:** Largest sharia microfinance bank; group lending community model; ultra-micro focus; sharia compliance; social empowerment.
**Customer Relationships:** Group meetings (Tunas); field officers; Bestee platform; community trust.
**Channels:** Branches; field officers; WhatsApp/video group meetings; Bestee app.
**Customer Segments:** Muslim women micro-entrepreneurs; ultra-micro borrowers; rural unbanked.
**Cost Structure:** Field officer salaries; branch network; technology; credit provisions; community programs.
**Revenue Streams:** Murabahah margin (89% of revenue); other sharia products.

## SWOT Analysis
**Strengths:** 100% sharia-compliant; group solidarity model (low NPL); SMBC parent; deep rural community penetration; high-quality murabahah income.
**Weaknesses:** Tiny scale (Rp21.74T assets); single product concentration; no digital banking; expensive field officer model; low brand awareness.
**Opportunities:** OIK Islamic banking roadmap (25% market share target); ultra-micro BPUM program; digitisation via WhatsApp; 30M unserved Muslim women; hajj savings; sharia capital market.
**Threats:** Digital Islamic competitors; OJK consolidation pressure; economic downturn raising NPL; government policy changes; fraud.

## PESTLE Analysis
**Political:** OIK sharia roadmap, government ultra-micro program, Prabowo pro-Islamic economy. **Economic:** GDP growth, BI rate, micro-borrower income. **Social:** 230M Muslim population, women empowerment, rural financial inclusion. **Technological:** Digital group meetings, biometric KYC, AI credit scoring. **Legal:** Sharia banking law, OJK regulations, AML. **Environmental:** Green finance, climate risk for rural borrowers.

## Porter's Five Forces
**Rivalry:** Low – few sharia microfinance banks. **New Entrants:** Moderate – digital Islamic banks emerging. **Supplier Power:** Low – depositors atomised. **Buyer Power:** Low – micro borrowers captive. **Substitutes:** BPR, cooperatives, informal lending.

## Management & Decision Making
Management focuses on community-based microfinance. Partnering with Baznas. Exploring digitisation to reduce field officer costs.

## Future Outlook
Digital group meetings (WhatsApp). Ultra-micro expansion. Sharia capital market products. Watch digital adoption, NPL, and OJK policy.""",
    "DMAS": """## Business Model Canvas
**Key Partners:** Sojitz Corporation (Japanese partner); industrial tenants (data centres, manufacturers); Bekasi Regency; BKPM; Japan-Indonesia IJEPA.
**Key Activities:** Industrial estate development (Kota Deltamas); land sales; infrastructure (roads, power, water); property management; township development.
**Key Resources:** 3,000-hectare Kota Deltamas; DC-ready plots with 132kV substations; GIIC warehouses; green belt; ISO 14001.
**Value Proposition:** Prime industrial land in Bekasi corridor; integrated township (residential, commercial, industrial); data centre-ready infrastructure; green estate.
**Customer Relationships:** Long-term land lease/sales; facility management; CSR programs.
**Channels:** Direct sales; BKPM facilitation; Sojitz network.
**Customer Segments:** Industrial manufacturers; data centre operators; logistics companies; residential buyers.
**Cost Structure:** Land acquisition; infrastructure development; maintenance; CSR.
**Revenue Streams:** Land sales; lease income; facility fees; utilities.

## SWOT Analysis
**Strengths:** Prime location Bekasi corridor; data centre-ready plots; green estate; ISO 14001; Sojitz partnership.
**Weaknesses:** Concentration in Bekasi; land sales cyclical; infrastructure cost high.
**Opportunities:** Data centre demand (Indonesia internet economy growing 20% p.a.); government manufacturing investment target Rp500T; Jakarta rental convergence; green building certification.
**Threats:** Competing estates; economic slowdown; construction cost inflation; regulatory changes.

## PESTLE Analysis
**Political:** Industrial policy, BKPM facilitation, data centre regulation, local permits. **Economic:** Data centre demand, industrial land prices, GDP growth. **Social:** Employment (500,000+ workers), housing demand. **Technological:** DC-ready infrastructure, BIM, smart water, LiDAR. **Legal:** Industrial estate regulation, building permits, environmental AMDAL. **Environmental:** ISO 14001, solar PV target, water recycling, net-zero by 2030.

## Porter's Five Forces
**Rivalry:** Moderate – several industrial estates in Bekasi. **New Entrants:** High barriers – land acquisition, permits. **Supplier Power:** Low – multiple contractors. **Buyer Power:** Moderate – large data centres negotiate. **Substitutes:** Other estates, greenfield development.

## Management & Decision Making
Management focused on data centre land sales (60% of 2025 sales). Green estate initiatives. Sojitz partnership provides Japanese FDI pipeline.

## Future Outlook
Data centre demand continues. Government manufacturing investment. Green building certification. Watch FDI inflows, land prices, and competition.""",
    "SPTO": """## Business Model Canvas
**Key Partners:** TOTO Japan (exclusive sole-agent since 1977); Villeroy & Boch, Geberit, Franke, Jacuzzi, Kaldewei, Stiebel Eltron; property developers; hotel chains; architects.
**Key Activities:** Distribution of premium bathroom products; showroom operations; specification sales to developers; project management; after-sales service.
**Key Resources:** Exclusive TOTO Japan rights; 9 global brands; 14 regional showrooms; 47-year relationship; strong B2B developer relationships.
**Value Proposition:** One-stop premium bathroom solution; TOTO exclusivity; wide brand portfolio; specification expertise.
**Customer Relationships:** B2B specification with developers; showroom retail; after-sales service.
**Channels:** Showrooms (14 cities); direct B2B sales; e-commerce (Tokopedia, Shopee); architect specification.
**Customer Segments:** Property developers; hotel chains; healthcare projects; high-end homeowners; renovators.
**Cost Structure:** Import costs (JPY); showroom rent; staff; logistics; marketing.
**Revenue Streams:** Product sales; specification fees; after-sales service.

## SWOT Analysis
**Strengths:** Exclusive TOTO Japan since 1977; 9 premium brands; national showroom network; strong developer relationships; high dividend yield (~10.8%).
**Weaknesses:** Asset-light import-dependent; TOTO concentration risk; narrow margins (gross 12-14%); premium-only; limited e-commerce.
**Opportunities:** Property supercycle; data centre commercial fit-out; hotel pipeline (20,000+ rooms); middle class expansion; e-commerce growth; healthcare expansion.
**Threats:** JPY appreciation; TOTO direct sales risk; Chinese premium brands (HEGIL, JOMOO); property slowdown; income polarisation.

## PESTLE Analysis
**Political:** Trade policy (IJEPA), luxury goods tax, import tariffs. **Economic:** Property market, middle class income, JPY/IDR. **Social:** Bathroom culture upgrade, social media trends, hotel guest expectations. **Technological:** TOTO Washlet, smart bathroom, BIM integration. **Legal:** SNI standards, import regulations, brand protection. **Environmental:** TOTO green products, water efficiency, packaging.

## Porter's Five Forces
**Rivalry:** Low – TOTO vs American Standard duopoly in premium. **New Entrants:** Very low – TOTO exclusivity is absolute barrier. **Supplier Power:** High – TOTO Japan sole supplier. **Buyer Power:** Moderate – developers bulk order. **Substitutes:** Local mass-market brands, Chinese mid-premium.

## Management & Decision Making
Management focused on maintaining TOTO exclusivity. Expanding showrooms to Tier-2 cities. Building architect specification program.

## Future Outlook
Property supercycle. Data centre fit-out. Hotel pipeline. Watch JPY/IDR, TOTO relationship, and property market.""",
    "TSM": """## Business Model Canvas
**Key Partners:** Apple, NVIDIA, AMD, Qualcomm, Broadcom (key customers); ASML (equipment); equipment vendors (Applied Materials, Lam Research); Taiwan government; research institutes.
**Key Activities:** Semiconductor wafer fabrication; advanced node R&D (3nm, 2nm); capacity expansion; packaging (CoWoS); customer co-development.
**Key Resources:** Advanced nodes (3nm, 5nm); 92% market share in advanced chips; 15+ fabs; massive capex (~$30B annual); strong customer relationships.
**Value Proposition:** World's largest dedicated foundry; unrivalled process technology; high yield rates; capacity scale; customer trust.
**Customer Relationships:** Long-term capacity agreements; joint technology development; dedicated teams.
**Channels:** Direct sales; technical support; design ecosystem (TSMC reference flows).
**Customer Segments:** Fabless semiconductor companies (Apple, NVIDIA, AMD, Qualcomm); IDMs (Intel outsourcing).
**Cost Structure:** Depreciation (heavy); R&D (~$5B annual); labour; utilities; materials.
**Revenue Streams:** Wafer sales; advanced node premiums; packaging services.

## SWOT Analysis
**Strengths:** Advanced node leadership (3nm, 2nm); ~92% market share; massive scale; strong customer loyalty; high margins.
**Weaknesses:** Geographic concentration (Taiwan); geopolitical risk; high capex intensity; customer concentration (Apple ~25%).
**Opportunities:** AI/HPC demand; 2nm ramp; global expansion (Arizona, Japan, Germany); chiplets/advanced packaging.
**Threats:** Geopolitical (China-Taiwan); competition from Samsung, Intel; cyclical downturns; customer vertical integration (Intel foundry).

## PESTLE Analysis
**Political:** Taiwan-US relations, CHIPS Act subsidies, China threat. **Economic:** Semiconductor cycles, AI capex boom. **Social:** Talent shortage. **Technological:** 2nm, GAAFET, CoWoS, HBM. **Legal:** Export controls, IP protection. **Environmental:** Water usage, renewable energy, carbon neutrality.

## Porter's Five Forces
**Rivalry:** Intense – Samsung, Intel catching up. **New Entrants:** Extremely high barriers (capex, IP, scale). **Supplier Power:** Moderate – ASML (EUV) dominant. **Buyer Power:** Low – customers dependent on TSMC's technology. **Substitutes:** IDMs producing in-house (Samsung, Intel).

## Management & Decision Making
Management committed to R&D and capex. Global expansion to reduce geopolitical risk. Focus on advanced packaging (CoWoS). Customer-centric.

## Future Outlook
AI/HPC demand drives 2nm ramp. Global fabs in Arizona, Japan, Germany. Watch geopolitical tensions, competition, and capex efficiency.""",
    "V": """## Business Model Canvas
**Key Partners:** Banks (issuers); merchants (acquirers); cardholders; VisaNet technology partners; fintechs (tokenisation).
**Key Activities:** Payment network operation; transaction processing; fraud prevention; digital identity; value-added services (data analytics).
**Key Resources:** VisaNet global network; brand trust; regulatory relationships; 800M+ cardholders; 130M+ merchants.
**Value Proposition:** Reliable global payment network; security (tokenisation); convenience; scale.
**Customer Relationships:** Long-term contracts with issuers/acquirers; API access; developer portals.
**Channels:** Direct to financial institutions; partner networks; digital wallets.
**Customer Segments:** Financial institutions (issuers, acquirers); merchants; cardholders; governments.
**Cost Structure:** Technology; marketing; fraud prevention; regulatory compliance.
**Revenue Streams:** Transaction fees; data processing; cross-border fees; value-added services.

## SWOT Analysis
**Strengths:** Largest global payment network; strong brand; network effects; high margins; recurring revenue.
**Weaknesses:** Regulatory pressure (interchange fees); competition from fintechs; mature markets growth.
**Opportunities:** Digital payments growth; tokenisation; cross-border e-commerce; B2B payments; crypto partnerships.
**Threats:** Fintech disruption (Stripe, Adyen); BNPL; central bank digital currencies; regulatory caps on fees.

## PESTLE Analysis
**Political:** Regulatory scrutiny on interchange fees. **Economic:** Consumer spending, cross-border travel. **Social:** Cashless adoption, digital wallets. **Technological:** Tokenisation, AI fraud detection. **Legal:** Antitrust, interchange regulation. **Environmental:** ESG focus, carbon neutrality.

## Porter's Five Forces
**Rivalry:** Duopoly with Mastercard, plus fintechs. **New Entrants:** Moderate – fintechs can enter but network effects strong. **Supplier Power:** Low – banks as issuers have some power. **Buyer Power:** Merchants have limited power (must accept card). **Substitutes:** BNPL, crypto, bank transfers.

## Management & Decision Making
Management focused on digital innovation, tokenisation, and strategic partnerships. Capital returns via dividends and buybacks.

## Future Outlook
Digital payments growth. Cross-border e-commerce. Tokenisation adoption. Watch regulatory caps, fintech competition, and consumer spending.""",
    "MA": """## Business Model Canvas
**Key Partners:** Banks, merchants, fintechs, digital wallets, crypto platforms.
**Key Activities:** Payment network; transaction processing; cyber security; data analytics; multi-rail solutions (credit, debit, prepaid, ACH).
**Key Resources:** Mastercard network; brand; 2.8B+ cards; regulatory relationships.
**Value Proposition:** Secure global payments; multi-rail flexibility; value-added services.
**Customer Relationships:** Issuer/acquirer contracts; developer APIs; innovation labs.
**Channels:** Direct to FIs; partner ecosystems.
**Customer Segments:** FIs, merchants, governments, consumers.
**Cost Structure:** Tech, marketing, fraud prevention, compliance.
**Revenue Streams:** Transaction fees, cross-border fees, value-added services.

## SWOT Analysis
**Strengths:** #2 global payment network; multi-rail strategy; strong brand; network effects.
**Weaknesses:** Regulatory pressure; less global than Visa in some markets.
**Opportunities:** Digital wallets, crypto partnerships, B2B payments, open banking.
**Threats:** Fintech disruption, CBDCs, regulatory caps.

## PESTLE Analysis
**Political:** Interchange regulation. **Economic:** Consumer spending. **Social:** Cashless adoption. **Technological:** Tokenisation, AI. **Legal:** Antitrust. **Environmental:** ESG.

## Porter's Five Forces
**Rivalry:** Duopoly with Visa. **New Entrants:** Moderate. **Supplier Power:** Low. **Buyer Power:** Moderate. **Substitutes:** BNPL, crypto.

## Management & Decision Making
Management focused on multi-rail expansion, crypto partnerships, and value-added services.

## Future Outlook
Digital payments growth. Crypto integration. B2B payments. Watch regulation and fintech competition.""",
    "PBR-A": """## Business Model Canvas
**Key Partners:** Brazilian government (controlling shareholder); Petrobras Distribuidora; pre-salt consortium partners; international oil companies.
**Key Activities:** Oil & gas exploration (pre-salt); refining; distribution; biofuels; petrochemicals.
**Key Resources:** Pre-salt deepwater fields (Tupi, Búzios); giant reserves; deepwater expertise; refining capacity.
**Value Proposition:** Low-cost pre-salt production; integrated value chain; domestic market leadership.
**Customer Relationships:** Long-term fuel supply contracts; spot sales; government policy.
**Channels:** Direct distribution; Petrobras Distribuidora; export terminals.
**Customer Segments:** Domestic fuel consumers; international oil buyers; industrial; petrochemical.
**Cost Structure:** Exploration & production; refining; royalties; taxes; interest.
**Revenue Streams:** Oil sales; refined products; natural gas; biofuels.

## SWOT Analysis
**Strengths:** World-class pre-salt assets; low production cost; deepwater expertise; large reserves.
**Weaknesses:** Government interference; high debt; corruption legacy; refining losses.
**Opportunities:** Pre-salt production growth; energy transition investments (biofuels, offshore wind); debt reduction.
**Threats:** Oil price volatility; government intervention; environmental pressure; competition from renewables.

## PESTLE Analysis
**Political:** Government control (majority shareholder), political risk. **Economic:** Oil prices, Brazil GDP, real exchange rate. **Social:** Corruption perception, local employment. **Technological:** Deepwater tech, carbon capture. **Legal:** Oil law, environmental regulations. **Environmental:** Pre-salt emissions, oil spills, net zero targets.

## Porter's Five Forces
**Rivalry:** Moderate – state-controlled, but private competitors in some blocks. **New Entrants:** High barriers (capex, deepwater expertise). **Supplier Power:** Moderate – specialised deepwater equipment. **Buyer Power:** Low – oil is global commodity. **Substitutes:** Renewables, electric vehicles.

## Management & Decision Making
Management focused on pre-salt growth, debt reduction, and dividend policy. Recent leadership changes aim for commercial discipline.

## Future Outlook
Pre-salt production growth. Biofuels and offshore wind diversification. Debt reduction. Watch oil prices, government policy, and energy transition.""",
    "MSFT": """## Business Model Canvas
**Key Partners:** OpenAI, LinkedIn, GitHub, Adobe (integration), cloud resellers, device manufacturers (OEMs).
**Key Activities:** Cloud computing (Azure); productivity software (Office 365, Teams); AI (Copilot); gaming (Xbox); LinkedIn; Windows.
**Key Resources:** Azure cloud infrastructure; Office 365 user base; OpenAI partnership; Windows OS dominance.
**Value Proposition:** Enterprise productivity suite; cloud scale; AI integration; security.
**Customer Relationships:** Subscription (SaaS); enterprise contracts; developer ecosystem.
**Channels:** Direct sales; cloud resellers; Microsoft Store; OEM pre-install.
**Customer Segments:** Enterprises; SMBs; consumers; developers; governments.
**Cost Structure:** Data centres; R&D; sales & marketing; G&A.
**Revenue Streams:** Azure; Office 365; Windows; LinkedIn; Xbox; advertising.

## SWOT Analysis
**Strengths:** Azure #2 cloud; Office 365 dominance; OpenAI partnership; strong balance sheet.
**Weaknesses:** Slowing Azure growth; antitrust risk; competition in AI (Google, AWS).
**Opportunities:** AI monetisation (Copilot); cloud growth; gaming (Activision); cybersecurity.
**Threats:** Regulatory antitrust; cloud competition; economic slowdown.

## PESTLE Analysis
**Political:** Antitrust scrutiny, export controls. **Economic:** IT spending, cloud budgets. **Social:** Remote work, digital transformation. **Technological:** AI, quantum computing. **Legal:** GDPR, antitrust cases. **Environmental:** Carbon negative goal.

## Porter's Five Forces
**Rivalry:** High – AWS, Google, Oracle, Salesforce. **New Entrants:** Moderate – cloud capex barrier. **Supplier Power:** Low – commoditised hardware. **Buyer Power:** Moderate – enterprises can multi-cloud. **Substitutes:** Open source, on-prem.

## Management & Decision Making
Management focused on AI (Copilot, OpenAI), cloud growth, and shareholder returns (dividends, buybacks).

## Future Outlook
AI monetisation (Copilot). Cloud growth. Gaming (Activision). Watch AI adoption, cloud competition, and regulation.""",
    "AMZN": """## Business Model Canvas
**Key Partners:** Third-party sellers (marketplace); AWS customers; content creators; logistics partners.
**Key Activities:** E-commerce (online retail); cloud computing (AWS); digital streaming (Prime Video); advertising; logistics.
**Key Resources:** AWS cloud infrastructure; fulfillment centres; Prime membership; customer data.
**Value Proposition:** Vast product selection; fast delivery (Prime); AWS compute & storage; advertising reach.
**Customer Relationships:** Prime loyalty; seller tools; AWS support; self-service.
**Channels:** Amazon.com; mobile app; Alexa; AWS console; physical stores (Whole Foods).
**Customer Segments:** Consumers; third-party sellers; enterprises (AWS); advertisers.
**Cost Structure:** Fulfillment; AWS infrastructure; content acquisition; marketing.
**Revenue Streams:** Product sales; AWS; advertising; subscription (Prime, Prime Video).

## SWOT Analysis
**Strengths:** Largest e-commerce; AWS #1 cloud; Prime flywheel; advertising growth; logistics network.
**Weaknesses:** Thin retail margins; regulatory antitrust; labour issues.
**Opportunities:** AI (Bedrock, Trainium); healthcare; satellite (Project Kuiper); international e-commerce.
**Threats:** Competition from Walmart, Temu, Shein; cloud competition (Azure, Google); antitrust.

## PESTLE Analysis
**Political:** Antitrust, labour laws. **Economic:** Consumer spending, cloud budgets. **Social:** E-commerce adoption, convenience culture. **Technological:** AI, robotics in fulfillment. **Legal:** Antitrust cases, data privacy. **Environmental:** Carbon footprint, renewable energy.

## Porter's Five Forces
**Rivalry:** High – Walmart, Target, Temu, Shein. **New Entrants:** Moderate – e-commerce easier but scale hard. **Supplier Power:** Low – many third-party sellers. **Buyer Power:** High – consumers price-sensitive. **Substitutes:** Physical retail, other e-commerce.

## Management & Decision Making
Management focused on cost optimisation, AI investment, and AWS growth. Recent layoffs and efficiency drive.

## Future Outlook
AI (Bedrock, Trainium). Healthcare expansion. Project Kuiper. Watch e-commerce margins, cloud competition, and antitrust.""",
    "AAPL": """## Business Model Canvas
**Key Partners:** TSMC (chip manufacturing); Foxconn, Pegatron (assembly); app developers; content providers (Apple Music, TV+).
**Key Activities:** Hardware design (iPhone, Mac, iPad, Watch); software (iOS, macOS); services (App Store, Apple Music, iCloud); retail.
**Key Resources:** Brand premium; ecosystem (1B+ active devices); App Store monopoly; supply chain expertise.
**Value Proposition:** Premium hardware; seamless ecosystem; privacy; status.
**Customer Relationships:** Retail (Apple Store); ecosystem lock-in; AppleCare.
**Channels:** Apple retail stores; online store; resellers; carriers.
**Customer Segments:** Consumers; professionals; enterprises; education.
**Cost Structure:** R&D; supply chain; marketing; retail.
**Revenue Streams:** iPhone (~50%); services (~25%); Mac, iPad, Wearables.

## SWOT Analysis
**Strengths:** Brand premium; ecosystem lock-in; high margins; loyal customer base; services growth.
**Weaknesses:** iPhone concentration; slow innovation; regulatory pressure (App Store).
**Opportunities:** AI integration; Vision Pro; services expansion; health tech.
**Threats:** Regulatory (App Store antitrust); competition from Android, Huawei; supply chain disruption.

## PESTLE Analysis
**Political:** US-China trade, antitrust. **Economic:** Consumer spending, disposable income. **Social:** Brand loyalty, privacy concerns. **Technological:** AI, AR/VR, chip design. **Legal:** App Store antitrust, EU DMA. **Environmental:** Carbon neutral, recycled materials.

## Porter's Five Forces
**Rivalry:** High – Samsung, Google, Huawei. **New Entrants:** Moderate – brand barrier high. **Supplier Power:** Moderate – TSMC sole advanced chip supplier. **Buyer Power:** Moderate – switching costs high (ecosystem). **Substitutes:** Android devices.

## Management & Decision Making
Management focused on services growth, AI integration, and Vision Pro. Strong capital returns (dividends, buybacks).

## Future Outlook
AI integration (Apple Intelligence). Vision Pro. Services expansion. Watch iPhone cycle, regulatory risk, and innovation.""",
    "META": """## Business Model Canvas
**Key Partners:** Advertisers; content creators; app developers; AI hardware vendors (NVIDIA).
**Key Activities:** Social media (Facebook, Instagram, WhatsApp, Messenger); advertising; AI research (Llama); metaverse (Reality Labs).
**Key Resources:** 3.3B+ daily active users; ad targeting data; AI models; brand.
**Value Proposition:** Social connection; ad reach; AI tools.
**Customer Relationships:** Free user accounts; advertiser dashboards; creator tools.
**Channels:** Mobile apps; website; WhatsApp API.
**Customer Segments:** Users (free); advertisers (revenue); creators.
**Cost Structure:** R&D (AI, metaverse); content moderation; marketing.
**Revenue Streams:** Advertising (>98%); metaverse (negligible).

## SWOT Analysis
**Strengths:** Unmatched social graph (3.3B+ DAUs); ad targeting data; AI leadership (Llama); strong cash flow.
**Weaknesses:** Metaverse losses; regulatory risk (privacy); user growth saturation; competition (TikTok).
**Opportunities:** AI monetisation (Meta AI); Reels growth; WhatsApp business; Threads.
**Threats:** TikTok; regulatory privacy; EU DMA; Apple ATT.

## PESTLE Analysis
**Political:** Data privacy regulation, antitrust. **Economic:** Advertising spend. **Social:** User mental health, screen time. **Technological:** AI, AR/VR. **Legal:** GDPR, EU DMA, FTC. **Environmental:** Data centre energy use.

## Porter's Five Forces
**Rivalry:** High – TikTok, YouTube, X. **New Entrants:** Moderate – network effects strong. **Supplier Power:** Low – users are suppliers of attention. **Buyer Power:** Advertisers have many options. **Substitutes:** Other social networks, TV, gaming.

## Management & Decision Making
Management focused on AI (Llama, Meta AI), efficiency (Year of Efficiency), and metaverse long-term bet. Aggressive share buybacks.

## Future Outlook
AI monetisation (Meta AI). Reels growth. WhatsApp business. Watch TikTok competition, regulatory risk, and metaverse progress.""",
    "NVDA": """## Business Model Canvas
**Key Partners:** TSMC (chip manufacturing); cloud providers (AWS, Azure, Google); server OEMs (Dell, HPE); AI startups.
**Key Activities:** GPU design; AI platform (CUDA, DGX); networking (Mellanox); software ecosystem.
**Key Resources:** CUDA ecosystem (10M+ developers); AI leadership (H100, Blackwell); strong R&D.
**Value Proposition:** Unrivalled AI compute; CUDA software moat; full-stack AI platform.
**Customer Relationships:** Direct enterprise; cloud partnerships; developer community.
**Channels:** Direct sales; OEMs; cloud marketplaces.
**Customer Segments:** Data centres (AI training/inference); gaming; professional visualisation; automotive.
**Cost Structure:** R&D (~$8B); wafer costs; marketing; G&A.
**Revenue Streams:** Data centre (>80%); gaming; professional visualisation; automotive.

## SWOT Analysis
**Strengths:** CUDA moat; 80%+ data centre GPU share; AI leadership; strong margins.
**Weaknesses:** Customer concentration (cloud providers); cyclicality; competition; high valuation.
**Opportunities:** AI inference growth; sovereign AI; edge AI; automotive.
**Threats:** Competition from AMD, Intel, custom chips (TPU, Inferentia); export controls (China); cyclical downturn.

## PESTLE Analysis
**Political:** US-China export controls, CHIPS Act. **Economic:** AI capex cycle. **Social:** AI adoption, energy concerns. **Technological:** Blackwell, chiplet, HBM. **Legal:** Export compliance, IP. **Environmental:** GPU energy efficiency.

## Porter's Five Forces
**Rivalry:** Intense – AMD, Intel, custom chips. **New Entrants:** High – capex, CUDA moat. **Supplier Power:** Moderate – TSMC sole advanced node. **Buyer Power:** Moderate – cloud providers have scale. **Substitutes:** Custom AI chips (TPU, Trainium).

## Management & Decision Making
Management focused on AI dominance, Blackwell ramp, and software ecosystem. Aggressive R&D and acquisitions.

## Future Outlook
AI inference growth. Blackwell ramp. Sovereign AI. Watch competition, export controls, and AI capex cycle.""",
    "GOOG": """## Business Model Canvas
**Key Partners:** Advertisers; content creators (YouTube); Android OEMs; cloud partners; AI research community.
**Key Activities:** Search; advertising; YouTube; cloud (GCP); AI (Gemini, DeepMind); hardware (Pixel, Nest).
**Key Resources:** Search monopoly (90%+ share); YouTube; Android; AI talent (DeepMind).
**Value Proposition:** Free search & services; ad reach; cloud infrastructure; AI tools.
**Customer Relationships:** Free user accounts; advertiser dashboards; GCP support.
**Channels:** Google.com; YouTube; Android; GCP console.
**Customer Segments:** Users (free); advertisers; enterprises (GCP); developers.
**Cost Structure:** R&D (AI); traffic acquisition costs; data centres; marketing.
**Revenue Streams:** Advertising (Search, YouTube); cloud; subscriptions (YouTube Premium, Google One).

## SWOT Analysis
**Strengths:** Search monopoly; YouTube #2 website; AI leadership (Gemini, DeepMind); strong cash flow.
**Weaknesses:** Advertising concentration; regulatory antitrust; cloud #3.
**Opportunities:** AI monetisation (Gemini, Search Generative Experience); cloud growth; YouTube subscriptions.
**Threats:** Regulatory antitrust (DOJ case); competition from OpenAI, Microsoft; search share erosion.

## PESTLE Analysis
**Political:** Antitrust, data privacy. **Economic:** Advertising spend. **Social:** Privacy concerns. **Technological:** AI, quantum. **Legal:** EU DMA, US antitrust. **Environmental:** Data centre energy.

## Porter's Five Forces
**Rivalry:** High – Microsoft (Bing, OpenAI), Amazon (ads). **New Entrants:** High – AI search startups. **Supplier Power:** Low – many content creators. **Buyer Power:** Advertisers have many options. **Substitutes:** AI chatbots (ChatGPT), social media ads.

## Management & Decision Making
Management focused on AI (Gemini, DeepMind), cloud growth, and cost efficiency. Capital returns via buybacks.

## Future Outlook
AI monetisation (Gemini, Search Generative Experience). Cloud growth. YouTube subscriptions. Watch antitrust, AI competition, and ad spend.""",
    "BKNG": """## Business Model Canvas
**Key Partners:** Hotels; airlines; car rental companies; online travel agencies; payment providers.
**Key Activities:** Online travel booking (Booking.com, Priceline, Kayak, OpenTable); merchant model; affiliate network.
**Key Resources:** Booking.com brand; merchant model inventory; 3M+ accommodation listings; 500M+ monthly visitors.
**Value Proposition:** Largest accommodation inventory; price comparison; merchant model (book now, pay later).
**Customer Relationships:** Loyalty program (Genius); 24/7 customer support.
**Channels:** Direct (website, app); affiliate partners; meta-search (Kayak).
**Customer Segments:** Leisure travellers; business travellers; restaurants (OpenTable).
**Cost Structure:** Marketing (performance); staff; technology; customer support.
**Revenue Streams:** Booking commissions; merchant model margin; advertising.

## SWOT Analysis
**Strengths:** Largest accommodation inventory (3M+); merchant model; strong brand in Europe; high margins.
**Weaknesses:** Concentration in Europe; competition from Airbnb; seasonality; merchant model credit risk.
**Opportunities:** US expansion; alternative accommodations; connected trip (flights, car, activities); AI personalisation.
**Threats:** Google Travel; Airbnb; recession travel slowdown; regulatory (short-term rentals).

## PESTLE Analysis
**Political:** Short-term rental regulations, tax policies. **Economic:** Travel demand, consumer spending. **Social:** Post-pandemic travel boom, alternative accommodations. **Technological:** AI personalisation, mobile booking. **Legal:** Competition law, consumer protection. **Environmental:** Flight shaming, sustainable travel.

## Porter's Five Forces
**Rivalry:** High – Expedia, Airbnb, Google Travel. **New Entrants:** Moderate – OTAs require scale. **Supplier Power:** Low – hotels need distribution. **Buyer Power:** High – travellers can compare. **Substitutes:** Direct hotel booking, Airbnb.

## Management & Decision Making
Management focused on merchant model, US expansion, and connected trip. Shareholder returns via buybacks.

## Future Outlook
US expansion. Alternative accommodations. AI personalisation. Watch travel demand, competition from Google, and regulation.""",
    "NAB": """## Business Model Canvas
**Key Partners:** Australian government (regulator), home loan aggregators, mortgage insurers, Visa/Mastercard, wealth management platforms, fintech partners (e.g., 86 400 acquisition), AWS (cloud migration).
**Key Activities:** Retail banking (home loans, deposits); business & corporate banking; wealth management (MLC); institutional banking; digital banking (NAB app, NAB Connect); home loan servicing.
**Key Resources:** #3 home lender in Australia (~15% market share); leading business bank (largest business lending share); strong deposit base; 1,500+ branches; NAB app with 2M+ daily users; conservative balance sheet.
**Value Proposition:** Focus on business banking as core differentiator; 'NAB Now, Pay Later' digital solutions; competitive home loan rates; strong customer service; digital innovation (AI-driven fraud detection).
**Customer Relationships:** Branch network; relationship managers for business clients; NAB app (24/7 banking); call centres; loyalty programs (NAB Rewards).
**Channels:** Branches; NAB app; NAB Connect (business); third-party brokers; ATM network; contact centre.
**Customer Segments:** Retail consumers (home buyers, savers); small to medium enterprises (SMEs); corporate & institutional; wealth clients (MLC); government.
**Cost Structure:** Branch network (~1,500); staff salaries; technology & digital transformation; regulatory compliance (APRA); marketing; bad debt provisions.
**Revenue Streams:** Net interest income (home loans, business lending); non-interest income (fees, wealth management, transactional fees); institutional banking; trading income.

## SWOT Analysis
**Strengths:** Largest business bank in Australia; strong deposit franchise; digital transformation progressing (AWS cloud migration); conservative risk culture; $7.3B cash earnings FY2024.
**Weaknesses:** Home loan market share behind CBA and Westpac; higher cost-to-income ratio (~50%) than peers; legacy systems in parts; reliance on Australian housing market.
**Opportunities:** Business lending growth from SME recovery; digital banking (NAB app features); wealth management cross-sell; home loan refinancing wave; cost-out initiatives.
**Threats:** Rising interest rates impacting mortgage stress; fintech competition (Judo Bank, Athena); regulatory scrutiny (Royal Commission legacy); economic slowdown; cybersecurity risks.

## PESTLE Analysis
**Political:** Banking royal commission recommendations, APRA capital requirements, open banking (CDR). **Economic:** Interest rate cycle, housing market, unemployment, GDP growth. **Social:** Digital adoption, trust in banks, financial literacy. **Technological:** AI, cloud, open banking APIs, cybersecurity. **Legal:** Banking Act, NCCP, AML/CTF, privacy law. **Environmental:** Climate risk in loan portfolios, sustainable finance, net-zero commitments.

## Porter's Five Forces
**Rivalry:** High – Big 4 plus regional banks, neobanks (Judo, Volt). **New Entrants:** Moderate – digital bank licences easier, but brand trust hard to build. **Supplier Power:** Low – depositors fragmented, but large wholesale funding markets have some power. **Buyer Power:** High – customers can switch home loans easily via brokers. **Substitutes:** Peer-to-peer lending, mortgage fintechs, non-bank lenders.

## Management & Decision Making
CEO Ross McEwan (since 2019, ex-RBS) focused on simplification, culture change, and digital. CFO Gary Lennon (since 2022) drives cost efficiency. Capital returns via dividends and buybacks. Underlying profit $7.3B, ROE 11.5%.

## Future Outlook
Business lending growth. Digital adoption reduces cost-to-income. Home loan refinancing wave. Watch housing market, interest rates, and competition from neobanks.""",
    "CVX": """## Business Model Canvas
**Key Partners:** OPEC+ (oil price influence), national oil companies (e.g., Saudi Aramco), joint venture partners (e.g., Tengizchevroil), LNG offtakers, renewable energy technology partners.
**Key Activities:** Oil & gas exploration & production (upstream); refining & marketing (downstream); LNG production (Gorgon, Wheatstone); low-carbon investments (renewables, hydrogen, carbon capture).
**Key Resources:** Permian Basin (largest US oil field); Tengiz field (Kazakhstan); Gorgon LNG (Australia); refining network; strong balance sheet ($15B+ cash).
**Value Proposition:** Low-cost oil producer (Permian breakeven ~$40/bbl); integrated model (upstream + downstream); reliable dividend growth; commitment to lower carbon (CCUS, renewable fuels).
**Customer Relationships:** Long-term supply contracts (LNG); spot market sales; branded fuel stations (Chevron, Texaco); industrial customers.
**Channels:** Direct sales; trading desks; retail fuel stations; pipelines; LNG carriers.
**Customer Segments:** Fuel retailers; industrial manufacturers; power utilities; airlines; governments; chemical companies.
**Cost Structure:** Exploration & production costs; refining costs; capex ($14-16B annually); G&A; environmental remediation.
**Revenue Streams:** Oil & gas sales; refined products; LNG; chemicals; renewable fuel credits.

## SWOT Analysis
**Strengths:** Permian Basin scale (700k boe/d); low-cost operator; strong balance sheet; 36-year dividend growth streak; leading LNG position in Australia.
**Weaknesses:** Oil price sensitivity; carbon footprint; legacy environmental liabilities; refining margins volatile.
**Opportunities:** Lower-carbon investments (CCUS, renewable diesel); LNG demand growth (Asia); Permian production growth; acquisition of PDC Energy (2023) adds scale.
**Threats:** Energy transition reducing fossil fuel demand; oil price collapse; competition from renewables; regulatory pressure (SEC climate disclosure).

## PESTLE Analysis
**Political:** US energy policy, OPEC+ decisions, sanctions (e.g., Venezuela). **Economic:** Oil & gas prices, global GDP growth, refining margins. **Social:** ESG pressure, workforce transition. **Technological:** CCUS, hydrogen, advanced drilling. **Legal:** Climate litigation, antitrust, tax law. **Environmental:** Net-zero commitments, methane regulations.

## Porter's Five Forces
**Rivalry:** High – Exxon, Shell, BP, TotalEnergies. **New Entrants:** High barriers (capex, expertise). **Supplier Power:** Low – oil as commodity, but OPEC has influence. **Buyer Power:** Moderate – refiners and large buyers. **Substitutes:** Renewables, electric vehicles, hydrogen.

## Management & Decision Making
CEO Mike Wirth (since 2018) – focused on capital discipline, lower carbon investments, and shareholder returns. CFO Pierre Breber (since 2019). Returned $26B to shareholders in 2024.

## Future Outlook
Permian production growth. Lower-carbon investments (CCUS, renewable diesel). LNG demand. Watch oil prices, energy transition policies, and project execution.""",
    "AXP": """## Business Model Canvas
**Key Partners:** Merchants (accept Amex cards); cardmembers; airlines/hotels (rewards transfer partners); third-party banks (co-brand cards); travel agencies.
**Key Activities:** Charge card & credit card issuing; merchant acquiring; travel services; rewards & loyalty management; payment processing; fraud prevention.
**Key Resources:** Premium brand; affluent customer base; Global Merchant Services network; Centurion lounges; data analytics capabilities; $1.1T network volume.
**Value Proposition:** Premium card experience (travel, dining, service); Membership Rewards points; global acceptance; small business tools (Open); no preset spending limit on charge cards.
**Customer Relationships:** Direct (consumer, small business, corporate); co-brand partners (Delta, Marriott); 24/7 customer service; Centurion lounges; mobile app.
**Channels:** Direct mail; online applications; partner marketing; mobile app; travel portals.
**Customer Segments:** Affluent consumers; small businesses; corporations; co-brand partners (airlines, hotels).
**Cost Structure:** Marketing & rewards; customer service; fraud prevention; technology; credit losses.
**Revenue Streams:** Discount revenue (merchant fees); net card fees (annual fees); interest income (from revolving balances); travel commissions; other fees.

## SWOT Analysis
**Strengths:** Premium brand; high-spend affluent cardholders; strong network effect (merchants want Amex customers); robust rewards program; low credit losses (targets affluent).
**Weaknesses:** Higher merchant fees than Visa/Mastercard; acceptance still lower internationally; reliance on travel & entertainment spending.
**Opportunities:** Small business expansion (Open platform); international growth (especially in Europe, Asia); digital wallet integration (Apple Pay, Google Pay); travel rebound.
**Threats:** Competition from Visa, Mastercard, and fintechs (Stripe, Square); regulatory interchange caps; economic downturn reducing card spend; credit cycle.

## PESTLE Analysis
**Political:** Regulation of interchange fees (Durbin Amendment, EU caps). **Economic:** Consumer spending, travel demand, interest rates (credit card interest). **Social:** Cashless adoption, loyalty expectations. **Technological:** Digital wallets, tokenisation, AI fraud detection. **Legal:** CARD Act, fair lending, data privacy. **Environmental:** ESG focus on sustainable travel.

## Porter's Five Forces
**Rivalry:** High – Visa, Mastercard, Discover, Capital One. **New Entrants:** Moderate – fintechs (e.g., Brex) but scale hard. **Supplier Power:** Low – cardholders are many, but affluent segment has options. **Buyer Power:** Merchants have limited power (must accept Amex or lose customers). **Substitutes:** BNPL (Affirm, Klarna), debit cards, cash.

## Management & Decision Making
CEO Stephen Squeri (since 2018) – focused on premium customer experience, digital innovation, and small business growth. CFO Christophe Le Caillec (since 2023). Strong capital returns (dividends, buybacks).

## Future Outlook
Travel rebound drives spending. Small business expansion. International growth. Watch consumer spending, regulatory interchange caps, and competition from BNPL.""",
    "BAC": """## Business Model Canvas
**Key Partners:** Depositors; borrowers; investment banking clients; wealth management clients (Merrill Lynch); fintech partners; government regulators.
**Key Activities:** Consumer banking (deposits, loans, credit cards); wealth management (Merrill); investment banking & trading (BofA Securities); global banking (corporate lending, treasury).
**Key Resources:** Largest deposit base in US ($1.9T); extensive branch network (4,000+); Merrill Lynch wealth platform; leading investment bank; digital banking (55M active users).
**Value Proposition:** ‘Responsible Growth’ strategy – balanced risk, customer focus, efficiency; ‘Life Plan’ digital financial advice; Merrill Edge self-directed investing; strong capital position.
**Customer Relationships:** Branch network; mobile app (Erica AI assistant); relationship managers (wealth, business); call centres; online banking.
**Channels:** Branches; BofA app; Merrill Edge; online banking; contact centre; financial advisors.
**Customer Segments:** Consumer (mass market, affluent, high net worth); small business; corporate & institutional; wealth management; government.
**Cost Structure:** Branch network; technology (AI, cloud); staff; marketing; legal & compliance; provision for credit losses.
**Revenue Streams:** Net interest income (loans, securities); non-interest income (fees, wealth management, investment banking, trading).

## SWOT Analysis
**Strengths:** Largest US deposit base; #2 investment bank; strong digital platform (Erica AI); conservative credit culture; $27.5B net income 2024, ROE 12.7%.
**Weaknesses:** Sensitive to interest rate cycle; large physical branch footprint; legacy mortgage issues (still facing litigation).
**Opportunities:** Rising rates boost NIM; wealth management cross-sell; investment banking market share gains; digital cost reduction; ESG lending.
**Threats:** Recession leading to credit losses; fintech competition (Chime, SoFi); regulatory capital requirements; cybersecurity.

## PESTLE Analysis
**Political:** Banking regulation (Dodd-Frank, CCAR), consumer protection (CFPB). **Economic:** Interest rates, unemployment, GDP growth, housing market. **Social:** Digital banking adoption, trust in banks. **Technological:** AI (Erica), blockchain, cloud migration. **Legal:** Ongoing mortgage litigation, antitrust, data privacy. **Environmental:** Climate stress testing, sustainable finance.

## Porter's Five Forces
**Rivalry:** High – JPMorgan, Wells Fargo, Citigroup, regional banks. **New Entrants:** Moderate – digital banks (Chime) but scale hard. **Supplier Power:** Low – depositors fragmented. **Buyer Power:** Moderate – consumers can switch banks easily. **Substitutes:** Fintech lenders, neobanks, credit unions.

## Management & Decision Making
CEO Brian Moynihan (since 2010) – transformed BAC post-2008, built capital, cut expenses, focused on responsible growth. CFO Alastair Borthwick (since 2019). Returned $16B to shareholders in 2024.

## Future Outlook
Interest rate tailwinds for NIM. Investment banking rebound. Digital adoption reduces cost. Watch credit quality, economic cycle, and regulatory environment.""",
    "ANZ": """## Business Model Canvas
**Key Partners:** Institutional investors, mortgage brokers, fintech partners (e.g., Cashrewards), Visa/Mastercard, AWS (cloud migration), Australian government (regulator).
**Key Activities:** Retail & commercial banking (home loans, deposits, business lending); institutional banking (markets, trade finance); wealth management (ANZ Private); digital banking (ANZ Plus, ANZ App); simplification of Asian operations.
**Key Resources:** #4 major Australian bank by market cap; strong institutional banking franchise; leading digital bank ANZ Plus (over 1M customers); cost-out program ($200M+ annual savings); conservative balance sheet.
**Value Proposition:** Focus on core Australian and New Zealand banking; simplified business model after exiting underperforming Asian retail; digital-first strategy with ANZ Plus; strong institutional banking capabilities.
**Customer Relationships:** Branch network (though reduced), relationship managers for business/institutional, digital self-service via ANZ App, ANZ Plus for retail.
**Channels:** Branches, ANZ App, ANZ Plus, brokers, institutional sales teams.
**Customer Segments:** Retail consumers (home buyers, savers), SMEs, corporate & institutional clients, wealth clients.
**Cost Structure:** Staff, technology & digital, branch network, regulatory compliance, bad debt provisions.
**Revenue Streams:** Net interest income (home loans, business lending), non-interest income (fees, trading, institutional banking).

## SWOT Analysis
**Strengths:** Strong institutional bank, successful digital platform ANZ Plus, simplified geographic focus, robust capital position.
**Weaknesses:** Lower home loan market share than CBA/Westpac, legacy issues from Asian expansion, reliance on Australian housing market.
**Opportunities:** Digital-only bank growth, cost-out initiatives, wealth management cross-sell, interest rate tailwinds.
**Threats:** Intense competition in home lending, fintech disruption, regulatory scrutiny, economic slowdown.

## PESTLE Analysis
**Political:** Banking regulation (APRA), open banking (CDR). **Economic:** Interest rates, housing market, GDP growth. **Social:** Digital adoption, trust in banks. **Technological:** AI, cloud migration, cybersecurity. **Legal:** Banking Act, AML/CTF, privacy. **Environmental:** Climate risk, sustainable finance.

## Porter's Five Forces
**Rivalry:** High – Big 4 plus regional banks, neobanks. **New Entrants:** Moderate – digital bank licences easier but scale hard. **Supplier Power:** Low – depositors fragmented. **Buyer Power:** High – customers can switch easily. **Substitutes:** Fintech lenders, neobanks.

## Management & Decision Making
CEO Shayne Elliott has led a strategic simplification, exiting underperforming Asian businesses and focusing on Australia/NZ. Investment in digital (ANZ Plus) and AI. Capital returns via dividends and buybacks.

## Future Outlook
Digital banking growth, cost-out program completion, potential for improved NIM as rates stabilize. Watch housing market and competition.""",
    "AVGO": """## Business Model Canvas
**Key Partners:** TSMC (chip manufacturing), cloud providers (AWS, Azure, Google), enterprise software customers (VMware), OEMs (Dell, HPE), AI chip customers (Google TPU, Meta).
**Key Activities:** Semiconductor design (networking, broadband, storage, wireless); infrastructure software (VMware, CA, Symantec); AI accelerator development (custom ASICs); strategic acquisitions.
**Key Resources:** Broad portfolio of connectivity chips (Ethernet, switching, routing); VMware software stack; strong relationships with hyperscalers; AI ASIC design expertise; Hock Tan's M&A track record.
**Value Proposition:** Critical connectivity infrastructure for data centers and AI clusters; comprehensive software stack for hybrid cloud (VMware); custom AI chip design for major cloud providers.
**Customer Relationships:** Long-term supply agreements with OEMs and cloud providers; enterprise software licensing and support; direct sales and channel partners.
**Channels:** Direct sales force, distributors, OEM partnerships, VMware channel ecosystem.
**Customer Segments:** Hyperscale data centers, enterprise IT, telecommunications providers, consumer electronics (Apple, Samsung).
**Cost Structure:** R&D for chip design, M&A integration costs, sales & marketing, wafer costs from TSMC.
**Revenue Streams:** Semiconductor solutions (networking, broadband, storage), infrastructure software (VMware licensing and subscription), AI ASIC development fees.

## SWOT Analysis
**Strengths:** Dominant position in data center networking (Ethernet switches, NICs); VMware provides sticky enterprise software revenue; proven M&A integration model; strong free cash flow.
**Weaknesses:** High debt from VMware acquisition; exposure to cyclical semiconductor industry; reliance on a few large customers for AI ASICs; complex product portfolio.
**Opportunities:** AI infrastructure build‑out driving demand for high‑speed networking; VMware subscription transition; custom AI chip opportunities with more cloud providers; edge computing.
**Threats:** Competition from NVIDIA (Spectrum switches), Marvell, and in‑house designs by cloud providers; geopolitical risks (US‑China trade); integration challenges with VMware; potential slowdown in AI capex.

## PESTLE Analysis
**Political:** US export controls on semiconductors, CHIPS Act funding. **Economic:** AI investment cycle, enterprise IT spending. **Social:** Demand for data center capacity, remote work. **Technological:** AI/ML, cloud computing, software‑defined networking. **Legal:** Antitrust scrutiny of acquisitions, IP protection. **Environmental:** Data center energy efficiency.

## Porter's Five Forces
**Rivalry:** Intense – NVIDIA, Marvell, Cisco in networking; Microsoft, Red Hat in software. **New Entrants:** High barriers due to IP, scale, and customer relationships. **Supplier Power:** Moderate – TSMC is key for advanced nodes. **Buyer Power:** High – hyperscalers can negotiate or design in‑house. **Substitutes:** White‑box switches, open‑source software.

## Management & Decision Making
CEO Hock Tan is renowned for disciplined M&A and cost management. The VMware acquisition is a transformative bet on hybrid cloud software. Focus on maximizing free cash flow and paying down debt.

## Future Outlook
AI networking demand is a major tailwind. VMware subscription transition will smooth revenue. Watch debt reduction progress and competitive dynamics in AI chips.""",
}

# ---------- LEADERSHIP ----------
LEADERSHIP = {
    "BHP": {"ceo": "Mike Henry (since 2020)", "cfo": "David Lamont (since 2021)", "track": "Henry drove portfolio simplification (sold petroleum to Woodside), disciplined capital returns, Jansen potash approval."},
    "WDS": {"ceo": "Meg O'Neill (since 2021)", "cfo": "Graham Tiver (since 2020)", "track": "O'Neill led acquisition of BHP's petroleum assets, Louisiana LNG FID, Beaumont ammonia purchase."},
    "CBA": {"ceo": "Matt Comyn (since 2018)", "cfo": "Alan Docherty (since 2021)", "track": "Comyn led cloud migration to AWS, OpenAI partnership, digital transformation. Strong capital returns."},
    "NAB": {"ceo": "Ross McEwan (since 2019)", "cfo": "Gary Lennon (since 2022)", "track": "McEwan led digital transformation, cost reduction, and capital management. Focus on business banking and home lending."},
    "ANZ": {"ceo": "Shayne Elliott", "cfo": "Farhan Faruqui", "track": "Elliott has led ANZ's simplification strategy, focusing on core banking in Australia and New Zealand while exiting underperforming Asian retail businesses. The bank is investing heavily in digital platforms and AI."},
    "BBRI": {"ceo": "Sunarso (since 2019)", "cfo": "Viviana Dyah Ayu (since 2020)", "track": "Sunarso drove 'BRIvolution' digital transformation, ultra-micro holding integration, record BRImo adoption."},
    "ADRO": {"ceo": "Garibaldi 'Boy' Thohir (since 2008)", "cfo": "Jodhi Pangestu", "track": "Thohir led spin-off of thermal coal, pivot to metcoal, aluminum smelter, and renewable energy."},
    "SMSM": {"ceo": "Tony S. Budiman", "cfo": "Suryadi", "track": "Consistent execution, export growth to 45+ countries, maintained debt-free balance sheet, EV product R&D."},
    "UNTR": {"ceo": "Darma Setiawan (since 2015)", "cfo": "Yunus Saifulhak", "track": "Maintained Komatsu exclusivity, PAMA largest contractor, diversification into gold and renewables."},
    "ITMG": {"ceo": "M. Qodrat (since 2022)", "cfo": "Agus Suhendar", "track": "Focused on high dividends, production efficiency, solar hybrid projects. Banpu parent strategy influence."},
    "POWR": {"ceo": "M. Firdaus", "cfo": "R. Agus", "track": "Conservative management, long-term PPAs, stable operations. Slow to adopt renewables but exploring solar."},
    "MPMX": {"ceo": "Djoko Susanto", "cfo": "Iwan Setiawan", "track": "Stable Honda distribution, integrated financing and rental. Investing in EV motorcycle transition."},
    "BTPS": {"ceo": "Ridwan Kurniawan", "cfo": "Dewi Sartika", "track": "Focused on sharia microfinance, digital group meetings, partnership with Baznas. Small scale but niche."},
    "DMAS": {"ceo": "Takeshi Koyama (Sojitz)", "cfo": "Santi Widjaja", "track": "Japanese parent backing, data centre land sales driving growth. Green estate certification."},
    "SPTO": {"ceo": "Widjaja (family)", "cfo": "Lukman", "track": "Long-term TOTO exclusivity maintained. Expanding to Tier-2 cities. High dividend yield."},
    "TSM": {"ceo": "C.C. Wei (since 2018)", "cfo": "Wendell Huang", "track": "Wei led 2nm/3nm ramp, global expansion (Arizona, Japan, Germany). Capital discipline, high R&D."},
    "V": {"ceo": "Ryan McInerney (since 2023)", "cfo": "Chris Suh (since 2023)", "track": "Focus on tokenisation, cross-border solutions, crypto partnerships. Strong capital returns."},
    "MA": {"ceo": "Michael Miebach (since 2020)", "cfo": "Sachin Mehra", "track": "Multi-rail expansion, crypto partnerships, B2B payments. Consistent growth."},
    "PBR-A": {"ceo": "Magda Chambriard (since 2024)", "cfo": "Fernando Melgarejo", "track": "Focus on pre-salt growth, debt reduction, and shareholder returns. Political interference risk."},
    "MSFT": {"ceo": "Satya Nadella (since 2014)", "cfo": "Amy Hood (since 2013)", "track": "Cloud and AI leadership, OpenAI partnership, Activision acquisition. Excellent capital allocation."},
    "AMZN": {"ceo": "Andy Jassy (since 2021)", "cfo": "Brian Olsavsky (since 2015)", "track": "Jassy focused on cost optimisation, AWS growth, AI (Bedrock). Healthcare and satellite long-term bets."},
    "AAPL": {"ceo": "Tim Cook (since 2011)", "cfo": "Luca Maestri (since 2014)", "track": "Services expansion, ecosystem lock-in, capital returns. Vision Pro and AI integration next."},
    "META": {"ceo": "Mark Zuckerberg (founder)", "cfo": "Susan Li (since 2022)", "track": "Year of Efficiency, AI (Llama), metaverse long-term bet. Aggressive buybacks."},
    "NVDA": {"ceo": "Jensen Huang (founder)", "cfo": "Colette Kress (since 2013)", "track": "AI dominance, Blackwell ramp, CUDA moat. Exceptional execution."},
    "GOOG": {"ceo": "Sundar Pichai (since 2015)", "cfo": "Ruth Porat (since 2015)", "track": "AI first (Gemini, DeepMind), cloud growth, cost efficiency. Antitrust headwinds."},
    "BKNG": {"ceo": "Glenn Fogel (since 2017)", "cfo": "David Goulden", "track": "Merchant model expansion, US growth, connected trip. Strong capital returns."},
    "AVGO": {"ceo": "Hock Tan", "cfo": "Kirsten Spears", "track": "Tan has built Broadcom into a semiconductor and infrastructure software powerhouse through a disciplined acquisition strategy (VMware, CA Technologies). The company is a key beneficiary of the AI infrastructure build-out."},
    "CVX": {"ceo": "Mike Wirth (since 2018)", "cfo": "Pierre Breber (since 2019)", "track": "Wirth focused on oil and gas production growth, lower carbon investments (renewables, hydrogen). Strong shareholder returns."},
    "AXP": {"ceo": "Stephen Squeri (since 2018)", "cfo": "Christophe Le Caillec (since 2023)", "track": "Squeri expanded premium card offerings, leveraged data and digital capabilities, maintained strong credit discipline."},
    "BAC": {"ceo": "Brian Moynihan (since 2010)", "cfo": "Alastair Borthwick (since 2019)", "track": "Moynihan transformed BAC post‑2008, reduced expenses, built capital, and focused on digital banking and ESG."},
}

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
