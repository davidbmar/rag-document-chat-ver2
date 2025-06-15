#!/usr/bin/env python3
"""
RAG Document Chat System - Main Entry Point
"""

import sys
import logging
from pathlib import Path

# Add src to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False
    st = None

from core.utils import print_usage, setup_logging
from core.config import core.config

logger = setup_logging()


def main():
    """Main application entry point"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "streamlit":
            if not STREAMLIT_AVAILABLE:
                print("Streamlit is not installed. Please install it with: pip install streamlit")
                print("Or run the API server with: python -m src.main api")
                return
            from ui.streamlit_app import create_streamlit_app
            create_streamlit_app()
            
        elif sys.argv[1] == "api":
            import uvicorn
            from api.app import app
            logger.info(f"🚀 Starting FastAPI server on {config.api_host}:{config.api_port}...")
            uvicorn.run(app, host=config.api_host, port=config.api_port)
            
        else:
            print_usage()
    else:
        # Default behavior - check what's available
        if STREAMLIT_AVAILABLE:
            from ui.streamlit_app import create_streamlit_app
            create_streamlit_app()
        else:
            print("Streamlit not available. Starting API server instead...")
            print(f"Access the API at: {config.api_url}")
            print(f"API docs at: {config.api_url}/docs")
            import uvicorn
            from api.app import app
            uvicorn.run(app, host=config.api_host, port=config.api_port)


if __name__ == "__main__":
    main()