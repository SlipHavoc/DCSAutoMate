"""Compare a nativeExtractions JSON against the committed (HEAD) version.

Usage:
	python tools/compareExtraction.py A-10C
	python tools/compareExtraction.py --all
	python tools/compareExtraction.py A-10C --ref main
	python tools/compareExtraction.py A-10C --old path/to/old.json

When comparing against git HEAD (default), the committed version is fetched
via `git show HEAD:...` and written to a temp file.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile


def loadJson(path):
	with open(path, 'r', encoding='utf-8') as f:
		return json.load(f)


def gitShow(ref, repoRelPath):
	"""Return the JSON content of a file at a given git ref, or None if not found."""
	result = subprocess.run(
		['git', 'show', f'{ref}:{repoRelPath}'],
		capture_output=True,
		text=True,
		encoding='utf-8',
	)
	if result.returncode != 0:
		return None
	return result.stdout


def getIndicatorFields(ind):
	"""Return the fields list from an indicator dict, handling both key names."""
	return ind.get('fields', ind.get('textFields', []))


def compareExtractions(moduleName, oldData, newData):
	"""Print a structured diff of two nativeExtraction dicts. Returns True if any differences found."""
	anyDiff = False

	def section(title):
		nonlocal anyDiff
		anyDiff = True
		print(f'\n  [{title}]')

	print(f'\n{"=" * 60}')
	print(f'  Module: {moduleName}')
	print(f'{"=" * 60}')

	# --- Devices ---
	oldDevs = oldData.get('devices', {})
	newDevs = newData.get('devices', {})
	addedDevs = sorted(set(newDevs) - set(oldDevs))
	removedDevs = sorted(set(oldDevs) - set(newDevs))
	changedDevs = sorted(k for k in set(oldDevs) & set(newDevs) if oldDevs[k] != newDevs[k])
	if addedDevs or removedDevs or changedDevs:
		section('Devices')
		if addedDevs:
			print(f'    Added ({len(addedDevs)}): {addedDevs}')
		if removedDevs:
			print(f'    Removed ({len(removedDevs)}): {removedDevs}')
		for k in changedDevs:
			print(f'    Changed: {k} {oldDevs[k]} -> {newDevs[k]}')
	else:
		print(f'  Devices: {len(newDevs)} (unchanged)')

	# --- Elements ---
	oldElems = oldData.get('elements', {})
	newElems = newData.get('elements', {})
	addedElems = sorted(set(newElems) - set(oldElems))
	removedElems = sorted(set(oldElems) - set(newElems))
	changedElems = [k for k in set(oldElems) & set(newElems) if oldElems[k] != newElems[k]]
	if addedElems or removedElems or changedElems:
		section('Elements')
		print(f'    Count: {len(oldElems)} -> {len(newElems)}')
		if addedElems:
			preview = addedElems[:5]
			more = f' (+{len(addedElems)-5} more)' if len(addedElems) > 5 else ''
			print(f'    Added ({len(addedElems)}): {preview}{more}')
		if removedElems:
			preview = removedElems[:5]
			more = f' (+{len(removedElems)-5} more)' if len(removedElems) > 5 else ''
			print(f'    Removed ({len(removedElems)}): {preview}{more}')
		if changedElems:
			print(f'    Value changes: {len(changedElems)}')
			for k in changedElems[:3]:
				print(f'      {k}: {oldElems[k]} -> {newElems[k]}')
			if len(changedElems) > 3:
				print(f'      ... and {len(changedElems)-3} more')
	else:
		print(f'  Elements: {len(newElems)} (unchanged)')

	# --- Command Tables ---
	oldCt = oldData.get('commandTables', {})
	newCt = newData.get('commandTables', {})
	if set(oldCt.keys()) != set(newCt.keys()) or oldCt != newCt:
		addedCt = sorted(set(newCt) - set(oldCt))
		removedCt = sorted(set(oldCt) - set(newCt))
		changedCt = [k for k in set(oldCt) & set(newCt) if oldCt[k] != newCt[k]]
		section('Command Tables')
		print(f'    Count: {len(oldCt)} -> {len(newCt)}')
		if addedCt:
			print(f'    Added: {addedCt}')
		if removedCt:
			print(f'    Removed: {removedCt}')
		if changedCt:
			print(f'    Changed: {changedCt}')
	else:
		print(f'  Command Tables: {len(newCt)} (unchanged)')

	# --- Indicators ---
	oldInds = {i['index']: i for i in oldData.get('indicators', [])}
	newInds = {i['index']: i for i in newData.get('indicators', [])}
	oldTotalFields = sum(len(getIndicatorFields(i)) for i in oldInds.values())
	newTotalFields = sum(len(getIndicatorFields(i)) for i in newInds.values())
	addedInds = sorted(set(newInds) - set(oldInds))
	removedInds = sorted(set(oldInds) - set(newInds))
	# Per-indicator changes (ignoring fields key name difference)
	indChanges = []
	for idx in sorted(set(oldInds) & set(newInds)):
		oi = oldInds[idx]
		ni = newInds[idx]
		changes = []
		for key in set(list(oi.keys()) + list(ni.keys())) - {'fields', 'textFields'}:
			if oi.get(key) != ni.get(key):
				changes.append(f'{key}: {oi.get(key)!r} -> {ni.get(key)!r}')
		ofields = len(getIndicatorFields(oi))
		nfields = len(getIndicatorFields(ni))
		if ofields != nfields:
			changes.append(f'fields: {ofields} -> {nfields}')
		if changes:
			indChanges.append((idx, ni.get('initFile', ''), changes))

	if addedInds or removedInds or indChanges or (oldTotalFields != newTotalFields):
		section('Indicators')
		print(f'    Count: {len(oldInds)} -> {len(newInds)}')
		print(f'    Total text fields: {oldTotalFields} -> {newTotalFields}')
		for idx in addedInds:
			print(f'    Added: index {idx} {newInds[idx].get("initFile","")} ({len(getIndicatorFields(newInds[idx]))} fields)')
		for idx in removedInds:
			print(f'    Removed: index {idx} {oldInds[idx].get("initFile","")}')
		for idx, initFile, changes in indChanges:
			print(f'    index {idx} {initFile[:45]}:')
			for c in changes:
				print(f'      {c}')
	else:
		print(f'  Indicators: {len(newInds)}, {newTotalFields} text fields (unchanged)')

	# --- Gauges and Lamps ---
	oldG = oldData.get('gaugesAndLamps', [])
	newG = newData.get('gaugesAndLamps', [])
	if len(oldG) != len(newG) or oldG != newG:
		section('Gauges and Lamps')
		print(f'    Count: {len(oldG)} -> {len(newG)}')
		oldNames = {g['name'] for g in oldG}
		newNames = {g['name'] for g in newG}
		addedG = sorted(newNames - oldNames)
		removedG = sorted(oldNames - newNames)
		if addedG:
			print(f'    Added ({len(addedG)}): {addedG[:5]}{"..." if len(addedG)>5 else ""}')
		if removedG:
			print(f'    Removed ({len(removedG)}): {removedG[:5]}{"..." if len(removedG)>5 else ""}')
	else:
		print(f'  Gauges and Lamps: {len(newG)} (unchanged)')

	# --- Equipment Properties ---
	oldEp = oldData.get('equipmentProperties', [])
	newEp = newData.get('equipmentProperties', [])
	if set(oldEp) != set(newEp):
		section('Equipment Properties')
		added = sorted(set(newEp) - set(oldEp))
		removed = sorted(set(oldEp) - set(newEp))
		if added:
			print(f'    Added: {added}')
		if removed:
			print(f'    Removed: {removed}')
	else:
		print(f'  Equipment Properties: {len(newEp)} (unchanged)')

	# --- Stats ---
	oldStats = oldData.get('stats', {})
	newStats = newData.get('stats', {})
	allStatKeys = sorted(set(list(oldStats.keys()) + list(newStats.keys())))
	statChanges = [(k, oldStats.get(k, '?'), newStats.get(k, '?')) for k in allStatKeys if oldStats.get(k) != newStats.get(k)]
	if statChanges:
		section('Stats')
		for k, ov, nv in statChanges:
			print(f'    {k}: {ov} -> {nv}')
	else:
		print(f'  Stats: unchanged')

	if not anyDiff:
		print('  No differences found.')

	return anyDiff


def compareModule(moduleName, ref, oldPath=None):
	"""Compare a single module. Returns True if differences found."""
	repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	relPath = f'config/nativeExtractions/{moduleName}.json'
	newPath = os.path.join(repoRoot, relPath)

	if not os.path.exists(newPath):
		print(f'Error: {newPath} not found.')
		return False

	newData = loadJson(newPath)

	if oldPath:
		if not os.path.exists(oldPath):
			print(f'Error: --old path not found: {oldPath}')
			return False
		oldData = loadJson(oldPath)
	else:
		oldContent = gitShow(ref, relPath.replace('\\', '/'))
		if oldContent is None:
			print(f'  {moduleName}: not found in git at ref {ref!r}, skipping.')
			return False
		# Write to a temp file so json.loads handles encoding correctly.
		with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tf:
			tf.write(oldContent)
			tmpPath = tf.name
		try:
			oldData = loadJson(tmpPath)
		finally:
			os.unlink(tmpPath)

	return compareExtractions(moduleName, oldData, newData)


def main():
	parser = argparse.ArgumentParser(description='Compare nativeExtraction JSONs against a git ref.')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('module', nargs='?', help='Module name, e.g. A-10C')
	group.add_argument('--all', action='store_true', help='Compare all modules in config/nativeExtractions/')
	parser.add_argument('--ref', default='HEAD', help='Git ref to compare against (default: HEAD)')
	parser.add_argument('--old', metavar='PATH', help='Path to old JSON file (overrides --ref)')
	args = parser.parse_args()

	repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

	if args.all:
		repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
		extractionsDir = os.path.join(repoRoot, 'config', 'nativeExtractions')
		modules = sorted(
			os.path.splitext(f)[0]
			for f in os.listdir(extractionsDir)
			if f.endswith('.json')
		)
		if not modules:
			print('No extraction JSON files found.')
			sys.exit(1)
		anyDiff = False
		for moduleName in modules:
			anyDiff |= compareModule(moduleName, args.ref, args.old)
		sys.exit(0 if not anyDiff else 1)
	else:
		if not args.module:
			parser.error('Provide a module name or --all.')
		hasDiff = compareModule(args.module, args.ref, args.old)
		sys.exit(1 if hasDiff else 0)


if __name__ == '__main__':
	main()
