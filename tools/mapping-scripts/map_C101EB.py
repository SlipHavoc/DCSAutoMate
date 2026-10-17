"""Control mapping generator for C-101EB.

Explicit helper-handler map for all Lua helper functions used in:
  c:/Games/DCS World/Mods/aircraft/C-101/Cockpit/C-101EB/clickabledata.lua
  (which dofiles Common/clickabledata_common.lua)

Every helper that appears in the nativeExtraction MUST have an entry here.
Untagged elements (local-function controls, inline table literals) use
structural fallback automatically.

The EB variant uses a strict subset of the CC helper functions (no EB-only
helpers). CC-only helpers (ADF_freq_set_knob, multiposition_switch_cycled_relative,
springloaded_1pos_switch2) are absent from the EB clickabledata and are not
included here.

Helper counts from nativeExtraction (exhaustive tagging):
  default_2_position_tumb:  (largest group, front+rear seat duplicates)
  default_button:           (large group, common panel buttons)
  multiposition_switch:     (covers/guards and multi-pos switches)
  default_axis:             (axis controls)
  default_button_axis:      (cage knob, test buttons with axis)
  default_axis_limited:     (limited range axes)
  springloaded_2pos_switch: (3-position spring-loaded switches)
  intercom_rotate_tumb:     (intercom combined switch+volume controls)
  springloaded_thumb:       (momentary spring-loaded thumbs)
  default_button_tumb:      (generator switch: BTN+TUMB)
  default_2_tumb_button:    (start switch: TUMB+BTN)
  pedals_adj_control:       (rudder pedal adjustment)
"""

from mapUtils import (
	runMapping,
	simpleDiscrete,
	continuousAxis,
	twoCommandSpringloaded,
	buttonOrAxis,
)

def c101MultipositionSwitch(elem, indices, ctx):
	# count=1 in Lua produces argLim=[x, x] (zero range), but the observable arg
	# range is [0, 1] — same shape as animated_guard_switch / binaryToggle.
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
	'default_button':           simpleDiscrete,
	'default_2_position_tumb':  simpleDiscrete,
	'multiposition_switch':     c101MultipositionSwitch,
	'springloaded_thumb':       simpleDiscrete,
	'default_2_tumb_button':    simpleDiscrete,
	'default_button_tumb':      twoCommandSpringloaded,

	# Continuous / relative axes.
	'default_axis':             continuousAxis,
	'default_axis_limited':     continuousAxis,

	# Multi-class helpers: BTN+LEV, TUMB+TUMB+LEV, BTN+MOVABLE_LEV.
	'default_button_axis':      buttonOrAxis,
	'intercom_rotate_tumb':     buttonOrAxis,
	'pedals_adj_control':       c101PedalsAdjControl,

	# Spring-loaded switches with two distinct commands.
	'springloaded_2pos_switch': twoCommandSpringloaded,
}

if __name__ == '__main__':
	runMapping('C-101EB', HELPER_MAP)
