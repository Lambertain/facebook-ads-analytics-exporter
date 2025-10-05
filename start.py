#!/usr/bin/env python3
"""
Entrypoint script for Railway deployment.
Reads PORT from environment variable and starts uvicorn.
"""
import os
import sys
import subprocess

def main():
    port = os.environ.get("PORT", "8000")
    print(f"Starting uvicorn on port {port}")
    
    cmd = [
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", port
    ]
    
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
