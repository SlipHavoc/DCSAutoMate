"""Explicit helper-handler map script for the Mi-8MTV2 Hip.

Run this script to regenerate config/controlMappings/Mi-8MT.json.

Helper distribution (from config/nativeExtractions/Mi-8MTV2.json):
  default_2_position_tumb          163
  default_button                    73
  default_axis_limited              31
  default_3_position_tumb           24
  small_2_position_tumb             18
  tumb_cover                        17
  multiposition_switch              14
  default_axis                      10
  (none)                            10
  default_1_position_tumb            9
  springloaded_3_pos_tumb            9
  stick_button                       9
  signal_flares                      8
  radio_wheel_1                      7
  default_button_axis                5
  radio_wheel_arc                    4
  multiposition_switch_limited       3
  triple_switch                      3
  default_springloaded_tumb          2
  radio_wheel_double                 1
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
	wheelOrContinuous,
	buttonOrAxis,
)

HELPER_MAP = {
	'default_2_position_tumb':        simpleDiscrete,
	'default_button':                 simpleDiscrete,
	'default_axis_limited':           continuousAxis,
	'default_3_position_tumb':        simpleDiscrete,
	# TUMB+TUMB, same cmd, argValues=[1,-1] → i=0, step=1.0, 2 positions.
	'small_2_position_tumb':          simpleDiscrete,
	# Cover/guard toggle: same structure as small_2_position_tumb.
	'tumb_cover':                     simpleDiscrete,
	'multiposition_switch':           simpleDiscrete,
	'default_axis':                   continuousAxis,
	'default_1_position_tumb':        simpleDiscrete,
	# BTN+BTN, SAME commandId, argValues=[-1,1], argLim=[[-1,0],[0,1]].
	# Structural dispatch: same cmd → not isPositionMapElement → falls to i=0
	# (argValue=-1, argLim=[-1,0]) → step=1.0, positions=2.
	# Contrast with Mi-24P springloaded_3_pos_tumb which uses DIFFERENT cmds.
	'springloaded_3_pos_tumb':        simpleDiscrete,
	'stick_button':                   simpleDiscrete,
	# Rocket/flare momentary: TUMB+TUMB, same cmd, argValues=[1,-1], 2 positions.
	'signal_flares':                  simpleDiscrete,
	'radio_wheel_1':                  wheelControl,
	'default_button_axis':            buttonOrAxis,
	# Non-relative TUMB rotary (relative=False): not a wheel, falls to
	# simpleDiscrete → i=0 → discrete with step=|argValue|.
	'radio_wheel_arc':                simpleDiscrete,
	'multiposition_switch_limited':   simpleDiscrete,
	# 4 sub-controls, same cmd, same arg: detectDualCommandRotary requires
	# exactly 2 indices so falls to i=0 → 4-position discrete.
	'triple_switch':                  simpleDiscrete,
	# BTN+TUMB with different commandIds → positionMap (same as springloaded_3_pos_tumb).
	'default_springloaded_tumb':      twoCommandSpringloaded,
	# Two arg groups per element: TUMB+TUMB wheel (arg 748) + relative LEV
	# axis (arg 749).  wheelOrContinuous tries wheelControl first (matches the
	# TUMB group), then falls through to continuousAxis for the LEV group.
	'radio_wheel_double':             wheelOrContinuous,
}

if __name__ == '__main__':
	runMapping('Mi-8MT', HELPER_MAP, extractionName='Mi-8MTV2')
