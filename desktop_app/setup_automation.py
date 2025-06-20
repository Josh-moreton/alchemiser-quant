#!/usr/bin/env python3
"""
LQQ3 Email Monitor - Crontab Setup Helper
Easy setup for automated daily signal monitoring
"""

import os
import subprocess
import sys
from pathlib import Path

def get_current_crontab():
    """Get current crontab entries"""
    try:
        result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return ""
    except Exception:
        return ""

def create_crontab_entry():
    """Create the crontab entry for LQQ3 monitoring"""
    current_dir = Path(__file__).parent.absolute()
    python_path = sys.executable
    
    # Crontab entry: Run Mon-Fri at 8:00 AM
    cron_entry = f"0 8 * * 1-5 cd {current_dir} && {python_path} lqq3_email_monitor.py"
    
    return cron_entry

def install_crontab():
    """Install the crontab entry"""
    print("🕐 Setting up automated daily signal monitoring...")
    
    # Get current crontab
    current_crontab = get_current_crontab()
    new_entry = create_crontab_entry()
    
    # Check if entry already exists
    if "lqq3_email_monitor.py" in current_crontab:
        print("✅ LQQ3 monitor is already in your crontab")
        print(f"Current entry: {[line for line in current_crontab.split('\\n') if 'lqq3_email_monitor.py' in line][0]}")
        return True
    
    # Add new entry
    if current_crontab:
        new_crontab = current_crontab + "\\n" + new_entry
    else:
        new_crontab = new_entry
    
    try:
        # Write new crontab
        process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
        process.communicate(input=new_crontab)
        
        if process.returncode == 0:
            print("✅ Crontab updated successfully!")
            print(f"📧 LQQ3 signals will be checked Mon-Fri at 8:00 AM")
            print(f"Entry added: {new_entry}")
            return True
        else:
            print("❌ Failed to update crontab")
            return False
            
    except Exception as e:
        print(f"❌ Error setting up crontab: {e}")
        return False

def show_gui_alternatives():
    """Show macOS GUI alternatives to crontab"""
    print("\\n" + "="*60)
    print("🖥️  macOS GUI ALTERNATIVES TO CRONTAB")
    print("="*60)
    
    print("\\n1. 📱 CRONETTE (Free)")
    print("   • Simple crontab GUI for macOS")
    print("   • Download: https://apps.apple.com/app/cronette/id1439967473")
    print("   • Just drag your script or add the command")
    
    print("\\n2. 🔧 CRONNIX (Free)")
    print("   • Classic crontab editor")
    print("   • Download: https://code.google.com/archive/p/cronnix/")
    print("   • More advanced interface")
    
    print("\\n3. ⚡ AUTOMATOR (Built-in)")
    print("   • Use macOS Automator to create a daily workflow")
    print("   • Applications → Automator → Calendar Alarm")
    print("   • Add 'Run Shell Script' action")
    
    print("\\n4. 📅 LAUNCHD (macOS Native)")
    print("   • More reliable than cron on macOS")
    print("   • I can create a .plist file for you")
    
    print("\\n5. 🤖 KEYBOARD MAESTRO (Paid)")
    print("   • Premium automation tool")
    print("   • Can trigger based on time, events, etc.")

def create_launchd_plist():
    """Create a launchd plist file (more reliable than cron on macOS)"""
    current_dir = Path(__file__).parent.absolute()
    python_path = sys.executable
    
    plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lqq3.signal.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>{current_dir}/lqq3_email_monitor.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{current_dir}</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
        <key>Weekday</key>
        <integer>1</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>{current_dir}/lqq3_monitor.log</string>
    <key>StandardErrorPath</key>
    <string>{current_dir}/lqq3_monitor_error.log</string>
</dict>
</plist>'''
    
    return plist_content

def install_launchd():
    """Install launchd plist (recommended for macOS)"""
    print("\\n🚀 Setting up macOS LaunchAgent (recommended for macOS)...")
    
    # Create plist content
    plist_content = create_launchd_plist()
    
    # LaunchAgents directory
    launch_agents_dir = Path.home() / "Library" / "LaunchAgents"
    launch_agents_dir.mkdir(exist_ok=True)
    
    plist_file = launch_agents_dir / "com.lqq3.signal.monitor.plist"
    
    try:
        # Write plist file
        with open(plist_file, 'w') as f:
            f.write(plist_content)
        
        # Load the agent
        subprocess.run(['launchctl', 'load', str(plist_file)], check=True)
        
        print(f"✅ LaunchAgent installed successfully!")
        print(f"📁 File: {plist_file}")
        print(f"📧 LQQ3 signals will be checked Mon-Fri at 8:00 AM")
        print(f"📝 Logs: {Path(__file__).parent.absolute()}/lqq3_monitor.log")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up LaunchAgent: {e}")
        return False

def uninstall_automation():
    """Remove automation"""
    print("\\n🗑️  Removing LQQ3 automation...")
    
    # Remove from crontab
    current_crontab = get_current_crontab()
    if "lqq3_email_monitor.py" in current_crontab:
        lines = current_crontab.split('\\n')
        new_lines = [line for line in lines if "lqq3_email_monitor.py" not in line]
        new_crontab = '\\n'.join(new_lines)
        
        try:
            process = subprocess.Popen(['crontab', '-'], stdin=subprocess.PIPE, text=True)
            process.communicate(input=new_crontab)
            print("✅ Removed from crontab")
        except Exception:
            print("❌ Failed to remove from crontab")
    
    # Remove LaunchAgent
    plist_file = Path.home() / "Library" / "LaunchAgents" / "com.lqq3.signal.monitor.plist"
    if plist_file.exists():
        try:
            subprocess.run(['launchctl', 'unload', str(plist_file)], check=False)
            plist_file.unlink()
            print("✅ Removed LaunchAgent")
        except Exception:
            print("❌ Failed to remove LaunchAgent")

def main():
    """Main setup function"""
    print("🏦 LQQ3 Email Monitor - Automation Setup")
    print("="*50)
    
    while True:
        print("\\nChoose an option:")
        print("1. 🕐 Setup Crontab (traditional)")
        print("2. 🚀 Setup LaunchAgent (recommended for macOS)")
        print("3. 🖥️  Show GUI alternatives") 
        print("4. 🗑️  Remove automation")
        print("5. 📋 Show current automation status")
        print("6. 🚪 Exit")
        
        choice = input("\\nEnter choice (1-6): ").strip()
        
        if choice == "1":
            install_crontab()
        elif choice == "2":
            install_launchd()
        elif choice == "3":
            show_gui_alternatives()
        elif choice == "4":
            uninstall_automation()
        elif choice == "5":
            print("\\n📋 Current Status:")
            crontab = get_current_crontab()
            if "lqq3_email_monitor.py" in crontab:
                print("✅ Found in crontab")
            else:
                print("❌ Not in crontab")
            
            plist_file = Path.home() / "Library" / "LaunchAgents" / "com.lqq3.signal.monitor.plist"
            if plist_file.exists():
                print("✅ LaunchAgent installed")
            else:
                print("❌ LaunchAgent not installed")
        elif choice == "6":
            break
        else:
            print("❌ Invalid choice")
    
    print("\\n👋 Setup complete!")

if __name__ == "__main__":
    main()
