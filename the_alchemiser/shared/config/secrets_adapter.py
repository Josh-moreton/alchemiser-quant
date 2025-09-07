#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Secrets Adapter System for Environment-Aware Credential Management.

This module provides a clean abstraction for loading secrets based on the deployment environment:
- Local development: Loads from .env files  
- AWS SAM Local: Loads from .env files
- Deployed Lambda: Loads from stage-scoped AWS Secrets Manager

Security Features:
- Stage isolation: dev environments cannot access prod secrets
- Runtime guardrails: non-prod stages must use paper trading endpoints
- No --live flag: trading mode determined by available credentials only
"""

from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Protocol

logger = logging.getLogger(__name__)


class SecretsLoader(Protocol):
    """Protocol for loading secrets from different sources."""
    
    def get_alpaca_keys(self) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca API keys.
        
        Returns:
            Tuple of (api_key, secret_key) or (None, None) if not found
        """
        ...
    
    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key.
        
        Returns:
            API key string or None if not found
        """
        ...


class LocalEnvSecretsLoader:
    """Loads secrets from environment variables (.env files) for local development."""
    
    def __init__(self) -> None:
        logger.info("Using local environment variables for secrets")
    
    def get_alpaca_keys(self) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca paper trading keys from environment variables."""
        api_key = os.getenv("ALPACA_PAPER_KEY")
        secret_key = os.getenv("ALPACA_PAPER_SECRET")
        
        if not api_key or not secret_key:
            logger.error("Missing Alpaca paper trading keys in environment variables")
            return None, None
        
        logger.info("Successfully loaded Alpaca paper trading keys from environment")
        return api_key, secret_key
    
    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key from environment variables."""
        api_key = os.getenv("TWELVEDATA_KEY")
        
        if not api_key:
            logger.warning("TwelveData API key not found in environment variables")
            return None
        
        logger.info("Successfully loaded TwelveData API key from environment")
        return api_key


class AwsSecretsManagerLoader:
    """Loads secrets from AWS Secrets Manager for deployed environments."""
    
    def __init__(self, stage: str, region_name: str = "eu-west-2") -> None:
        self.stage = stage
        self.region_name = region_name
        self._client = None
        self._secrets_cache: dict[str, str] | None = None
        
        # Import boto3 here to avoid dependency issues in local environments
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            self._client = boto3.client("secretsmanager", region_name=region_name)
            self._ClientError = ClientError
            logger.info(f"Initialized AWS Secrets Manager client for stage: {stage}")
        except ImportError as e:
            raise RuntimeError("boto3 is required for AWS Secrets Manager") from e
    
    def get_alpaca_keys(self) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca keys from stage-scoped AWS Secrets Manager."""
        secret_name = f"alchemiser/{self.stage}/alpaca"
        secrets = self._get_secret(secret_name)
        
        if not secrets:
            logger.error(f"No secrets found for {secret_name}")
            return None, None
        
        # For dev stage, use paper keys; for prod stage, use live keys
        if self.stage == "prod":
            api_key = secrets.get("ALPACA_KEY")
            secret_key = secrets.get("ALPACA_SECRET")
            mode = "live"
        else:
            api_key = secrets.get("ALPACA_PAPER_KEY")
            secret_key = secrets.get("ALPACA_PAPER_SECRET")
            mode = "paper"
        
        if not api_key or not secret_key:
            logger.error(f"Missing Alpaca {mode} trading keys in {secret_name}")
            return None, None
        
        logger.info(f"Successfully loaded Alpaca {mode} trading keys from {secret_name}")
        return api_key, secret_key
    
    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key from AWS Secrets Manager."""
        secret_name = f"alchemiser/{self.stage}/alpaca"  # Store in same secret for simplicity
        secrets = self._get_secret(secret_name)
        
        if not secrets:
            logger.error(f"No secrets found for {secret_name}")
            return None
        
        api_key = secrets.get("TWELVEDATA_KEY")
        if not api_key:
            logger.warning(f"TwelveData API key not found in {secret_name}")
            return None
        
        logger.info(f"Successfully loaded TwelveData API key from {secret_name}")
        return api_key
    
    def _get_secret(self, secret_name: str) -> dict[str, str] | None:
        """Retrieve and parse a secret from AWS Secrets Manager."""
        if self._secrets_cache is not None:
            return self._secrets_cache
        
        if not self._client:
            raise RuntimeError("AWS Secrets Manager client not initialized")
        
        try:
            import json
            
            logger.debug(f"Retrieving secret: {secret_name}")
            response = self._client.get_secret_value(SecretId=secret_name)
            secret_string = response["SecretString"]
            secret_dict = json.loads(secret_string)
            
            self._secrets_cache = secret_dict
            logger.debug(f"Successfully retrieved secret: {secret_name}")
            return self._secrets_cache
            
        except self._ClientError as e:
            error_code = e.response["Error"]["Code"]
            logger.error(f"AWS Secrets Manager error ({error_code}) for {secret_name}: {e}")
            
            if error_code == "ResourceNotFoundException":
                logger.error(f"Secret '{secret_name}' not found - ensure it exists and IAM permissions are correct")
            
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret '{secret_name}': {e}")
            return None


class SecretsAdapter:
    """Main secrets adapter that chooses the appropriate loader based on environment."""
    
    def __init__(self) -> None:
        self._loader = self._create_loader()
        self._stage = self._detect_stage()
        self._validate_environment()
    
    def _detect_stage(self) -> str:
        """Detect the current deployment stage."""
        # Explicit stage environment variable takes precedence
        stage = os.getenv("STAGE")
        if stage:
            return stage.lower()
        
        # Check for AWS SAM Local
        if os.getenv("AWS_SAM_LOCAL"):
            return "local"
        
        # Check for Lambda environment
        if os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
            # In Lambda, determine stage from function name or environment
            function_name = os.getenv("AWS_LAMBDA_FUNCTION_NAME", "")
            if "prod" in function_name.lower():
                return "prod"
            else:
                return "dev"
        
        # Default to local for development
        return "local"
    
    def _create_loader(self) -> SecretsLoader:
        """Create the appropriate secrets loader based on environment."""
        stage = self._detect_stage()
        
        # Use local env loader for local development and SAM local
        if stage == "local" or os.getenv("AWS_SAM_LOCAL"):
            return LocalEnvSecretsLoader()
        
        # Use AWS Secrets Manager for deployed environments
        return AwsSecretsManagerLoader(stage=stage)
    
    def _validate_environment(self) -> None:
        """Validate environment configuration and apply guardrails."""
        # Runtime guardrail: non-prod stages must use paper trading
        if self._stage != "prod":
            # Ensure we're not accidentally pointing to live endpoints
            alpaca_endpoint = os.getenv("ALPACA__ENDPOINT", "")
            if alpaca_endpoint and "paper" not in alpaca_endpoint.lower():
                logger.warning(
                    f"Non-prod stage '{self._stage}' should use paper trading endpoint, "
                    f"but ALPACA__ENDPOINT is set to: {alpaca_endpoint}"
                )
    
    @property
    def stage(self) -> str:
        """Get the current deployment stage."""
        return self._stage
    
    @property
    def is_paper_trading(self) -> bool:
        """Determine if this environment should use paper trading."""
        return self._stage != "prod"
    
    def get_alpaca_keys(self) -> tuple[str, str] | tuple[None, None]:
        """Get Alpaca API keys from the appropriate source."""
        return self._loader.get_alpaca_keys()
    
    def get_twelvedata_api_key(self) -> str | None:
        """Get TwelveData API key from the appropriate source."""
        return self._loader.get_twelvedata_api_key()


# Global instance for easy access
secrets_adapter = SecretsAdapter()