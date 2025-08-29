#!/usr/bin/env python3
"""
DLA CRM System - Main Application Entry Point
============================================

This is the main entry point for the DLA CRM system.
It imports and runs the Flask application from the src/core module.

Usage:
    python app.py                   # Start web server on localhost:5000
    python app.py --port 8080      # Start on custom port
    python app.py --debug          # Start in debug mode

Author: CDE Prosperity
Version: 2.0
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to Python path (not needed for root import)
# src_path = Path(__file__).parent / 'src'
# sys.path.insert(0, str(src_path))

def main():
    """Main application entry point"""
    parser = argparse.ArgumentParser(description='DLA CRM System')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on (default: 5000)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to (default: 127.0.0.1)')
    
    args = parser.parse_args()
    
    # Print startup banner
    print("=" * 60)
    print("DLA CRM SYSTEM - CDE Prosperity")
    print("=" * 60)
    print(f"🌐 Starting web server on http://{args.host}:{args.port}")
    print(f"🔧 Debug mode: {'ON' if args.debug else 'OFF'}")
    print("=" * 60)
    
    try:
        # Import the Flask app from root crm_app module
        import crm_app
        app = crm_app.app
        
        # Configure app paths
        app.config['TEMPLATES_AUTO_RELOAD'] = True
        
        # Start the Flask application
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Error importing application: {e}")
        print("Make sure all required modules are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
