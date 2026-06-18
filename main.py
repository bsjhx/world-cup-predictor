#!/usr/bin/env python3
"""
Convenience wrapper to run src/main.py from project root
Usage: python main.py <command> <args>
"""
import subprocess
import sys

if __name__ == "__main__":
    result = subprocess.run([sys.executable, "-m", "src.main"] + sys.argv[1:])
    sys.exit(result.returncode)
