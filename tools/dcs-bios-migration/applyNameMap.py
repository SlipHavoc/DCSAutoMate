#!/usr/bin/env python
"""Apply a nameMap JSON file to a Python script, renaming control references.

Uses longest-first word-boundary replacement to avoid partial matches.

Usage:
	python applyNameMap.py <nameMap.json> <script.py> [--dry-run]
"""

import argparse
import json
import re
import sys


def main():
	parser = argparse.ArgumentParser(description='Apply nameMap to a script file.')
	parser.add_argument('nameMap', help='Path to nameMap JSON file.')
	parser.add_argument('script', help='Path to script file to rename.')
	parser.add_argument('--dry-run', action='store_true', help='Show what would change without writing.')
	args = parser.parse_args()

	with open(args.nameMap) as f:
		nameMap = json.load(f)

	with open(args.script) as f:
		content = f.read()

	# Sort by longest old name first to avoid partial matches.
	sortedMap = sorted(nameMap.items(), key=lambda x: len(x[0]), reverse=True)

	totalReplacements = 0
	namesReplaced = 0
	for oldName, newName in sortedMap:
		# Word-boundary replacement: not preceded/followed by alphanumeric or underscore.
		pattern = r'(?<![a-zA-Z0-9_])' + re.escape(oldName) + r'(?![a-zA-Z0-9_])'
		matches = len(re.findall(pattern, content))
		if matches > 0:
			content = re.sub(pattern, newName, content)
			totalReplacements += matches
			namesReplaced += 1
			print(f'{oldName:40s} -> {newName} ({matches}x)')

	print(f'\nTotal: {namesReplaced} names, {totalReplacements} replacements')

	if args.dry_run:
		print('\n[DRY RUN] No changes written.')
	else:
		with open(args.script, 'w') as f:
			f.write(content)
		print(f'Written to {args.script}')


if __name__ == '__main__':
	main()
