# conftest.py — Auto-adds D:\pylibs to sys.path so spaCy and PyMuPDF are available
import sys
import os

extra_libs = r"D:\pylibs"
if os.path.isdir(extra_libs) and extra_libs not in sys.path:
    sys.path.insert(0, extra_libs)
