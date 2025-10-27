"""Launch script for Service20 FastAPI application."""

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """Launch the FastAPI application with uvicorn."""
    # Configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "true").lower() == "true"
    workers = int(os.getenv("API_WORKERS", 1))
    log_level = os.getenv("API_LOG_LEVEL", "info")

    print("=" * 80)
    print("Service20 Investment Opportunities API")
    print("=" * 80)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Reload: {reload}")
    print(f"Workers: {workers}")
    print(f"Log Level: {log_level}")
    print("=" * 80)
    print()
    print("🚀 Starting API server...")
    print()
    print("📊 Interactive API Documentation:")
    print(f"   - Swagger UI: http://localhost:{port}/docs")
    print(f"   - ReDoc: http://localhost:{port}/redoc")
    print()
    print("🔍 API Endpoints:")
    print(f"   - Health Check: http://localhost:{port}/health")
    print(f"   - Chat Query: http://localhost:{port}/chat/query")
    print(f"   - Root Info: http://localhost:{port}/")
    print()
    print("📝 Example Request:")
    print(f"""   curl -X POST http://localhost:{port}/chat/query \\
     -H "Content-Type: application/json" \\
     -d '{{"city": "Paris", "country_code": "FRA"}}'""")
    print()
    print("=" * 80)
    print()

    # Launch uvicorn
    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            workers=workers if not reload else 1,  # Workers not supported with reload
            log_level=log_level,
            access_log=True,
            use_colors=True
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped gracefully")
    except Exception as e:
        print(f"\n\n✗ Error starting server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
