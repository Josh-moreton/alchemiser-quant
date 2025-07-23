import sys
from main import main

def lambda_handler(event=None, context=None):
    sys.argv = ["main.py", "trade", "--live"]
    result = main()
    return {"status": "success" if result else "failed"}
