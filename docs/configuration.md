# Configuration Guide

The Alchemiser now uses a typed `Settings` model based on [Pydantic](https://docs.pydantic.dev/).
Configuration values are loaded from `config.yaml` and can be overridden using
environment variables. Nested keys can be set via environment variables using
`__` as a delimiter.

## Example

```bash
# Override Alpaca endpoint
export ALPACA__endpoint="https://override.example.com"
```

```yaml
# config.yaml
alpaca:
  endpoint: "https://api.alpaca.markets/v2"
```

When `load_settings()` is called, the environment value takes precedence over the
YAML file.

## Local Usage

```python
from the_alchemiser.core.config import load_settings
settings = load_settings()
print(settings.alpaca.endpoint)
```

## Production Usage

In production (e.g. AWS Lambda), provide environment variables for any secrets
or overrides and call `load_settings()` at the application entry point. Pass the
resulting `Settings` object to modules that require configuration.
