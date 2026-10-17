"""Control-mapping generator for the AH-64D Apache.

Reads config/nativeExtractions/AH-64D.json and writes
config/controlMappings/AH-64D.json using the explicit archetype dispatch.

All helpers are mapped to explicit archetype functions.  Controls without
a helper tag (anonymous inline table elements in clickabledata.lua) fall
through to the structural processElements() path inside mapUtils.

24 helpers in this module, zero STRUCTURAL_FALLBACK entries.

Helper notes (from clickable_defs.lua):
  mpd_button / eufd_button / ku_button     -- thin wrappers over button_prototype (BTN)
  knuppel_button                           -- BTN with variable arg_value
  default_button                           -- BTN with animation
  Rocker_switch_positive                   -- delegates to short_way_button (BTN, positive)
  Rocker_switch_negative                   -- BTN with arg_value=-1, arg_lim={-1,0}
  lighted_pushbutton                       -- BTN+BTN same command (springloaded shape)
  lighted_pushbutton_cover                 -- TUMB+TUMB same command
  lighted_push_button_tumb                 -- TUMB single element
  default_2_position_tumb                  -- TUMB+TUMB same command
  default_3_position_tumb                  -- TUMB+TUMB same command
  default_red_cover                        -- TUMB+TUMB same command
  default_animated_lever                   -- TUMB+TUMB same command, arg_value={1,0}
  multiposition_switch                     -- TUMB+TUMB same command, delta-step
  wiper_multiposition_spring_switch        -- BTN+TUMB, different cmds, OVERLAPPING
                                              argLims [-0.1,0.2] for both. simpleDiscrete
                                              uses indices[0] (BTN, cmd=PARK, argValue=-0.1)
                                              → 4-pos discrete matching "PARK/OFF/LO/HI".
                                              NOT twoCommandSpringloaded (that gives
                                              positions=3 incorrectly).
  default_axis_limited                     -- LEV single command
  default_rheostat                         -- delegates to default_axis_limited (LEV)
  default_lever                            -- MOVABLE_LEV+MOVABLE_LEV same command
  sunvisor_handle                          -- delegates to default_lever (MOVABLE_LEV)
  springloaded_3_pos_tumb                  -- BTN+BTN, two commands, complementary argLims
  spring_3_position_tumb                   -- TUMB+BTN, two commands, complementary argLims
                                              (TUMB stays, BTN springs back). twoCommandSpringloaded
                                              does not check class — only len(indices)==2.
  default_button_axis                      -- BTN(arg1)+LEV(arg2), split by arg group
  comm_knob                                -- TUMB+TUMB(arg_pull)+LEV(arg_rotate), split
                                              by arg group → simpleDiscrete + continuousAxis
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, twoCommandSpringloaded, rotaryWithMomentary, buttonOrAxis,
)

HELPER_MAP = {
	# BTN controls — single-element, single command
	'mpd_button':                         simpleDiscrete,
	'eufd_button':                        simpleDiscrete,
	'ku_button':                          simpleDiscrete,
	'knuppel_button':                     simpleDiscrete,  # BTN, variable arg_value
	'default_button':                     simpleDiscrete,
	'Rocker_switch_positive':             simpleDiscrete,  # BTN, arg_value=+1
	'Rocker_switch_negative':             simpleDiscrete,  # BTN, arg_value=-1, arg_lim={-1,0}
	# BTN+BTN same command (springloaded shape but single-command → simpleDiscrete)
	'lighted_pushbutton':                 simpleDiscrete,
	# TUMB+TUMB same command
	'lighted_pushbutton_cover':           simpleDiscrete,
	'default_2_position_tumb':            simpleDiscrete,
	'default_3_position_tumb':            simpleDiscrete,
	'default_red_cover':                  simpleDiscrete,
	'default_animated_lever':             simpleDiscrete,  # TUMB+TUMB, arg_value={1,0}
	'multiposition_switch':               simpleDiscrete,
	# TUMB single element
	'lighted_push_button_tumb':           simpleDiscrete,
	# BTN+TUMB, different cmds, overlapping argLims [-0.1,0.2].
	# TUMB is the latch (stopAction=0, step=0.1 < range=0.3), BTN is momentary
	# (stopAction≠0, argValue=-0.1 → extendLow). Produces 5-position positionMap
	# using the TUMB's cmd for all positions (range extended down by one step).
	'wiper_multiposition_spring_switch':  rotaryWithMomentary,
	# LEV axis controls
	'default_axis_limited':               continuousAxis,
	'default_rheostat':                   continuousAxis,  # wraps default_axis_limited
	# MOVABLE_LEV+MOVABLE_LEV, same command.
	# continuousAxis hardcodes 'LEV' to classifyType — never reads element class.
	'default_lever':                      continuousAxis,
	'sunvisor_handle':                    continuousAxis,  # wraps default_lever
	# 3-pos springloaded: two different commands, same arg, complementary argLims
	'springloaded_3_pos_tumb':            twoCommandSpringloaded,  # BTN+BTN
	'spring_3_position_tumb':             twoCommandSpringloaded,  # TUMB+BTN
	# Multi-arg compound controls: BTN/TUMB group at one arg + LEV at another.
	# buttonOrAxis dispatches per-arg-group to simpleDiscrete or continuousAxis.
	'default_button_axis':                buttonOrAxis,
	'comm_knob':                          buttonOrAxis,  # TUMB+TUMB(pull) + LEV(rotate)
}

if __name__ == '__main__':
	runMapping('AH-64D_BLK_II', HELPER_MAP, extractionName='AH-64D')
