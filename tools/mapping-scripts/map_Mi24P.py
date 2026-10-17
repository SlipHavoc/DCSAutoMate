"""Explicit helper-handler map script for the Mi-24P.

Run this script to regenerate config/controlMappings/Mi-24P.json.

Helper distribution (from config/nativeExtractions/Mi-24P.json):
  default_2_position_tumb          205
  default_button                    82
  multiposition_switch              40
  default_blue_cover                34
  default_axis                      33
  default_3_position_tumb           25
  default_square_button             17
  (none)                            13
  default_2_position_small_tumb     10
  default_axis_limited               9
  default_position_tumb              9
  default_animated_lever             8
  default_2_position_flares_tumb     8
  radio_wheel_1                      5
  springloaded_3_pos_tumb            5
  triple_switch                      4
  stick_button                       3
  default_tumb_button                2
  default_spring_button              2
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
)

HELPER_MAP = {
	'default_2_position_tumb':       simpleDiscrete,
	'default_button':                simpleDiscrete,
	'multiposition_switch':          simpleDiscrete,
	'default_blue_cover':            simpleDiscrete,
	'default_axis':                  continuousAxis,
	'default_3_position_tumb':       simpleDiscrete,
	'default_square_button':         simpleDiscrete,
	'default_2_position_small_tumb': simpleDiscrete,
	'default_axis_limited':          continuousAxis,
	'default_position_tumb':         simpleDiscrete,
	'default_animated_lever':        simpleDiscrete,
	'default_2_position_flares_tumb': simpleDiscrete,
	'radio_wheel_1':                 wheelControl,
	'springloaded_3_pos_tumb':       twoCommandSpringloaded,
	'triple_switch':                 simpleDiscrete,
	'stick_button':                  simpleDiscrete,
	'default_tumb_button':           simpleDiscrete,
	'default_spring_button':         simpleDiscrete,
}

if __name__ == '__main__':
	runMapping('Mi-24P', HELPER_MAP)
