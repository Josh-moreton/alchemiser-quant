"""Business Unit: shared | Status: current.

Auto-load .env file into OS environment variables.

This module automatically loads the .env file when imported, ensuring that
environment variables are available via os.getenv().
"""

from pathlib import Path

try:
    from dotenv import load_dotenv

    # Find the .env file in the project root
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent  # Go up to the project root
    env_file = project_root / ".env"

    if env_file.exists():
        # Load the .env file into OS environment
        load_dotenv(env_file, override=True)

except ImportError:
    # python-dotenv not available, skip silently
    pass
