#!/usr/bin/env python3
"""
Example script showing how to run the ZeroPhi API with custom configuration.

This demonstrates how to programmatically configure and run the API server
instead of relying solely on environment variables.
"""

import logging
from zerophix.config import APIConfig
from zerophix.api import create_app

# Example 1: Run with custom configuration object
def run_custom_config():
    """Run API with programmatically defined configuration"""
    
    # Create custom configuration
    config = APIConfig(
        host="0.0.0.0",
        port=8080,
        workers=2,
        cors_enabled=True,
        cors_origins=["https://example.com", "https://app.example.com"],
        require_auth=True,
        api_keys=["test-key-1", "test-key-2"],
        environment="staging",
        log_level="info",
        docs_enabled=True
    )
    
    # Create app with custom config
    app = create_app(config)
    
    # Run with uvicorn
    import uvicorn
    
    logging.info(f"Starting ZeroPhi API on {config.host}:{config.port}")
    logging.info(f"Environment: {config.environment}")
    logging.info(f"Documentation: http://{config.host}:{config.port}/docs")
    
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        workers=config.workers if config.environment == "production" else 1,
        log_level=config.log_level.lower(),
        access_log=config.access_log
    )


# Example 2: Development server
def run_development():
    """Run API in development mode"""
    config = APIConfig(
        host="127.0.0.1",
        port=8000,
        reload=True,
        environment="development",
        log_level="debug",
        require_auth=False,
        docs_enabled=True
    )
    
    app = create_app(config)
    
    import uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        reload=True,
        log_level="debug"
    )


# Example 3: Production server with SSL
def run_production_ssl():
    """Run API in production mode with SSL"""
    config = APIConfig(
        host="0.0.0.0",
        port=8443,
        workers=4,
        cors_enabled=True,
        cors_origins=["https://app.example.com"],
        require_auth=True,
        api_keys=["production-key-change-this"],
        ssl_enabled=True,
        ssl_keyfile="/etc/ssl/private/api.key",
        ssl_certfile="/etc/ssl/certs/api.crt",
        environment="production",
        log_level="warning",
        docs_enabled=False,
        proxy_headers=True,
        rate_limit_enabled=True
    )
    
    app = create_app(config)
    
    import uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        workers=config.workers,
        ssl_keyfile=config.ssl_keyfile,
        ssl_certfile=config.ssl_certfile,
        log_level=config.log_level.lower(),
        proxy_headers=config.proxy_headers
    )


# Example 4: Docker/Cloud deployment
def run_docker():
    """Run API configured for Docker/cloud deployment"""
    import os
    
    config = APIConfig(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),  # Support Heroku, Cloud Run dynamic ports
        workers=2,
        cors_enabled=True,
        cors_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
        require_auth=True,
        api_keys=os.environ.get("API_KEYS", "").split(","),
        environment="production",
        log_level="info",
        docs_enabled=False,
        proxy_headers=True
    )
    
    app = create_app(config)
    
    import uvicorn
    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        workers=config.workers,
        log_level=config.log_level.lower(),
        proxy_headers=True
    )


if __name__ == "__main__":
    import sys
    
    # Select mode from command line argument
    mode = sys.argv[1] if len(sys.argv) > 1 else "development"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if mode == "development":
        run_development()
    elif mode == "production":
        run_production_ssl()
    elif mode == "docker":
        run_docker()
    elif mode == "custom":
        run_custom_config()
    else:
        print("Usage: python run_api.py [development|production|docker|custom]")
        print("\nExamples:")
        print("  python run_api.py development  # Run dev server on localhost:8000")
        print("  python run_api.py production   # Run production server with SSL")
        print("  python run_api.py docker       # Run in Docker/cloud mode")
        print("  python run_api.py custom       # Run with custom configuration")
        sys.exit(1)
