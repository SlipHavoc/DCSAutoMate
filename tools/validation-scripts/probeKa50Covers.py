"""Empirical probe: classify each Ka-50 BSII cover as TOGGLE vs ABSOLUTE.

Usage:
	1. Launch DCS, take off the deck or sit on a ramp with the Ka-50 BSII loaded.
	2. Make sure all systems likely to gate the covers are powered:
	   - Both batteries ON (so battery covers respond)
	   - Aux power on bus if available
	   - Otherwise probes for un-powered covers will report "no response" and you
	     can re-run them after powering up.
	3. From the repo root, with the venv active:
	     python tools/probeKa50Covers.py
	4. Read the table.  Re-run after manually resetting any covers that ended up
	   open if you don't want to leave them open.

The probe per cover:
	t0: read arg s0
	send command value=1
	t1: read arg s1  (after settle delay)
	send command value=1 again
	t2: read arg s2

Classification:
	abs(s1 - s2) > 0.5  -> TOGGLE  (second identical send flipped it back)
	abs(s1 - s2) <= 0.5 and s1 > 0.5  -> ABSOLUTE
	otherwise -> NO_RESPONSE / UNKNOWN

This script does NOT restore covers to their original state.  Toggle covers will
end at s0; absolute covers will end at 1 (open).  Manually close any you don't
want left open.
"""

import json
import os
import sys
import time

currentDir = os.path.dirname(os.path.abspath(__file__))
parentDir = os.path.dirname(currentDir)
sys.path.append(parentDir)

from network.DCSDirectManager import DCSDirectManager
from utils.SettingsManager import SettingsManager


SETTLE_DELAY = 1.2   # Seconds to wait for cover animation to finish.
QUERY_TIMEOUT = 1.5  # Seconds per arg-value query.

# All 22 covers built by `animated_guard_switch` in Ka-50 clickabledata.lua.
# (deviceId, commandId, arg, elementName)
COVERS = [
	(2, 3004, 544, 'ELEC_INTERFACE.ENERG_COVER_AKK2_PTR'),
	(22, 3012, 497, 'UV_26.UV26_POWER_COVER_PTR'),
	(42, 3002, 219, 'IFF.COVER_SRO_PTR'),
	(3, 3013, 283, 'FUELSYS_INTERFACE.PAV_CRANE_COVER_CYKLIZATION_PTR'),
	(6, 3004, 217, 'EJECT_SYS_INTERFACE.RIGHT_COVER_EMERG_VACATION_PTR'),
	(2, 3002, 263, 'ELEC_INTERFACE.ENERG_COVER_AER_RIT_PTR'),
	(40, 3010, 247, 'FIRE_EXTING_INTERFACE.BALOONS_COVER_PTR'),
	(40, 3007, 249, 'FIRE_EXTING_INTERFACE.FIREEXT_COVER_PTR'),
	(4, 3016, 569, 'ENGINE_INTERFACE.PAV_CRANE_COVER_VSU_PTR01'),
	(3, 3007, 277, 'FUELSYS_INTERFACE.PAV_CRANE_COVER_ENGINE_LEFT_PTR'),
	(4, 3004, 293, 'ENGINE_INTERFACE.ERD_RIGHT_COVER_PTR'),
	(2, 3006, 265, 'ELEC_INTERFACE.ENERG_COVER_AKK1_PTR'),
	(4, 3002, 291, 'ENGINE_INTERFACE.ERD_LEFT_COVER_PTR'),
	(11, 3002, 57, 'LASERRANGER.LD_LDP_COVER_PTR'),
	(34, 3005, 67, 'CPT_MECH.AVAR_GEAR_COVER_PTR'),
	(5, 3002, 221, 'HYDRO_SYS_INTERFACE.HYDRO_COVER_PTR02'),
	(4, 3018, 570, 'ENGINE_INTERFACE.PAV_CRANE_COVER_VSU_PTR02'),
	(22, 3013, 499, 'UV_26.UV26_TEST_COVER_PTR'),
	(12, 3019, 548, 'WEAP_INTERFACE.SUO_COVER_PTR'),
	(3, 3009, 279, 'FUELSYS_INTERFACE.PAV_CRANE_COVER_ENGINE_RIGHT_PTR'),
	(3, 3011, 281, 'FUELSYS_INTERFACE.PAV_CRANE_COVER_VSU_PTR'),
	(34, 3003, 453, 'CPT_MECH.P_CONTR_VMG_HYDRO_COVER_PTR'),
]


