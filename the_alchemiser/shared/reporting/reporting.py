"""Business Unit: shared | Status: current..keys())

    for symbol in all_symbols:
        target_weight = target_portfolio.get(symbol, 0.0)
        target_value = target_values.get(symbol, 0.0)
        current_value = current_values.get(symbol, 0.0)

        current_weight, _ = calculate_allocation_discrepancy(
            target_weight, current_value, portfolio_value
        )

        allocations[symbol] = {
            "target_percent": target_weight * 100,
            "current_percent": current_weight * 100,
            "target_value": target_value,
            "current_value": current_value,
        }

    return {"allocations": allocations}
