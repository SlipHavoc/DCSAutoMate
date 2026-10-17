"""A script that crashes says so in the in-game overlay and over TTS, not just in the desktop window the player may not be looking at."""
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)

pytest.importorskip('PySide6')

from DCSAutoMate import DCSAutoMateApp # noqa: E402


def overlayText(app):
	return '\n'.join(call.args[0] for call in app._uiSendLog.call_args_list)


def runScript(executeError=None):
	"""Run DCSAutoMateApp.runScript against a stand-in app whose executor raises executeError, if given."""
	app = MagicMock()
	app.scriptManager.loadScriptFunction.return_value = (MagicMock(), MagicMock())
	app.scriptManager.getScriptInfo.return_value = None
	with patch('DCSAutoMate.DCSSeqExecute') as executorClass:
		if executeError:
			executorClass.return_value.execute.side_effect = executeError
		DCSAutoMateApp.runScript(app)
	return app


def test_crashIsShownInGameAndSpoken():
	app = runScript(IndexError('list index out of range'))
	assert 'Script error: IndexError: list index out of range' in overlayText(app)
	assert 'desktop window' in overlayText(app)
	app.ttsManager.speak.assert_called_once()
	assert 'desktop window' in app.ttsManager.speak.call_args.args[0]


def test_scriptThatFailsToLoadIsAlsoReportedInGame():
	app = MagicMock()
	app.scriptManager.loadScriptFunction.side_effect = SyntaxError('invalid syntax')
	DCSAutoMateApp.runScript(app)
	assert 'Script error: SyntaxError: invalid syntax' in overlayText(app)
	app.ttsManager.speak.assert_called_once()


def test_cleanRunReportsNoError():
	app = runScript()
	assert 'Script error' not in overlayText(app)
	app.ttsManager.speak.assert_not_called()
