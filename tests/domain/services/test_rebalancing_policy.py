from the_alchemiser.domain.services.rebalancing_policy import calculate_rebalance_orders


def test_calculate_rebalance_orders_returns_empty_list_when_no_positions() -> None:
    assert calculate_rebalance_orders({}, {}) == []
