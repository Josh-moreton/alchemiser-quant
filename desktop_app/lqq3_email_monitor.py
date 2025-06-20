#!/usr/bin/env python3
"""
LQQ3 Signal Monitor with Email Alerts
Monitors TQQQ signals and sends email notifications when they change
"""

import yfinance as yf
import pandas as pd
import smtplib
import json
import os
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import warnings
warnings.filterwarnings('ignore')

class LQQ3SignalMonitor:
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.state_file = 'signal_state.json'
        self.config = self.load_config()
        
    def load_config(self):
        """Load email configuration from file"""
        default_config = {
            "email": {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "sender_email": "",
                "sender_password": "",
                "recipient_email": "",
                "use_app_password": True
            },
            "monitoring": {
                "check_enabled": True,
                "send_daily_summary": False,
                "send_only_on_changes": True
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                # Merge with defaults
                for key in default_config:
                    if key not in config:
                        config[key] = default_config[key]
                return config
            except Exception as e:
                print(f"Error loading config: {e}")
                return default_config
        else:
            # Create default config file
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            print(f"Created default config file: {self.config_file}")
            print("Please edit the config file with your email settings")
            return default_config
    
    def fetch_signals(self):
        """Fetch current TQQQ signals"""
        try:
            # Fetch recent TQQQ data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=300)
            
            tqqq = yf.download('TQQQ', start=start_date, end=end_date, progress=False)
            
            if tqqq.empty:
                raise ValueError("No data received")
            
            if tqqq.columns.nlevels > 1:
                tqqq.columns = tqqq.columns.get_level_values(0)
            
            # Calculate MACD
            ema_12 = tqqq['Close'].ewm(span=12).mean()
            ema_26 = tqqq['Close'].ewm(span=26).mean()
            tqqq['MACD'] = ema_12 - ema_26
            tqqq['MACD_Signal'] = tqqq['MACD'].ewm(span=9).mean()
            tqqq['MACD_Histogram'] = tqqq['MACD'] - tqqq['MACD_Signal']
            
            # Calculate 200-day SMA
            tqqq['SMA_200'] = tqqq['Close'].rolling(window=200).mean()
            
            # Generate signals
            tqqq['MACD_Bullish'] = (tqqq['MACD'] > tqqq['MACD_Signal']).astype(int)
            tqqq['SMA_Bullish'] = (tqqq['Close'] > tqqq['SMA_200']).astype(int)
            
            # Latest values
            latest = tqqq.iloc[-1]
            
            return {
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'date': latest.name.strftime('%Y-%m-%d'),
                'tqqq_price': float(latest['Close']),
                'sma_200': float(latest['SMA_200']),
                'price_vs_sma_pct': float((latest['Close'] / latest['SMA_200'] - 1) * 100),
                'macd': float(latest['MACD']),
                'macd_signal': float(latest['MACD_Signal']),
                'macd_histogram': float(latest['MACD_Histogram']),
                'macd_bullish': bool(latest['MACD_Bullish']),
                'sma_bullish': bool(latest['SMA_Bullish']),
                'bullish_count': int(latest['MACD_Bullish']) + int(latest['SMA_Bullish'])
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def calculate_allocation(self, signals):
        """Calculate allocation recommendation"""
        if not signals['success']:
            return None
            
        bullish_count = signals['bullish_count']
        
        if bullish_count == 0:
            return {
                'lqq3_pct': 33,
                'cash_pct': 67,
                'stance': 'DEFENSIVE',
                'emoji': '🛡️',
                'description': 'Both signals bearish - minimum exposure'
            }
        elif bullish_count == 1:
            desc = "Momentum positive, trend neutral" if signals['macd_bullish'] else "Trend positive, momentum weak"
            return {
                'lqq3_pct': 66,
                'cash_pct': 34,
                'stance': 'BALANCED',
                'emoji': '⚖️',
                'description': desc
            }
        else:
            return {
                'lqq3_pct': 100,
                'cash_pct': 0,
                'stance': 'AGGRESSIVE',
                'emoji': '🚀',
                'description': 'Both signals bullish - maximum exposure'
            }
    
    def load_previous_state(self):
        """Load previous signal state"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return None
        return None
    
    def save_current_state(self, signals, allocation):
        """Save current signal state"""
        state = {
            'signals': signals,
            'allocation': allocation,
            'saved_at': datetime.now().isoformat()
        }
        
        try:
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save state: {e}")
    
    def detect_changes(self, current_signals, previous_state):
        """Detect signal changes from previous state"""
        if not previous_state or not current_signals['success']:
            return None
        
        prev_signals = previous_state.get('signals', {})
        changes = []
        
        # Check MACD changes
        if prev_signals.get('macd_bullish') != current_signals['macd_bullish']:
            old_state = "bullish" if prev_signals.get('macd_bullish') else "bearish"
            new_state = "bullish" if current_signals['macd_bullish'] else "bearish"
            changes.append({
                'signal': 'MACD',
                'old_state': old_state,
                'new_state': new_state,
                'description': f"MACD signal changed from {old_state} to {new_state}"
            })
        
        # Check SMA changes
        if prev_signals.get('sma_bullish') != current_signals['sma_bullish']:
            old_state = "bullish" if prev_signals.get('sma_bullish') else "bearish"
            new_state = "bullish" if current_signals['sma_bullish'] else "bearish"
            changes.append({
                'signal': 'SMA',
                'old_state': old_state,
                'new_state': new_state,
                'description': f"SMA signal changed from {old_state} to {new_state}"
            })
        
        # Check allocation changes
        prev_allocation = previous_state.get('allocation', {})
        current_allocation = self.calculate_allocation(current_signals)
        
        allocation_changed = False
        if prev_allocation.get('lqq3_pct') != current_allocation['lqq3_pct']:
            allocation_changed = True
            changes.append({
                'signal': 'ALLOCATION',
                'old_state': f"{prev_allocation.get('lqq3_pct', 'Unknown')}% LQQ3",
                'new_state': f"{current_allocation['lqq3_pct']}% LQQ3",
                'description': f"Allocation changed from {prev_allocation.get('lqq3_pct', 'Unknown')}% to {current_allocation['lqq3_pct']}% LQQ3"
            })
        
        return {
            'has_changes': len(changes) > 0,
            'changes': changes,
            'allocation_changed': allocation_changed
        }
    
    def create_email_content(self, signals, allocation, change_info=None):
        """Create email content for signal update"""
        if not signals['success']:
            subject = "🚨 LQQ3 Signal Monitor - Error"
            body = f"""
LQQ3 Signal Monitor Error

Error fetching signals: {signals.get('error', 'Unknown error')}
Time: {signals.get('timestamp', 'Unknown')}

Please check the monitor and try again.
"""
            return subject, body
        
        # Determine email type
        if change_info and change_info['has_changes']:
            if change_info['allocation_changed']:
                subject = "🚨 LQQ3 ALLOCATION CHANGE ALERT"
                urgency = "⚠️ IMMEDIATE ACTION REQUIRED"
            else:
                subject = "📊 LQQ3 Signal Change Alert"
                urgency = "📋 For Your Information"
        else:
            subject = "📈 LQQ3 Daily Signal Summary"
            urgency = "📊 Daily Update"
        
        # Signal status
        macd_emoji = "🟢" if signals['macd_bullish'] else "🔴"
        sma_emoji = "🟢" if signals['sma_bullish'] else "🔴"
        macd_status = "BULLISH" if signals['macd_bullish'] else "BEARISH"
        sma_status = "BULLISH" if signals['sma_bullish'] else "BEARISH"
        
        body = f"""
{urgency}

LQQ3 Trading Signal Update
Date: {signals['date']}
Time: {datetime.now().strftime('%H:%M:%S')}

CURRENT SIGNALS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 TQQQ Price: ${signals['tqqq_price']:.2f}

📈 200-day SMA: {sma_emoji} {sma_status}
   Level: ${signals['sma_200']:.2f}
   Distance: {signals['price_vs_sma_pct']:+.1f}%

⚡ MACD (12,26,9): {macd_emoji} {macd_status}
   MACD: {signals['macd']:.4f}
   Signal: {signals['macd_signal']:.4f}
   Histogram: {signals['macd_histogram']:+.4f}

PORTFOLIO ALLOCATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

{allocation['emoji']} {allocation['stance']} STANCE
🏦 LQQ3: {allocation['lqq3_pct']}%
💰 Cash: {allocation['cash_pct']}%

Recommendation: {allocation['description']}
"""
        
        # Add change information if applicable
        if change_info and change_info['has_changes']:
            body += f"""
CHANGES DETECTED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            for change in change_info['changes']:
                body += f"🔄 {change['description']}\n"
            
            if change_info['allocation_changed']:
                body += f"""
⚠️  PORTFOLIO REBALANCING REQUIRED
   Previous allocation vs New allocation
   Action: Adjust LQQ3 position to {allocation['lqq3_pct']}%
"""
        
        body += f"""
STRATEGY SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Binary Exit with Laddered Entry Strategy:
• 0 bullish signals → 33% LQQ3 (Defensive)
• 1 bullish signal  → 66% LQQ3 (Balanced)
• 2 bullish signals → 100% LQQ3 (Aggressive)

Historical Performance: 6,187% returns, 1.15 Sharpe ratio

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This is an automated message from LQQ3 Signal Monitor.
"""
        
        return subject, body
    
    def send_email(self, subject, body):
        """Send email notification"""
        try:
            email_config = self.config['email']
            
            # Validate email configuration
            if not email_config['sender_email'] or not email_config['recipient_email']:
                print("Error: Email addresses not configured")
                return False
            
            if not email_config['sender_password']:
                print("Error: Email password not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = email_config['sender_email']
            msg['To'] = email_config['recipient_email']
            msg['Subject'] = subject
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(email_config['smtp_server'], email_config['smtp_port'])
            server.starttls()
            server.login(email_config['sender_email'], email_config['sender_password'])
            
            text = msg.as_string()
            server.sendmail(email_config['sender_email'], email_config['recipient_email'], text)
            server.quit()
            
            print(f"✅ Email sent successfully to {email_config['recipient_email']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")
            return False
    
    def run_check(self, force_email=False):
        """Run signal check and send email if needed"""
        print(f"🔄 Running LQQ3 signal check at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Fetch current signals
        current_signals = self.fetch_signals()
        
        if not current_signals['success']:
            print(f"❌ Error fetching signals: {current_signals.get('error')}")
            # Send error email
            subject, body = self.create_email_content(current_signals, None)
            self.send_email(subject, body)
            return False
        
        # Calculate allocation
        allocation = self.calculate_allocation(current_signals)
        
        # Load previous state and detect changes
        previous_state = self.load_previous_state()
        change_info = self.detect_changes(current_signals, previous_state)
        
        # Print current status
        print(f"📊 TQQQ: ${current_signals['tqqq_price']:.2f}")
        print(f"📈 SMA: {'🟢' if current_signals['sma_bullish'] else '🔴'} | ⚡ MACD: {'🟢' if current_signals['macd_bullish'] else '🔴'}")
        print(f"{allocation['emoji']} {allocation['stance']}: {allocation['lqq3_pct']}% LQQ3")
        
        # Determine if we should send email
        should_send_email = force_email
        
        if change_info and change_info['has_changes']:
            print(f"🚨 Signal changes detected!")
            for change in change_info['changes']:
                print(f"   • {change['description']}")
            should_send_email = True
        elif self.config['monitoring']['send_daily_summary']:
            should_send_email = True
        elif not self.config['monitoring']['send_only_on_changes']:
            should_send_email = True
        
        # Send email if needed
        if should_send_email:
            subject, body = self.create_email_content(current_signals, allocation, change_info)
            email_sent = self.send_email(subject, body)
            if not email_sent:
                print("❌ Failed to send email notification")
        else:
            print("✅ No changes detected, no email sent")
        
        # Save current state
        self.save_current_state(current_signals, allocation)
        
        return True

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='LQQ3 Signal Monitor with Email Alerts')
    parser.add_argument('--force-email', action='store_true', 
                       help='Force send email even if no changes')
    parser.add_argument('--test-email', action='store_true',
                       help='Send test email to verify configuration')
    parser.add_argument('--setup', action='store_true',
                       help='Interactive setup of email configuration')
    
    args = parser.parse_args()
    
    monitor = LQQ3SignalMonitor()
    
    if args.setup:
        setup_email_config(monitor)
        return
    
    if args.test_email:
        test_email_config(monitor)
        return
    
    # Run the signal check
    success = monitor.run_check(force_email=args.force_email)
    
    if success:
        print("✅ Signal check completed successfully")
    else:
        print("❌ Signal check failed")

def setup_email_config(monitor):
    """Interactive email configuration setup"""
    print("📧 Email Configuration Setup")
    print("=" * 40)
    
    config = monitor.config['email']
    
    print("\nEnter your email settings:")
    config['sender_email'] = input(f"Sender email [{config['sender_email']}]: ") or config['sender_email']
    config['sender_password'] = input(f"Sender password (use app password for Gmail): ") or config['sender_password']
    config['recipient_email'] = input(f"Recipient email [{config['recipient_email']}]: ") or config['recipient_email']
    
    # Save configuration
    with open(monitor.config_file, 'w') as f:
        json.dump(monitor.config, f, indent=4)
    
    print(f"✅ Configuration saved to {monitor.config_file}")
    print("\n📧 Gmail Setup Instructions:")
    print("1. Enable 2-factor authentication on your Gmail account")
    print("2. Generate an 'App Password' for this application")
    print("3. Use the app password instead of your regular password")

def test_email_config(monitor):
    """Test email configuration"""
    print("📧 Testing email configuration...")
    
    test_subject = "🧪 LQQ3 Signal Monitor - Test Email"
    test_body = f"""
This is a test email from LQQ3 Signal Monitor.

If you receive this email, your configuration is working correctly!

Test sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

You can now run the signal monitor to receive automated alerts.
"""
    
    success = monitor.send_email(test_subject, test_body)
    
    if success:
        print("✅ Test email sent successfully!")
        print("Check your inbox to confirm receipt.")
    else:
        print("❌ Test email failed.")
        print("Please check your email configuration.")

if __name__ == "__main__":
    main()
