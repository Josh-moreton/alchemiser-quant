# The Alchemiser

Institutional-grade, event-driven portfolio automation that blends multiple quantitative strategies into a single, resilient execution engine. Designed for clients who value disciplined processes, transparent risk, and operational reliability.

## What You Get

- Consistent process, not guesswork: rules-based, multi-strategy portfolio management.
- Event-driven resilience: idempotent, traceable workflows built for real markets.
- Account-safe by design: paper/live separation and strict risk controls.
- Full transparency: structured logs, notifications, and clear status reporting.

## Key Capabilities

- Multi-strategy allocation: Nuclear, TECL momentum, and KLM ensemble.
- Automated rebalancing and execution with slippage controls.
- Live account monitoring: balances, positions, exposure, and risk flags.
- Cloud-native operation (AWS) with secure secrets management.
- Paper trading support for evaluation and sign-off.

## How It Works

1) Strategies generate signals based on market data.
2) Portfolio planning converts signals into a risk-aware rebalance plan.
3) Execution places orders with safeguards (slippage, sizing, circuit breakers).
4) Event-driven orchestration ties the workflow together with end-to-end traceability.

## Safety & Governance

- Environment isolation: paper trading locally; live trading when deployed to AWS.
- Idempotent processing: safe under retries and message reordering.
- Auditability: correlation IDs on every workflow; concise, structured logs.
- No secrets in code: credentials managed via AWS Secrets Manager or local .env for paper.

## Deployment Options

- Managed cloud (AWS Lambda): reliable, cost-efficient, and monitored.
- Local paper-trading: evaluate behavior, outputs, and notifications without risk.

## Typical Outcomes

- Clear, rules-based trade logs and status updates.
- Timely rebalances and disciplined exposure management.
- Reduced manual overhead with consistent execution quality.

## Frequently Asked Questions

- What assets can it trade? Today: equities and ETFs via Alpaca. Extensible design.
- How do you control risk? Position sizing, allocation caps, and slippage limits.
- Can we review decisions? Yes—events, logs, and plans are traceable end-to-end.
- How do we trial it? Start in paper trading, then promote to live once approved.

## Next Steps

- Explore a paper-trading run-through and example outputs.
- Review allocation policy and custom constraints for your mandate.
- Schedule a technical enablement for your environment (AWS or preferred).

—

Version: 2.0.0 | License: MIT | Author: Josh Moreton
