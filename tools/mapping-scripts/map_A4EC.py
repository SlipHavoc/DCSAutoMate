"""Control-mapping generator for the A-4E-C Skyhawk.

Reads config/nativeExtractions/A-4E-C.json and writes
config/controlMappings/A-4E-C.json using the explicit archetype dispatch.

All helpers are mapped to explicit archetype functions.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, twoCommandSpringloaded, buttonOrAxis,
)

HELPER_MAP = {
	# ── Single BTN/TUMB controls ──────────────────────────────────────────────
	'default_button':                           simpleDiscrete,
	'default_2_position_tumb':                 simpleDiscrete,
	'default_3_position_tumb':                 simpleDiscrete,
	'inverted_3_position_tumb':                simpleDiscrete,
	'multiposition_switch_limited':            simpleDiscrete,
	'multiposition_switch_limited_inverted':   simpleDiscrete,

	# ── LEV axis controls ─────────────────────────────────────────────────────
	'default_axis':                             continuousAxis,
	'default_axis_limited':                     continuousAxis,
	'default_movable_axis':                     continuousAxis,

	# ── Multi-arg compound: BTN(push arg) + LEV(rotate arg) ──────────────────
	'default_button_axis':                      buttonOrAxis,

	# ── Springloaded switches ─────────────────────────────────────────────────
	'springloaded_3_pos_tumb':                  twoCommandSpringloaded,
	'springloaded_forward_only_3_pos_tumb':     twoCommandSpringloaded,
	'springloaded_aft_only_3_pos_tumb':         twoCommandSpringloaded,
}

if __name__ == '__main__':
	runMapping('A-4E-C', HELPER_MAP)
