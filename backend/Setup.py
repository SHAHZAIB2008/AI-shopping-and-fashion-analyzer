#!/usr/bin/env python3
"""
Setup Script for AI Fashion Analyzer with Web Scraping
This script helps set up the complete environment for the fashion analyzer.
"""

import subprocess
import sys
import os
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_command(command, description=""):
    """Run a command and handle errors"""
    try:
        logger.info(f"Running: {description or command}")
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Command failed: {command}")
            logger.error(f"Error: {result.stderr}")
            return False
        logger.info(f"Success: {description or command}")
        return True
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        logger.error("Python 3.8 or higher is required")
        return False
    logger.info(f"Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def install_requirements():
    """Install Python requirements"""
    logger.info("Installing Python dependencies...")
    
    requirements = [
        "fastapi==0.104.1",
        "uvicorn==0.24.0", 
        "streamlit==1.28.1",
        "python-multipart==0.0.6",
        "Pillow==10.4.0"]