"""pytest configuration for the test suite.

Sets up PYTHONPATH to include the shared layer for imports.
"""

import sys
from pathlib import Path

# Add layers/shared to PYTHONPATH for the_alchemiser imports
layers_shared = Path(__file__).parent.parent / "layers" / "shared"
sys.path.insert(0, str(layers_shared))
