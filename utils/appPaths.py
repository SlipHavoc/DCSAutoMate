import os
import sys


def appBaseDir():
	"""The folder holding config/, docs/ and Scripts/: the exe's folder when packaged (PyInstaller unpacks the code to a temp folder), else the repo root."""
	if getattr(sys, 'frozen', False):
		return os.path.dirname(os.path.abspath(sys.executable))
	return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
