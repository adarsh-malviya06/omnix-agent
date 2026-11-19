"""
Root conftest.py — ensures the project root is on sys.path so that
'omnix' is importable when pytest is invoked as plain 'pytest' or
'python -m pytest' from any working directory.
"""
import sys
import os

# Insert the project root (directory containing this file) at the front of
# sys.path if it is not already there.
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Ensure local HuggingFace cache is used without waiting for network timeouts
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


