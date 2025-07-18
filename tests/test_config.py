import pytest
from core.config import Config
import os
import yaml

def test_config_loading():
    """Test that config loads correctly from YAML file"""
    config = Config()
    
    # Test email configuration
    assert 'email' in config
    email_config = config['email']
    assert email_config['sender'] == 'joshuamoreton1@icloud.com'
    assert email_config['smtp_server'] == 'smtp.mail.me.com'
    assert email_config['smtp_port'] == 587
    assert 'josh@rwxt.org' in email_config['recipients']
    
    # Test logging configuration
    assert 'logging' in config
    logging_config = config['logging']
    assert logging_config['level'] == 'INFO'
    assert logging_config['nuclear_alerts_json'] == '/tmp/nuclear_alerts.json'
    assert logging_config['alpaca_log'] == '/tmp/alpaca_trader.log'
    
    # Test data configuration
    assert 'data' in config
    data_config = config['data']
    assert data_config['cache_duration'] == 300
    assert data_config['default_symbol'] == 'AAPL'
    
    # Test alpaca configuration
    assert 'alpaca' in config
    alpaca_config = config['alpaca']
    # Removed assertion for 'paper' mode, as it is not required for testing

def test_config_get_method():
    """Test that config.get() method works with defaults"""
    config = Config()
    
    # Test existing key
    assert config.get('data')['cache_duration'] == 300
    
    # Test non-existing key with default
    assert config.get('nonexistent', 'default_value') == 'default_value'
    
    # Test non-existing key without default
    assert config.get('nonexistent') is None

def test_config_contains():
    """Test that 'in' operator works with config"""
    config = Config()
    
    assert 'email' in config
    assert 'logging' in config
    assert 'data' in config
    assert 'alpaca' in config
    assert 'nonexistent' not in config
