#!/usr/bin/env python3
"""
Entrypoint script for Railway deployment.
Reads PORT from environment variable and starts uvicorn.
"""
import os
import sys
import subprocess

def main():
    # Debug: print all environment variables
    print("=== DEBUG: Environment Variables ===")
    for key, value in os.environ.items():
        if key in ['PORT', 'RAILWAY_']:
            print(f"{key} = {value}")
    print("====================================")

    port = os.environ.get("PORT", "8000")
    print(f"Starting uvicorn on port {port}")
    print(f"Port type: {type(port)}")
    print(f"Port value repr: {repr(port)}")

    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", str(port)  # Explicitly convert to string
    ]

    print(f"Running command: {' '.join(cmd)}")
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
