"""The app version lives in utils/version.py; the README heading must agree with it."""
import os
import re

from utils.version import APP_VERSION

README = os.path.join(os.path.dirname(__file__), '..', 'README.md')


def test_versionIsMajorMinorPatch():
	assert re.fullmatch(r'\d+\.\d+\.\d+', APP_VERSION)


def test_readmeHeadingShowsTheVersion():
	with open(README, encoding='utf-8') as f:
		firstLine = f.readline().strip()
	assert firstLine == f'# DCSAutoMate {APP_VERSION}'
