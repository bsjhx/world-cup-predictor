#!/usr/bin/env python3
"""
Convenience wrapper to run main.py from project root
Usage: python main.py <args>
"""
import subprocess
import sys

if __name__ == "__main__":
    # Run the src/main.py with the same arguments
    result = subprocess.run([sys.executable, "src/main.py"] + sys.argv[1:])
    sys.exit(result.returncode)
