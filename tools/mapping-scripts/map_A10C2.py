"""Explicit helper-handler map script for the A-10C II Tank Killer.

Run this script to regenerate config/controlMappings/A-10C_2.json.

Helper distribution (from config/nativeExtractions/A-10C_2.json):
  default_button                       200
  push_button_tumb                      46
  default_2_position_tumb               31
  default_2_position_small_tumb         28
  action_button                         24
  default_axis                          23
  multiposition_switch_tumb             17
  (none)                                12
  default_3_position_tumb               12
  default_3_position_small_tumb         10
  intercom_rotate_tumb                   8
  multiposition_switch_limited           7
  electrically_held_switch               7
  multiposition_switch_1_side            7
  default_tumb_button                    6
  default_springloaded_switch            6
  default_axis_limited                   5
  springloaded_3_pos_tumb                4
  multiposition_switch                   4
  radio_wheel                            4
  default_button_tumb                    3
  default_button_axis                    3
  default_animated_lever                 2
  default_2_position_cover               2
  axis_limited_1_side                    1
  default_small_tumb_button              1
  default_2_position_cover_plastic       1
  multiposition_switch_intercom          1
  IFF_multiposition_spring_switch        1
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete,
	continuousAxis,
	twoCommandSpringloaded,
	btnPulseCounter,
	wheelControl,
	wheelOrDiscrete,
	buttonOrAxis,
)

HELPER_MAP = {
	'default_button':                     simpleDiscrete,
	'push_button_tumb':                   simpleDiscrete,
	'default_2_position_tumb':            simpleDiscrete,
	'default_2_position_small_tumb':      simpleDiscrete,
	'action_button':                      simpleDiscrete,
	'default_axis':                       continuousAxis,
	'multiposition_switch_tumb':          simpleDiscrete,
	'default_3_position_small_tumb':      simpleDiscrete,
	# Mixed: most instances are discrete rotaries; PTR-ANARC186-VHF*-PRESET are
	# relative wheels (relative=True TUMB).  wheelOrDiscrete tries detectWheel
	# first and falls back to simpleDiscrete for the non-relative majority.
	'multiposition_switch_1_side':        wheelOrDiscrete,
	'default_3_position_tumb':            simpleDiscrete,
	'radio_wheel':                        wheelControl,
	'intercom_rotate_tumb':               buttonOrAxis,
	'electrically_held_switch':           simpleDiscrete,
	'multiposition_switch_limited':       simpleDiscrete,
	# IFF panel: different commandIds on TUMB+BTN → positionMap.
	'default_springloaded_switch':        twoCommandSpringloaded,
	# TUMB + springloaded BTN with different commandIds → positionMap.
	'default_tumb_button':                twoCommandSpringloaded,
	'default_axis_limited':               continuousAxis,
	'multiposition_switch':               simpleDiscrete,
	'springloaded_3_pos_tumb':            twoCommandSpringloaded,
	'default_button_tumb':                twoCommandSpringloaded,
	'default_button_axis':                buttonOrAxis,
	'default_animated_lever':             simpleDiscrete,
	# TUMB + springloaded BTN with different commandIds → positionMap.
	'default_small_tumb_button':          twoCommandSpringloaded,
	'default_2_position_cover':           simpleDiscrete,
	'default_2_position_cover_plastic':   simpleDiscrete,
	# Same commandId BTN pulse counter with stopAction → wheel=True output.
	# (UH-1H uses iffRelativeKnob for the no-stopAction variant instead.)
	'IFF_multiposition_spring_switch':    btnPulseCounter,
	'multiposition_switch_intercom':      simpleDiscrete,
	'axis_limited_1_side':                continuousAxis,
}

if __name__ == '__main__':
	runMapping('A-10C_2', HELPER_MAP)
