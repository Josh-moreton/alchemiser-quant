"""AWS Lambda Handler for The Alchemiser Trading Bot.

This module provides the entry point for running The Alchemiser trading bot
as an AWS Lambda function, enabling serverless execution and automated trading
in the cloud environment.

The handler wraps the main application entry point and provides appropriate
response formatting for AWS Lambda integration. It supports different trading
modes based on the event payload.
"""

import json
import logging
from typing import Dict, Any, List
from the_alchemiser.main import main

# Set up logging
logger = logging.getLogger(__name__)


def parse_event_mode(event: Dict[str, Any]) -> List[str]:
    """Parse the Lambda event to determine which trading mode to execute.
    
    Args:
        event: AWS Lambda event data containing mode configuration
        
    Returns:
        List of command arguments for the main function
        
    Event Structure:
        {
            "mode": "trade" | "bot",           # Required: Operation mode
            "trading_mode": "paper" | "live",  # Optional: Trading mode (default: paper)
            "ignore_market_hours": bool        # Optional: Override market hours (default: false)
        }
        
    Examples:
        Paper trading: {"mode": "trade", "trading_mode": "paper"}
        Live trading: {"mode": "trade", "trading_mode": "live"}  
        Signals only: {"mode": "bot"}
        Testing: {"mode": "trade", "ignore_market_hours": true}
    """
    # Default to live trading for backward compatibility
    default_args = ["trade", "--live"]
    
    # Handle empty or None event
    if not event:
        logger.info("No event provided, using default live trading mode")
        return default_args
    
    # Extract mode (bot or trade)
    mode = event.get("mode", "trade")
    if mode not in ["bot", "trade"]:
        logger.warning(f"Invalid mode '{mode}', defaulting to 'trade'")
        mode = "trade"
    
    # Build command arguments
    args = [mode]
    
    # Only add trading-specific flags for trade mode
    if mode == "trade":
        # Extract trading mode (paper or live)
        trading_mode = event.get("trading_mode", "live")  # Default to live for existing deployments
        if trading_mode not in ["paper", "live"]:
            logger.warning(f"Invalid trading_mode '{trading_mode}', defaulting to 'live'")
            trading_mode = "live"
        
        # Add live flag if specified
        if trading_mode == "live":
            args.append("--live")
        
        # Add market hours override if specified
        if event.get("ignore_market_hours", False):
            args.append("--ignore-market-hours")
    
    logger.info(f"Parsed event to command: {' '.join(args)}")
    return args


def lambda_handler(event=None, context=None):
    """AWS Lambda function handler for The Alchemiser trading bot.
    
    This function serves as the entry point when the trading bot is deployed
    as an AWS Lambda function. It supports multiple trading modes based on the
    event configuration and returns detailed status information.
    
    Args:
        event (dict, optional): AWS Lambda event data containing mode configuration.
            See parse_event_mode() for expected structure.
        context (LambdaContext, optional): AWS Lambda runtime context object
            containing information about the Lambda function execution environment.
    
    Returns:
        dict: A dictionary containing the execution status with the following structure:
            {
                "status": "success" | "failed",
                "mode": str,                    # The executed mode
                "trading_mode": str,            # The trading mode (if applicable)  
                "message": str,                 # Human-readable status message
                "request_id": str               # Lambda request ID (if available)
            }
            
    Examples:
        Paper trading event:
        >>> event = {"mode": "trade", "trading_mode": "paper"}
        >>> result = lambda_handler(event, context)
        >>> print(result)
        {
            "status": "success", 
            "mode": "trade", 
            "trading_mode": "paper",
            "message": "Paper trading completed successfully",
            "request_id": "12345-abcde"
        }
        
        Live trading event (default):
        >>> event = {"mode": "trade", "trading_mode": "live"}
        >>> result = lambda_handler(event, context)
        >>> print(result)
        {
            "status": "success",
            "mode": "trade", 
            "trading_mode": "live",
            "message": "Live trading completed successfully",
            "request_id": "12345-abcde"
        }
        
        Signals only event:
        >>> event = {"mode": "bot"}
        >>> result = lambda_handler(event, context)
        >>> print(result)
        {
            "status": "success",
            "mode": "bot",
            "trading_mode": "n/a",
            "message": "Signal analysis completed successfully", 
            "request_id": "12345-abcde"
        }
    
    Backward Compatibility:
        - Empty event defaults to live trading for existing CloudWatch triggers
        - Maintains existing behavior while supporting new event-driven modes
    """
    # Extract request ID for tracking
    request_id = getattr(context, 'aws_request_id', 'unknown') if context else 'local'
    
    try:
        # Log the incoming event for debugging
        logger.info(f"Lambda invoked with event: {json.dumps(event) if event else 'None'}")
        
        # Parse event to determine command arguments
        command_args = parse_event_mode(event or {})
        
        # Extract mode information for response
        mode = command_args[0] if command_args else "unknown"
        trading_mode = "live" if "--live" in command_args else "paper" if mode == "trade" else "n/a"
        
        logger.info(f"Executing command: {' '.join(command_args)}")
        
        from the_alchemiser.core.config import load_settings
        settings = load_settings()
        result = main(command_args, settings=settings)
        
        # Build response message
        if mode == "bot":
            message = "Signal analysis completed successfully" if result else "Signal analysis failed"
        else:
            mode_str = trading_mode.title()
            message = f"{mode_str} trading completed successfully" if result else f"{mode_str} trading failed"
        
        response = {
            "status": "success" if result else "failed",
            "mode": mode,
            "trading_mode": trading_mode,
            "message": message,
            "request_id": request_id
        }
        
        logger.info(f"Lambda execution completed: {response}")
        return response
        
    except Exception as e:
        error_message = f"Lambda execution error: {str(e)}"
        logger.error(error_message, exc_info=True)
        
        return {
            "status": "failed",
            "mode": "unknown", 
            "trading_mode": "unknown",
            "message": error_message,
            "request_id": request_id
        }
