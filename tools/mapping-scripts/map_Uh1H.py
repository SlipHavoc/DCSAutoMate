"""Control mapping generator for UH-1H.

Explicit helper-handler map for all Lua helper functions used in:
  c:/Games/DCS World/Mods/aircraft/Uh-1H/Cockpit/Scripts/clickabledata.lua

Every helper that appears in the nativeExtraction MUST have an entry here.
Adding a new helper to UH-1H's clickabledata.lua will cause this script to
fail with a clear error rather than silently misclassifying controls.

Helper counts from nativeExtraction (exhaustive tagging, 2025):
  default_2_position_button:      74
  default_2_position_tumb:        32
  default_button:                 15
  default_axis:                   12
  default_axis_limited:           12
  multiposition_switch_limited:   12
  default_3_position_tumb:        11
  default_springloaded_switch:     7
  multiposition_switch:            7
  default_springloaded_3pos_switch: 5
  default_1_position_tumb:         4
  multiposition_tumb_limited:      4
  multiposition_switch_axis:       3
  default_2_position_cover:        3
  default_button_axis:             2
  IFF_multiposition_spring_switch: 2

12 untagged elements (inline-table literals, names ending in -PTR) use
structural fallback automatically.
"""

from mapUtils import (
	runMapping,
	simpleDiscrete,
	continuousAxis,
	springloadedTumb,
	iffRelativeKnob,
	relativeAxis,
	buttonOrAxis,
)

HELPER_MAP = {
	'default_2_position_button':       simpleDiscrete,
	'default_2_position_tumb':         simpleDiscrete,
	'default_button':                  simpleDiscrete,
	'default_axis':                    continuousAxis,
	'default_axis_limited':            continuousAxis,
	'multiposition_switch_limited':    simpleDiscrete,
	'default_3_position_tumb':         simpleDiscrete,
	'default_springloaded_switch':     springloadedTumb,
	'multiposition_switch':            simpleDiscrete,
	'default_springloaded_3pos_switch': springloadedTumb,
	'default_1_position_tumb':         simpleDiscrete,
	'multiposition_tumb_limited':      simpleDiscrete,
	'multiposition_switch_axis':       relativeAxis,
	'default_2_position_cover':        simpleDiscrete,
	'default_button_axis':             buttonOrAxis,
	'IFF_multiposition_spring_switch': iffRelativeKnob,
}

if __name__ == '__main__':
	runMapping('UH-1H', HELPER_MAP)
