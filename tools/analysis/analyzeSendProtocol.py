#!/usr/bin/env python3
"""Phase 1 analysis: cross-reference existing relative controls with their
command_defs variant suffix (base / _EXT / _ITER / _AXIS).

Reads existing nativeExtractions and controlMappings (does NOT modify them),
resolves each relative control's action id to its command_defs name via a
device-name → command-table heuristic, and prints a table.

Purpose: empirically test the hypothesis that suffix predicts the protocol
(C: vs S:) needed, before changing the generator.

Usage:
	python tools/analysis/analyzeSendProtocol.py
"""
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXTRACT_DIR = ROOT / 'config' / 'nativeExtractions'
MAPPING_DIR = ROOT / 'config' / 'controlMappings'

# Map mapping-file stem to extraction-file stem (where they differ).
MAPPING_TO_EXTRACT = {
	'FA-18C_hornet': 'FA-18C',
	'AH-64D_BLK_II': 'AH-64D',
	'AV8BNA': 'AV8BNA',
	'Mi-24P': 'Mi-24P',
}


def normalizeName(name):
	"""Normalize a name for fuzzy matching: lowercase, strip underscores/dashes."""
	return re.sub(r'[_\-]', '', name.lower())


def variantNames(name):
	"""Generate alternative normalized forms of a device name for matching.

	Mi-24P patterns:
	- Pilot/operator pairs: BAROALT_P, BAROALT_O → baroaltimeter
	- Interfaces: ENGINE_INTERFACE → engine
	- Abbreviations: WEAP_SYS → weapon
	- With/without numbers: ARC_15 ↔ arc15
	"""
	variants = set()
	n = name.lower()
	variants.add(normalizeName(n))
	# Strip trailing _P / _O (pilot/operator).
	stripped = re.sub(r'_[po]$', '', n)
	variants.add(normalizeName(stripped))
	# Strip _INTERFACE / _SYSTEM / _SYS / _INT suffixes.
	for suf in ('_interface', '_system', '_sys', '_int', '_proxy'):
		if stripped.endswith(suf):
			variants.add(normalizeName(stripped[:-len(suf)]))
	# Strip digits.
	variants.add(re.sub(r'\d+', '', normalizeName(stripped)))
	# Known stems.
	for variant in list(variants):
		if variant.startswith('weap'):
			variants.add('weapon')
		if variant.startswith('baroalt'):
			variants.add('baroaltimeter')
		if variant == 'clockp' or variant == 'clocko' or variant == 'clock':
			variants.add('timers')
		if variant.startswith('extlights'):
			variants.add('extlights')
		if variant.startswith('intlights'):
			variants.add('intlights')
	variants.discard('')
	return variants


def buildDeviceToTable(devices, commandTables):
	"""Return {deviceId: tableName} using fuzzy name matching.

	devices: {deviceName: deviceId}
	commandTables: {tableName: {cmdName: cmdId}}
	"""
	# Precompute normalized table stems (strip trailing _commands).
	tableStems = {}
	for tName in commandTables.keys():
		stem = tName
		if stem.endswith('_commands'):
			stem = stem[:-len('_commands')]
		tableStems[tName] = normalizeName(stem)

	result = {}
	for devName, devId in devices.items():
		variants = variantNames(devName)
		# Try exact match against each variant.
		matched = []
		for v in variants:
			matched = [t for t, s in tableStems.items() if s == v]
			if matched:
				break
		if not matched:
			# Substring both ways, trying each variant.
			for v in variants:
				matched = [t for t, s in tableStems.items() if s and (s in v or v in s) and len(s) >= 3]
				if matched:
					break
		if len(matched) == 1:
			result[devId] = matched[0]
		elif len(matched) > 1:
			# Prefer the longest shared prefix with the primary normalized form.
			primary = normalizeName(devName)
			matched.sort(key=lambda t: -len(os.path.commonprefix([tableStems[t], primary])))
			result[devId] = matched[0]
	return result


def resolveActionName(deviceId, actionId, deviceToTable, commandTables):
	"""Return the command_defs name for (deviceId, actionId) or None."""
	tableName = deviceToTable.get(deviceId)
	if not tableName:
		return None
	table = commandTables.get(tableName, {})
	for name, cid in table.items():
		if cid == actionId:
			return name
	return None


def classifySuffix(name):
	"""Classify a command name by its command_defs suffix.

	Handles both snake_case (FREQ_100HZ_EXT) and camelCase (VertAdjEXT).
	"""
	if not name:
		return 'unknown'
	for suffix in ('_EXT', '_ITER', '_AXIS'):
		if name.endswith(suffix):
			return suffix[1:]  # 'EXT', 'ITER', 'AXIS'
	# CamelCase suffix variants (Mi-24P MAP_DISPLAY uses VertAdjEXT etc.).
	for suffix in ('EXT', 'ITER', 'AXIS'):
		if name.endswith(suffix) and len(name) > len(suffix) and name[-len(suffix)-1].islower():
			return suffix
	return 'base'


def loadJson(path):
	with open(path, 'r', encoding='utf-8') as f:
		return json.load(f)


def main():
	print(f"{'module':<16} {'control':<32} {'dev':>4} {'cmd':>5} {'sfx':<6} {'proto':<6} {'argLim':<14} {'actionName'}")
	print('-' * 130)

	# For each mapping, find deviceId/action via existing extraction.
	for mapPath in sorted(MAPPING_DIR.glob('*.json')):
		mapStem = mapPath.stem
		if mapStem not in MAPPING_TO_EXTRACT:
			continue
		extStem = MAPPING_TO_EXTRACT[mapStem]
		extPath = EXTRACT_DIR / f'{extStem}.json'
		if not extPath.exists():
			print(f'# Missing extraction for {mapStem}', file=sys.stderr)
			continue

		mapping = loadJson(mapPath)
		extraction = loadJson(extPath)

		devices = extraction.get('devices', {})
		commandTables = extraction.get('commandTables', {})
		deviceToTable = buildDeviceToTable(devices, commandTables)

		# Report unmapped devices (debug).
		unmapped = [n for n, i in devices.items() if i not in deviceToTable]
		if unmapped:
			print(f'# {mapStem}: {len(unmapped)} devices without command-table match: '
				f'{", ".join(unmapped[:6])}{" ..." if len(unmapped) > 6 else ""}', file=sys.stderr)

		controls = mapping.get('controls', {})

		# Aggregate suffix counts for summary.
		counts = {'base': 0, 'EXT': 0, 'ITER': 0, 'AXIS': 0, 'unknown': 0}

		for ctrlName, ctrl in controls.items():
			if ctrl.get('type') != 'relative':
				continue
			devId = ctrl.get('deviceId')
			cmdId = ctrl.get('commandId')
			proto = ctrl.get('sendProtocol', '-')
			argLim = ctrl.get('argLim')
			actionName = resolveActionName(devId, cmdId, deviceToTable, commandTables)
			suffix = classifySuffix(actionName)
			counts[suffix] = counts.get(suffix, 0) + 1

			argLimStr = f'[{argLim[0]:.2f},{argLim[1]:.2f}]' if isinstance(argLim, list) and len(argLim) == 2 else str(argLim)
			print(f'{mapStem:<16} {ctrlName:<32} {devId!s:>4} {cmdId!s:>5} {suffix:<6} {proto:<6} {argLimStr:<14} {actionName}')

		print(f'# {mapStem} summary: base={counts["base"]}  EXT={counts["EXT"]}  ITER={counts["ITER"]}  AXIS={counts["AXIS"]}  unknown={counts["unknown"]}')
		print()


if __name__ == '__main__':
	main()
