"""Control mapping generator for OH-58D Kiowa Warrior.

Explicit helper-handler map for all Lua helper functions used in:
  c:/Games/DCS World/Mods/aircraft/OH-58D/Cockpit/clickabledata.lua

Every helper that appears in the nativeExtraction MUST have an entry here.
Untagged elements (structural fallback for inline-table controls) are handled
automatically.

Helper counts from nativeExtraction (exhaustive tagging):
  default_button:                 114
  circuit_breaker:                 74
  default_2_position_tumb:         55
  default_button_tumb:             35
  default_axis_limited:            18
  default_tumbler_axis:            10
  multiposition_switch_limited:     9
  default_3_position_tumb:          7
  default_axis:                     4
  default_3_position_button:        2
  two_axis_lever:                   1
  springloaded_3_pos_tumb:          1
  default_movable_axis:             1
  default_button_axis:              1
  default_button_vr_all_sides:      1

Notes:
  - default_button_tumb (BTN+TUMB, two different commands, argLim={{-1,0},{0,1}})
    maps to twoCommandSpringloaded.  All 3 style variants produce the same
    complementary-argLim shape that twoCommandSpringloaded expects.
  - springloaded_3_pos_tumb: normally BTN+BTN with two different commands →
    twoCommandSpringloaded.  OH-58D has one same-command instance
    (HLP_DESIG_BUTTON) where the positive direction is a module bug and only
    the dec direction works → springloaded3PosTumb produces positions=2.
  - default_3_position_tumb (TUMB+TUMB, SAME command, argLim={{-1,1},{-1,1}})
    maps to simpleDiscrete — same-command so not a dual-command rotary; indices[0]
    path gives argLim=[-1,1], step=1.0, positions=3.
  - default_3_position_button (BTN+BTN, SAME command, argLim={{-1,1},{-1,1}})
    same analysis as above → simpleDiscrete → 3 positions.
  - default_button_axis and default_tumbler_axis have DIFFERENT args for the two
    sub-controls, so the dispatch groups them separately.  buttonOrAxis delegates
    to simpleDiscrete for BTN/TUMB and continuousAxis for LEV.
  - two_axis_lever (LEV+LEV) also has DIFFERENT args — each gets its own
    continuousAxis via buttonOrAxis.
  - circuit_breaker is structurally identical to default_2_position_tumb.
"""

from mapUtils import (
	runMapping,
	simpleDiscrete,
	continuousAxis,
	twoCommandSpringloaded,
	buttonOrAxis,
)


def springloaded3PosTumb(elem, indices, ctx):
	"""Handles springloaded_3_pos_tumb where both sub-controls share the same commandId.

	When cmd0 == cmd1 the positive direction is not actionable in DCS — only the
	negative direction works physically (e.g. HLP_DESIG_BUTTON: target designate
	down).  Produces a simpleDiscrete-style control (no positionMap) using the dec
	direction's argLim:
	  Position 0 (dec/active):    sends argLim[0] (e.g. -1.0) — activates the switch.
	  Position 1 (center/release): sends argLim[1] (e.g.  0.0) — releases the spring.
	Using argLim+step instead of positionMap avoids the trailing-null interpolation
	bug: a positionMap [active, None] has no right anchor for the null entry, so
	reverse translation collapses both positions to -1.0 and the Current display
	never changes from position 0.

	When cmd0 != cmd1, delegates to twoCommandSpringloaded.
	"""
	if len(indices) != 2:
		return None

	actions = elem.get('action', [])
	i0, i1 = indices
	cmd0 = actions[i0] if i0 < len(actions) else 0
	cmd1 = actions[i1] if i1 < len(actions) else 0
	if not cmd0 or not cmd1:
		return None

	if cmd0 != cmd1:
		return twoCommandSpringloaded(elem, indices, ctx)

	# Same-command: only the dec (lower argValue) direction is usable.
	argValues = elem.get('argValue', [])
	argLims = elem.get('argLim', [])
	args = elem.get('arg', [])

	val0 = argValues[i0] if i0 < len(argValues) else 0.0
	val1 = argValues[i1] if i1 < len(argValues) else 0.0
	decIdx = i0 if val0 <= val1 else i1

	decCmd = actions[decIdx]
	decArgLim = argLims[decIdx] if decIdx < len(argLims) else None

	if not (isinstance(decArgLim, list) and len(decArgLim) == 2 and decArgLim[0] != decArgLim[1]):
		return None

	arg = args[decIdx] if decIdx < len(args) else 0

	# Encode as simpleDiscrete over the dec argLim range.
	# step = full range width so that:
	#   pos 0 native = argLim[0] + step*0 = argLim[0]  (e.g. -1.0, activate)
	#   pos 1 native = argLim[0] + step*1 = argLim[1]  (e.g.  0.0, release)
	argStep = round(decArgLim[1] - decArgLim[0], 6)
	canonical = ctx.canonical(decCmd, arg)
	control = {
		**ctx.meta(),
		'type': 'discrete',
		'deviceId': ctx.deviceId,
		'commandId': decCmd,
		'argLim': [round(decArgLim[0], 6), round(decArgLim[1], 6)],
		'step': argStep,
		'positions': 2,
	}
	if arg != 0:
		control['arg'] = arg
	control['elementName'] = ctx.elemKey
	return {canonical: control}

HELPER_MAP = {
	# Momentary push buttons.
	'default_button':                  simpleDiscrete,
	'default_button_vr_all_sides':     simpleDiscrete,

	# 2-position toggle switches and circuit breakers.
	'default_2_position_tumb':         simpleDiscrete,
	'circuit_breaker':                 simpleDiscrete,

	# 3-position switches (same command, argLim=[-1,1], step=1.0, positions=3).
	'default_3_position_tumb':         simpleDiscrete,
	'default_3_position_button':       simpleDiscrete,

	# N-position selector switches.
	'multiposition_switch_limited':    simpleDiscrete,

	# Continuous axes.
	'default_axis':                    continuousAxis,
	'default_axis_limited':            continuousAxis,
	'default_movable_axis':            buttonOrAxis,

	# Spring-loaded 3-position (BTN+BTN or BTN+TUMB, two different commands).
	# Same-command variant (HLP_DESIG_BUTTON) → positions=2 via module-local function.
	'springloaded_3_pos_tumb':         springloaded3PosTumb,
	'default_button_tumb':             twoCommandSpringloaded,

	# Compound push+axis and toggle+axis (different args per sub-control).
	'default_button_axis':             buttonOrAxis,
	'default_tumbler_axis':            buttonOrAxis,

	# Dual-axis lever (grease pencil) — LEV+LEV with different args.
	'two_axis_lever':                  buttonOrAxis,
}


if __name__ == '__main__':
	runMapping('OH58D', HELPER_MAP, extractionName='OH-58D')
