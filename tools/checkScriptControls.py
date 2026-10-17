"""Report controls used by a module's scripts that are missing from its control mapping.

This is the same "not found in descriptions" check the app does at run time, run offline for every script in the module file.

Usage: python tools/checkScriptControls.py <scriptModule> <mappingName>
	e.g. python tools/checkScriptControls.py "Ka-50 Blackshark III" Ka-50_3
"""
import importlib
import os
import sys
from unittest.mock import MagicMock

repoRoot = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, repoRoot)
sys.modules.setdefault('PySide6', MagicMock())

from engine.SequenceHelper import SequenceHelper
from network.DCSDirectManager import DCSDirectManager, TELEMETRY_MODULE, parseTelemetryRef

moduleFile, moduleName = sys.argv[1], sys.argv[2]
config = {'debug': True}
descriptions = DCSDirectManager(config).getDescriptions(moduleName)
scriptModule = importlib.import_module(f'DCSAutoMateScripts.{moduleFile}')
for script in scriptModule.getScriptData()['scripts']:
	defaults = {k: next(iter(v.get('options', {'': ''}))) for k, v in script.get('vars', {}).items()}
	helper = SequenceHelper(config)
	sequence = helper.collectSequence(getattr(scriptModule, script['function'])(config, defaults, helper))
	missing = []
	for command in sequence:
		cmd = command.get('cmd', '')
		control = command.get('control') if cmd in ('scriptCockpitState', 'scriptLoopUntilStart', 'scriptLoopUntilEnd') else (cmd if cmd and not cmd.startswith('script') else None)
		if control:
			if control.startswith(f'{TELEMETRY_MODULE}/'):
				if parseTelemetryRef(control) is None:
					missing.append(control)
				continue
			name = control.split('/', 1)[-1]
			if descriptions.get(name, {}).get('description', name) == name:
				missing.append(name)
	print(f'{script["name"]:24} {len(sequence):4} commands, {len(missing)} not found {sorted(set(missing))}')
