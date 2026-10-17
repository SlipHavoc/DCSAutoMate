"""Unit tests for extractListenedCommands() in tools/extraction-scripts/extractUtils.py."""
import os
import sys

import lupa
import pytest

EXTRACTION_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'tools', 'extraction-scripts'))
if EXTRACTION_DIR not in sys.path:
	sys.path.insert(0, EXTRACTION_DIR)

from extractUtils import extractListenedCommands


@pytest.fixture
def scriptsDir(tmp_path):
	(tmp_path / 'proxy.lua').write_text(
		'local dev = GetSelf()\n'
		'make_default_activity(0.1)\n'
		'for i = 20000, 20002 do dev:listen_command(i) end\n'
		'dev:listen_command(iCommandUndefinedInSandbox)\n',
		encoding='utf-8',
	)
	(tmp_path / 'engine.lua').write_text(
		'local dev = GetSelf()\n'
		'local other = GetDevice(5)\n'
		'function post_initialize() dev:listen_command(3042) end\n'
		'dev:listen_command(3040)\n',
		encoding='utf-8',
	)
	(tmp_path / 'broken.lua').write_text(
		'local dev = GetSelf()\n'
		'dev:listen_command(3001)\n'
		'dofile(LockOn_Options.script_path .. "missing.lua")\n'
		'dev:listen_command(3002)\n',
		encoding='utf-8',
	)
	return tmp_path


def runtimeWithCreators(scriptsDir):
	path = str(scriptsDir).replace('\\', '/') + '/'
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	lua.execute(f'''
		creators = {{}}
		creators[7] = {{"avLuaDevice", "{path}proxy.lua"}}
		creators[9] = {{"avAChS_1", "{path}engine.lua"}}
		creators[11] = {{"avLuaDevice", "{path}broken.lua"}}
		creators[12] = {{"avSimpleElectricSystem"}}
	''')
	return lua


def test_extractListenedCommandsCapturesEveryScriptedDevice(scriptsDir):
	listened, _ = extractListenedCommands(runtimeWithCreators(scriptsDir), str(scriptsDir))
	assert {'deviceId': 7, 'commandId': 20000} in listened
	assert {'deviceId': 7, 'commandId': 20002} in listened
	assert {'deviceId': 9, 'commandId': 3040} in listened


def test_extractListenedCommandsIncludesPostInitialize(scriptsDir):
	listened, _ = extractListenedCommands(runtimeWithCreators(scriptsDir), str(scriptsDir))
	assert {'deviceId': 9, 'commandId': 3042} in listened


def test_extractListenedCommandsIgnoresNonNumericIds(scriptsDir):
	listened, _ = extractListenedCommands(runtimeWithCreators(scriptsDir), str(scriptsDir))
	assert [entry for entry in listened if entry['deviceId'] == 7] == [
		{'deviceId': 7, 'commandId': 20000},
		{'deviceId': 7, 'commandId': 20001},
		{'deviceId': 7, 'commandId': 20002},
	]


def test_extractListenedCommandsReportsFailureAndKeepsEarlierCommands(scriptsDir):
	listened, failures = extractListenedCommands(runtimeWithCreators(scriptsDir), str(scriptsDir))
	assert {'deviceId': 11, 'commandId': 3001} in listened
	assert {'deviceId': 11, 'commandId': 3002} not in listened
	assert len(failures) == 1
	assert failures[0][0] == 'broken.lua'
	assert 'missing.lua' in failures[0][1]


def test_extractListenedCommandsSkipsCreatorsWithoutScript(scriptsDir):
	listened, _ = extractListenedCommands(runtimeWithCreators(scriptsDir), str(scriptsDir))
	assert all(entry['deviceId'] != 12 for entry in listened)
