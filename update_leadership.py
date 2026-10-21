#!/usr/bin/env python3
"""
Updates the Leadership section in data.json for all stocks
whose CEO/leadership has changed since the file was generated.

Run:  python update_leadership.py
Reads:  data.json
Writes: data_updated.json
"""

import json
import re
import sys
from pathlib import Path

INPUT  = "data.json"
OUTPUT = "data_updated.json"

LEADERSHIP = {
    # ---- ORIGINAL 8 (already in your first script) ----
    "BHP": """## Leadership
**CEO:** Brandon Craig (effective 1 July 2026)  
**CFO:** David Lamont  
**Track Record:** Craig succeeds Mike Henry, who led BHP for six and a half years. Craig previously led BHP's iron ore division and, most recently, its Americas operations. The transition comes as BHP focuses on copper and potash growth.""",

    "WDS": """## Leadership
**CEO:** Liz Westcott (appointed March 2026)  
**CFO:** Graham Tiver  
**Track Record:** Westcott was Acting CEO since December 2025 after Meg O'Neill departed to lead BP. She joined Woodside in 2023 and previously served as Executive Vice President and Chief Operating Officer Australia, overseeing the Scarborough project. She has over 25 years of energy industry experience, including a long tenure at ExxonMobil.""",

    "NAB": """## Leadership
**CEO:** Andrew Irvine (since April 2024)  
**CFO:** Gary Lennon  
**Track Record:** Irvine succeeded Ross McEwan. He previously led NAB's Business and Private Banking division and has over 26 years of financial services experience, including senior roles at Bank of Montreal and McKinsey & Company.""",

    "ANZ": """## Leadership
**CEO:** Nuno Matos (since 12 May 2025)  
**CFO:** (verify current CFO)  
**Track Record:** Matos succeeded Shayne Elliott, who retired after nine years. Matos previously spent his career at HSBC, most recently as CEO of Wealth and Personal Banking.""",

    "WBC": """## Leadership
**CEO:** Anthony Miller (Managing Director and Chief Executive)  
**CFO:** Michael Rowland  
**Track Record:** Miller succeeded Peter King. He has extensive banking and legal experience, including a partnership at Goldman Sachs and prior roles at Credit Suisse.""",

    "AAPL": """## Leadership
**CEO:** John Ternus (effective 1 September 2026)  
**CFO:** Luca Maestri  
**Track Record:** Ternus succeeded Tim Cook, who became Executive Chairman. Ternus joined Apple in 2001 and led Hardware Engineering since 2021. Cook remains involved with policymaker engagement and certain company aspects.""",

    "BBRI": """## Leadership
**President Director:** Hery Gunardi (appointed March 2025)  
**CFO:** Viviana Dyah Ayu  
**Track Record:** Gunardi succeeded Sunarso. He previously served as President Director of Bank Syariah Indonesia (BSI) and held senior roles at Bank Mandiri, including leading its micro and retail banking transformation.""",

    "ADRO": """## Leadership
**President Director:** Iwan Dewono Budiyuwono (appointed June 2025)  
**CFO:** (verify current CFO)  
**Track Record:** Budiyuwono succeeded Garibaldi "Boy" Thohir, who moved to Vice President Commissioner. Budiyuwono previously served as a Director of AlamTri.""",

    # ---- ADDITIONAL 8 INDONESIAN STOCKS ----
    "SMSM": """## Leadership
**President Director:** Djojo Hartono (since June 2024)  
**Finance Director:** Sumarni  
**Track Record:** Hartono succeeded Eddy Hartono. He previously served as Vice President Director and has been with the ADR Group since 1998.""",

    "UNTR": """## Leadership
**President Director:** Iwan Hadiantoro (since April 2026)  
**CFO:** (verify current CFO)  
**Track Record:** Hadiantoro succeeded Frans Kesuma. He has held various senior roles within the Astra Group and United Tractors, most recently as Corporate Legal & Business Development Director.""",

    "ITMG": """## Leadership
**President Director:** Mulianto  
**CFO:** (verify current CFO)  
**Track Record:** Mulianto leads Indo Tambangraya Megah's operations and strategy. Refer to recent company filings for current strategic direction.""",

    "POWR": """## Leadership
**President Director:** Andrew K. Labbaika  
**Financial Director:** Christanto Pranata  
**Track Record:** Labbaika has led Cikarang Listrindo as the sole private power supplier in the Cikarang industrial estates. He was first appointed in 2015 and reappointed in 2021.""",

    "MPMX": """## Leadership
**President Director & Group CEO:** Suwito Mawarwati (since September 2018)  
**Group CFO:** Beatrice Kartika Busono  
**Track Record:** Mawarwati leads MPMX's integrated automotive ecosystem, including Honda distribution, financing, and rental operations.""",

    "BTPS": """## Leadership
**President Director:** Hadi Wibowo (since April 2020)  
**Finance Director:** Fachmy Achmad  
**Track Record:** Wibowo leads Bank BTPN Syariah's sharia microfinance operations and group lending model.""",

    "DMAS": """## Leadership
**President Director:** Hongky Jeffry Nantung (since 2016)  
**Vice President Director:** Shinji Yoneda (appointed September 2026)  
**Track Record:** Nantung leads Puradelta Lestari's industrial estate development at Kota Deltamas, including data centre land sales.""",

    "SPTO": """## Leadership
**President Director:** Willianto Alim (since 2023)  
**Finance Director:** Adhi Sudargo Tasmin  
**Track Record:** Alim leads Surya Toto Indonesia's premium bathroom products distribution, maintaining the exclusive TOTO Japan relationship.""",

    # ---- VERIFIED UNCHANGED (optional: replace to be 100% sure) ----
    "CBA": """## Leadership
**CEO:** Matt Comyn (since 2018, confirmed until 2028)  
**CFO:** Alan Docherty  
**Track Record:** Comyn has led CBA's digital transformation, AWS cloud migration, and OpenAI partnership. The board has extended his tenure through 2028.""",

    "FMG": """## Leadership
**CEO:** Dino Otranto (CEO of Metals and Operations)  
**Co-CEO Growth & Energy:** Agustin Pichot  
**Track Record:** Otranto leads Fortescue's iron ore operations and decarbonisation strategy. Pichot leads the growth and energy division.""",

    "STO": """## Leadership
**CEO:** Kevin Gallagher (Managing Director and CEO)  
**CFO:** (verify current CFO)  
**Track Record:** Gallagher has led Santos since 2016, focusing on LNG, cost reduction, and CCS projects.""",

    "ALD": """## Leadership
**CEO:** Matt Halliday (Managing Director and CEO since March 2020)  
**CFO:** Greg Barnes  
**Track Record:** Halliday leads Ampol's integrated fuel supply chain strategy, including the EG Australia acquisition and EV charging network expansion.""",

    "MQG": """## Leadership
**CEO:** Shemara Wikramanayake (until 6 November 2026) · **Greg Ward** (incoming CEO, effective 7 November 2026)  
**CFO:** Frank Kwok  
**Track Record:** Wikramanayake retires after nearly eight years as CEO. Ward, a 30-year Macquarie veteran who previously led Banking and Financial Services, succeeds her.""",

    "TSM": """## Leadership
**CEO:** C.C. Wei (Chairman and CEO)  
**CFO:** Wendell Huang  
**Track Record:** Wei leads TSMC's advanced node roadmap (3nm, 2nm) and global expansion across Arizona, Japan, and Germany.""",

    "V": """## Leadership
**CEO:** Ryan McInerney (since February 2023)  
**CFO:** Chris Suh  
**Track Record:** McInerney leads Visa's tokenisation, cross-border solutions, and crypto partnerships.""",

    "MA": """## Leadership
**CEO:** Michael Miebach (since January 2021)  
**CFO:** Sachin Mehra  
**Track Record:** Miebach leads Mastercard's multi-rail expansion, crypto partnerships, and B2B payments strategy.""",

    "MSFT": """## Leadership
**CEO:** Satya Nadella (Chairman and CEO)  
**CFO:** Amy Hood  
**Track Record:** Nadella leads Microsoft's AI and cloud strategy, including the OpenAI partnership and Copilot monetisation.""",

    "AMZN": """## Leadership
**CEO:** Andy Jassy (since July 2021)  
**CFO:** Brian Olsavsky  
**Track Record:** Jassy focuses on cost optimisation, AWS growth, and AI investment (Bedrock, Trainium).""",

    "META": """## Leadership
**CEO:** Mark Zuckerberg (Founder and CEO)  
**CFO:** Susan Li  
**Track Record:** Zuckerberg leads Meta's AI and metaverse strategy, including Llama models and Meta AI.""",

    "GOOG": """## Leadership
**CEO:** Sundar Pichai (CEO of Google and Alphabet)  
**CFO:** Anat Ashkenazi  
**Track Record:** Pichai leads Alphabet's AI-first strategy (Gemini, DeepMind) and cloud growth.""",

    "NVDA": """## Leadership
**CEO:** Jensen Huang (Founder and CEO)  
**CFO:** Colette Kress  
**Track Record:** Huang leads NVIDIA's AI computing dominance, including the Blackwell platform and CUDA ecosystem.""",

    "BKNG": """## Leadership
**CEO:** Glenn Fogel (President and CEO)  
**CFO:** David Goulden  
**Track Record:** Fogel leads Booking Holdings' connected trip strategy and AI-driven travel personalisation.""",

    "AVGO": """## Leadership
**CEO:** Hock Tan (President and CEO)  
**CFO:** Kirsten Spears  
**Track Record:** Tan leads Broadcom's semiconductor and infrastructure software strategy, including the VMware integration.""",

    "CVX": """## Leadership
**CEO:** Mike Wirth (Chairman and CEO)  
**CFO:** (verify current CFO)  
**Track Record:** Wirth focuses on capital discipline, lower-carbon investments, and shareholder returns.""",

    "AXP": """## Leadership
**CEO:** Stephen Squeri (Chairman and CEO)  
**CFO:** Christophe Le Caillec  
**Track Record:** Squeri leads American Express's premium customer strategy and small business expansion.""",

    "BAC": """## Leadership
**CEO:** Brian Moynihan (Chair and CEO)  
**CFO:** Alastair Borthwick  
**Track Record:** Moynihan leads Bank of America's responsible growth strategy and digital banking investment.""",

    "RHHBY": """## Leadership
**CEO:** Thomas Schinecker (Group CEO)  
**CFO:** Alan Hippe  
**Track Record:** Schinecker leads Roche's pharmaceutical and diagnostics strategy, with a focus on oncology and immunology.""",

    "PBR-A": """## Leadership
**CEO:** Magda Chambriard (President and CEO, reappointed through April 2027)  
**CFO:** (verify current CFO)  
**Track Record:** Chambriard leads Petrobras's pre-salt production growth and renewable energy diversification.""",

    "ASML": """## Leadership
**CEO:** Christophe Fouquet (President and CEO)  
**CFO:** Roger Dassen  
**Track Record:** Fouquet leads ASML's EUV and High-NA roadmap, maintaining the company's monopoly in advanced lithography.""",

    "ESSA": """## Leadership
**CEO:** Kanishk Laroya (President Director since 2023)  
**CFO:** Prakash Chand Bumb  
**Track Record:** Laroya led ESSA's rebranding from Surya Esa Perkasa and the expansion into ammonia production.""",
}


