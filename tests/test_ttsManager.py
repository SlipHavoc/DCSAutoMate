import os

import pytest

win32com = pytest.importorskip('win32com.client')

from utils.TTSManager import TTSManager


def speakToWavSize(manager, text, path):
	stream = win32com.Dispatch('SAPI.SpFileStream')
	stream.Open(str(path), 3)
	manager.speaker.AudioOutputStream = stream
	manager.speak(text, asyncFlag=False)
	stream.Close()
	return os.path.getsize(path)


def test_speakParsesSapiXmlTagsMidSentence(tmp_path):
	manager = TTSManager({})
	if manager.speaker is None:
		pytest.skip('SAPI voice not available.')

	plainSize = speakToWavSize(manager, 'Then click resume.', tmp_path / 'plain.wav')
	taggedSize = speakToWavSize(manager, 'Then click <pron sym="r ih z uw m"/>.', tmp_path / 'tagged.wav')

	# If the tag were read aloud letter by letter, the audio would be more than twice as long.
	assert taggedSize < plainSize * 1.5
