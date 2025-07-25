“TECL for the Long Term” Strategy Definition (JSON vs Clojure)

Summary: The TECL for the Long Term strategy appears in two significantly different forms. While both JSON and Clojure versions share a high-level concept (using market regime to toggle between bull and bear strategies), the specific logic, thresholds, and asset allocations diverge substantially beyond the initial check. The Clojure version includes many additional conditions and different asset choices not present in the JSON. Below is a detailed comparison highlighting where the two definitions match and where they differ:

Strategy Metadata and High-Level Structure
 • Name & Basics: The JSON strategy is named “TECL for the Long Term | BT 2022-07-05” ￼, whereas the Clojure version’s name string (from the defsymphony call) includes additional notes (“(v7) | Less VIX | KMLM signal boost”) but clearly refers to a TECL for the Long Term strategy (likely a later iteration) ￼. Both target Equities and use daily rebalancing ￼ ￼. This suggests they intend to represent the same strategy concept, but possibly different versions.
 • Overall Structure: Both versions start with a top-level weight_equal container and immediately use an if to branch logic based on a 200-day moving average trend of SPY ￼ ￼. This is a common regime filter:
 • Regime Check: If SPY’s current price is greater than its 200-day moving average, the strategy enters the “bull” regime branch; else it enters the “bear” regime branch. This condition is identically defined in both JSON and Clojure (same indicator types and window) ￼ ￼. Thus, the first decision point (market regime determination) is the same in both versions.
 • After this point, however, the Bull and Bear branches differ notably between JSON and Clojure, as detailed below.

Bull Regime Branch (SPY above 200-day MA)

Once in the bull regime, both strategies aim to be net long equities but use different indicators to adjust exposure.

1. Overbought Tech Check – RSI(TQQQ):
 • JSON: The JSON strategy immediately checks if the 10-day RSI of TQQQ (3x Nasdaq 100 ETF) is above 80 ￼. This serves as a signal that the tech sector may be overheated.
 • Clojure: The Clojure strategy also checks RSI of TQQQ but uses a threshold of 79 (one point lower) ￼. It’s a minor difference: RSI > 79 in clj versus > 80 in JSON. This is a small discrepancy in threshold value right at the start of the bull logic.
 • If TQQQ RSI is above the threshold (overbought tech market): The two versions take entirely different actions:
 • JSON True Branch: If RSI_TQQQ > 80, the JSON does not directly allocate to any asset. Instead, it enters a nested set of conditions focusing on market breadth and volatility to decide how to reposition:
 • It checks RSI(SPY, 10) > 80 (is the broad market also overbought?) ￼. If yes, it then examines a volatility indicator:
 • UVXY trend: Specifically, it checks if UVXY’s current price is above its 20-day moving average (i.e., if volatility is starting to uptick) ￼.
 • If UVXY is trending up (sign of potential trouble ahead), the JSON strategy allocates to KMLM ￼ ￼. (KMLM is a managed futures strategy fund, used here presumably as a diversifier/hedge in overheated equity conditions.)
 • If UVXY is not above its MA (no volatility spike), it allocates to SPXS ￼, which is a 3x inverse S&P 500 ETF (a bearish position). This implies taking a short bias when equities are extremely overbought and volatility is still low.
 • If RSI(SPY) was not > 80 (meaning tech is overheated but the broad market isn’t as extreme), the JSON logic would fall through (by structure) to an allocation of SPXS as well – essentially, any time TQQQ RSI > 80 triggers a move to defensive assets (KMLM or SPXS) in the JSON version.
 • Outcome in JSON: Under TQQQ RSI > 80, the JSON strategy completely exits TECL and moves into either KMLM or SPXS based on the UVXY condition. No direct cash or volatility ETF (UVXY) allocation is made – rather, it uses KMLM (managed futures) as a proxy defensive asset when volatility rises, and SPXS (short equities) when volatility does not yet rise.
 • Clojure True Branch: If RSI_TQQQ > 79 in the Clojure version, the reaction is very different:
 • The strategy immediately allocates to a group “UVXY+75%BIL”, which is a fixed 25% UVXY and 75% BIL allocation ￼. (BIL is an ETF for 1-3 month U.S. T-bills, essentially cash-like exposure.) This means the Clojure strategy, upon detecting an overbought tech market, shifts 75% of the portfolio to cash (T-Bills) and 25% to a volatility spike play (UVXY). There are no further nested checks in this branch in Clojure – it directly takes this defensive stance.
 • It’s important to note that the JSON strategy never explicitly allocates to UVXY or BIL in its bull regime logic, whereas the Clojure strategy does exactly that. JSON used KMLM as a “signal boost” and SPXS as a hedge, whereas Clojure uses UVXY (volatility) and BIL (cash) as the response to an overheated tech market.
 • Discrepancy: This is a major difference. For an extreme overbought condition in equities:
 • JSON version hedges via alternative funds (KMLM) or outright short equity (SPXS),
 • Clojure version hedges via volatility and cash (UVXY + BIL).
