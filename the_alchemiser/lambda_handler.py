"""
AWS Lambda Handler for The Alchemiser.

Enables running the trading bot as an AWS Lambda function for automated cloud execution.
Wraps the main entry point and returns status for integration with AWS services.
"""

from the_alchemiser.main import main

def lambda_handler(event=None, context=None):
    result = main(["trade", "--live"])
    return {"status": "success" if result else "failed"}
