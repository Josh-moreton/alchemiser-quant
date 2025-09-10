"""Business Unit: portfolio assessment & management; Status: current.

Pure calculation logic for portfolio rebalancing.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.math.trading_math import calculate_rebalance_amounts

from .rebalance_plan import RebalancePlan


class RebalanceCalculator:
    """Pure calculation logic for portfolio rebalancing.

    This class contains no side effects and only performs calculations.
    It delegates to the existing trading_math module but returns proper domain objects.
    """

    def __init__(self, min_trade_threshold: Decimal = Decimal("0.001")) -> None:
        """Initialize the calculator with a minimum trade threshold.

        Args:
            min_trade_threshold: Minimum weight difference to trigger a trade (default 0.1%)

        """
        self.min_trade_threshold = min_trade_threshold

    def calculate_rebalance_plan(
        self,
        target_weights: dict[str, Decimal],
        current_values: dict[str, Decimal],
        total_portfolio_value: Decimal,
    ) -> dict[str, RebalancePlan]:
        """Calculate comprehensive rebalancing plan using existing trading_math.

        Args:
            target_weights: Dictionary mapping symbols to target weights (0.0 to 1.0)
            current_values: Dictionary mapping symbols to current position values in dollars
            total_portfolio_value: Total portfolio value in dollars

        Returns:
            Dictionary mapping symbols to RebalancePlan domain objects

        """
        # === REBALANCE CALCULATOR DATA TRANSFER LOGGING ===
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info("=== REBALANCE CALCULATOR: CALCULATE_REBALANCE_PLAN ===")
        logger.info(f"CALCULATOR_TYPE: {type(self).__name__}")
        logger.info(f"MIN_TRADE_THRESHOLD: {self.min_trade_threshold}")
        
        # Log exactly what we received
        logger.info("=== RECEIVED BY CALCULATOR ===")
        logger.info(f"TARGET_WEIGHTS_TYPE: {type(target_weights)}")
        logger.info(f"TARGET_WEIGHTS_COUNT: {len(target_weights) if target_weights else 0}")
        logger.info(f"CURRENT_VALUES_TYPE: {type(current_values)}")
        logger.info(f"CURRENT_VALUES_COUNT: {len(current_values) if current_values else 0}")
        logger.info(f"TOTAL_PORTFOLIO_VALUE: {total_portfolio_value} (type: {type(total_portfolio_value)})")
        
        # Detailed data logging
        if target_weights:
            logger.info("=== TARGET WEIGHTS RECEIVED BY CALCULATOR ===")
            target_total = sum(target_weights.values())
            logger.info(f"TARGET_WEIGHTS_TOTAL: {target_total}")
            for symbol, weight in target_weights.items():
                logger.info(f"CALC_TARGET: {symbol} = {weight} (type: {type(weight)})")
        
        if current_values:
            logger.info("=== CURRENT VALUES RECEIVED BY CALCULATOR ===")
            current_total = sum(current_values.values())
            logger.info(f"CURRENT_VALUES_TOTAL: ${current_total}")
            for symbol, value in current_values.items():
                logger.info(f"CALC_CURRENT: {symbol} = ${value} (type: {type(value)})")
        else:
            logger.info("CURRENT_VALUES: Empty")
        
        # === DATA CONVERSION FOR TRADING_MATH ===
        logger.info("=== CONVERTING DATA FOR TRADING_MATH ===")
        
        # Convert to float for trading_math compatibility
        target_weights_float = {k: float(v) for k, v in target_weights.items()}
        current_values_float = {k: float(v) for k, v in current_values.items()}
        portfolio_value_float = float(total_portfolio_value)
        threshold_float = float(self.min_trade_threshold)
        
        # Log converted data
        logger.info("=== CONVERTED DATA FOR TRADING_MATH ===")
        logger.info(f"CONVERTED_TARGET_WEIGHTS: {target_weights_float}")
        logger.info(f"CONVERTED_CURRENT_VALUES: {current_values_float}")
        logger.info(f"CONVERTED_PORTFOLIO_VALUE: {portfolio_value_float}")
        logger.info(f"CONVERTED_THRESHOLD: {threshold_float}")
        
        # === CALL TO TRADING_MATH ===
        logger.info("=== CALLING TRADING_MATH.CALCULATE_REBALANCE_AMOUNTS ===")
        
        # Delegate to existing calculate_rebalance_amounts but return proper domain objects
        raw_plan = calculate_rebalance_amounts(
            target_weights_float,
            current_values_float,
            portfolio_value_float,
            threshold_float,
        )
        
        # === TRADING_MATH RESULTS ANALYSIS ===
        logger.info("=== TRADING_MATH RESULTS ===")
        logger.info(f"RAW_PLAN_TYPE: {type(raw_plan)}")
        logger.info(f"RAW_PLAN_COUNT: {len(raw_plan) if raw_plan else 0}")
        
        if raw_plan:
            logger.info("=== RAW PLAN DETAILS FROM TRADING_MATH ===")
            for symbol, data in raw_plan.items():
                logger.info(f"RAW_RESULT: {symbol}")
                for key, value in data.items():
                    logger.info(f"  {key}: {value} (type: {type(value)})")
        else:
            logger.error("❌ TRADING_MATH_RETURNED_EMPTY")
        
        # === DOMAIN OBJECT CONVERSION ===
        logger.info("=== CONVERTING TO DOMAIN OBJECTS ===")
        
        domain_plans = {}
        symbols_needing_rebalance = 0
        
        for symbol, data in raw_plan.items():
            try:
                domain_plan = RebalancePlan(
                    symbol=symbol,
                    current_weight=Decimal(str(data["current_weight"])),
                    target_weight=Decimal(str(data["target_weight"])),
                    weight_diff=Decimal(str(data["weight_diff"])),
                    target_value=Decimal(str(data["target_value"])),
                    current_value=Decimal(str(data["current_value"])),
                    trade_amount=Decimal(str(data["trade_amount"])),
                    # Use the needs_rebalance calculation from trading_math.py - do not recalculate
                    needs_rebalance=data["needs_rebalance"],
                )
                
                domain_plans[symbol] = domain_plan
                
                if domain_plan.needs_rebalance:
                    symbols_needing_rebalance += 1
                    logger.info(f"✅ DOMAIN_PLAN_NEEDS_REBALANCE: {symbol}")
                else:
                    logger.info(f"❌ DOMAIN_PLAN_NO_REBALANCE: {symbol}")
                    
            except Exception as e:
                logger.error(f"❌ FAILED_TO_CONVERT_DOMAIN_PLAN: {symbol} - {e}")
        
        # === FINAL RESULTS SUMMARY ===
        logger.info("=== CALCULATOR RESULTS SUMMARY ===")
        logger.info(f"DOMAIN_PLANS_COUNT: {len(domain_plans)}")
        logger.info(f"SYMBOLS_NEEDING_REBALANCE: {symbols_needing_rebalance}")
        logger.info(f"SYMBOLS_NOT_NEEDING_REBALANCE: {len(domain_plans) - symbols_needing_rebalance}")
        
        symbols_to_rebalance = [symbol for symbol, plan in domain_plans.items() if plan.needs_rebalance]
        if symbols_to_rebalance:
            logger.info(f"SYMBOLS_TO_REBALANCE: {symbols_to_rebalance}")
        else:
            logger.warning("❌ NO_SYMBOLS_TO_REBALANCE - All below threshold or calculation error")
        
        logger.info("=== REBALANCE CALCULATOR COMPLETE ===")
        return domain_plans

    def get_symbols_needing_rebalance(
        self, rebalance_plan: dict[str, RebalancePlan]
    ) -> dict[str, RebalancePlan]:
        """Filter rebalance plan to only symbols that need rebalancing."""
        return {symbol: plan for symbol, plan in rebalance_plan.items() if plan.needs_rebalance}

    def get_sell_plans(self, rebalance_plan: dict[str, RebalancePlan]) -> dict[str, RebalancePlan]:
        """Get rebalance plans that require selling (negative trade amounts)."""
        return {
            symbol: plan
            for symbol, plan in rebalance_plan.items()
            if plan.needs_rebalance and plan.trade_amount < 0
        }

    def get_buy_plans(self, rebalance_plan: dict[str, RebalancePlan]) -> dict[str, RebalancePlan]:
        """Get rebalance plans that require buying (positive trade amounts)."""
        return {
            symbol: plan
            for symbol, plan in rebalance_plan.items()
            if plan.needs_rebalance and plan.trade_amount > 0
        }

    def calculate_total_trade_value(self, rebalance_plan: dict[str, RebalancePlan]) -> Decimal:
        """Calculate the total dollar value of trades needed."""
        return sum(
            (plan.trade_amount_abs for plan in rebalance_plan.values() if plan.needs_rebalance),
            Decimal("0"),
        )
