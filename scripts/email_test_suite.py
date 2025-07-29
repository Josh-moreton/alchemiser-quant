#!/usr/bin/env python3
"""
Email Test Suite for The Alchemiser

Sends comprehensive test emails demonstrating all email templates
with realistic trading data and enhanced signal explanations.
"""

import sys
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_alchemiser.core.ui.email_utils import (
    send_email_notification, 
    build_multi_strategy_email_html,
    build_trading_report_html,
    build_error_email_html
)
from the_alchemiser.core.trading.strategy_manager import StrategyType


def create_enhanced_signal_data():
    """Create realistic strategy signals with detailed explanations"""
    return {
        StrategyType.NUCLEAR: {
            'symbol': 'NUCLEAR_PORTFOLIO',
            'action': 'BUY', 
            'reason': """Market Analysis: Bull Market (SPY $578.45 vs 200MA $552.30)
SPY RSI(10): 77.8 - Not overbought, checking secondary conditions

Bull Market Strategy: SPY above 200MA ($578.45 > $552.30)
Nuclear Energy Growth Strategy:
• Portfolio: SMR (22.1%), BWXT (18.5%), LEU (19.4%), EXC (20.0%), NLR (20.0%)
• Rationale: Bull market favors growth sectors
• Nuclear renaissance theme with clean energy transition
• Diversified across uranium miners, utilities, and tech""",
            'timestamp': datetime.now().isoformat(),
            'technical_indicators': {
                'SPY': {'rsi_10': 77.8, 'rsi_20': 65.2, 'ma_200': 552.30, 'current_price': 578.45},
                'IOO': {'rsi_10': 81.1, 'rsi_20': 72.4, 'ma_200': 89.50, 'current_price': 92.15},
                'TQQQ': {'rsi_10': 74.3, 'rsi_20': 68.1, 'ma_200': 48.20, 'current_price': 52.80},
                'VTV': {'rsi_10': 69.5, 'rsi_20': 61.2, 'ma_200': 158.70, 'current_price': 165.40},
                'XLF': {'rsi_10': 71.8, 'rsi_20': 64.9, 'ma_200': 42.80, 'current_price': 45.90},
                'SMR': {'rsi_10': 55.2, 'rsi_20': 58.7, 'ma_200': 12.40, 'current_price': 14.80},
                'BWXT': {'rsi_10': 62.1, 'rsi_20': 59.3, 'ma_200': 89.20, 'current_price': 95.75}
            }
        },
        StrategyType.TECL: {
            'symbol': 'TECL',
            'action': 'BUY',
            'reason': """Market Regime Analysis:
• SPY Price: $578.45 vs 200MA: $552.30
• SPY RSI(10): 77.8
• Regime: BULL MARKET (SPY above 200MA)

KMLM Switcher Technology Timing:
• XLK (Technology) RSI(10): 75.2 vs KMLM (Materials) RSI(10): 68.9
• Sector Comparison: Technology STRONGER than Materials
• XLK Status: Strong but sustainable (<81)
• Strategy: Technology momentum play
• Target: TECL (3x leveraged tech) for sector strength
• Rationale: Tech outperforming materials, trend continuation""",
            'timestamp': datetime.now().isoformat(),
            'technical_indicators': {
                'SPY': {'rsi_10': 77.8, 'rsi_20': 65.2, 'ma_200': 552.30, 'current_price': 578.45},
                'XLK': {'rsi_10': 75.2, 'rsi_20': 67.8, 'ma_200': 198.50, 'current_price': 215.30},
                'KMLM': {'rsi_10': 68.9, 'rsi_20': 62.4, 'ma_200': 42.15, 'current_price': 44.60},
                'TECL': {'rsi_10': 72.8, 'rsi_20': 69.1, 'ma_200': 38.40, 'current_price': 42.95}
            }
        }
    }


