#!/usr/bin/env python
"""Build BIOS-name → canonical mapping for Mi-8MT.

Parses the DCS BIOS Mi-8MT.lua module file (line-based regex; the file is
uniform: every Mi_8MT:defineXXX("NAME", dev, cmd, arg, ...) is on a single
line). Joins captured (deviceId, commandId, arg) triples against the
canonical control mapping at config/controlMappings/Mi-8MT.json.

Outputs (under tools/):
- biosNameMap_Mi-8MT.json — confident BIOS_NAME → canonical mapping.
- biosNameMap_Mi-8MT.unmapped.json — BIOS entries with no canonical
  match, recorded as { BIOS_NAME: { dev, cmd, arg, kind } } for review.
- biosNameMap_Mi-8MT.audit.md — multi-position discrete controls whose
  position label list is available in BIOS Lua, shown alongside the
  canonical positionMap so the integer values used by Mi-8MTV2.py can
  be manually verified.

Usage:
	python tools/buildBiosNameMap_Mi8MT.py
"""

import json
import re
import sys
from pathlib import Path


BIOS_LUA = Path('C:/Workspace/DCS related/DCS-BIOS from Saved Games/DCS-BIOS/lib/modules/aircraft_modules/Mi-8MT.lua')
MAPPING_JSON = Path('config/controlMappings/Mi-8MT.json')
OUT_DIR = Path('tools')
OUT_MAP = OUT_DIR / 'biosNameMap_Mi-8MT.json'
OUT_UNMAPPED = OUT_DIR / 'biosNameMap_Mi-8MT.unmapped.json'
OUT_AUDIT = OUT_DIR / 'biosNameMap_Mi-8MT.audit.md'

# Captures `Mi_8MT:defineKIND("NAME", dev, cmd, arg, ...)`. Skips lines
# whose first non-whitespace chars are `--` (commented-out defines).
DEFINE_RE = re.compile(
	r'^\s*Mi_8MT:define(\w+)\(\s*"([A-Z][A-Z0-9_]*)"\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\b'
)
POSITIONS_RE = re.compile(r'positions\s*=\s*\{\s*((?:"[^"]*"\s*,?\s*)+)\}')
LABEL_RE = re.compile(r'"([^"]*)"')


def parseBiosLua(path):
	"""Yield dicts for every define call in the BIOS Lua file."""
	defines = []
	for lineno, raw in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
		# Skip commented-out lines.
		stripped = raw.lstrip()
		if stripped.startswith('--'):
			continue
		m = DEFINE_RE.match(raw)
		if not m:
			continue
		kind, name, dev, cmd, arg = m.groups()
		positions = None
		pm = POSITIONS_RE.search(raw)
		if pm:
			positions = LABEL_RE.findall(pm.group(1))
		defines.append({
			'name': name,
			'kind': kind,
			'dev': int(dev),
			'cmd': int(cmd),
			'arg': int(arg),
			'positions': positions,
			'lineno': lineno,
		})
	return defines


def buildIndexes(mapping):
	"""Return (byTriple, byPair) indexes.

	byTriple: {(dev, cmd, arg): [(canonical, entry)]}
	byPair:   {(dev, cmd): [(arg, canonical, entry)]}
	"""
	byTriple = {}
	byPair = {}
	for canonical, entry in mapping.get('controls', {}).items():
		dev = entry.get('deviceId')
		cmd = entry.get('commandId')
		arg = entry.get('arg')
		if dev is None or cmd is None:
			continue
		byPair.setdefault((dev, cmd), []).append((arg, canonical, entry))
		if arg is not None:
			byTriple.setdefault((dev, cmd, arg), []).append((canonical, entry))
	return byTriple, byPair


def pickPreferred(entries):
	"""From a list of (canonical, entry) tuples, prefer non-inferred. Return one canonical or None if ambiguous."""
	nonInferred = [(c, e) for c, e in entries if not e.get('inferred')]
	pool = nonInferred or entries
	if len(pool) == 1:
		return pool[0][0]
	# Multiple non-inferred matches → ambiguous; caller decides.
	return None


