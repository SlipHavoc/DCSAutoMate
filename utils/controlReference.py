"""Builds the data files for docs/controlReference.html from config/controlMappings.

Browsers won't let a page opened from disk fetch JSON, but they will load a <script src>, so each module's rows are written as a small JavaScript file.
"""
import json
import os
import sys

from utils.appPaths import appBaseDir

MODULES_FILE = 'modules.js'
STAMP_FILE = 'sources.json'
_knownKeys = {'arg', 'argLim', 'bindings', 'commandId', 'crewAccess', 'decrementValue', 'description', 'deviceId', 'elementName', 'fieldName', 'incrementValue', 'indicationId', 'indicatorArgLim', 'positionMap', 'positions', 'sendProtocol', 'step', 'type'}


def _number(value):
	return f'{value:g}' if isinstance(value, (int, float)) else str(value)


def _range(limits):
	return f'{_number(limits[0])} to {_number(limits[1])}'


def _bindingText(binding):
	if binding.get('axis'):
		return f"{binding['name']}: axis"
	parts = []
	pressed = binding.get('valuePressed', binding.get('valueDown'))
	if pressed is not None:
		parts.append(_number(pressed))
	if 'valueUp' in binding:
		parts.append(f"release {_number(binding['valueUp'])}")
	return f"{binding['name']}: {', '.join(parts)}" if parts else binding.get('name', '')


def _values(control):
	controlType = control.get('type')
	if controlType == 'discrete':
		positions = control.get('positions') or len(control.get('positionMap', []))
		return f'0 to {positions - 1}' if positions else ''
	if controlType == 'continuous':
		return _range(control.get('argLim', [0, 1]))
	if controlType == 'relative':
		return '+1 / -1'
	if controlType == 'raw':
		texts = []
		for binding in control.get('bindings', []):
			text = _bindingText(binding)
			if text not in texts:
				texts.append(text)
		return ', '.join(texts)
	return ''


def _positionCommand(index, entry):
	if not entry:
		return f'{index}: none'
	value = entry.get('value', entry.get('sendValue'))
	text = f"{index}: {entry['commandId']} = {_number(value)}"
	if 'readbackValue' in entry and entry['readbackValue'] != value:
		text += f" (reads {_number(entry['readbackValue'])})"
	return text


def _positionCommands(positionMap):
	return 'position commands ' + ', '.join(_positionCommand(index, entry) for index, entry in enumerate(positionMap))


def _details(control):
	controlType = control.get('type')
	parts = []
	if 'indicationId' in control:
		parts.append(f"indicator {control['indicationId']}")
	if 'fieldName' in control:
		parts.append(f"field {control['fieldName']}")
	if 'arg' in control:
		parts.append(f"arg {control['arg']}")
	positionMap = control.get('positionMap')
	if 'deviceId' in control:
		parts.append(f"device {control['deviceId']}")
	elif positionMap:
		deviceIds = sorted({entry['deviceId'] for entry in positionMap if entry})
		parts.append('device ' + ', '.join(str(deviceId) for deviceId in deviceIds))
	if 'commandId' in control:
		parts.append(f"command {control['commandId']}")
	if positionMap:
		parts.append(_positionCommands(positionMap))
	if 'argLim' in control and controlType != 'continuous':
		parts.append(f"arg range {_range(control['argLim'])}")
	if 'indicatorArgLim' in control:
		parts.append(f"indicator range {_range(control['indicatorArgLim'])}")
	if 'positions' in control and controlType != 'discrete':
		parts.append(f"{control['positions']} positions")
	if 'step' in control:
		parts.append(f"step {_number(control['step'])}")
	if 'incrementValue' in control:
		parts.append(f"increment {_number(control['incrementValue'])}")
	if 'decrementValue' in control:
		parts.append(f"decrement {_number(control['decrementValue'])}")
	if 'sendProtocol' in control:
		parts.append(f"protocol {control['sendProtocol']}")
	if 'crewAccess' in control:
		parts.append('crew ' + ', '.join(str(seat) for seat in control['crewAccess']))
	for key in sorted(set(control) - _knownKeys):
		parts.append(f'{key} {json.dumps(control[key])}')
	if 'elementName' in control:
		parts.append(control['elementName'])
	return ' · '.join(parts)