def create_realistic_execution_result():
    """Create a realistic multi-strategy execution result"""
    class MockResult:
        def __init__(self):
            self.success = True
            self.strategy_signals = create_enhanced_signal_data()
            self.consolidated_portfolio = {
                'SMR': 0.111,      # 22.1% of 50% nuclear allocation 
                'BWXT': 0.092,     # 18.5% of 50% nuclear allocation
                'LEU': 0.097,      # 19.4% of 50% nuclear allocation
                'EXC': 0.100,      # 20.0% of 50% nuclear allocation
                'NLR': 0.100,      # 20.0% of 50% nuclear allocation
                'TECL': 0.500      # 50% TECL allocation
            }
            self.orders_executed = [
                {
                    'symbol': 'SMR',
                    'side': 'BUY',
                    'qty': 75.0,
                    'filled_price': 14.82,
                    'estimated_value': 1111.50,
                    'order_type': 'market'
                },
                {
                    'symbol': 'BWXT', 
                    'side': 'BUY',
                    'qty': 9.6,
                    'filled_price': 95.89,
                    'estimated_value': 920.54,
                    'order_type': 'limit'
                },
                {
                    'symbol': 'LEU',
                    'side': 'BUY', 
                    'qty': 1.4,
                    'filled_price': 69.25,
                    'estimated_value': 96.95,
                    'order_type': 'market'
                },
                {
                    'symbol': 'TECL',
                    'side': 'BUY',
                    'qty': 116.3,
                    'filled_price': 42.98,
                    'estimated_value': 5000.47,
                    'order_type': 'market'
                },
                {
                    'symbol': 'UVXY',
                    'side': 'SELL',
                    'qty': 45.2,
                    'filled_price': 12.34,
                    'estimated_value': 557.77,
                    'order_type': 'market'
                }
            ]
            
            self.execution_summary = {
                'strategy_summary': {
                    'Nuclear': {
                        'allocation': 0.50,
                        'signal': 'BUY',
                        'symbol': 'NUCLEAR_PORTFOLIO',
                        'reason': self.strategy_signals[StrategyType.NUCLEAR]['reason']
                    },
                    'TECL': {
                        'allocation': 0.50,
                        'signal': 'BUY', 
                        'symbol': 'TECL',
                        'reason': self.strategy_signals[StrategyType.TECL]['reason']
                    }
                },
                'trading_summary': {
                    'total_trades': 5,
                    'total_buy_value': 7128.46,
                    'total_sell_value': 557.77,
                    'net_value': 6570.69,
                    'buy_orders': 4,
                    'sell_orders': 1
                },
                'account_info_before': {
                    'equity': 98450.32,
                    'cash': 8234.56,
                    'buying_power': 8234.56
                },
                'account_info_after': {
                    'equity': 105021.01,
                    'cash': 1663.87,
                    'buying_power': 1663.87,
                    'daily_pl': 6570.69,
                    'daily_pl_percent': 0.0667
                }
            }
            
            self.final_portfolio_state = {
                'allocations': {
                    'SMR': {
                        'current_percent': 11.1,
                        'target_percent': 11.1, 
                        'market_value': 11652.30,
                        'shares': 786.5,
                        'unrealized_pl': 523.80,
                        'unrealized_pl_percent': 4.7
                    },
                    'BWXT': {
                        'current_percent': 9.2,
                        'target_percent': 9.2,
                        'market_value': 9659.20,
                        'shares': 100.8,
                        'unrealized_pl': 145.90,
                        'unrealized_pl_percent': 1.5
                    },
                    'TECL': {
                        'current_percent': 49.8,
                        'target_percent': 50.0,
                        'market_value': 52304.51,
                        'shares': 1217.3,
                        'unrealized_pl': 2143.20,
                        'unrealized_pl_percent': 4.3
                    }
                },
                'total_unrealized_pl': 2812.90,
                'total_unrealized_pl_percent': 2.8
            }
    
    return MockResult()


