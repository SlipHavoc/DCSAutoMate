"""Which DCS version the committed control extractions and mappings were last checked against, and whether DCS has been updated since."""
import json
import os

CHECKED_VERSION_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'dcsVersionChecked.json')


def dcsInstallDir(dcsExePath):
	"""The DCS install folder for .../bin/DCS.exe or .../bin-mt/DCS.exe, or None."""
	if not dcsExePath:
		return None
	return os.path.dirname(os.path.dirname(os.path.normpath(dcsExePath)))


def readInstalledDcsVersion(dcsDir):
	"""The installed DCS version from its autoupdate.cfg, or None if it can't be read."""
	if not dcsDir:
		return None
	try:
		with open(os.path.join(dcsDir, 'autoupdate.cfg'), encoding='utf-8') as f:
			return json.load(f).get('version')
	except (OSError, ValueError):
		return None


def readCheckedDcsVersion(path=CHECKED_VERSION_FILE):
	try:
		with open(path, encoding='utf-8') as f:
			return json.load(f).get('version')
	except (OSError, ValueError):
		return None


def writeCheckedDcsVersion(version, path=CHECKED_VERSION_FILE):
	with open(path, 'w', encoding='utf-8') as f:
		json.dump({'version': version}, f, indent='\t')
		f.write('\n')


def dcsUpdateNotice(installedVersion, checkedVersion):
	"""A reminder to run the update check if DCS has changed since the control mappings were last checked, else None."""
	if not installedVersion or installedVersion == checkedVersion:
		return None
	checked = f'were last checked against DCS {checkedVersion}' if checkedVersion else "haven't been checked against it yet"
	return f'DCS is now {installedVersion}, and the control mappings {checked}.  Run "python tools/checkDcsUpdate.py" to check for control changes.'
