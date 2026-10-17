"""Paths written into extraction JSON must not contain the user's profile folder (it holds their Windows user name)."""
import os
import sys

EXTRACTION_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'extraction-scripts'))
if EXTRACTION_DIR not in sys.path:
	sys.path.insert(0, EXTRACTION_DIR)

from extractUtils import portableUserPath

PROFILE = r'C:\Users\Pilot'


def test_profilePrefixBecomesEnvVar():
	path = r'C:\Users\Pilot\Saved Games\DCS\Mods\aircraft\A-4E-C\Cockpit\Scripts'
	assert portableUserPath(path, PROFILE) == r'%USERPROFILE%\Saved Games\DCS\Mods\aircraft\A-4E-C\Cockpit\Scripts'


def test_matchIgnoresCaseAndSlashDirection():
	assert portableUserPath('c:/users/pilot/Saved Games/DCS', PROFILE) == r'%USERPROFILE%\Saved Games\DCS'


def test_profileItselfBecomesEnvVar():
	assert portableUserPath(PROFILE, PROFILE) == '%USERPROFILE%'


def test_pathOutsideProfileIsUnchanged():
	path = r'C:\Games\DCS World\Mods\aircraft\FA-18C\Cockpit\Scripts'
	assert portableUserPath(path, PROFILE) == path


def test_siblingFolderSharingThePrefixIsUnchanged():
	path = r'C:\Users\Pilot2\Saved Games\DCS'
	assert portableUserPath(path, PROFILE) == path


def test_noProfileLeavesPathUnchanged():
	path = r'C:\Users\Pilot\Saved Games\DCS'
	assert portableUserPath(path, '') == path
