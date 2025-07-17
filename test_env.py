#!/usr/bin/env python3
"""
Test Alpaca keys loading
"""

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print("Testing .env file loading:")
print(f"ALPACA_KEY: {os.getenv('ALPACA_KEY')}")
print(f"ALPACA_SECRET: {os.getenv('ALPACA_SECRET')}")
print(f"ALPACA_PAPER_KEY: {os.getenv('ALPACA_PAPER_KEY')}")
print(f"ALPACA_PAPER_SECRET: {os.getenv('ALPACA_PAPER_SECRET')}")