def create_overbought_signal_result():
    """Create result showing overbought market conditions with volatility hedge"""
    class MockResult:
        def __init__(self):
            self.success = True
            self.strategy_signals = {
                StrategyType.NUCLEAR: {
                    'symbol': 'UVXY',
                    'action': 'BUY',
                    'reason': """Market Analysis: Bull Market (SPY $578.45 vs 200MA $552.30)
SPY RSI(10): 81.5 - Primary overbought condition triggered (>79)

Signal: SPY extremely overbought (RSI 81.5 > 81)
Action: Buy UVXY volatility hedge - expect major market correction""",
                    'timestamp': datetime.now().isoformat(),
                    'technical_indicators': {
                        'SPY': {'rsi_10': 81.5, 'rsi_20': 75.8, 'ma_200': 552.30, 'current_price': 578.45},
                        'UVXY': {'rsi_10': 45.2, 'rsi_20': 42.8, 'ma_200': 18.90, 'current_price': 15.60}
                    }
                },
                StrategyType.TECL: {
                    'symbol': {'UVXY': 0.25, 'BIL': 0.75},
                    'action': 'BUY',
                    'reason': """Market Regime Analysis:
• SPY Price: $578.45 vs 200MA: $552.30
• SPY RSI(10): 81.5
• Regime: BULL MARKET (SPY above 200MA)

Market Overbought Signal:
• SPY RSI(10): 81.5 > 80 (high overbought threshold)
• Strategy: Broad market protection in bull market
• Allocation: UVXY 25% (volatility) + BIL 75% (cash)
• Rationale: Market stretched, preparing for pullback""",
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            self.consolidated_portfolio = {
                'UVXY': 0.625,    # 50% nuclear + 25% of 50% TECL = 62.5% 
                'BIL': 0.375      # 75% of 50% TECL = 37.5%
            }
            
            self.orders_executed = [
                {
                    'symbol': 'UVXY',
                    'side': 'BUY',
                    'qty': 400.3,
                    'filled_price': 15.58,
                    'estimated_value': 6236.67,
                    'order_type': 'market'
                },
                {
                    'symbol': 'BIL',
                    'side': 'BUY',
                    'qty': 37.8,
                    'filled_price': 99.12,
                    'estimated_value': 3746.74,
                    'order_type': 'market'
                },
                {
                    'symbol': 'TECL',
                    'side': 'SELL',
                    'qty': 116.3,
                    'filled_price': 42.85,
                    'estimated_value': 4983.46,
                    'order_type': 'market'
                }
            ]
            
            self.execution_summary = {
                'strategy_summary': {
                    'Nuclear': {
                        'allocation': 0.50,
                        'signal': 'BUY',
                        'symbol': 'UVXY',
                        'reason': 'SPY extremely overbought - volatility hedge'
                    },
                    'TECL': {
                        'allocation': 0.50,
                        'signal': 'BUY',
                        'symbol': 'UVXY_BIL_PORTFOLIO',
                        'reason': 'Market overbought - defensive hedge position'
                    }
                },
                'trading_summary': {
                    'total_trades': 3,
                    'total_buy_value': 9983.41,
                    'total_sell_value': 4983.46,
                    'net_value': 4999.95
                },
                'account_info_after': {
                    'equity': 103021.27,
                    'cash': 3000.00
                }
            }
    
    return MockResult()


def send_test_email_1_successful_trading():
    """Test 1: Successful multi-strategy trading with detailed signals"""
    print("📧 Test 1: Sending successful multi-strategy trading report...")
    
    result = create_realistic_execution_result()
    html_content = build_multi_strategy_email_html(result, "LIVE")
    
    success = send_email_notification(
        subject="🧪 [TEST 1] The Alchemiser - Successful Multi-Strategy Execution",
        html_content=html_content,
        text_content="Test email showing successful multi-strategy execution with detailed signal explanations"
    )
    
    print(f"   {'✅ Sent successfully' if success else '❌ Failed to send'}")
    return success


def send_test_email_2_overbought_hedge():
    """Test 2: Overbought market conditions with volatility hedge"""
    print("📧 Test 2: Sending overbought market hedge report...")
    
    result = create_overbought_signal_result()
    html_content = build_multi_strategy_email_html(result, "LIVE")
    
    success = send_email_notification(
        subject="🧪 [TEST 2] The Alchemiser - Overbought Market Volatility Hedge",
        html_content=html_content,
        text_content="Test email showing volatility hedge strategy during overbought market conditions"
    )
    
    print(f"   {'✅ Sent successfully' if success else '❌ Failed to send'}")
    return success


def send_test_email_3_classic_report():
    """Test 3: Classic trading report format with positions and P&L"""
    print("📧 Test 3: Sending classic trading report with positions...")
    
    # Sample positions with realistic P&L
    open_positions = [
        {
            'symbol': 'SMR',
            'market_value': 11652.30,
            'unrealized_pl': 523.80,
            'unrealized_plpc': 0.047,
            'qty': 786.5,
            'avg_cost': 14.15
        },
        {
            'symbol': 'BWXT',
            'market_value': 9659.20,
            'unrealized_pl': 145.90,
            'unrealized_plpc': 0.015,
            'qty': 100.8,
            'avg_cost': 94.45
        },
        {
            'symbol': 'TECL',
            'market_value': 52304.51,
            'unrealized_pl': 2143.20,
            'unrealized_plpc': 0.043,
            'qty': 1217.3,
            'avg_cost': 41.22
        },
        {
            'symbol': 'LEU',
            'market_value': 4890.25,
            'unrealized_pl': -89.75,
            'unrealized_plpc': -0.018,
            'qty': 70.6,
            'avg_cost': 70.53
        },
        {
            'symbol': 'UVXY',
            'market_value': 6240.00,
            'unrealized_pl': 45.30,
            'unrealized_plpc': 0.007,
            'qty': 400.0,
            'avg_cost': 15.49
        }
    ]
    
    # Sample recent orders
    orders = [
        {
            'side': 'BUY',
            'symbol': 'SMR',
            'qty': 75,
            'filled_price': 14.82,
            'timestamp': datetime.now() - timedelta(minutes=5)
        },
        {
            'side': 'BUY', 
            'symbol': 'TECL',
            'qty': 116.3,
            'filled_price': 42.98,
            'timestamp': datetime.now() - timedelta(minutes=3)
        },
        {
            'side': 'SELL',
            'symbol': 'UVXY',
            'qty': 45.2,
            'filled_price': 12.34,
            'timestamp': datetime.now() - timedelta(minutes=1)
        }
    ]
    
    # Mock signal with detailed explanation
    class MockSignal:
        def __init__(self):
            self.action = "BUY"
            self.symbol = "NUCLEAR_PORTFOLIO"
            self.reason = """Nuclear Energy Growth Strategy:
• Portfolio: SMR (22.1%), BWXT (18.5%), LEU (19.4%), EXC (20.0%), NLR (20.0%)
• Rationale: Bull market favors growth sectors with nuclear renaissance theme
• Market Analysis: SPY above 200MA, technology sector outperforming materials
• Risk Management: Diversified across uranium miners, utilities, and technology"""
    
    html_content = build_trading_report_html(
        mode="LIVE",
        success=True,
        account_before={'equity': 98450.32, 'cash': 8234.56},
        account_after={'equity': 105021.01, 'cash': 1663.87},
        positions={},
        orders=orders,
        signal=MockSignal(),
        open_positions=open_positions
    )
    
    success = send_email_notification(
        subject="🧪 [TEST 3] The Alchemiser - Classic Trading Report with Positions",
        html_content=html_content,
        text_content="Test email showing classic trading report format with detailed positions and P&L"
    )
    
    print(f"   {'✅ Sent successfully' if success else '❌ Failed to send'}")
    return success


def send_test_email_4_error_alert():
    """Test 4: Error alert email"""
    print("📧 Test 4: Sending error alert email...")
    
    error_html = build_error_email_html(
        "Market Data Connection Failed",
        """Failed to connect to market data provider after 3 retry attempts.

Error Details:
- Connection timeout after 30 seconds
- DNS resolution failed for api.alpaca.markets
- Last successful connection: 2025-07-29 14:23:15 UTC
- Network status: OFFLINE

Action Required:
- Check internet connection
- Verify Alpaca API credentials
- Monitor system logs for recurring issues

System will retry in 5 minutes."""
    )
    
    success = send_email_notification(
        subject="🧪 [TEST 4] The Alchemiser - ERROR: Market Data Connection Failed",
        html_content=error_html,
        text_content="Test error alert email showing system failure notification"
    )
    
    print(f"   {'✅ Sent successfully' if success else '❌ Failed to send'}")
    return success


def send_test_email_5_paper_trading():
    """Test 5: Paper trading mode report"""
    print("📧 Test 5: Sending paper trading mode report...")
    
    result = create_realistic_execution_result()
    html_content = build_multi_strategy_email_html(result, "PAPER")
    
    success = send_email_notification(
        subject="🧪 [TEST 5] The Alchemiser - PAPER Trading Multi-Strategy Report", 
        html_content=html_content,
        text_content="Test email showing paper trading execution with enhanced signal explanations"
    )
    
    print(f"   {'✅ Sent successfully' if success else '❌ Failed to send'}")
    return success


def main():
    """Run comprehensive email test suite"""
    print("🧪 The Alchemiser Email Test Suite")
    print("=" * 50)
    print("Sending enhanced email reports with detailed signal explanations...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all test emails
    tests = [
        send_test_email_1_successful_trading,
        send_test_email_2_overbought_hedge, 
        send_test_email_3_classic_report,
        send_test_email_4_error_alert,
        send_test_email_5_paper_trading
    ]
    
    results = []
    for test_func in tests:
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append(False)
        print()
    
    # Summary
    successful = sum(results)
    total = len(results)
    
    print("📋 Email Test Summary:")
    print(f"   ✅ Successful: {successful}/{total}")
    print(f"   ❌ Failed: {total - successful}/{total}")
    
    if successful == total:
        print("\n🎉 All email tests completed successfully!")
        print("📬 Check your inbox for 5 test emails showcasing:")
        print("   • Enhanced signal explanations with market analysis")
        print("   • Technical indicator tables with RSI and MA values")
        print("   • Detailed strategy reasoning and decision logic") 
        print("   • Beautiful responsive HTML formatting")
        print("   • Error alerts and system notifications")
    else:
        print(f"\n⚠️  {total - successful} email(s) failed to send. Check your email configuration.")
    
    print("\n💡 These emails demonstrate the enhanced format with:")
    print("   • Detailed market regime analysis")
    print("   • Step-by-step strategy decision logic")
    print("   • Technical indicator values and thresholds")
    print("   • Risk management explanations")
    print("   • Portfolio allocation reasoning")


if __name__ == "__main__":
    main()
