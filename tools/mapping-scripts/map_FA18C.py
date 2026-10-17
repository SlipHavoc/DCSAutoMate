"""Control-mapping generator for the FA-18C Hornet.

Reads config/nativeExtractions/FA-18C.json and writes
config/controlMappings/FA-18C.json using the explicit archetype dispatch.

All helpers are mapped to explicit archetype functions.  Controls without
a helper tag (anonymous inline table elements in clickabledata.lua) fall
through to the structural processElements() path inside mapUtils.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, springloadedTumb, twoCommandSpringloaded, buttonOrAxis,
)

HELPER_MAP = {
	# Single-arg BTN / TUMB controls
	'default_button':                   simpleDiscrete,
	'default_button2':                  simpleDiscrete,
	'limit_button':                     simpleDiscrete,
	'short_way_button':                 simpleDiscrete,
	'AMPCD_switch_positive':            simpleDiscrete,
	'AMPCD_switch_negative':            simpleDiscrete,
	'push_button_tumb':                 simpleDiscrete,
	'default_CB_button':                simpleDiscrete,
	'default_2_position_tumb':          simpleDiscrete,
	'default_3_position_tumb':          simpleDiscrete,
	'multiposition_switch':             simpleDiscrete,
	'multiposition_switch_cl':          simpleDiscrete,
	'default_red_cover':                simpleDiscrete,
	# default_button_tumb_v2: TUMB+BTN pair, two different commands, complementary
	# argLims — same positionMap structure as springloaded_3_pos_tumb.
	'default_button_tumb_v2':           twoCommandSpringloaded,
	# LEV and MOVABLE_LEV axis controls — same continuous output; MOVABLE_LEV
	# is a DCS animation hint and does not affect the control mapping.
	'default_axis':                     continuousAxis,
	'default_axis_limited':             continuousAxis,
	'default_movable_axis':             continuousAxis,
	# FA-18C springloaded_2_pos_tumb uses same command+same arg_lim for both
	# sub-elements (arg_value={1,1}) — not a dec/inc pair. Use simpleDiscrete.
	'springloaded_2_pos_tumb':          simpleDiscrete,
	'springloaded_2_pos_tumb2':         simpleDiscrete,
	# 3-pos springloaded switches have different commands for each direction
	# → twoCommandSpringloaded (positionMap with null center).
	'springloaded_3_pos_tumb':          twoCommandSpringloaded,
	'springloaded_3_pos_tumb2':         twoCommandSpringloaded,
	# Multi-arg helpers: BTN/TUMB group + LEV group (or two TUMB groups)
	'default_button_axis':              buttonOrAxis,
	'default_button_axis_extended':     buttonOrAxis,
	'default_button_axis_tumb':         buttonOrAxis,
	'LDG_Gear_Control_Handle':          buttonOrAxis,
	'multiposition_switch_with_pull':   buttonOrAxis,
	'default_double_tumb':              buttonOrAxis,
}

if __name__ == '__main__':
	runMapping('FA-18C_hornet', HELPER_MAP, extractionName='FA-18C')