def classify(s0, s1, s2):
	"""Return (label, note) for the (s0, s1, s2) tuple, where each is a float or None."""
	if s0 is None or s1 is None or s2 is None:
		return ('READ_FAIL', f's0={s0} s1={s1} s2={s2}')
	# After 2 sends of value=1: a toggle cover ends at s0; an absolute cover ends at ~1.
	if abs(s1 - 1.0) < 0.2 and abs(s2 - 1.0) < 0.2:
		# Both reads near 1: stayed open across two identical sends -> ABSOLUTE.
		return ('ABSOLUTE', f's0={s0:.2f} s1={s1:.2f} s2={s2:.2f}')
	if abs(s1 - s2) > 0.5:
		# State alternated between the two reads -> TOGGLE.
		return ('TOGGLE', f's0={s0:.2f} s1={s1:.2f} s2={s2:.2f}')
	if abs(s1 - s0) < 0.2 and abs(s2 - s0) < 0.2:
		# Cover never moved -> probably unpowered.
		return ('NO_RESPONSE', f's0={s0:.2f} s1={s1:.2f} s2={s2:.2f}')
	return ('UNKNOWN', f's0={s0:.2f} s1={s1:.2f} s2={s2:.2f}')


def probeOne(mgr, deviceId, commandId, arg, name):
	s0 = mgr.queryArgumentValue(arg, device=0, timeout=QUERY_TIMEOUT)
	if not mgr.sendCommand(deviceId, commandId, 1.0):
		return ('SEND_FAIL', f'sendCommand 1 returned False (s0={s0})')
	time.sleep(SETTLE_DELAY)
	s1 = mgr.queryArgumentValue(arg, device=0, timeout=QUERY_TIMEOUT)
	if not mgr.sendCommand(deviceId, commandId, 1.0):
		return ('SEND_FAIL', f'sendCommand 1 (2nd) returned False (s0={s0} s1={s1})')
	time.sleep(SETTLE_DELAY)
	s2 = mgr.queryArgumentValue(arg, device=0, timeout=QUERY_TIMEOUT)
	return classify(s0, s1, s2)


def main():
	settings = SettingsManager()
	mgr = DCSDirectManager(settings.config)
	mgr.start()

	# Brief wait for connection.
	for _ in range(20):
		if mgr.connected:
			break
		time.sleep(0.1)

	if not mgr.connected:
		print('ERROR: Could not connect to DCSAutoMate Direct (DCS not running, or aircraft not loaded?)')
		mgr.stop()
		return 1

	moduleName = mgr.queryModuleName(timeout=2.0)
	print(f'Connected.  Module: {moduleName!r}')
	if moduleName != 'Ka-50':
		print(f'WARNING: expected module Ka-50, got {moduleName!r}.  Continuing anyway.')

	results = []
	print()
	print(f'{"name":<55} {"dev":>4} {"cmd":>5} {"arg":>5} {"label":<12} note')
	print('-' * 120)
	for deviceId, commandId, arg, name in COVERS:
		label, note = probeOne(mgr, deviceId, commandId, arg, name)
		results.append((name, deviceId, commandId, arg, label, note))
		print(f'{name:<55} {deviceId:>4} {commandId:>5} {arg:>5} {label:<12} {note}')

	# Summary by label.
	print()
	print('Summary:')
	from collections import Counter
	for label, count in Counter(r[4] for r in results).most_common():
		print(f'  {label:<12} {count}')

	# Persist JSON for follow-up analysis.
	outPath = os.path.join(parentDir, 'tools', 'probeKa50Covers.results.json')
	with open(outPath, 'w', encoding='utf-8') as f:
		json.dump([{'name': n, 'deviceId': d, 'commandId': c, 'arg': a, 'label': l, 'note': nt} for (n,d,c,a,l,nt) in results], f, indent=2)
	print(f'\nSaved: {outPath}')

	mgr.stop()
	return 0


if __name__ == '__main__':
	sys.exit(main())
