#!/usr/bin/env python
"""
Booklet Website - Main Entry Point
"""
import os
import sys

# Add parent directory to path for shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config import config

# Get configuration
env = os.environ.get('FLASK_ENV', 'development')
app = create_app()
app.config.from_object(config[env])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
