"""Check a DCS update for control changes: re-extract every module, regenerate every mapping, and report what changed against git HEAD.

Usage: python tools/checkDcsUpdate.py

Leaves the new extractions and mappings in the working tree for review, and records the DCS version in config/dcsVersionChecked.json when every extractor and mapper ran.
"""
import glob
import json
import os
import subprocess
import sys

repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repoRoot not in sys.path:
	sys.path.insert(0, repoRoot)

from utils.dcsVersion import readCheckedDcsVersion, readInstalledDcsVersion, writeCheckedDcsVersion

DCS_DIR = 'C:/Games/DCS World' # The extractors' default install folder.


def changedSections(old, new):
	"""Top-level sections of an extraction that differ, apart from the stats that count them."""
	return sorted(key for key in set(old) | set(new) if key != 'stats' and old.get(key) != new.get(key))


def isCockpitControl(control):
	return control.get('type') not in ('raw', 'readOnly', None)


def cockpitChanges(old, new):
	"""(removed, added, changed) clickable control names between two mappings' controls; raw and read-only churn is left out."""
	removed = sorted(name for name in set(old) - set(new) if isCockpitControl(old[name]))
	added = sorted(name for name in set(new) - set(old) if isCockpitControl(new[name]))
	changed = sorted(name for name in set(old) & set(new) if old[name] != new[name] and (isCockpitControl(old[name]) or isCockpitControl(new[name])))
	return removed, added, changed


def runTools(pattern):
	"""Run each matching tool script; prints and returns the ones that failed."""
	failures = []
	for script in sorted(glob.glob(os.path.join(repoRoot, 'tools', pattern))):
		name = os.path.basename(script)
		try:
			proc = subprocess.run([sys.executable, script], cwd=repoRoot, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=300)
		except subprocess.TimeoutExpired:
			print(f'  FAILED {name}: timed out')
			failures.append(name)
			continue
		if proc.returncode != 0:
			print(f'  FAILED {name}: exit {proc.returncode}')
			for line in proc.stderr.strip().splitlines()[-3:]:
				print(f'      {line}')
			failures.append(name)
	return failures


def changedFiles(relFolder):
	"""[(name, oldJson or None, newJson)] for the JSON files in relFolder that differ from git HEAD."""
	status = subprocess.run(['git', 'status', '--porcelain', '-z', '--', relFolder], capture_output=True, encoding='utf-8', cwd=repoRoot, check=True).stdout
	changes = []
	for entry in filter(None, status.split('\0')):
		relPath = entry[3:]
		if not relPath.endswith('.json'):
			continue
		with open(os.path.join(repoRoot, relPath), encoding='utf-8') as f:
			new = json.load(f)
		head = subprocess.run(['git', 'show', f'HEAD:{relPath}'], capture_output=True, encoding='utf-8', cwd=repoRoot)
		old = json.loads(head.stdout) if head.returncode == 0 else None
		if old != new:
			changes.append((os.path.basename(relPath)[:-len('.json')], old, new))
	return changes


def listNames(label, names):
	if names:
		shown = ', '.join(names[:10]) + (f', ... ({len(names)} in all)' if len(names) > 10 else '')
		print(f'      {label}: {shown}')


def main():
	installed = readInstalledDcsVersion(DCS_DIR)
	print(f'DCS {installed or "(version unknown)"}; mappings last checked against {readCheckedDcsVersion() or "(never)"}.')

	print('\nExtracting every module...')
	extractFailures = runTools('extraction-scripts/extract_*.py')
	extractions = changedFiles('config/nativeExtractions')
	for name, old, new in extractions:
		print(f'  {name}: ' + ('new extraction' if old is None else 'changed ' + ', '.join(changedSections(old, new))))
	if not extractions:
		print('  No extraction changed.')

	print('\nRegenerating every mapping...')
	mapFailures = runTools('mapping-scripts/map_*.py')
	mappings = changedFiles('config/controlMappings')
	reviewNames = []
	for name, old, new in mappings:
		if old is None:
			print(f'  {name}: new mapping')
			reviewNames.append(name)
			continue
		removed, added, changed = cockpitChanges(old.get('controls', {}), new.get('controls', {}))
		if removed or added or changed:
			print(f'  {name}: cockpit controls removed {len(removed)}, added {len(added)}, changed {len(changed)}')
			listNames('removed', removed)
			listNames('added', added)
			listNames('changed', changed)
			reviewNames.append(name)
		else:
			print(f'  {name}: raw / read-only changes only')
	if not mappings:
		print('  No mapping changed.')

	print("\nChecking every script's controls against its mapping...")
	tests = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'tests/test_scriptControls.py'], cwd=repoRoot, capture_output=True, text=True, encoding='utf-8', errors='replace')
	for line in tests.stdout.splitlines():
		if line.startswith('FAILED'):
			print(f'  {line}')
	print(f"  {tests.stdout.strip().splitlines()[-1] if tests.stdout.strip() else 'pytest gave no output'}")

	failed = extractFailures or mapFailures or tests.returncode != 0
	print()
	if installed and not (extractFailures or mapFailures):
		writeCheckedDcsVersion(installed)
		print(f'Recorded DCS {installed} in config/dcsVersionChecked.json.')
	if reviewNames:
		print('Details: python tools/diffCockpitControls.py ' + ' '.join(f'"{name}"' for name in reviewNames))
	if extractions or mappings:
		print('Review the changes with git diff, then commit config/nativeExtractions, config/controlMappings and config/dcsVersionChecked.json.')
	elif not failed:
		print('No control changes.  Commit config/dcsVersionChecked.json to record the check.')
	return 1 if failed else 0


if __name__ == '__main__':
	sys.exit(main())
