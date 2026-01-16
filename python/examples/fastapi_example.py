#!/usr/bin/env python3
"""FastAPI integration example for agora-log."""

import sys
from pathlib import Path

# Add src to path for examples
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.testclient import TestClient
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi")
    sys.exit(1)

from agora_log import initialize, get_logger, LogConfig, LogLevel
from agora_log.integrations.fastapi import LoggingMiddleware, get_request_logger


def create_app() -> FastAPI:
    """Create FastAPI application with logging middleware."""

    # Initialize logging
    config = LogConfig(
        service_name="api-example",
        environment="development",
        version="1.0.0",
        level=LogLevel.DEBUG,
        console_enabled=True,
        console_format="json",
        file_enabled=False,
    )

    initialize(config)

    # Create FastAPI app
    app = FastAPI(title="Agora Log FastAPI Example")

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Routes
    @app.get("/")
    async def root():
        """Root endpoint."""
        logger = get_request_logger()
        logger.info("Root endpoint accessed")
        return {"message": "Welcome to Agora Log FastAPI Example"}

    @app.get("/prices/{symbol}")
    async def get_price(symbol: str):
        """Get price for a symbol."""
        logger = get_request_logger()
        logger.info("Fetching price", symbol=symbol)

        # Simulate some processing
        logger.debug("Querying database", table="stock_prices")
        logger.debug("Cache lookup", key=f"price:{symbol}")

        # Return mock data
        return {
            "symbol": symbol,
            "price": 150.25,
            "currency": "USD"
        }

    @app.post("/orders")
    async def create_order(order: dict):
        """Create a new order."""
        logger = get_request_logger()
        logger.info("Creating order", order_data=order)

        # Log with timer
        with logger.timer("Order validation"):
            # Simulate validation
            if "symbol" not in order:
                logger.warning("Invalid order", reason="missing_symbol")
                raise HTTPException(status_code=400, detail="Symbol required")

        logger.info("Order created successfully", order_id="order-123")

        return {
            "order_id": "order-123",
            "status": "pending"
        }

    @app.get("/error")
    async def error_endpoint():
        """Endpoint that raises an error."""
        logger = get_request_logger()
        logger.info("Error endpoint called")

        try:
            raise ValueError("Simulated error")
        except ValueError as e:
            logger.error("Error in endpoint", exception=e)
            raise HTTPException(status_code=500, detail="Internal server error")

    @app.get("/slow")
    async def slow_endpoint():
        """Slow endpoint to demonstrate duration logging."""
        import time

        logger = get_request_logger()
        logger.info("Slow endpoint started")

        with logger.timer("Slow operation"):
            time.sleep(0.2)

        return {"message": "Completed"}

    return app


def run_examples():
    """Run example requests."""
    print("\n" + "=" * 60)
    print("FastAPI Integration Examples")
    print("=" * 60 + "\n")

    app = create_app()
    client = TestClient(app)

    # Example 1: Simple GET request
    print("Example 1: Simple GET request")
    print("-" * 60)
    response = client.get("/")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Example 2: GET with path parameter
    print("Example 2: GET with path parameter")
    print("-" * 60)
    response = client.get("/prices/AAPL")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Example 3: GET with correlation ID header
    print("Example 3: GET with correlation ID")
    print("-" * 60)
    response = client.get(
        "/prices/TSLA",
        headers={"X-Correlation-ID": "correlation-abc-123"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print(f"Correlation ID in response: {response.headers.get('X-Correlation-ID')}")
    print()

    # Example 4: POST request
    print("Example 4: POST request")
    print("-" * 60)
    response = client.post(
        "/orders",
        json={"symbol": "AAPL", "quantity": 100, "side": "buy"}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Example 5: POST with validation error
    print("Example 5: POST with validation error")
    print("-" * 60)
    response = client.post(
        "/orders",
        json={"quantity": 100}  # Missing symbol
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Example 6: Error endpoint
    print("Example 6: Error handling")
    print("-" * 60)
    response = client.get("/error")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    # Example 7: Slow endpoint (duration logging)
    print("Example 7: Slow endpoint (duration logging)")
    print("-" * 60)
    response = client.get("/slow")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_examples()
