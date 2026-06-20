"""
Ensures `backend/` (this file's directory) is on sys.path during test
collection, so test modules can `from evaluation.metrics import ...` etc.
without needing the package installed. Pytest auto-loads conftest.py files
and adds their directory to sys.path.
"""
