#!/usr/bin/env python3
"""
Updates the Leadership section in data.json for stocks whose
CEO/leadership has changed since the file was generated.

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

# ------------------------------------------------------------------
# Corrected Leadership blocks. Key = ticker symbol.
# Only stocks with confirmed changes are listed. Everything else
# keeps its original Leadership section untouched.
# ------------------------------------------------------------------
LEADERSHIP = {
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
}


def replace_leadership(profile: str, new_block: str) -> tuple[str, bool]:
    """
    Replace the '## Leadership' section in `profile` with `new_block`.
    Returns (new_profile, changed_flag).

    Leadership is conventionally the last section of the profile
    markdown, so we match from '## Leadership' to end-of-string.
    If no Leadership section exists, append the new block.
    """
    # Try to match Leadership through to end of string
    pattern = re.compile(r'##\s+Leadership\b[\s\S]*$', re.IGNORECASE)
    if pattern.search(profile):
        return pattern.sub(new_block, profile), True

    # No existing section: append
    sep = "\n\n" if not profile.endswith("\n\n") else ""
    return profile.rstrip() + sep + new_block, True


def main() -> int:
    src = Path(INPUT)
    if not src.exists():
        print(f"ERROR: {INPUT} not found in {Path.cwd()}")
        return 1

    with src.open("r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"ERROR: {INPUT} is not valid JSON: {e}")
            return 1

    stocks = data.get("stocks", {})
    if not stocks:
        print("ERROR: no 'stocks' key found in JSON")
        return 1

    updated, skipped = [], []
    for ticker, new_block in LEADERSHIP.items():
        if ticker not in stocks:
            skipped.append((ticker, "not in stocks"))
            continue
        stock = stocks[ticker]
        profile = stock.get("profile", "")
        if not profile:
            skipped.append((ticker, "empty profile"))
            continue
        new_profile, changed = replace_leadership(profile, new_block)
        if changed:
            stock["profile"] = new_profile
            updated.append(ticker)
        else:
            skipped.append((ticker, "no change"))

    dst = Path(OUTPUT)
    with dst.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    # Summary
    print(f"✓ Wrote {OUTPUT}")
    print(f"  Updated {len(updated)} stocks: {', '.join(updated) if updated else '—'}")
    if skipped:
        print(f"  Skipped {len(skipped)}:")
        for t, reason in skipped:
            print(f"    - {t}: {reason}")

    # Sanity check: re-parse the output
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