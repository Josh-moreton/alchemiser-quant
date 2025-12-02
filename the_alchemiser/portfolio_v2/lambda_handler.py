"""Business Unit: portfolio_v2 | Status: current.

Lambda handler for portfolio microservice.
"""

from __future__ import annotations

from mangum import Mangum

from the_alchemiser.portfolio_v2.api import create_app

# Create FastAPI app with lightweight EventBus
app = create_app()

# Wrap with Mangum for Lambda/Function URL support
lambda_handler = Mangum(app, lifespan="off")