def controlRows(controls):
	"""One row per control: name, description, group (device or indicator), kind (control, arg or ind), type, the values a script sends, and the rest of the data as one line of details."""
	indicatorNames = {}
	for name, control in controls.items():
		if name.startswith('ind.') and name.count('.') == 1:
			indicatorNames[name] = control.get('description', '').replace(' (all fields)', '')
	rows = []
	for name, control in controls.items():
		if name.startswith('ind.'):
			indicator = '.'.join(name.split('.')[:2])
			group, kind, controlType = f'{indicator} {indicatorNames.get(indicator, "")}'.strip(), 'ind', 'display text'
		elif name.startswith('arg.'):
			group, kind, controlType = 'arg', 'arg', 'arg (read only)'
		else:
			group, kind, controlType = name.split('.')[0], 'control', control.get('type', '')
		rows.append({
			'name': name,
			'description': control.get('description', ''),
			'group': group,
			'kind': kind,
			'type': controlType,
			'values': _values(control),
			'details': _details(control),
		})
	return rows


def _mappingFiles(mappingsDir):
	"""{fileName without .json: path}, skipping nameMap files."""
	files = {}
	if not os.path.isdir(mappingsDir):
		return files
	for fileName in os.listdir(mappingsDir):
		if fileName.endswith('.json') and not fileName.endswith('_nameMap.json'):
			files[fileName[:-len('.json')]] = os.path.join(mappingsDir, fileName)
	return files


def _sourceStamps(mappingsDir):
	stamps = {name: os.path.getmtime(path) for name, path in _mappingFiles(mappingsDir).items()}
	# A changed generator rebuilds the data; when packaged, the code lives in a fresh temp folder each launch, so the exe dates it.
	stamps['_generator'] = os.path.getmtime(sys.executable if getattr(sys, 'frozen', False) else __file__)
	return stamps


def _readStamps(outputDir):
	try:
		with open(os.path.join(outputDir, STAMP_FILE), encoding='utf-8') as f:
			return json.load(f)
	except (OSError, ValueError):
		return None


def controlReferenceIsStale(mappingsDir, outputDir):
	"""True if a mapping file was added, removed or changed (or this generator changed) since the data files were written."""
	return _readStamps(outputDir) != _sourceStamps(mappingsDir) or not os.path.isfile(os.path.join(outputDir, MODULES_FILE))


def _writeScript(path, prefix, data):
	with open(path, 'w', encoding='utf-8', newline='\n') as f:
		f.write(f"{prefix}{json.dumps(data, separators=(',', ':'))};\n")


def buildControlReference(mappingsDir, outputDir):
	"""Write modules.js and one <moduleName>.js per mapping, remove data for mappings that are gone, and return the module names written."""
	stamps = _sourceStamps(mappingsDir)
	os.makedirs(outputDir, exist_ok=True)
	modules = []
	for fileName, path in sorted(_mappingFiles(mappingsDir).items(), key=lambda item: item[0].lower()):
		with open(path, encoding='utf-8') as f:
			mapping = json.load(f)
		# Same rule as DCSDirectManager: only <moduleName>.json is a module's mapping.
		if mapping.get('moduleName', fileName) != fileName:
			continue
		rows = controlRows(mapping.get('controls', {}))
		_writeScript(os.path.join(outputDir, f'{fileName}.js'), f'window.controlReferenceData[{json.dumps(fileName)}] = ', rows)
		modules.append({'name': fileName, 'count': len(rows)})
	for oldName in (_readStamps(outputDir) or {}):
		oldPath = os.path.join(outputDir, f'{oldName}.js')
		if oldName not in stamps and os.path.isfile(oldPath):
			os.remove(oldPath)
	_writeScript(os.path.join(outputDir, MODULES_FILE), 'window.controlReferenceModules = ', modules)
	with open(os.path.join(outputDir, STAMP_FILE), 'w', encoding='utf-8') as f:
		json.dump(stamps, f)
	return [module['name'] for module in modules]


def controlReferencePaths():
	"""(mappingsDir, outputDir, pagePath) for this install."""
	baseDir = appBaseDir()
	return os.path.join(baseDir, 'config', 'controlMappings'), os.path.join(baseDir, 'docs', 'controlData'), os.path.join(baseDir, 'docs', 'controlReference.html')


def updateControlReference():
	"""Rebuild docs/controlData if it's stale; returns True if it was rebuilt."""
	mappingsDir, outputDir, _ = controlReferencePaths()
	if not controlReferenceIsStale(mappingsDir, outputDir):
		return False
	buildControlReference(mappingsDir, outputDir)
	return True


if __name__ == '__main__':
	mappingsDir, outputDir, pagePath = controlReferencePaths()
	names = buildControlReference(mappingsDir, outputDir)
	print(f'Wrote control reference data for {len(names)} modules; open {pagePath}')