The logic and assets chosen are completely different, indicating the strategies would behave differently in such scenarios. Additionally, the threshold is slightly different (80 vs 79) but the qualitative response differs more significantly than that numeric tweak.
 • If TQQQ RSI is not above the threshold (i.e., RSI_TQQQ <= 80/79): The strategies move to the next set of conditions, which involve the S&P 500’s momentum and other indicators. Here we see further differences:
 • Both versions next consider RSI(SPY, 10) > 80 as a check for broad-market overbought conditions, but they handle it differently:
 • JSON (RSI SPY > 80): If the S&P 500’s RSI > 80 (and we already know TQQQ’s RSI was not > 80 in this branch):
 • The JSON then evaluates the UVXY 20-day trend again in this context ￼. If UVXY is above its 20MA, it allocates to KMLM; if not, it allocates to SPXS ￼. This is exactly analogous to the earlier logic, just gated under SPY’s RSI condition now. Essentially, JSON says: if broad market is overheated (RSI>80), use rising volatility as a cue to go into KMLM, otherwise short the market (SPXS).
 • Notably, if SPY RSI > 80 in JSON’s bull branch, the outcome again does not include TECL at all – it’s either KMLM or SPXS allocation.
 • If RSI(SPY) > 80 is false (meaning neither tech nor the broad market are extremely overbought), the JSON falls through to its default bull allocation, which is simply to hold TECL (the 3x tech bull fund) ￼. In the JSON file, this appears as the false branch of the entire chain: "false_branch": { "type": "asset", "symbol": "TECL", ... } once all the conditions above are bypassed ￼. So, in normal conditions (no extreme RSI signals), JSON stays 100% in TECL.
 • Clojure (RSI SPY > 80): In the Clojure version, if SPY’s RSI > 80 (with TQQQ RSI <= 79):
 • The strategy again allocates immediately to the UVXY+75%BIL (25/75) defensive mix ￼, exactly as it did when TQQQ’s RSI was high. In other words, either TQQQ RSI > 79 or SPY RSI > 80 will trigger the Clojure strategy to park 75% in cash and 25% in volatility. There is no secondary nuance like checking UVXY’s trend; it simply assumes an overbought market calls for the same UVXY/BIL allocation.
 • If RSI(SPY) > 80 is false (meaning neither TQQQ nor SPY hit those extreme overbought thresholds), the Clojure logic does not simply hold TECL. Instead, it enters a more complex decision structure encapsulated in a group named "KMLM Switcher | SimplyGreen | No short" ￼. This group’s logic has no direct counterpart in the JSON:
 • Inside this group, the Clojure strategy compares the RSI of XLK vs the RSI of KMLM:
 • XLK vs KMLM RSI: It checks if RSI(XLK, 10) > RSI(KMLM, 10) ￼. (XLK is the Technology Select Sector SPDR, essentially a non-leveraged tech sector ETF; KMLM is the managed futures ETF.) This serves as a relative strength test between the tech sector and a trend-following strategy.
 • If RSI(XLK) > RSI(KMLM) (tech momentum is stronger than managed futures):
 • Then it further checks if RSI(XLK) > 81 (tech extremely strong, even if not overbought enough to trigger earlier) ￼. If yes, it allocates to BIL (cash) instead of equities, assuming an intermediate level of overheating (tech stronger than KMLM and RSI above 81) – essentially a safety move to cash in this scenario ￼.
 • If RSI(XLK) ≤ 81, it allocates to TECL (staying in the leveraged tech position) ￼. So when tech is leading and not too overbought, Clojure stays long TECL.
 • If RSI(XLK) ≤ RSI(KMLM) (tech sector is not stronger than the managed futures trend, i.e., KMLM is doing as well or better):
 • It then checks if RSI(XLK) < 29 (tech extremely oversold relative to its norm) ￼. If yes, it allocates to TECL (a contrarian buy-the-dip in tech) ￼.
 • If RSI(XLK) is ≥ 29 (tech is not severely oversold and is in fact underperforming KMLM’s trend), it allocates to BIL (cash) ￼, effectively stepping aside from equities.
 • Outcome in Clojure normal bull conditions: The strategy dynamically toggles between full TECL and full cash (BIL) depending on a relative strength comparison and additional RSI thresholds (81 and 29 for XLK’s RSI). In essence:
 • When tech is leading and reasonably strong (but not extreme): stay in TECL.
 • When tech is lagging or the signal is weak: move to cash (unless tech is extremely oversold, in which case buy TECL for a rebound).
 • These nuances (using XLK vs KMLM, RSI 81/29 triggers) are absent in the JSON strategy.
 • Contrast: The JSON strategy has no comparable mechanism; it simply remains in TECL unless broad RSI > 80 triggers a move to KMLM/SPXS. The Clojure introduces KMLM only as a signal (comparing RSIs) but notably does not directly allocate to KMLM in bull mode, whereas the JSON actually allocates to KMLM under certain conditions. Conversely, the Clojure allocates to BIL (cash) in many cases, which the JSON never does in bull mode.
 • Summary of Bull Branch Differences:
 • The initial RSI thresholds differ slightly (79 vs 80 for TQQQ), but more importantly the responses to overbought conditions differ greatly:
 • JSON responds to overbought conditions by reallocating to managed futures (KMLM) or short equity (SPXS) depending on volatility, whereas Clojure reallocates to volatility (UVXY) and cash (BIL) directly.
 • The subsequent moderate condition logic is much simpler in JSON (basically, “if no extremes, just hold TECL”). In Clojure, moderate conditions trigger a sophisticated toggle between TECL and cash based on relative RSI signals (XLK vs KMLM) and additional thresholds (81, 29) on XLK’s RSI.
 • Asset Differences: JSON’s bull branch can hold TECL, KMLM, or SPXS. Clojure’s bull branch can hold TECL, BIL, or UVXY (in a mix). Notably, JSON never uses BIL or UVXY as assets in bull regime, and Clojure never uses KMLM or SPXS as direct allocations (KMLM appears only as a comparison signal, and SPXS is not used at all in clj’s bull logic). This is a clear divergence in strategy design.
 • Therefore, beyond the very first regime check, the bull portions are not the same strategy: numerous conditionals and threshold values are unique to each version. The JSON is following a more straightforward momentum/volatility toggle approach, whereas the Clojure implements a more complex RSI-based rotation including cash and sector signals.

