"""Pytest bootstrap shared by GUI and non-GUI tests."""

import os


# This must be set before pytest imports any PySide6 test module. Individual
# modules keep their own fallback so unittest discovery remains supported.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
