"""Control-mapping generator for the F-4E Phantom II.

Reads config/nativeExtractions/F-4E.json and writes
config/controlMappings/F-4E-45MC.json using the explicit archetype dispatch.

DCS internal name: F-4E-45MC  (→ output file and moduleName)
Extraction name:   F-4E       (→ input file, install-dir name)

24 helpers.  All explicitly mapped.

Helper notes:
  # Standard 2-position controls (step = full range, positions = 2)
  default_2_position_tumb / default_animated_lever / default_circuit_breaker /
  default_displaybutton / default_flipcover
    -- 2x TUMB same cmd, argVals=[±1.0], argLim=[0,1] → simpleDiscrete

  # Multi-position controls
  default_3_position_tumb                 -- 2x TUMB same cmd, val=±0.1, 3 pos
  default_3_position_0_to_1_tumb          -- 2x TUMB same cmd, val=±0.5, 3 pos over [0,1]
  multiposition_switch                    -- delta-step, dual-cmd subset handled via dualRotary
  multiposition_switch_limited            -- delta-step limited
  multiposition_switch_limited_v2         -- delta-step, asymmetric range
  multiposition_roller_limited            -- delta-step roller

  # Button
  default_button                          -- 2x BTN or single BTN
  default_springloaded_up_2pos_switch     -- single BTN, argVal=1.0

  # Springloaded switches — all fall to structural else(indices[0])
  default_springloaded_3pos_switch_tiny               -- 2x BTN, argLim=[-1,0]/[0,1]
  default_springloaded_down_3pos_switch               -- BTN+TUMB, argLim=[-1,0]/[0,1]
  default_springloaded_down_3pos_0_to_1_switch        -- BTN+TUMB, argLim=[0,0.5]/[0.5,1]
  default_springloaded_first_knob                     -- TUMB+BTN, asymmetric argVals
  default_springloaded_inversed_down_3pos_switch      -- BTN+TUMB, argLim=[0,1]/[-1,0]
  default_springloaded_inversed_down_3pos_0_to_1_switch -- TUMB+BTN, argLim=[0.5,1]/[0,0.5]
  default_springloaded_last_knob                      -- TUMB+BTN, asymmetric argVals
  default_springloaded_up_3pos_switch                 -- TUMB+BTN, argLim=[-1,0]/[0,1]

  # Proper springloaded center-return (detectSpringloadedSwitch merges both halves)
  default_springloaded_3pos_switch        -- BTN+BTN, complementary argLims → 3-pos merged

  # Axis
  default_axis                            -- LEV; relative=True→type=relative, else→continuous

  # Mixed (BTN press + LEV rotation on DIFFERENT args — buttonOrAxis dispatches per arg group)
  dim_test_lamp                           -- BTN→discrete + LEV non-relative→continuous
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, springloadedTumb, buttonOrAxis,
)

HELPER_MAP = {
	# ── 2-position TUMB / lever / cover controls ──────────────────────────────
	'default_2_position_tumb':                              simpleDiscrete,
	'default_animated_lever':                               simpleDiscrete,
	'default_circuit_breaker':                              simpleDiscrete,
	'default_displaybutton':                                simpleDiscrete,
	'default_flipcover':                                    simpleDiscrete,

	# ── Multi-position TUMB controls ──────────────────────────────────────────
	'default_3_position_tumb':                              simpleDiscrete,
	'default_3_position_0_to_1_tumb':                      simpleDiscrete,
	'multiposition_switch':                                 simpleDiscrete,
	'multiposition_switch_limited':                         simpleDiscrete,
	'multiposition_switch_limited_v2':                      simpleDiscrete,
	'multiposition_roller_limited':                         simpleDiscrete,

	# ── Button controls ───────────────────────────────────────────────────────
	'default_button':                                       simpleDiscrete,
	'default_springloaded_up_2pos_switch':                  simpleDiscrete,

	# ── Springloaded variants — all resolve to else(indices[0]) ──────────────
	# Each uses only the first sub-control's argLim and step (not merged).
	'default_springloaded_3pos_switch_tiny':                simpleDiscrete,
	'default_springloaded_down_3pos_0_to_1_switch':         simpleDiscrete,
	'default_springloaded_down_3pos_switch':                simpleDiscrete,
	'default_springloaded_first_knob':                      simpleDiscrete,
	'default_springloaded_inversed_down_3pos_0_to_1_switch': simpleDiscrete,
	'default_springloaded_inversed_down_3pos_switch':       simpleDiscrete,
	'default_springloaded_last_knob':                       simpleDiscrete,
	'default_springloaded_up_3pos_switch':                  simpleDiscrete,

	# ── Proper springloaded 3-position (merges complementary halves → 3 pos) ─
	'default_springloaded_3pos_switch':                     springloadedTumb,

	# ── LEV axis ──────────────────────────────────────────────────────────────
	'default_axis':                                         continuousAxis,

	# ── Mixed BTN press + LEV rotation on different args (2 controls/element) ─
	'dim_test_lamp':                                        buttonOrAxis,
}

if __name__ == '__main__':
	runMapping('F-4E-45MC', HELPER_MAP, extractionName='F-4E')
