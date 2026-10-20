# -*- coding: utf-8 -*-
"""
Entry point for python -m traffic_stats
"""
import sys
from .orchestrator import main

if __name__ == "__main__":
    sys.exit(main())
