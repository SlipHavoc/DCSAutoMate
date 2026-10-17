"""Control mapping generator for C-101CC.

Explicit helper-handler map for all Lua helper functions used in:
  c:/Games/DCS World/Mods/aircraft/C-101/Cockpit/C-101CC/clickabledata.lua
  (which dofiles Common/clickabledata_common.lua)

Every helper that appears in the nativeExtraction MUST have an entry here.
15 untagged elements (local-function controls, inline table literals) use
structural fallback automatically.

Helper counts from nativeExtraction (exhaustive tagging):
  default_button:                        73
  multiposition_switch:                  72
  default_axis:                          51
  default_button_axis:                   17
  default_axis_limited:                  16
  multiposition_switch_cycled_relative:  12
  springloaded_2pos_switch:              12
  intercom_rotate_tumb:                  16
  default_2_position_tumb:               85
  springloaded_thumb:                     5
  default_button_tumb:                    1
  default_2_tumb_button:                  2
  springloaded_1pos_switch2:              1
  pedals_adj_control:                     2
  ADF_freq_set_knob:                      2

All helper functions are defined in Common/clickabledata_common.lua except
ADF_freq_set_knob which is a global function in C-101CC/clickabledata.lua.
"""

from mapUtils import (
	runMapping,
	simpleDiscrete,
	continuousAxis,
	springloadedTumb,
	twoCommandSpringloaded,
	buttonOrAxis,
	wheelControl,
)

# IFF code dial args: PNT-M1D1-CPD through PNT-M3A4-CPD.
# Lua defines count=10 (argLim=[0, 0.9]) but the flight model enforces octal
# digits 0-7, so only 8 positions (argLim=[0.0, 0.7]) are physically reachable.
_IFF_DIAL_ARGS = frozenset([355, 356, 357, 358, 359, 360])

def c101MultipositionSwitch(elem, indices, ctx):
	# Delegate to simpleDiscrete first, then patch two C-101-specific quirks.
	result = simpleDiscrete(elem, indices, ctx)
	if result is None:
		return None

	argLims = elem.get('argLim', [])
	lim = argLims[0] if argLims else [0.0, 1.0]

	# count=1 in Lua produces argLim=[x, x] (zero range) — a true DCS toggle.
	# Any command send flips state; absolute-position set is not possible.
	if isinstance(lim, list) and len(lim) == 2 and abs(lim[1] - lim[0]) < 1e-9:
		for ctrl in result.values():
			ctrl['type'] = 'toggle'
			ctrl['argLim'] = [0.0, 1.0]
			ctrl.pop('positions', None)
			ctrl.pop('step', None)
		return result

	# IFF code dials: Lua says count=10 but FM enforces octal (0-7).
	args = elem.get('arg', [])
	if args and args[0] in _IFF_DIAL_ARGS:
		for ctrl in result.values():
			ctrl['positions'] = 8
			ctrl['argLim'] = [0.0, 0.7]
			ctrl['step'] = 0.1
		return result

	return result


def c101PedalsAdjControl(elem, indices, ctx):
	# Delegate to buttonOrAxis, then fix the BTN sub-control's argLim.
	# The Lua arg_lim for the pull-handle is the visual animation range
	# {1, 0} (= [1.0, 0.0]), but the actual DCS arg value when pulled is
	# argValue = -1.0.  Override argLim[1] with argValue so that pos 1
	# maps to the correct native value.
	result = buttonOrAxis(elem, indices, ctx)
	if result is None:
		return None
	i = indices[0]
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	argValue = argValues[i] if i < len(argValues) else None
	lim = argLims[i] if i < len(argLims) else None
	if (
		isinstance(lim, list) and len(lim) == 2
		and argValue is not None
		and abs(argValue - lim[1]) > 1e-9
	):
		for ctrl in result.values():
			if ctrl.get('type') == 'discrete':
				ctrl['argLim'] = [round(lim[0], 6), round(argValue, 6)]
				# Step must equal (argLim[1] - argLim[0]) so the send/receive
				# formulas (argLim[0] + step * pos) work for inverted ranges.
				ctrl['step'] = round(argValue - lim[0], 6)
	return result

HELPER_MAP = {
	# Plain discrete toggle / multi-position switches.
	'default_button':                       simpleDiscrete,
	'default_2_position_tumb':              simpleDiscrete,
	'multiposition_switch':                 c101MultipositionSwitch,
	'springloaded_thumb':                   simpleDiscrete,
	'default_2_tumb_button':                simpleDiscrete,
	'default_button_tumb':                  twoCommandSpringloaded,

	# Continuous / relative axes.
	'default_axis':                         continuousAxis,
	'default_axis_limited':                 continuousAxis,

	# Multi-class helpers: BTN+LEV, TUMB+TUMB+LEV, BTN+MOVABLE_LEV.
	'default_button_axis':                  buttonOrAxis,
	'intercom_rotate_tumb':                 buttonOrAxis,
	'pedals_adj_control':                   c101PedalsAdjControl,
	'ADF_freq_set_knob':                    buttonOrAxis,

	# Spring-loaded switches with two distinct commands.
	'springloaded_2pos_switch':             twoCommandSpringloaded,
	'springloaded_1pos_switch2':            twoCommandSpringloaded,

	# Cycled relative encoder wheels (radio frequency selectors).
	'multiposition_switch_cycled_relative': wheelControl,
}

if __name__ == '__main__':
	runMapping('C-101CC', HELPER_MAP)
