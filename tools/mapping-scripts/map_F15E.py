"""Explicit helper-handler map script for the F-15E Strike Eagle (F-15ESE).

Run this script to regenerate config/controlMappings/F-15ESE.json.

Helper distribution (from config/nativeExtractions/F-15E.json):
  default_button                                     223
  default_2_position_tumb_animated                    70
  default_axis_limited                                49
  multiposition_switch_limited_animated               32
  MFDG_button_negative                                21
  MFDG_button_positive                                21
  default_3_position_tumb_animated                    18
  None                                                 6
  springloaded_3_pos_tumb                              6
  default_button_lever_cycled                          4
  multiposition_switch_limited                         3
  Mirror_Adjust_Control                                3
  wca_knob                                             2
  default_2_way_spring_switch                          2
  auxadi_knob                                          2
  Pull_And_Rotate_Control_Handle                       2
  LDG_Gear_Control_Lever                               1
  default_2_position_tumb                              1
  fuel_mon_multiposition_switch_limited                1
  default_3_position_tumb                              1
  multiposition_switch                                 1

None-tagged elements (6): all TUMB+TUMB, same cmd, av=[1,0] — emergency
handles (canopy jettison, vent, brake/steering, landing gear).  These go
through the structural dispatch which correctly resolves them as 2-position
discrete controls.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	STRUCTURAL_FALLBACK,
	simpleDiscrete,
	continuousAxis,
	rotaryWithMomentary,
	buttonOrAxis,
)

HELPER_MAP = {
	# Single BTN sub-control with stopAction set — standard momentary button.
	'default_button':                                   simpleDiscrete,

	# 2-position TUMB toggles: TUMB+TUMB, same cmd, av=[1,-1], argLim=[0,1].
	'default_2_position_tumb_animated':                 simpleDiscrete,
	'default_2_position_tumb':                          simpleDiscrete,

	# Single LEV continuous axis (relative=False).
	'default_axis_limited':                             continuousAxis,

	# Multi-position TUMB rotaries: TUMB+TUMB, same cmd, small av step.
	'multiposition_switch_limited_animated':            simpleDiscrete,
	'multiposition_switch_limited':                     simpleDiscrete,
	'multiposition_switch':                             simpleDiscrete,
	# Fuel monitor variant: TUMB+TUMB, same cmd, but i=0 has stopAction set
	# (momentary extend-low direction, av=-0.1).  Structural detectRotaryWithMomentary
	# picks up the i=1 latch (av=+0.1, lim=[-0.1,0.5], step=0.1, 6 positions) and
	# extends one step below the latch (extendLow) → 8-position positionMap from -0.2.
	'fuel_mon_multiposition_switch_limited':            rotaryWithMomentary,

	# MFD guard buttons: single BTN with half-range argLim ([−1,0] or [0,1]).
	'MFDG_button_negative':                             simpleDiscrete,
	'MFDG_button_positive':                             simpleDiscrete,

	# 3-position TUMB toggles: TUMB+TUMB, same cmd, av=[-1,1] or [1,-1],
	# argLim=[-1,1].
	'default_3_position_tumb_animated':                 simpleDiscrete,
	'default_3_position_tumb':                          simpleDiscrete,

	# Springloaded 3-position switch: 5 of 6 are BTN+BTN, same cmd, av=[-1,1],
	# mismatched argLims → i=0 path, positions=3 via structural dispatch.
	# PTN_508 is the exception: BTN+BTN with DIFFERENT cmds (3508/508) and
	# same arg=0 → isPositionMapElement=True → structural buildPositionMap
	# produces a 3-entry positionMap with a null for the missing middle position.
	# STRUCTURAL_FALLBACK covers both sub-patterns correctly.
	'springloaded_3_pos_tumb':                          STRUCTURAL_FALLBACK,

	# Landing-gear control lever: TUMB+TUMB, same cmd, av=[1,0], argLim=[0,1]
	# → 2-position discrete via i=0 path.
	'LDG_Gear_Control_Lever':                           simpleDiscrete,

	# Spring-centred 2-way switch: BTN+BTN, same cmd, av=[1,-1],
	# complementary argLims ([-1,0]/[0,1]) → 2-position discrete via i=0 path.
	'default_2_way_spring_switch':                      simpleDiscrete,

	# Multi-group elements — dispatch per arg group by first sub-control class:
	# BTN/TUMB group → simpleDiscrete, LEV group → continuousAxis.

	# BTN+LEV with two distinct args: BTN group → discrete; LEV group
	# with relative=True → continuousAxis (type=relative, sendProtocol=C).
	'default_button_lever_cycled':                      buttonOrAxis,

	# BTN+BTN+LEV with two distinct args: BTN+BTN group → discrete;
	# LEV group → continuousAxis.
	'auxadi_knob':                                      buttonOrAxis,

	# TUMB+TUMB with TWO DIFFERENT args (e.g. arg=[386, 430]) — each sub-
	# control forms its own single-element arg group → each resolves as
	# simpleDiscrete independently.
	'Pull_And_Rotate_Control_Handle':                   buttonOrAxis,

	# --- STRUCTURAL_FALLBACK: structural dispatch is required ---

	# arg=[] → argGroups empty → no controls emitted regardless of archetype.
	# Structural fallback is cleaner here.
	'Mirror_Adjust_Control':                            STRUCTURAL_FALLBACK,

	# LEV+BTN+BTN all same arg.  Structural wcaKnob branch (triggered by
	# helper='wca_knob' tag) emits TWO controls per element: one continuous
	# LEV axis (sendProtocol=S) plus one springloaded discrete BTN.  There is
	# no single-output archetype that matches this dual-emit pattern.
	'wca_knob':                                         STRUCTURAL_FALLBACK,
}

if __name__ == '__main__':
	runMapping('F-15ESE', HELPER_MAP, extractionName='F-15E')
