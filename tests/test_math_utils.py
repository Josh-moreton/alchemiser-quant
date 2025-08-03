import numpy as np
import pandas as pd
import pytest

from the_alchemiser.utils import math_utils, trading_math


def test_calculate_stdev_returns_basic():
    prices = pd.Series([100, 102, 101, 103, 105, 106])
    result = math_utils.calculate_stdev_returns(prices, window=3)
    expected = prices.pct_change().dropna().rolling(window=3).std().iloc[-1]
    assert result == pytest.approx(expected)


def test_calculate_stdev_returns_insufficient_data():
    prices = pd.Series([100, 101])
    assert math_utils.calculate_stdev_returns(prices, window=5) == pytest.approx(0.1)


def test_calculate_moving_average_and_return():
    prices = pd.Series([100, 102, 104, 106])
    ma = math_utils.calculate_moving_average(prices, window=2)
    assert ma == pytest.approx(105)

    ma_return = math_utils.calculate_moving_average_return(prices, window=2)
    # moving average series: [NaN, 101, 103, 105]; last two: 103 -> 105 => (105-103)/103*100
    assert ma_return == pytest.approx((105 - 103) / 103 * 100)


def test_calculate_percentage_change_and_safe_division():
    assert math_utils.calculate_percentage_change(110, 100) == pytest.approx(10)
    assert math_utils.calculate_percentage_change(100, 0) == pytest.approx(0)
    assert math_utils.safe_division(10, 2) == pytest.approx(5)
    assert math_utils.safe_division(10, 0, fallback=-1) == -1


def test_calculate_rolling_metric_variants():
    data = pd.Series([1, 2, 3, 4, 5])
    assert math_utils.calculate_rolling_metric(data, window=3, metric='mean') == pytest.approx(4)
    assert math_utils.calculate_rolling_metric(data, window=3, metric='std') == pytest.approx(data.rolling(3).std().iloc[-1])


@pytest.mark.parametrize(
    "value,min_val,max_val,target_min,target_max,expected",
    [
        (5, 0, 10, 0, 1, 0.5),
        (10, 0, 10, -1, 1, 1),
        (0, 0, 10, -1, 1, -1),
    ],
)
def test_normalize_to_range(value, min_val, max_val, target_min, target_max, expected):
    assert math_utils.normalize_to_range(value, min_val, max_val, target_min, target_max) == pytest.approx(expected)


def test_calculate_ensemble_score_with_weights():
    metrics = [1, 2, 3]
    weights = [3, 2, 1]
    # weighted average = (1*3 + 2*2 + 3*1) / 6 = (3+4+3)/6 = 10/6
    expected = 10 / 6
    assert math_utils.calculate_ensemble_score(metrics, weights) == pytest.approx(expected)
    # Without weights defaults to average
    assert math_utils.calculate_ensemble_score(metrics) == pytest.approx(sum(metrics)/len(metrics))


# Tests for trading_math utilities

def test_calculate_position_size_and_slippage():
    shares = trading_math.calculate_position_size(100, 0.25, 10000)
    assert shares == pytest.approx(25.0)
    assert trading_math.calculate_position_size(0, 0.5, 10000) == pytest.approx(0)

    buffer = trading_math.calculate_slippage_buffer(100.0, 50)  # 50 bps = 0.5%
    assert buffer == pytest.approx(0.5)


def test_calculate_dynamic_limit_price():
    # For a buy order step 0 midpoint 100.05
    price = trading_math.calculate_dynamic_limit_price(True, 100.0, 100.10, step=0)
    assert price == pytest.approx(100.05)
    # After many retries should use ask for buy
    price = trading_math.calculate_dynamic_limit_price(True, 100.0, 100.10, step=10, max_steps=5)
    assert price == pytest.approx(100.10)
    # For sell order, ensure moves toward bid
    price = trading_math.calculate_dynamic_limit_price(False, 100.0, 100.10, step=2)
    assert price < 100.05
