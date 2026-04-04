# ... (everything before main is the same as the last script I gave you)

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

        # Compute metrics (same as before)
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

    # Try to get API key from multiple possible secret names
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY", "")

    if api_key:
        generate_ai_content(all_stocks, out, api_key, all_metrics)
    else:
        print("No API key found in environment variables (tried ANTHROPIC_API_KEY, GEMINI_API_KEY, GOOGLE_API_KEY).", flush=True)
        print("Skipping AI generation. Financial data only.", flush=True)

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data.json"))
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\n{'='*50}\nWritten: {path}\nLive yfinance: {ok}/{len(all_stocks)}\n{'='*50}", flush=True)

if __name__ == "__main__":
    main()
