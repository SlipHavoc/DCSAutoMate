"""Show cockpit-control differences between HEAD and the working-copy control mappings.

Raw and read-only controls are skipped so DCS indicator churn and keybinding changes don't bury the clickable controls.

Usage: python tools/diffCockpitControls.py <mappingName> [<mappingName> ...]
	e.g. python tools/diffCockpitControls.py AJS37 "F-86F Sabre"
"""
import json
import os
import subprocess
import sys

repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def isCockpitControl(control):
	return control.get('type') not in ('raw', 'readOnly', None)


for mappingName in sys.argv[1:]:
	relPath = f'config/controlMappings/{mappingName}.json'
	headText = subprocess.run(['git', 'show', f'HEAD:{relPath}'], capture_output=True, encoding='utf-8', cwd=repoRoot, check=True).stdout
	old = json.loads(headText)['controls']
	with open(os.path.join(repoRoot, relPath), encoding='utf-8') as f:
		new = json.load(f)['controls']
	removed = sorted(n for n in set(old) - set(new) if isCockpitControl(old[n]))
	added = sorted(n for n in set(new) - set(old) if isCockpitControl(new[n]))
	changed = sorted(n for n in set(old) & set(new) if old[n] != new[n] and (isCockpitControl(old[n]) or isCockpitControl(new[n])))
	print(f'=== {mappingName}: removed={len(removed)} added={len(added)} changed={len(changed)}')
	for label, names, data in (('REMOVED', removed, old), ('ADDED', added, new)):
		for name in names:
			print(f'  {label:8} {name:45} {data[name]["type"]:10} {data[name].get("elementName", "")}: {data[name].get("description", "")[:50]}')
	for name in changed:
		diffKeys = sorted(k for k in set(old[name]) | set(new[name]) if old[name].get(k) != new[name].get(k))
		print(f'  CHANGED  {name:45} ' + ', '.join(f'{k}: {old[name].get(k)!r} -> {new[name].get(k)!r}' for k in diffKeys)[:300])
