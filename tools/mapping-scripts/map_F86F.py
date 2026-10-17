"""Control-mapping generator for the F-86F Sabre.

Reads config/nativeExtractions/F-86F Sabre.json and writes
config/controlMappings/F-86F Sabre.json using the explicit archetype dispatch.

DCS internal name: F-86F Sabre  (→ output file and moduleName)
Extraction name:   F-86F Sabre  (→ same as module name)

17 helpers actively used.  All explicitly mapped.  Zero STRUCTURAL_FALLBACK.
23 inline elements (no helper tag) use structural inference via processElements().

Helper notes:

  # Simple button controls (single BTN with stop_action)
  default_button / stick_button / default_button_with_lamp / default_button_soft
    -- BTN, stop_action, arg_val default=1 → simpleDiscrete
    -- Variants differ only in sound/appearance, identical structure

  # 2-position TUMB controls (same command, two positions)
  default_2_position_tumb
    -- 2x TUMB same cmd, argVals=[1,−1], argLim=[{0,1},{0,1}] → simpleDiscrete
  default_2_position_btn
    -- same structure as default_2_position_tumb, different VR class → simpleDiscrete
  default_red_cover
    -- same structure as default_2_position_tumb, cover sound → simpleDiscrete
  default_2_position_tumb11
    -- 2x TUMB same cmd, argVals=[2,−2], argLim=[{−1,1},{−1,1}]
       (center=0 is neutral/off, argLim spans −1 to 1) → simpleDiscrete
  default_animated_lever
    -- 2x TUMB same cmd, argVals=[1,−1], animated=true → simpleDiscrete

  # 3-position TUMB controls
  default_3_position_tumb
    -- 2x TUMB same cmd, argVals=[−av,+av], cycled=true (default), inversed_
       optional, arg_limit_ optional → simpleDiscrete (3-pos)

  # Multi-position TUMB controls (delta-step)
  multiposition_switch
    -- 2x TUMB same cmd, delta-step, cycled (default) → simpleDiscrete
  multiposition_switch_limited
    -- same as multiposition_switch, cycle=false → simpleDiscrete

  # Axis / lever controls
  default_axis
    -- single LEV; relative=False (default) → continuousAxis
  default_axis_limited
    -- single LEV, custom argLim → continuousAxis
  default_movable_axis
    -- 2x MOVABLE_LEV same cmd same arg, argLim=[{0,1},{0,1}]
       (bombing altimeter handler, rocket depression pointer, wing span knob)
       incIdx=indices[0] → continuousAxis

  # Springloaded 3-pos with TWO commands (one per direction)
  default_button_tumb
    -- BTN+TUMB, DIFFERENT cmds (cmd1,cmd2), same arg, stop_action={cmd1,0}
       argVals=[−1,+1], argLim=[−1,0]/[0,1] → twoCommandSpringloaded
  springloaded_3_pos_tumb
    -- BTN+BTN, DIFFERENT cmds (cmd1,cmd2), both stop_action
       argVals=[val1,val3], argLim=[val1,0]/[0,val3] → twoCommandSpringloaded

Unused helpers (defined in clickabledata.lua but zero usages):
  default_1_position_tumb, default_button_axis, default_springloaded_tumb,
  radio_wheel
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, twoCommandSpringloaded,
	STRUCTURAL_FALLBACK,
)

HELPER_MAP = {
	# ── Button controls (BTN, stop_action) ───────────────────────────────────
	'default_button':                               simpleDiscrete,
	'stick_button':                                 simpleDiscrete,
	'default_button_with_lamp':                     simpleDiscrete,
	'default_button_soft':                          simpleDiscrete,

	# ── 2-position TUMB / lever / cover controls ──────────────────────────────
	'default_2_position_tumb':                      simpleDiscrete,
	'default_2_position_btn':                       simpleDiscrete,
	'default_red_cover':                            simpleDiscrete,
	'default_2_position_tumb11':                    simpleDiscrete,
	'default_animated_lever':                       simpleDiscrete,

	# ── 3-position TUMB controls ──────────────────────────────────────────────
	'default_3_position_tumb':                      simpleDiscrete,

	# ── Multi-position TUMB controls ──────────────────────────────────────────
	'multiposition_switch':                         simpleDiscrete,
	'multiposition_switch_limited':                 simpleDiscrete,

	# ── Axis / lever controls ─────────────────────────────────────────────────
	'default_axis':                                 continuousAxis,
	'default_axis_limited':                         continuousAxis,
	'default_movable_axis':                         continuousAxis,

	# ── Springloaded 3-pos with TWO commands (one per direction) ──────────────
	'default_button_tumb':                          twoCommandSpringloaded,
	'springloaded_3_pos_tumb':                      twoCommandSpringloaded,
}

if __name__ == '__main__':
	runMapping('F-86F Sabre', HELPER_MAP)
