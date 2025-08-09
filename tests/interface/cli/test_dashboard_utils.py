from the_alchemiser.interface.cli.dashboard_utils import extract_portfolio_metrics


def test_extract_portfolio_metrics_daily_pl():
    account_info = {
        "equity": 1000,
        "cash": 500,
        "portfolio_history": {"profit_loss": [1, 2, 3], "profit_loss_pct": [0.01, 0.02, 0.03]},
    }
    metrics = extract_portfolio_metrics(account_info)
    assert metrics["daily_pl"] == 3
    assert metrics["daily_pl_percent"] == 3.0
