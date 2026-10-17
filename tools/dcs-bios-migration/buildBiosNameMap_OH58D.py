#!/usr/bin/env python
"""Build BIOS-name → canonical mapping for OH-58D.

Parses the DCS BIOS OH-58D.lua module file.  Key difference from Ka-50: device
IDs in OH-58D.lua are symbolic (`devices.ELECTRIC`) rather than numeric.  The
script first extracts the `local devices = { ... }` table to build a
deviceName → numericId lookup, then applies it when parsing define calls.

The define regex captures two numeric args after the device.  For standard
single-command defines (toggleSwitch, pushButton, etc.) these are (cmd, arg).
For two-command spring-loaded defines (defineSpringloaded_3PosTumb,
defineTumbSwitch3, etc.) they are (cmd1, cmd2) — the arg follows as a *third*
number that falls outside the capture.  In that case the triple lookup (dev,
cmd1, cmd2) will fail to match, and the resolver falls back to pair lookup
(dev, cmd1), which uniquely identifies the control.

Outputs (under tools/dcs-bios-migration/):
- biosNameMap_OH-58D.json     — confident BIOS_NAME → canonical mapping.
- biosNameMap_OH-58D.unmapped.json — BIOS entries with no canonical match.
- biosNameMap_OH-58D.audit.md — multi-position discrete controls with BIOS
  position labels alongside canonical positionMap for manual verification.

Usage:
	python tools/dcs-bios-migration/buildBiosNameMap_OH58D.py
"""

import json
import re
import sys
from pathlib import Path


BIOS_LUA = Path('C:/Workspace/DCS related/DCS-BIOS from Saved Games/DCS-BIOS/lib/modules/aircraft_modules/OH-58D.lua')
MAPPING_JSON = Path('config/controlMappings/OH-58D.json')
OUT_DIR = Path('tools/dcs-bios-migration')
OUT_MAP = OUT_DIR / 'biosNameMap_OH-58D.json'
OUT_UNMAPPED = OUT_DIR / 'biosNameMap_OH-58D.unmapped.json'
OUT_AUDIT = OUT_DIR / 'biosNameMap_OH-58D.audit.md'

# Matches lines inside `local devices = { ... }`: `  ELECTRIC = 7,`
DEVICE_ENTRY_RE = re.compile(r'^\s+(\w+)\s*=\s*(\d+)\s*,?\s*$')

# Matches OH_58D:defineXXX("NAME", devices.DEVNAME, num1, num2, ...).
# For single-command defines: num1=cmd, num2=arg.
# For two-command spring-loaded: num1=cmd1, num2=cmd2 (arg is 3rd number).
DEFINE_RE = re.compile(
	r'^\s*OH_58D:define(\w+)\(\s*"([A-Z][A-Z0-9_]*)"\s*,\s*devices\.(\w+)\s*,\s*(\d+)\s*,\s*(\d+)\b'
)

POSITIONS_RE = re.compile(r'positions\s*=\s*\{\s*((?:"[^"]*"\s*,?\s*)+)\}')
LABEL_RE = re.compile(r'"([^"]*)"')


def parseDeviceTable(text):
	"""Extract `local devices = { ... }` and return {name: numericId}."""
	devices = {}
	inBlock = False
	for line in text.splitlines():
		if re.match(r'\s*local\s+devices\s*=\s*\{', line):
			inBlock = True
			continue
		if inBlock:
			if line.strip() == '}':
				break
			m = DEVICE_ENTRY_RE.match(line)
			if m:
				devices[m.group(1)] = int(m.group(2))
	return devices


def parseBiosLua(path, deviceTable):
	"""Yield dicts for every define call in the BIOS Lua file."""
	defines = []
	text = path.read_text(encoding='utf-8')
	for lineno, raw in enumerate(text.splitlines(), 1):
		stripped = raw.lstrip()
		if stripped.startswith('--'):
			continue
		m = DEFINE_RE.match(raw)
		if not m:
			continue
		kind, name, devName, num1, num2 = m.groups()
		devId = deviceTable.get(devName)
		if devId is None:
			continue  # Unknown device — skip (not a cockpit element).
		positions = None
		pm = POSITIONS_RE.search(raw)
		if pm:
			positions = LABEL_RE.findall(pm.group(1))
		defines.append({
			'name': name,
			'kind': kind,
			'devName': devName,
			'dev': devId,
			'cmd': int(num1),
			'arg': int(num2),  # May be cmd2 for two-command defines.
			'positions': positions,
			'lineno': lineno,
		})
	return defines


