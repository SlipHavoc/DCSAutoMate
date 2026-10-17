"""Decisions Auto Select makes from DCS telemetry."""

# Well above cold-engine RPM noise (C-101CC reads up to ~0.001), well below idle even if a module reports a 0-1 fraction.
RUNNING_RPM_THRESHOLD = 0.05


def isEngineRunning(engineInfo):
	"""True if any engine in LoGetEngineInfo() shows RPM above the running threshold."""
	rpm = (engineInfo or {}).get('RPM')
	values = rpm.values() if isinstance(rpm, dict) else [rpm]
	return any(isinstance(v, (int, float)) and not isinstance(v, bool) and v > RUNNING_RPM_THRESHOLD for v in values)


class AutoSelectContext:
	"""What an aircraft script's autoSelect(context) can see: the script Auto Select picked, the telemetry, and live cockpit reads."""

	def __init__(self, script, telemetry, readControls):
		self.script = script
		self.telemetry = telemetry
		self.readControls = readControls # Callable taking a list of control names, returning {name: value} for those DCS answered.
		self.reads = {} # Everything read, for the Auto Select report.

	def read(self, *controls):
		"""Current values of the given controls (script convention, as a script would send them) in one batch; None where DCS didn't answer."""
		values = self.readControls(list(controls)) or {}
		result = {control: values.get(control) for control in controls}
		self.reads.update(result)
		return result


def applyModuleAutoSelect(module, context):
	"""Run the aircraft script's optional autoSelect(context); returns what it wants to change, e.g. {'script': ..., 'vars': {...}}."""
	hook = getattr(module, 'autoSelect', None)
	if not callable(hook):
		return {}
	return hook(context) or {}


def classifyPosition(altAGL, altMSL, trueAirSpeed):
	"""'ground' under 5 m AGL; 'carrier' at deck height (15 to 25 m MSL, AGL about MSL) under 40 m/s; else 'air'."""
	if altAGL < 5:
		return 'ground'
	if altAGL - altMSL < 2 and 15 < altMSL < 25 and trueAirSpeed < 40:
		return 'carrier'
	return 'air'


def timeOfDay(clockSeconds):
	"""'day' from 06:00 to 20:00 mission time, else 'night'."""
	seconds = clockSeconds % 86400
	return 'day' if 6 * 3600 <= seconds <= 20 * 3600 else 'night'


def _clock(seconds):
	seconds = int(seconds) % 86400
	return f'{seconds // 3600:02d}:{seconds // 60 % 60:02d}:{seconds % 60:02d}'


def _rpmText(engineInfo):
	rpm = (engineInfo or {}).get('RPM')
	if isinstance(rpm, dict):
		return 'RPM ' + ', '.join(f'{side} {value:.1f}' for side, value in rpm.items() if isinstance(value, (int, float)))
	if isinstance(rpm, (int, float)):
		return f'RPM {rpm:.1f}'
	return 'RPM unknown'


def _valueText(value):
	return f'{value:g}' if isinstance(value, float) else str(value)


def autoSelectReport(aircraft, scriptFile, altAGL, altMSL, trueAirSpeed, engineInfo, clockSeconds, script, hookReads, hookResult, setVars, unsetVars):
	"""Output lines saying what Auto Select detected, the rule behind each choice, and what it set."""
	position = classifyPosition(altAGL, altMSL, trueAirSpeed)
	positionText = {
		'ground': f'on the ground (AGL {altAGL:.1f} m; under 5 m is the ground)',
		'carrier': f'on a carrier deck (AGL {altAGL:.1f} m, MSL {altMSL:.1f} m, TAS {trueAirSpeed:.1f} m/s; deck is 15 to 25 m MSL under 40 m/s)',
		'air': f'in the air (AGL {altAGL:.1f} m, TAS {trueAirSpeed:.1f} m/s)',
	}[position]
	lines = [
		'Auto Select:',
		f'  Aircraft: {aircraft} ({scriptFile} scripts)',
		f'  Position: {positionText}',
		f"  Engines: {'running' if isEngineRunning(engineInfo) else 'off'} ({_rpmText(engineInfo)}; over {RUNNING_RPM_THRESHOLD:g} is running)",
	]
	if clockSeconds is None:
		lines.append('  Mission time: unknown, so time of day not set')
	else:
		lines.append(f'  Mission time: {_clock(clockSeconds)}, so {timeOfDay(clockSeconds)} (06:00 to 20:00)')
	lines.append(f'  Script: {script}')
	parts = []
	if hookReads:
		parts.append('read ' + ', '.join(f'{control} = {_valueText(value)}' for control, value in hookReads.items()))
	if hookResult.get('script'):
		parts.append(f"chose {hookResult['script']}")
	if hookResult.get('vars'):
		parts.append('set ' + ', '.join(f'{name} = {value}' for name, value in hookResult['vars'].items()))
	if parts:
		reason = f" ({hookResult['reason']})" if hookResult.get('reason') else ''
		lines.append(f'  {scriptFile} autoSelect ' + ', and '.join(parts) + reason)
	if setVars:
		lines.append('  Set: ' + ', '.join(setVars))
	if unsetVars:
		lines.append('  Not set, please choose: ' + ', '.join(unsetVars))
	return lines
