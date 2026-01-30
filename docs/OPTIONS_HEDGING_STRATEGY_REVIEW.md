	1.	Lock the objective and constraints (so the maths can’t wriggle)

	•	Write a single sentence objective in the README: “Reduce equity drawdowns of a 2.0x–2.5x book by X under Y scenarios, with ≤Z annual drag.”
	•	Pick two hard constraints and make them parameters, not vibes:
	•	Max premium spend per year (e.g., 4% NAV/year) and max per month (e.g., 0.35% NAV/month).
	•	Minimum required protection at –20% (e.g., ≥6% NAV) and what you’ll do if you can’t afford it (clip + report; or switch template; or do nothing).
	•	Add a “what this is NOT” line: e.g., “This will not fully hedge a –20% index move on a 2.5x book.”

	2.	Replace the VIX proxy with an instrument-specific vol signal

	•	Stop using “VIXY × 10 ≈ VIX” as the primary driver (keep it only as a secondary sanity check if you want).
	•	Implement an IV data source for the actual hedge underlying:
	•	At minimum: ATM IV for the chosen tenor (e.g., 60–90 DTE) + a skew metric (e.g., 25-delta put IV – ATM IV).
	•	Track IV percentile/rank over a rolling window (252 trading days).
	•	Rebuild the “regime” decision off IV percentile + skew richness + term structure (if available).
	•	Add alarms for “signal unavailable” → system fails closed (no trades) rather than defaulting.

	3.	Make sizing payoff-anchored, then budget-constrained (not the other way round)

	•	Implement scenario-based sizing for tail puts and put spreads:
	•	Inputs: scenario moves (–10, –20, –30), target payoff bands (e.g., 3–5% at –10, 6–10% at –20), leverage factor, days to expiry, vol assumptions.
	•	Outputs: contracts required to hit payoff targets.
	•	Add a premium cap step that clips the contract count, then emits an explicit report:
	•	“Target: 8% NAV at –20%. Affordable: 3.8% NAV at –20% (clipped by premium cap).”
	•	Add a rolling 12-month premium spend tracker and refuse new hedges if cap exceeded (fail closed).

	4.	Fix the economics (stop accidental 14%/year bleed)

	•	Recalculate your proposed monthly budgets into annual drag at 1.0x, 2.0x, 2.5x leverage and bake those numbers into docs and dashboard.
	•	Decide (and encode) an annual premium spend target band (e.g., 2–5% NAV/year) with hard caps.
	•	Add logic to reduce hedge intensity when IV/skew is rich:
	•	Either reduce target payoff, widen tenor, or favour spreads/ratio structures where appropriate.
	•	Add a “carry expectation” section: expected theta bleed in normal regimes, and the trade-off you’re accepting.

	5.	Contract selection: stop “fixed 15-delta at 90 DTE” being a religion

	•	Implement dynamic selection rules:
	•	Tenor ladder option (e.g., split between 60–90 and 120–180 DTE) OR choose tenor based on term structure/IV percentile.
	•	Delta/strike selection based on effective convexity per premium (not just delta).
	•	Tighten the strike filter so it doesn’t pick nonsense:
	•	Replace 75%–95% spot band with something anchored to delta and/or scenario move (e.g., strikes that contribute meaningfully by –20%).
	•	Add liquidity gates that actually work:
	•	Minimum OI and/or volume.
	•	Use absolute spread thresholds (e.g., ≤$0.05 or ≤$0.10 depending on premium), not only % spread.
	•	Minimum option mid price (avoid “2¢ options” where % spread is meaningless).

	6.	Execution: make fills real, not aspirational

	•	Replace “limit at mid × 0.98” with a marketability algorithm:
	•	Start at mid, then step toward ask in controlled increments until filled or max slippage reached.
	•	Separate rules for open vs close; separate rules for calm vs high IV.
	•	Encode a “max slippage per trade” and “max total slippage per day”.
	•	Add a “no fill” outcome that is explicit:
	•	If not filled by X minutes or Y attempts → cancel and mark hedge as NOT placed.
	•	Write tests with recorded market snapshots (bid/ask) so you can reproduce fill logic failures.

	7.	Implement multi-leg execution for put spreads (or disable them entirely)

	•	If spread execution isn’t implemented, the system must refuse to trade the smoothing template.
	•	Implement proper spread trading:
	•	Native vertical spread order if your broker supports it; otherwise legging rules with worst-case guards.
	•	Ensure net debit/credit constraints and retry logic.
	•	Add controls for legging risk:
	•	If one leg fills and the other doesn’t within N seconds → hedge with a temporary stopgap or aggressively complete the second leg within slippage bounds.

	8.	Assignment and lifecycle runbooks (operational, not just “alerts”)

	•	Write an explicit assignment handling procedure:
	•	If short leg assigned → immediately close/exercise the paired leg to restore defined risk, and flatten any accidental underlying exposure.
	•	Add automated detection for assignment and forced actions (or at least forced “halt trading until resolved”).
	•	Define roll rules precisely:
	•	Tail: roll <45 DTE (already) but also include roll triggers based on delta, remaining extrinsic, and “skew regime”.
	•	Spreads: roll criteria based on remaining width value, delta, and time.

	9.	Regime/template chooser that is honest and testable

	•	Define when you use tail vs spread (or a blend):
	•	Example: low IV percentile + normal skew → cheap tails; high IV + rich skew → spreads or reduced size.
	•	Encode it as deterministic logic with a printed “why” each rebalance.
	•	Backtest the regime switch itself (it’s easy to overfit a chooser).

	10.	Reporting and dashboards (so you can see if it’s doing what you wrote)

	•	Create a daily/weekly hedge report:
	•	Premium spent MTD/YTD/rolling 12m vs caps.
	•	Current hedge inventory: tenor ladder, deltas, strikes, Greeks (delta/gamma/theta/vega).
	•	Scenario payoff table at –10/–20/–30 for both unlevered and levered book.
	•	“Affordable vs target” variance line.
	•	Add a “silent failure detector”:
	•	If hedge was supposed to be placed but not filled → alert + log + mark as out of compliance.
	•	Add a post-event report template:
	•	“During a –X% move, hedges returned Y% NAV; expected was Z%.”

	11.	Backtesting and reality checks (before you trust it with size)

	•	Backtest with transaction costs and realistic spreads (especially for OTM puts).
	•	Include at least two ugly periods (named, with dates):
	•	Feb–Mar 2020, and the 2022 drawdown (or another stress period relevant to QQQ).
	•	Validate three things:
	•	Realised annual drag vs cap.
	•	Achieved protection vs targets at the scenario moves.
	•	Fill rates and slippage in high vol.

	12.	“Fail closed” safety rails (non-negotiable for automation)

	•	If any of these are missing, do not trade:
	•	IV/skew data missing or stale.
	•	Scenario sizing fails.
	•	Premium cap would be breached.
	•	Liquidity filters fail for all candidates.
	•	Spread execution not available (for smoothing template).
	•	Add an emergency kill switch and a “do nothing” state that is treated as success (not error spam).