def buildIndexes(mapping):
	"""Return (byTriple, byPair) indexes from the canonical control mapping.

	byTriple: {(dev, cmd, arg): [(canonical, entry)]}
	byPair:   {(dev, cmd): [(arg, canonical, entry)]}

	Indexes both top-level deviceId/commandId and positionMap entries so that
	multi-position discrete controls are reachable via either sub-command.
	"""
	byTriple = {}
	byPair = {}
	for canonical, entry in mapping.get('controls', {}).items():
		dev = entry.get('deviceId')
		cmd = entry.get('commandId')
		arg = entry.get('arg')
		if dev is not None and cmd is not None:
			byPair.setdefault((dev, cmd), []).append((arg, canonical, entry))
			if arg is not None:
				byTriple.setdefault((dev, cmd, arg), []).append((canonical, entry))
		for pm in entry.get('positionMap') or []:
			if not isinstance(pm, dict):
				continue
			pmDev = pm.get('deviceId')
			pmCmd = pm.get('commandId')
			if pmDev is None or pmCmd is None:
				continue
			byPair.setdefault((pmDev, pmCmd), []).append((arg, canonical, entry))
			if arg is not None:
				byTriple.setdefault((pmDev, pmCmd, arg), []).append((canonical, entry))
	# Deduplicate (a positionMap entry may add the same canonical multiple times).
	for k, v in list(byTriple.items()):
		seen = set(); dedup = []
		for c, e in v:
			if c not in seen:
				seen.add(c); dedup.append((c, e))
		byTriple[k] = dedup
	for k, v in list(byPair.items()):
		seen = set(); dedup = []
		for a, c, e in v:
			if c not in seen:
				seen.add(c); dedup.append((a, c, e))
		byPair[k] = dedup
	return byTriple, byPair


def pickPreferred(entries):
	"""Return one canonical from a list of (canonical, entry) tuples, or None if ambiguous."""
	nonInferred = [(c, e) for c, e in entries if not e.get('inferred')]
	pool = nonInferred or entries
	if len(pool) == 1:
		return pool[0][0]
	return None  # Ambiguous.


def resolve(biosEntry, byTriple, byPair):
	"""Return (canonical, reason) or (None, reason)."""
	dev, cmd, arg = biosEntry['dev'], biosEntry['cmd'], biosEntry['arg']
	# Step 1: exact triple match (works for all single-command defines).
	hits = byTriple.get((dev, cmd, arg))
	if hits:
		canonical = pickPreferred(hits)
		if canonical:
			return canonical, 'triple'
		return None, f'triple-ambiguous:{[c for c, _ in hits]}'
	# Step 2: pair fallback (handles two-command spring-loaded defines where
	# `arg` is actually cmd2, not the canonical arg).
	pairHits = byPair.get((dev, cmd))
	if pairHits:
		nonInferred = [(c, e) for a, c, e in pairHits if not e.get('inferred')]
		pool = nonInferred or [(c, e) for a, c, e in pairHits]
		if len(pool) == 1:
			return pool[0][0], 'pair'
		return None, f'pair-ambiguous:{[c for c, _ in pool]}'
	return None, 'no-match'


def buildAuditEntries(defines, mapping, nameMap):
	"""Return audit entries for multi-position BIOS controls that have canonical positionMaps."""
	controls = mapping.get('controls', {})
	audit = []
	for d in defines:
		if not d['positions'] or len(d['positions']) <= 2:
			continue
		canonical = nameMap.get(d['name'])
		if not canonical:
			continue
		entry = controls.get(canonical, {})
		audit.append({
			'biosName': d['name'],
			'canonical': canonical,
			'biosPositions': d['positions'],
			'canonicalPositions': entry.get('positions'),
			'canonicalPositionMap': entry.get('positionMap'),
		})
	return audit


def writeAudit(path, audit):
	lines = [
		'# OH-58D multi-position discrete audit',
		'',
		'For each control, verify that the integer position index used in `OH-58D.py`',
		'still selects the intended cockpit position under the canonical positionMap.',
		'BIOS positions are listed in the order DCS BIOS enumerated them; canonical',
		'positionMap (when present) reflects the mapping order.',
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

	text = BIOS_LUA.read_text(encoding='utf-8')
	deviceTable = parseDeviceTable(text)
	print(f'Device table: {len(deviceTable)} entries')

	defines = parseBiosLua(BIOS_LUA, deviceTable)
	mapping = json.loads(MAPPING_JSON.read_text(encoding='utf-8'))
	byTriple, byPair = buildIndexes(mapping)

	nameMap = {}
	unmapped = {}
	tripleCount = 0
	pairCount = 0
	for d in defines:
		canonical, reason = resolve(d, byTriple, byPair)
		if canonical:
			if d['name'] not in nameMap:
				nameMap[d['name']] = canonical
				if reason == 'triple':
					tripleCount += 1
				elif reason == 'pair':
					pairCount += 1
		else:
			unmapped[d['name']] = {
				'devName': d['devName'],
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
