"""Control mapping generator for AJS37 Viggen.

Explicit helper-handler map for all Lua helper functions used in:
  c:/Games/DCS World/Mods/aircraft/AJS37/Cockpit/scripts/clickabledata.lua

Every helper that appears in the nativeExtraction MUST have an entry here.
Adding a new helper to AJS37's clickabledata.lua will cause this script to
fail with a clear error rather than silently misclassifying controls.

Helper counts from nativeExtraction (exhaustive tagging, 2026):
  default_button:                      62
  default_2_position_tumb:             40
  default_axis_limited:                21
  multiposition_switch_limited:         9
  default_animated_lever:               9
  default_3_position_tumb:              8
  default_2_position_tumb_altsound01:   8
  multiposition_switch_limited_metallic: 6
  default_2_way_spring_switch:          5
  default_2_position_tumb_flipcover:    4
  default_axis:                         4
  default_1_position_tumb:              1
  NO_HELPER (inline table):             1 (AltsetL-PTR — altimeter knob, STRUCTURAL_FALLBACK)

AJS37 notes:
  - All factory helpers are defined inline in clickabledata.lua (no separate
    clickable_defs.lua).
  - default_2_way_spring_switch: BTN+BTN, same cmd, av=[±1], complementary
    argLims ({0,1}/{-1,0}) — spring-centred 2-way switch → simpleDiscrete.
  - default_animated_lever: TUMB+TUMB, same cmd, av=[1,0], argLim=[{0,1}],
    cycle=true — lever with animation (gear handle, reverser, etc.) → simpleDiscrete.
  - default_axis: LEV class, relative=True (all 4 uses are radio frequency knobs
    with relative=True) → continuousAxis handles relative LEV controls.
  - default_axis_limited: LEV class, relative=False for most but True for one
    (PNT_126 backup altimeter) → continuousAxis handles both relative values.
  - The one inline-table (AltsetL-PTR) has no helper tag and falls through to
    STRUCTURAL_FALLBACK automatically.
"""

from mapUtils import (
	runMapping,
	STRUCTURAL_FALLBACK,
	simpleDiscrete,
	continuousAxis,
)

HELPER_MAP = {
	# Standard momentary button: BTN, single sub-control, stopAction set.
	'default_button':                       simpleDiscrete,

	# 2-position TUMB toggles: TUMB+TUMB, same cmd, av=[1,-1], argLim={0,1}.
	'default_2_position_tumb':              simpleDiscrete,
	'default_2_position_tumb_altsound01':   simpleDiscrete,
	'default_2_position_tumb_flipcover':    simpleDiscrete,

	# 3-position TUMB toggle: TUMB+TUMB, same cmd, av=[1,-1], argLim={-1,1}.
	'default_3_position_tumb':              simpleDiscrete,

	# Animated lever: TUMB+TUMB, same cmd, av=[1,0], argLim={0,1}, cycle=true.
	# Used for gear handle, reverser, ejection seat arm, etc.
	'default_animated_lever':               simpleDiscrete,

	# Spring-centred 2-way switch: BTN+BTN, same cmd, av=[1,-1],
	# complementary argLims ({0,1}/{-1,0}) → 2-position discrete via i=0 path.
	'default_2_way_spring_switch':          simpleDiscrete,

	# Single TUMB 1-position control (used for missile select button).
	'default_1_position_tumb':              simpleDiscrete,

	# Multi-position TUMB rotaries: TUMB+TUMB, same cmd, small argValue step.
	# multiposition_switch is the unlimited variant (no cycle=false; transponder code wheels).
	'multiposition_switch':                 simpleDiscrete,
	'multiposition_switch_limited':         simpleDiscrete,
	'multiposition_switch_limited_metallic': simpleDiscrete,

	# Continuous axis controls: LEV class, argLim defines range.
	# default_axis uses relative=True (radio frequency knobs).
	# default_axis_limited uses relative=False/True depending on control.
	# continuousAxis reads the relative field from each element.
	'default_axis_limited':                 continuousAxis,
	'default_axis':                         continuousAxis,
}

if __name__ == '__main__':
	runMapping('AJS37', HELPER_MAP)
