"""Compare a controlMappings JSON against the committed (HEAD) version.

Performs a logical comparison (ignoring key ordering) so regenerations
that only reorder JSON keys are correctly reported as unchanged.

Usage:
	python tools/compareControlMapping.py Ka-50
	python tools/compareControlMapping.py --all
	python tools/compareControlMapping.py Ka-50 --ref HEAD~1
	python tools/compareControlMapping.py Ka-50 --old path/to/old.json
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


def controlKey(ctrl):
	"""Return a stable sort key for a control dict (deep-sorted for consistency)."""
	return json.dumps(ctrl, sort_keys=True, ensure_ascii=False)


def compareControlMappings(fileName, oldData, newData):
	"""Print a structured diff of two controlMapping dicts. Returns True if any differences found."""
	anyDiff = False

	def flag(title):
		nonlocal anyDiff
		anyDiff = True
		print(f'\n  [{title}]')

	print(f'\n{"=" * 60}')
	print(f'  File: {fileName}')
	print(f'{"=" * 60}')

	# Module name.
	oldMod = oldData.get('moduleName', '?')
	newMod = newData.get('moduleName', '?')
	if oldMod != newMod:
		flag('moduleName')
		print(f'    {oldMod!r} -> {newMod!r}')
	else:
		print(f'  moduleName: {newMod!r}')

	oldControls = oldData.get('controls', {})
	newControls = newData.get('controls', {})

	oldIds = set(oldControls.keys())
	newIds = set(newControls.keys())
	addedIds = sorted(newIds - oldIds)
	removedIds = sorted(oldIds - newIds)
	commonIds = oldIds & newIds

	# Find controls whose content changed (key-order-insensitive deep compare).
	changed = []
	for cid in sorted(commonIds):
		ov = oldControls[cid]
		nv = newControls[cid]
		# Deep compare: serialize with sorted keys to ignore dict key order.
		if json.dumps(ov, sort_keys=True) != json.dumps(nv, sort_keys=True):
			changed.append(cid)

	if addedIds or removedIds or changed:
		flag('Controls')
		print(f'    Total: {len(oldControls)} -> {len(newControls)}')
		if addedIds:
			preview = addedIds[:5]
			more = f' (+{len(addedIds) - 5} more)' if len(addedIds) > 5 else ''
			print(f'    Added ({len(addedIds)}): {preview}{more}')
		if removedIds:
			preview = removedIds[:5]
			more = f' (+{len(removedIds) - 5} more)' if len(removedIds) > 5 else ''
			print(f'    Removed ({len(removedIds)}): {preview}{more}')
		if changed:
			print(f'    Changed ({len(changed)}):')
			for cid in changed[:10]:
				ov = oldControls[cid]
				nv = newControls[cid]
				# Show which fields differ.
				allKeys = sorted(set(list(ov.keys()) + list(nv.keys())))
				fieldDiffs = []
				for k in allKeys:
					if json.dumps(ov.get(k), sort_keys=True) != json.dumps(nv.get(k), sort_keys=True):
						fieldDiffs.append(f'{k}: {ov.get(k)!r} -> {nv.get(k)!r}')
				print(f'      {cid}:')
				for fd in fieldDiffs[:4]:
					print(f'        {fd}')
				if len(fieldDiffs) > 4:
					print(f'        ... and {len(fieldDiffs) - 4} more fields')
			if len(changed) > 10:
				print(f'    ... and {len(changed) - 10} more changed controls')
	else:
		print(f'  Controls: {len(newControls)} (unchanged)')

	if not anyDiff:
		print('  No differences found.')

	return anyDiff


def compareFile(fileName, ref, oldPath=None):
	"""Compare a single controlMapping file. Returns True if differences found."""
	repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
	relPath = f'config/controlMappings/{fileName}'
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
			print(f'  {fileName}: not found in git at ref {ref!r}, skipping.')
			return False
		with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as tf:
			tf.write(oldContent)
			tmpPath = tf.name
		try:
			oldData = loadJson(tmpPath)
		finally:
			os.unlink(tmpPath)

	return compareControlMappings(fileName, oldData, newData)


def main():
	parser = argparse.ArgumentParser(description='Compare controlMapping JSONs against a git ref.')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('file', nargs='?', help='JSON filename, e.g. Ka-50.json')
	group.add_argument('--all', action='store_true', help='Compare all files in config/controlMappings/')
	parser.add_argument('--ref', default='HEAD', help='Git ref to compare against (default: HEAD)')
	parser.add_argument('--old', metavar='PATH', help='Path to old JSON file (overrides --ref)')
	args = parser.parse_args()

	repoRoot = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

	if args.all:
		mappingsDir = os.path.join(repoRoot, 'config', 'controlMappings')
		files = sorted(f for f in os.listdir(mappingsDir) if f.endswith('.json'))
		if not files:
			print('No controlMapping JSON files found.')
			sys.exit(1)
		anyDiff = False
		for fileName in files:
			anyDiff |= compareFile(fileName, args.ref, args.old)
		sys.exit(0 if not anyDiff else 1)
	else:
		if not args.file:
			parser.error('Provide a filename or --all.')
		hasDiff = compareFile(args.file, args.ref, args.old)
		sys.exit(1 if hasDiff else 0)


if __name__ == '__main__':
	main()
