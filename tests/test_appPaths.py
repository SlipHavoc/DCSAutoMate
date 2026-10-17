"""The packaged exe finds its data files (control mappings, sim commands) next to itself, not in PyInstaller's temp folder."""
import json
import os
import sys

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

import engine.simCommands as simCommands
from network.DCSDirectManager import DCSDirectManager
from utils.appPaths import appBaseDir


def runAsExe(monkeypatch, tmp_path):
	"""Pretend to be DCSAutoMate.exe in tmp_path, with a config folder of its own."""
	monkeypatch.setattr(sys, 'frozen', True, raising=False)
	monkeypatch.setattr(sys, 'executable', str(tmp_path / 'DCSAutoMate.exe'))
	(tmp_path / 'config' / 'controlMappings').mkdir(parents=True)


def test_baseDirIsTheRepoFromSource():
	assert os.path.normcase(appBaseDir()) == os.path.normcase(projectRoot)


def test_baseDirIsTheExeFolderWhenPackaged(monkeypatch, tmp_path):
	runAsExe(monkeypatch, tmp_path)
	assert os.path.normcase(appBaseDir()) == os.path.normcase(str(tmp_path))


def test_packagedExeLoadsControlMappingsFromItsFolder(monkeypatch, tmp_path):
	runAsExe(monkeypatch, tmp_path)
	mapping = {'moduleName': 'ShippedModule', 'controls': {'DEV.switch': {'description': 'Switch', 'type': 'discrete', 'arg': 1, 'positions': 2}}}
	(tmp_path / 'config' / 'controlMappings' / 'ShippedModule.json').write_text(json.dumps(mapping), encoding='utf-8')
	assert list(DCSDirectManager({}).controlMappings) == ['ShippedModule']


def test_packagedExeLoadsSimCommandsFromItsFolder(monkeypatch, tmp_path):
	runAsExe(monkeypatch, tmp_path)
	(tmp_path / 'config' / 'simCommands.json').write_text(json.dumps({'iCommandShipped': 1}), encoding='utf-8')
	monkeypatch.setattr(simCommands, 'simCommands', None)
	monkeypatch.setattr(simCommands, 'commsMenuIds', None)
	assert simCommands.loadSimCommands() == {'iCommandShipped': 1}


def test_packagedExeBuildsTheControlReferenceOnceNextToItself(monkeypatch, tmp_path):
	"""PyInstaller unpacks the code to a new temp folder each launch, so the code's own files can't date the data."""
	from utils.controlReference import updateControlReference
	runAsExe(monkeypatch, tmp_path)
	(tmp_path / 'DCSAutoMate.exe').write_bytes(b'')
	(tmp_path / 'config' / 'controlMappings' / 'ShippedModule.json').write_text(json.dumps({'moduleName': 'ShippedModule', 'controls': {}}), encoding='utf-8')
	monkeypatch.setattr('utils.controlReference.__file__', str(tmp_path / '_MEI12345' / 'controlReference.pyc'))
	assert updateControlReference() is True
	assert (tmp_path / 'docs' / 'controlData' / 'ShippedModule.js').is_file()
	assert updateControlReference() is False
