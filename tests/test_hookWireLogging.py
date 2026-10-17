"""Hook wire logging: wireRxLabel() in the Hook picks which received messages are logged, run here through lupa."""
import os
import re

import lupa
import pytest

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HOOK_FILE = os.path.join(projectRoot, 'Scripts', 'Hooks', 'DCSAutoMateHook.lua')


@pytest.fixture(scope='module')
def wireRxLabel():
	"""The pure function, cut from the Hook between its marker comments (the rest of the Hook needs DCS)."""
	with open(HOOK_FILE, encoding='utf-8') as f:
		source = f.read()
	match = re.search(r'-- wireRxLabel: begin\n(.*?)-- wireRxLabel: end', source.replace('\r\n', '\n'), re.S)
	assert match, 'wireRxLabel markers not found in the Hook'
	lua = lupa.LuaRuntime(unpack_returned_tuples=True)
	return lua.execute(match.group(1) + '\nreturn wireRxLabel')


def test_uiMessageFromAppIsLogged(wireRxLabel):
	"""Messages DCSAutoMate sends the in-game window (DCSAutoMate.py _uiSendLog)."""
	assert wireRxLabel('DCSAUTOMATE_UI;event=log;text=Starting Cold Start;') == 'UI wire RX'


def test_coordConvertRequestIsLogged(wireRxLabel):
	"""Requests from SequenceHelper's coordinate conversion."""
	assert wireRxLabel('DCSAUTOMATE_COORD_CONVERT;requestId=1;replyPort=7790;x=1;y=2;z=3;') == 'Coord wire RX'


def test_otherTextIsNotLogged(wireRxLabel):
	assert wireRxLabel('Plain monitor text') is None


def test_prefixMustBeComplete(wireRxLabel):
	"""A message that only shares the start of a prefix isn't one of ours."""
	assert wireRxLabel('DCSAUTOMATE_U') is None
	assert wireRxLabel('DCSAUTOMATE_UIX;event=log;') is None
	assert wireRxLabel('DCSAUTOMATE_COORD_CONVERTED;') is None