def replace_leadership(profile: str, new_block: str) -> tuple[str, bool]:
    pattern = re.compile(r'##\s+Leadership\b[\s\S]*$', re.IGNORECASE)
    if pattern.search(profile):
        return pattern.sub(new_block, profile), True
    sep = "\n\n" if not profile.endswith("\n\n") else ""
    return profile.rstrip() + sep + new_block, True


def main() -> int:
    src = Path(INPUT)
    if not src.exists():
        print(f"ERROR: {INPUT} not found")
        return 1

    with src.open("r", encoding="utf-8") as f:
        data = json.load(f)

    stocks = data.get("stocks", {})
    if not stocks:
        print("ERROR: no 'stocks' key")
        return 1

    updated, skipped = [], []
    for ticker, new_block in LEADERSHIP.items():
        if ticker not in stocks:
            skipped.append((ticker, "not in stocks"))
            continue
        profile = stocks[ticker].get("profile", "")
        if not profile:
            skipped.append((ticker, "empty profile"))
            continue
        stocks[ticker]["profile"] = replace_leadership(profile, new_block)[0]
        updated.append(ticker)

    dst = Path(OUTPUT)
    with dst.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"✓ Wrote {OUTPUT}")
    print(f"  Updated {len(updated)} stocks:")
    for t in updated:
        print(f"    ✓ {t}")
    if skipped:
        print(f"  Skipped {len(skipped)}:")
        for t, reason in skipped:
            print(f"    - {t}: {reason}")

    # Validate
    try:
        with dst.open("r", encoding="utf-8") as f:
            json.load(f)
        print("  JSON validation: OK")
    except json.JSONDecodeError as e:
        print(f"  JSON validation: FAILED — {e}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
