"""Business Unit: scripts | Status: current.

Validation scripts for data quality and signal verification.

Available scripts:
- validate_data_lake.py: Validate S3 market data against yfinance
- validate_signals.py: Validate strategy signals against Composer.trade
- validate_dynamo_data.py: Validate DynamoDB data for per-strategy metrics
- validate_s3_against_yfinance.py: Legacy S3 vs yfinance validation (use validate_data_lake.py)
"""
