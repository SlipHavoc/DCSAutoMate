"""Explicit helper-handler map script for the CH-47F Chinook (bl1).

Run this script to regenerate config/controlMappings/CH-47Fbl1.json.

Helper distribution (from config/nativeExtractions/CH-47Fbl1.json):
  pdp_special                                        223
  mfd_special_key                                    160
  cdu_special                                        150
  comm_knob                                           66
  animated_rocker_small                               44
  animated_tumbler_small                              38
  animated_button                                     33
  axis_limited                                        32
  button                                              30
  action_button                                       30
  animated_multiposition_switch_limited               28
  animated_tumbler                                    23
  animated_multiposition_switch_limited_small         11
  axis                                                 9
  (none)                                               4
  vhf_radio_wheel                                      4
  animated_rocker                                      3
  multiposition_switch_limited                         3
  rocker                                               3
  MultiFunctionKnob                                    2
  multiposition_switch_cyclic                          2
  rocker_and_axis_limited                              2
  button_and_axis_limited                              2
  default_button                                       1
  multiposition_switch_tumb                            1
  multiposition_switch_limited_1_side                  1
  default_tumb_button                                  1
  animated_pull_handle                                 1

The bulk of the output (≈7 100 entries) is type=raw controls emitted by
processRawCommands() for command-table entries that have no physical element
binding (AI-crew and _ITER/_AXIS/_EXT siblings).
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete,
	continuousAxis,
	twoCommandSpringloaded,
	wheelControl,
	buttonOrAxis,
	pdpSpecial,
)

HELPER_MAP = {
	# Circuit-breaker push/pull: BTN+BTN, same cmd, asymmetric argValues
	# (e.g. 0.9 pull-trigger / 0.6 push-in stable).
	'pdp_special':                                      pdpSpecial,

	# Momentary pushbuttons (various UI skins, identical structure).
	# BTN+BTN, same cmd, argValues=[1, 1], stopAction set.
	'mfd_special_key':                                  simpleDiscrete,
	'cdu_special':                                      simpleDiscrete,
	'animated_button':                                  simpleDiscrete,
	'button':                                           simpleDiscrete,
	# BTN+BTN, same cmd, argValues=[±1, ±1] (both same sign), stopAction set.
	'action_button':                                    simpleDiscrete,
	# Single BTN sub-control (e.g. cargo-hook door handle).
	'animated_pull_handle':                             simpleDiscrete,
	# BTN+BTN, same cmd (inherited default_button shape).
	'default_button':                                   simpleDiscrete,

	# 2-position TUMB toggles: TUMB+TUMB, same cmd, argValues=[±1, ∓1], argLim=[0,1].
	'animated_tumbler':                                 simpleDiscrete,
	'animated_tumbler_small':                           simpleDiscrete,
	# TUMB+TUMB, same cmd, argValues=[±1, ∓1], argLim=[0,1] — cyclic is irrelevant
	# for the discrete output shape.
	'multiposition_switch_cyclic':                      simpleDiscrete,

	# Multi-position TUMB discrete rotaries: TUMB+TUMB, same cmd, small step.
	'animated_multiposition_switch_limited':            simpleDiscrete,
	'animated_multiposition_switch_limited_small':      simpleDiscrete,
	'multiposition_switch_limited':                     simpleDiscrete,
	# TUMB+TUMB, same cmd — same shape as animated_multiposition_switch_limited.
	'multiposition_switch_tumb':                        simpleDiscrete,

	# Springloaded rockers: BTN+BTN, same cmd, symmetric argValues,
	# argLim=[-1,1] (both same) → 3-position discrete via i=0 path.
	'animated_rocker':                                  simpleDiscrete,
	'animated_rocker_small':                            simpleDiscrete,
	# BTN+BTN, same cmd, argValues=[±1, ∓1], complementary argLims (e.g.
	# [-1,0]/[0,1]) → 2-position discrete via i=0 path.
	'rocker':                                           simpleDiscrete,

	# TUMB+BTN, different cmds, complementary argLims, BTN has stopAction —
	# same structure as A-10C default_tumb_button.
	'default_tumb_button':                              twoCommandSpringloaded,

	# Relative encoder wheels: TUMB+TUMB, relative=True.
	# vhf_radio_wheel uses different cmds per direction (A-10C radio_wheel pattern).
	'vhf_radio_wheel':                                  wheelControl,
	# multiposition_switch_limited_1_side: same cmd, relative=True
	# (ARC-186 preset selector wheel).
	'multiposition_switch_limited_1_side':              wheelControl,

	# Continuous axes: single LEV sub-control.
	'axis':                                             continuousAxis,
	'axis_limited':                                     continuousAxis,

	# Multi-group elements: one arg group is TUMB/BTN (→ simpleDiscrete),
	# the other is a LEV axis (→ continuousAxis).  buttonOrAxis dispatches
	# per-group based on the first sub-control's class.
	# comm_knob:           TUMB+TUMB discrete + LEV volume knob.
	'comm_knob':                                        buttonOrAxis,
	# MultiFunctionKnob:   BTN+BTN pushbutton + relative LEV outer ring.
	'MultiFunctionKnob':                                buttonOrAxis,
	# rocker_and_axis_limited: BTN+BTN fire-handle rocker + LEV axis.
	'rocker_and_axis_limited':                          buttonOrAxis,
	# button_and_axis_limited: BTN+BTN button + LEV axis.
	'button_and_axis_limited':                          buttonOrAxis,
	# button_and_axis_cyclic: BTN+BTN button + relative cyclic LEV axis (SFD adjustment knobs).
	'button_and_axis_cyclic':                           buttonOrAxis,
}

if __name__ == '__main__':
	runMapping('CH-47Fbl1', HELPER_MAP)
