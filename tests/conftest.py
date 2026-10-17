"""Shared fixtures for DCSAutoMate tests."""
import json
import os
import struct
import sys
import tempfile

import pytest


# ---------------------------------------------------------------------------
# DCS availability detection — used by the requires_dcs marker.
# ---------------------------------------------------------------------------

def _isDcsRunning():
	"""Return True if a DCS window can be found on the desktop."""
	try:
		import pygetwindow as gw
		return bool(gw.getWindowsWithTitle('Digital Combat Simulator'))
	except Exception:
		return False


@pytest.fixture(scope='session')
def dcsRunning():
	"""Session-scoped fixture: True when DCS is running, False otherwise."""
	return _isDcsRunning()


@pytest.fixture(autouse=True)
def skipIfRequiresDcs(request, dcsRunning):
	"""Auto-skip any test marked requires_dcs when DCS is not running."""
	if request.node.get_closest_marker('requires_dcs') and not dcsRunning:
		pytest.skip('DCS is not running')

# Ensure the project root is on sys.path so that engine/network/utils are importable.
projectRoot = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if projectRoot not in sys.path:
	sys.path.insert(0, projectRoot)


# ---------------------------------------------------------------------------
# DCS BIOS binary packet helpers
# ---------------------------------------------------------------------------

def buildBiosPacket(*writes):
	"""Build a DCS BIOS-style binary packet.

	Each *write* is a tuple (address, data_bytes).
	The packet starts with a 4-byte sync word (0x55 x4), followed by one or more
	address+count+data chunks.
	"""
	# Frame sync
	packet = b'\x55\x55\x55\x55'
	for address, data in writes:
		dataBytes = bytes(data) if not isinstance(data, (bytes, bytearray)) else data
		packet += struct.pack('<H', address)  # address (little-endian uint16)
		packet += struct.pack('<H', len(dataBytes))  # count (little-endian uint16)
		packet += dataBytes
	return packet


# ---------------------------------------------------------------------------
# Sample DCS BIOS JSON metadata (minimal, one module)
# ---------------------------------------------------------------------------

SAMPLE_BIOS_JSON = {
	'Test': {
		'APU_SW': {
			'identifier': 'APU_SW',
			'description': 'APU Switch',
			'outputs': [{
				'address': 0x1000,
				'type': 'integer',
				'mask': 0x0001,
				'shift_by': 0,
				'max_length': None,
			}],
		},
		'DISPLAY_TEXT': {
			'identifier': 'DISPLAY_TEXT',
			'description': 'Display Text',
			'outputs': [{
				'address': 0x2000,
				'type': 'string',
				'mask': None,
				'shift_by': None,
				'max_length': 16,
			}],
		},
		'GEAR_LEVER': {
			'identifier': 'GEAR_LEVER',
			'description': 'Gear Lever',
			'outputs': [{
				'address': 0x1002,
				'type': 'integer',
				'mask': 0xFF00,
				'shift_by': 8,
				'max_length': None,
			}],
		},
	},
}


@pytest.fixture
def sampleBiosJson():
	"""Return the minimal DCS BIOS JSON metadata dictionary."""
	return SAMPLE_BIOS_JSON


@pytest.fixture
def sampleBiosJsonDir(tmp_path):
	"""Create a temp directory with a single DCS BIOS json file and return its path."""
	jsonDir = tmp_path / 'Scripts' / 'DCS-BIOS' / 'doc' / 'json'
	jsonDir.mkdir(parents=True)

	# Write test module JSON
	testJson = jsonDir / 'TestModule.json'
	testJson.write_text(json.dumps(SAMPLE_BIOS_JSON), encoding='utf-8')

	# Write a minimal AircraftAliases.json that maps 'TestModule' to itself.
	aliasJson = jsonDir / 'AircraftAliases.json'
	aliasJson.write_text(json.dumps({
		'TestModule': ['TestModule'],
	}), encoding='utf-8')

	return tmp_path


# ---------------------------------------------------------------------------
# Export data sample strings
# ---------------------------------------------------------------------------

SAMPLE_EXPORT_DATA = (
	b'LoGetAltitudeAboveSeaLevel=1500.5;'
	b'LoGetAltitudeAboveGroundLevel=120.3;'
	b'LoGetRadarAltimeter=118.7;'
	b'LoGetHeightWithObjects=119.0;'
	b'LoGetTrueAirSpeed=250.0;'
	b'LoGetIndicatedAirSpeed=230.0;'
	b'LoGetMissionStartTime=21600;'
	b'LoGetModelTime=300;'
	b'LoGetSelfData.Name=FA-18C_hornet;'
	b'LoGetEngineInfo.RPM.left=80;'
	b'LoGetPayloadInfo.Stations.1.CLSID=;'
	b'LoGetPayloadInfo.Stations.1.count=0'
)


@pytest.fixture
def sampleExportData():
	return SAMPLE_EXPORT_DATA


# ---------------------------------------------------------------------------
# SettingsManager helpers
# ---------------------------------------------------------------------------

@pytest.fixture
def tempConfigDir(tmp_path):
	"""Create a temporary config directory and return its path.

	Monkeypatches SettingsManager class attributes so it uses the temp dir.
	"""
	configDir = tmp_path / 'config'
	configDir.mkdir()
	return {
		'configFile': str(configDir / 'DCSAutoMateConfig.json'),
		'settingsFile': str(configDir / 'DCSAutoMateSettings.json'),
		'tmpPath': tmp_path,
	}


# ---------------------------------------------------------------------------
# Scratchpad sample content
# ---------------------------------------------------------------------------

SAMPLE_SCRATCHPAD = """\
DMS: N  42°03'00.89", E 041°46'04.84"
DDM: N  42°03.0150', E 041°46.0808'
MGRS: 37 T GG 29069 59063
N/S (m): -305405, E/W (m): 626345
5m, 16ft
"""


@pytest.fixture
def scratchpadDir(tmp_path):
	"""Create a temp Scratchpad directory with one sample file."""
	spDir = tmp_path / 'Scratchpad'
	spDir.mkdir()
	(spDir / 'test.txt').write_text(SAMPLE_SCRATCHPAD, encoding='utf-8')
	return spDir
