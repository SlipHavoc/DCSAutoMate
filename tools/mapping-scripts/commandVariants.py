"""Command variant sibling discovery for DCS control generators.

In DCS modules, command_defs.lua defines commands in families: a base command
and optional `_EXT` / `_ITER` / `_AXIS` siblings (sometimes with other casing
like `_Ext`, `EXT`, `_Iter`, `Axis`), plus occasional `_CLICK` flavors that
the clickable cockpit elements bind to for mouse stepping.  Clickable elements
(clickabledata.lua) usually bind to the base or `_CLICK` command, while
keyboard/joystick bindings (Input/*/default.lua) bind to the `_Ext` or `_Iter`
sibling for pulse-style ±1 input.  Our TCP C:/S: protocol mimics external
input and therefore generally needs one of the ext/iter siblings.

This module gives each control generator a way to discover all siblings of an
element-bound command and emit each as its own top-level control entry (with
`_ext`, `_iter`, `_axis` suffixes on the control name).  Script authors then
pick the right variant per control.  The unsuffixed control always carries
the cmd the clickable element binds to (preserves backward compatibility with
existing mappings); each sibling is emitted only when its cmd id differs.
"""

import re


# Suffix patterns (regex at end of name) → variant name.  Order matters: ext
# is matched before iter/axis so the longest common suffix wins.
_VARIANT_PATTERNS = [
	('ext',  re.compile(r'(_EXT|_Ext|_ext|EXT)$')),
	('iter', re.compile(r'(_ITER|_Iter|_iter)$')),
	('axis', re.compile(r'(_AXIS|_Axis|_axis|Axis)$')),
]

# Additional suffixes that carry no variant meaning but should be stripped
# when computing a command's family stem, so e.g. `CONTROL_LEFT_THROTTLE_CLICK`
# is grouped with `CONTROL_LEFT_THROTTLE_ITER` under the shared stem.  These
# are treated as 'base' variants for classification.
_STEM_ONLY_SUFFIXES = re.compile(r'(_CLICK|_Click|_click)$')


def stripVariantSuffix(cmdName):
	"""Return (stem, variant) for a command_defs name.

	variant is 'base', 'ext', 'iter', or 'axis'.  `_CLICK`-style semantic
	suffixes are also stripped to build the stem but classified as 'base'.
	"""
	if not cmdName:
		return cmdName, 'base'
	for variant, pat in _VARIANT_PATTERNS:
		m = pat.search(cmdName)
		if m:
			return cmdName[:m.start()], variant
	m = _STEM_ONLY_SUFFIXES.search(cmdName)
	if m:
		return cmdName[:m.start()], 'base'
	return cmdName, 'base'


def computeVariantFamily(elementCmdId, elementCmdName, tableName, commandTables):
	"""Discover sibling variants for an element-bound command.

	Returns an ordered list of (variant, cmdName, cmdId) tuples.  The first
	entry is always the element's own cmd (variant = 'base' regardless of
	whether the cmd name itself looks basic, _CLICK, or ambiguous).
	Subsequent entries list ext/iter/axis siblings in that order.  Siblings
	whose cmd id equals the element's own cmd id are omitted (no duplicates).

	Args:
		elementCmdId: numeric cmd id the element is bound to.
		elementCmdName: resolved name of that cmd (may be None).
		tableName: matched command-table name (may be None).
		commandTables: {tableName: {cmdName: cmdId}} from the extraction.
	"""
	primary = ('base', elementCmdName or f'cmd_{elementCmdId}', elementCmdId)
	if not elementCmdName:
		return [primary]

	stem, _ = stripVariantSuffix(elementCmdName)
	table = commandTables.get(tableName, {}) if tableName else {}

	# Collect first entry found per non-base variant within this stem family.
	siblings = {}
	for name, cmdId in table.items():
		nStem, nVariant = stripVariantSuffix(name)
		if nStem == stem and nVariant != 'base' and nVariant not in siblings:
			if cmdId != elementCmdId:
				siblings[nVariant] = (name, cmdId)

	ordered = [primary]
	for v in ('ext', 'iter', 'axis'):
		if v in siblings:
			ordered.append((v, siblings[v][0], siblings[v][1]))
	return ordered


def makeSiblingName(baseName, variant):
	"""Return the control-mapping name for a sibling variant.

	baseName stays unchanged for the 'base' variant.  Other variants append
	'_ext', '_iter', or '_axis' (lowercase snake, regardless of source casing).
	"""
	if variant == 'base':
		return baseName
	return f'{baseName}_{variant}'


def appendVariantToHint(hint, variant):
	"""Append a parenthesized variant marker to a hint string."""
	if variant == 'base' or not hint:
		return hint
	return f'{hint} ({variant})'


def inferDeviceTableMapByEvidence(elements, commandTables, deviceNameById=None):
	"""Augment/override name-based device→table matching using element evidence.

	For each deviceId referenced by any element, collect the cmd ids that its
	elements' actions reference.  Restrict candidates to tables whose cmd-id
	set contains all of those.  Rank remaining candidates by device-name ↔
	table-stem similarity (longest-common-prefix + substring-containment after
	normalization and `_P`/`_O` pilot/operator suffix stripping).  Return the
	top candidate when there is a unique best-scorer with score ≥ 3 chars, or
	when only one candidate remains after filtering.

	Module-agnostic: relies only on extraction data.  Complements name-based
	fuzzy matching without replacing it; callers merge the evidence-based map
	into their existing map, filling gaps rather than overriding.

	Returns {deviceId: tableName}.
	"""
	# deviceId → set of cmd ids referenced.
	devCmdIds = {}
	for elem in elements.values():
		devId = elem.get('device')
		if devId is None:
			continue
		for cmdId in elem.get('action', []) or []:
			if cmdId and cmdId > 0:
				devCmdIds.setdefault(devId, set()).add(cmdId)

	# Filter out the global Keys table.
	tableCmdIds = {}
	for tName, cmds in commandTables.items():
		if tName == 'Keys':
			continue
		tableCmdIds[tName] = set(cmds.values())

	def normalize(s):
		return re.sub(r'[_\-]', '', s.lower()) if s else ''

	def nameScore(devName, tableName):
		dn = normalize(devName)
		if len(dn) > 2 and dn[-1] in ('p', 'o'):
			dn = dn[:-1]
		stem = tableName[:-len('_commands')] if tableName.endswith('_commands') else tableName
		tn = normalize(stem)
		if not dn or not tn:
			return 0
		i = 0
		while i < len(dn) and i < len(tn) and dn[i] == tn[i]:
			i += 1
		contains = min(len(dn), len(tn)) if (dn in tn or tn in dn) else 0
		return max(i, contains)

	result = {}
	for devId, cmdIds in devCmdIds.items():
		candidates = [t for t, ids in tableCmdIds.items() if cmdIds.issubset(ids)]
		if not candidates:
			continue
		if len(candidates) == 1:
			result[devId] = candidates[0]
			continue
		devName = deviceNameById.get(devId, '') if deviceNameById else ''
		if not devName:
			continue
		scored = sorted(((nameScore(devName, t), t) for t in candidates), key=lambda x: (-x[0], x[1]))
		best, second = scored[0], scored[1]
		if best[0] >= 3 and best[0] > second[0]:
			result[devId] = best[1]
	return result
