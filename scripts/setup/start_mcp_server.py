"""Startup script for Digital FTE MCP server.

Launches the FastAPI MCP server with uvicorn.
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def main():
    """Main entry point for MCP server."""
    parser = argparse.ArgumentParser(
        description="Start Digital FTE MCP server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Digital FTE MCP Server")
    print("=" * 60)
    print(f"Starting server on {args.host}:{args.port}")
    print(f"Auto-reload: {'enabled' if args.reload else 'disabled'}")
    print()
    print("Available endpoints:")
    print(f"  - Health check: http://{args.host}:{args.port}/health")
    print(f"  - List tools: http://{args.host}:{args.port}/tools/list")
    print(f"  - Invoke tool: http://{args.host}:{args.port}/tools/invoke")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    # Import and run uvicorn
    import uvicorn
    uvicorn.run(
        "mcp_servers.digital_fte_server.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
