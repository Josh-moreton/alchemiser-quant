"""AWS Lambda Handler for The Alchemiser Trading Bot.

This module provides the entry point for running The Alchemiser trading bot
as an AWS Lambda function, enabling serverless execution and automated trading
in the cloud environment.

The handler wraps the main application entry point and provides appropriate
response formatting for AWS Lambda integration.
"""

from the_alchemiser.main import main


def lambda_handler(_event=None, _context=None):
    """AWS Lambda function handler for The Alchemiser trading bot.
    
    This function serves as the entry point when the trading bot is deployed
    as an AWS Lambda function. It executes the trading bot in live mode and
    returns a status response suitable for AWS Lambda integration.
    
    Args:
        event (dict, optional): AWS Lambda event data. Contains information about
            the triggering event (e.g., CloudWatch Events, API Gateway request).
            Defaults to None.
        context (LambdaContext, optional): AWS Lambda runtime context object
            containing information about the Lambda function execution environment.
            Defaults to None.
    
    Returns:
        dict: A dictionary containing the execution status with the following structure:
            {
                "status": "success" | "failed"
            }
            
    Example:
        When triggered by CloudWatch Events:
        >>> result = lambda_handler(event={}, context=lambda_context)
        >>> print(result)
        {"status": "success"}
        
    Note:
        This function automatically runs the trading bot in live mode ("--live" flag).
        The event and context parameters are currently unused but are included
        for future extensibility and AWS Lambda standard compliance.
    """
    result = main(["trade", "--live"])
    return {"status": "success" if result else "failed"}