def resolve(biosEntry, byTriple, byPair):
	"""Return (canonical, reason) or (None, reason)."""
	dev, cmd, arg = biosEntry['dev'], biosEntry['cmd'], biosEntry['arg']
	# Step 1: exact triple.
	hits = byTriple.get((dev, cmd, arg))
	if hits:
		canonical = pickPreferred(hits)
		if canonical:
			return canonical, 'triple'
		return None, f'triple-ambiguous:{[c for c, _ in hits]}'
	# Step 2: pair fallback (BIOS arg differs from canonical arg, e.g. BIOS
	# uses command-pulse arg while canonical uses display arg).
	pairHits = byPair.get((dev, cmd))
	if pairHits:
		nonInferred = [(c, e) for a, c, e in pairHits if not e.get('inferred')]
		pool = nonInferred or [(c, e) for a, c, e in pairHits]
		if len(pool) == 1:
			return pool[0][0], 'pair'
		return None, f'pair-ambiguous:{[c for c, _ in pool]}'
	return None, 'no-match'


def buildAuditEntries(defines, mapping, nameMap):
	"""Return audit list: BIOS multi-position controls with their label list and canonical positionMap (if any)."""
	controls = mapping.get('controls', {})
	audit = []
	for d in defines:
		if not d['positions'] or len(d['positions']) <= 2:
			continue
		canonical = nameMap.get(d['name'])
		if not canonical:
			continue
		entry = controls.get(canonical, {})
		canonicalPositionMap = entry.get('positionMap')
		canonicalPositions = entry.get('positions')
		audit.append({
			'biosName': d['name'],
			'canonical': canonical,
			'biosPositions': d['positions'],
			'canonicalPositions': canonicalPositions,
			'canonicalPositionMap': canonicalPositionMap,
		})
	return audit


def writeAudit(path, audit):
	lines = [
		'# Mi-8MT multi-position discrete audit',
		'',
		'For each control, verify that the integer position index used in `Mi-8MTV2.py`',
		'still selects the intended cockpit position under the canonical positionMap.',
		'BIOS positions are listed in the order DCS BIOS enumerated them; canonical',
		'positionMap (when present) reflects the new mapping order.',
		'',
	]
	for a in audit:
		lines.append(f"## `{a['biosName']}` → `{a['canonical']}`")
		lines.append('')
		lines.append('BIOS positions:')
		for i, label in enumerate(a['biosPositions']):
			lines.append(f'- {i}: {label}')
		lines.append('')
		if a['canonicalPositionMap']:
			lines.append('Canonical positionMap:')
			for i, p in enumerate(a['canonicalPositionMap']):
				lines.append(f'- {i}: {p}')
		elif a['canonicalPositions']:
			lines.append(f"Canonical positions count: {a['canonicalPositions']}")
		else:
			lines.append('Canonical positionMap: (none — positions inferred by step/argLim)')
		lines.append('')
	path.write_text('\n'.join(lines), encoding='utf-8')


def main():
	if not BIOS_LUA.exists():
		print(f'BIOS Lua not found: {BIOS_LUA}', file=sys.stderr)
		return 1
	if not MAPPING_JSON.exists():
		print(f'Mapping JSON not found: {MAPPING_JSON}', file=sys.stderr)
		return 1

	defines = parseBiosLua(BIOS_LUA)
	mapping = json.loads(MAPPING_JSON.read_text(encoding='utf-8'))
	byTriple, byPair = buildIndexes(mapping)

	nameMap = {}
	unmapped = {}
	tripleCount = 0
	pairCount = 0
	for d in defines:
		canonical, reason = resolve(d, byTriple, byPair)
		if canonical:
			# In case of duplicate BIOS names (shouldn't happen), keep first.
			if d['name'] not in nameMap:
				nameMap[d['name']] = canonical
				if reason == 'triple':
					tripleCount += 1
				elif reason == 'pair':
					pairCount += 1
		else:
			unmapped[d['name']] = {
				'dev': d['dev'],
				'cmd': d['cmd'],
				'arg': d['arg'],
				'kind': d['kind'],
				'lineno': d['lineno'],
				'reason': reason,
			}

	audit = buildAuditEntries(defines, mapping, nameMap)

	OUT_DIR.mkdir(parents=True, exist_ok=True)
	OUT_MAP.write_text(json.dumps(nameMap, indent='\t', sort_keys=True), encoding='utf-8')
	OUT_UNMAPPED.write_text(json.dumps(unmapped, indent='\t', sort_keys=True), encoding='utf-8')
	writeAudit(OUT_AUDIT, audit)

	print(f'BIOS defines parsed: {len(defines)}')
	print(f'  triple-matched:    {tripleCount}')
	print(f'  pair-matched:      {pairCount}')
	print(f'  unmapped:          {len(unmapped)}')
	print(f'  audit (multi-pos): {len(audit)}')
	print(f'Wrote {OUT_MAP}')
	print(f'Wrote {OUT_UNMAPPED}')
	print(f'Wrote {OUT_AUDIT}')
	return 0


if __name__ == '__main__':
	sys.exit(main())