Bear Regime Branch (SPY below 200-day MA)

When the market regime is bearish (SPY under its 200-day MA), the two versions again take notably different approaches to risk management:
 • Overall Intent: Both aim to avoid or hedge equities in a downtrend, but the JSON does so by rotating between treasury bond ETFs, whereas the Clojure uses a variety of conditions to sometimes stay in cash, sometimes take contrarian long positions, or short the market. The contrast is stark:

2. Safe Asset Allocation vs Complex Conditions:
 • JSON Bear Strategy: The JSON file defines the bear regime extremely succinctly as a filter selecting one asset out of two ￼ ￼:
 • It uses a 60-day momentum (labeled “momentum” filter with window 60) to compare TLT vs SHY ￼ ￼:
 • TLT = iShares 20+ Year Treasury Bond ETF (long-duration bonds),
 • SHY = iShares 1-3 Year Treasury Bond ETF (short-duration bonds).
 • It then selects the top 1 performer among these two based on the 60-day metric ￼ and allocates the entire bear portfolio to that asset ￼ ￼. Essentially, in a bear market, the JSON strategy moves entirely into either long-term Treasuries or short-term Treasuries, whichever has higher recent momentum (relative strength). This is a simple bond rotation aiming to capitalize on the flight-to-quality trends (if long bonds are rallying, hold TLT; if not, prefer the safety of SHY).
 • There are no other conditions or asset types in JSON’s bear branch: it will never hold equities, cash, or shorts in this mode – only one of those two bond funds. The logic is straightforward and contains no RSI checks or volatility measures in the bear portion, just the 60-day return comparison.
 • Clojure Bear Strategy: The Clojure version’s bear logic is much more elaborate, consisting of multiple if layers that allow for dynamic responses. Key checks and moves in the Clojure bear branch (none of which exist in JSON) include:
 1. RSI(TQQQ, 10) < 31: The first thing Clojure checks in a bear regime is if the 3x Nasdaq bull ETF is extremely oversold (RSI below 31) ￼.
 • If true, it does something very unconventional for a bear market: it allocates fully to TECL (Direxion Daily Technology Bull 3x) ￼ despite the bearish regime. This is a contrarian play, betting on a sharp rebound if tech is deeply oversold. (JSON absolutely never does this; in bear mode JSON would be in bonds, not triple-leveraged long equity).
 • If false (TQQQ RSI not that low), move to next condition.
 2. RSI(SPXL, 10) < 29: Next, Clojure checks if the 3x S&P 500 bull fund (SPXL) is extremely oversold ￼.
 • If true, allocate SPXL (3x long S&P) as a contrarian play ￼. (Again, going long equities in a downtrend if they’re very oversold – JSON never does this).
 • If false, continue.
 3. RSI(UVXY, 10) > 74: Next, it looks at volatility conditions by checking if UVXY’s RSI is above 74 (very high) ￼.
 • If UVXY RSI > 84 (extremely high, indicating potentially climaxing fear) ￼:
 • Allocate to “UVXY+85%BIL” group ￼, which is 15% UVXY and 85% BIL. This is a partial volatility play with majority cash, used when volatility is at extreme highs (the strategy anticipates a volatility spike may mean a market bottom is near, but still keeps most funds in cash).
 • Else if UVXY RSI is between 75 and 84 (elevated but not max):
 • Allocate 100% to BIL (all cash) ￼, essentially stepping aside from the market until volatility subsides. (JSON’s bear logic did not consider UVXY at all, and did not explicitly allocate to cash except insofar as SHY is a cash-like short-term bond; here BIL is true cash equivalent.)
 • If UVXY RSI ≤ 74 (volatility not extreme), proceed to next condition block.
 4. RSI(XLK) vs RSI(KMLM): If we reach here, it means no extreme oversold bounce was taken and volatility isn’t peaking. The Clojure strategy now uses a relative strength approach even in bear regime, comparing tech vs managed futures:
 • Check if RSI(XLK,10) > RSI(KMLM,10) ￼ (tech sector vs KMLM, similar to what it did in bull mode, but now interpreted in a bear context):
 • If true (tech showing more strength than the trend-following fund):
 • If RSI(XLK) > 81 (even in a bear market, if tech sector RSI is very high) ￼, allocate BIL (cash) – implying the rally is too strong/suspect, so go safe ￼.
 • Else (XLK RSI ≤ 81), allocate TECL – meaning despite the overall SPY downtrend, tech is leading and not extremely overbought, so the strategy takes a bullish position on tech ￼. (This is a momentum play within a bear regime: if tech is outperforming and momentum is decent, bet on a tech rally even though the broad market is below 200MA).
 • If false (tech sector is not stronger than KMLM, i.e., managed futures trend is equal/stronger):
 • If RSI(XLK) < 29 (tech sector extremely oversold) ￼, allocate TECL (again a contrarian buy on tech at a potential bottom) ￼.
 • Else (tech not oversold and is lagging KMLM), then the strategy uses a short-term momentum filter:
 • It applies a filter on 9-day RSI (as an indicator of very recent momentum) to select the top 1 between SQQQ (3x short Nasdaq) and BSV (Vanguard Short-Term Bond ETF) ￼.
 • In effect:
 • If SQQQ’s 9-day RSI is higher than BSV’s, it indicates strong downward momentum in equities (since SQQQ is performing well), so the strategy allocates to SQQQ (leveraged short position) ￼.
 • If BSV’s 9-day RSI is higher, it indicates bond outperformance (equities not crashing at the moment), so it allocates to BSV (a short-term bond, a safe haven) ￼.
 • This final step ensures the strategy can choose between being short or in bonds based on very near-term trends.
 • Bear Branch Assets & Threshold Differences: It’s clear that the Clojure bear branch employs many specific RSI thresholds (31, 29, 74, 84, 81, 29 again) and comparisons that simply do not exist in the JSON:
 • JSON’s only threshold-like parameter in bear mode is the -10% cumulative return for QQQ in Bear1 (which is encapsulated in Bear sub-strategies, not a top-level bear branch decision) and the 60-day momentum ranking for TLT vs SHY. It never uses RSI values or volatility indicators (UVXY) in its bear allocation decision – it always results in either TLT or SHY holding.
 • Clojure’s bear can allocate to TECL or SPXL (leveraged long positions) on oversold signals – JSON’s bear would never allocate to a long equity in a downtrend regime.
 • Clojure can allocate to UVXY (volatility) and BIL (cash) in certain proportions – JSON’s bear never holds UVXY, and while SHY is akin to cash, it doesn’t explicitly allocate pure cash or any volatility product.
 • Clojure can allocate to SQQQ (3x short) or BSV (short-term bonds) based on a short-term RSI filter – JSON’s bear could allocate at most a 1x short via PSQ within Bear1 logic, but not to SQQQ (except within Bear1 internal logic if conditions hit, but not as a broad bear regime allocation) and BSV is not considered at all in JSON.
 • Managed Futures (KMLM): Interestingly, JSON uses KMLM as an actual allocation in bull conditions (when volatility rises), but in bear mode JSON does not use KMLM at all – it sticks to bonds. Clojure, on the other hand, uses KMLM as a comparative signal in both bull and bear logic, but never allocates to KMLM directly. So, the role of KMLM is completely different between the two: JSON treats it as an asset to hold in bull markets occasionally, Clojure treats it as an indicator to gauge relative strength but allocates elsewhere.
 • Treasury Bonds: JSON’s primary bear assets are TLT and SHY (long vs short Treasuries). The Clojure bear strategy does not mention TLT or SHY at all – instead it uses BSV (a short-term bond ETF) as one option, and no long-term bond fund explicitly. This is a fundamental difference in approach (JSON leans on treasury duration rotation, Clojure does not).
 • All these points illustrate that the logic in the bear regime is fundamentally different.
 • Summary of Bear Branch Differences:
 • Strategy Approach: JSON is simplistic and defensive: it always moves to bonds (long or short duration) based on momentum. Clojure is dynamic and even opportunistic: it may move to cash, short, or even back into long equities depending on RSI signals.
 • Conditions: JSON has essentially one primary condition (the momentum comparison) in bear mode. Clojure has layered conditions (RSI oversold triggers, volatility triggers, relative strength, etc.) – a much more complex decision tree.
 • Thresholds: Many numeric thresholds in clj (31, 29, 74, 84, 81…) that don’t exist in JSON. The only common threshold is the general concept of RSI oversold/overbought, but JSON doesn’t use RSI in bear mode explicitly.
 • Assets: Zero overlap in final bear holdings – JSON selects between TLT/SHY only; Clojure can end up in TECL, SPXL, UVXY, BIL, SQQQ, or BSV (vastly different set). The JSON never touches these in bear regime (and the clj never touches TLT/SHY).
 • These differences mean the two versions would behave very differently in a bear market scenario.

Conclusion – TECL Strategy:

The JSON and Clojure definitions of “TECL for the Long Term” are not 100% identical – in fact, they differ on multiple levels. While they share a common entry point (using SPY’s 200-day MA to split bull vs bear logic), every subsequent branch shows discrepancies:
 • In the bull regime, the Clojure version uses different RSI thresholds (e.g. 79 vs 80) and adds extra layers of logic (comparing XLK vs KMLM, using UVXY+cash allocations) that are absent in JSON. The JSON strategy’s use of KMLM and SPXS differs from Clojure’s use of BIL and UVXY.
 • In the bear regime, the JSON’s simple bond-selection approach is entirely unlike the Clojure’s multi-faceted strategy that can even go long or short equities. The Clojure introduces numerous conditions (RSI oversold bounce trades, volatility-based hedging, etc.) not found in JSON. Conversely, JSON’s reliance on TLT/SHY is not mirrored in Clojure.
 • Every major decision branch has at least some inconsistency: from the initial overbought-tech response through to the final bear allocation, there are mismatched thresholds or entirely different indicators. For example, one small numeric example: JSON uses RSI > 80 for TQQQ while clj uses > 79 ￼ ￼ – and larger logical differences, such as JSON allocating KMLM vs clj allocating UVXY/BIL under similar conditions. Even the presence/absence of certain checks (like cumulative return or IEF’s RSI in Nuclear vs absence in TECL’s clj) highlight they are different versions.

Therefore, the TECL JSON and Clojure files do not encode the same strategy. There are substantial discrepancies in logic, thresholds, and asset usage, meaning they are not semantically identical. The Clojure appears to be a revised or more complex strategy compared to the simpler JSON version. Each pair of branches yields different outcomes, so the two should not be considered the same in a line-by-line sense.
