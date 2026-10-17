"""Control-mapping generator for the AV-8B Night Attack (AV8BNA).

Reads config/nativeExtractions/AV8BNA.json and writes
config/controlMappings/AV8BNA.json using the explicit archetype dispatch.

DCS internal name: AV8BNA  (→ output file and moduleName)
Extraction name:   AV8BNA  (same)

14 distinct helpers (6 no-helper elements fall through to structural dispatch).

Helper notes:
  # 2-position TUMB controls
  default_2_position_tumb / default_2_position_tumb_animated
    -- BTN/TUMB with argVal=1.0, argLim=[0,1] or reversed → simpleDiscrete

  # Multi-position TUMB controls
  multiposition_switch_limited_animated   -- delta-step, limited range

  # 3-position TUMB
  default_3_position_tumb_animated        -- TUMB, argLim=[-1,1] → simpleDiscrete

  # Button controls
  default_button                          -- BTN, argVal=1.0 or similar

  # Spring-switch (2-way, same commandId, ±argValue)
  default_2_way_spring_switch
    -- 2x BTN, same commandId, argVals=[1.0,-1.0], argLims=[[0,1],[-1,0]]
    -- structural else(indices[0]) path: uses argLim=[0,1], positions=2

  # AMPCD knob halves (split sub-elements, each a single BTN)
  AMPCD_switch_positive                   -- single BTN, argVal=+1.0, argLim=[0,1]
  AMPCD_switch_negative                   -- single BTN, argVal=-1.0, argLim=[-1,0]
    -- Each appears as a separate PTN_xxx_1 / PTN_xxx_2 element (already split).
    -- simpleDiscrete on indices[0] produces the correct half-range discrete control.

  # Relative axis (cycled LEV knob)
  default_axis_cycle                      -- LEV with relative=True, cycle=True
    -- type=relative, sendProtocol=C, argLim from element → relativeAxis

  # Standard LEV axis
  default_axis_limited                    -- LEV, relative=False → type=continuous

  # Mixed controls (BTN + LEV on DIFFERENT args → 2 control types per element)
  default_button_lever
    -- PTN_351: BTN→discrete (cage) + LEV non-relative→continuous (knob)
  default_button_lever_cycled
    -- PTN_300/301: BTN→discrete (button) + LEV-relative→relative (channel selector)
  LDG_Gear_Control_Handle
    -- PTN_461: 2x TUMB→discrete (gear up/dn) + LEV-relative→relative (emerg dn)
    -- buttonOrAxis for all three: per arg-group dispatch inspects controlClass,
       delegates BTN/TUMB→simpleDiscrete, LEV→continuousAxis (handles relative=True)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, relativeAxis, buttonOrAxis,
)

HELPER_MAP = {
	# ── 2-position TUMB / button controls ─────────────────────────────────────
	'default_button':                                       simpleDiscrete,
	'default_2_position_tumb':                              simpleDiscrete,
	'default_2_position_tumb_animated':                     simpleDiscrete,

	# ── 3-position TUMB controls ──────────────────────────────────────────────
	'default_3_position_tumb_animated':                     simpleDiscrete,

	# ── Multi-position TUMB controls ──────────────────────────────────────────
	'multiposition_switch_limited_animated':                simpleDiscrete,

	# ── 2-way spring switch (same commandId, ±argValue, falls to indices[0]) ──
	'default_2_way_spring_switch':                          simpleDiscrete,

	# ── AMPCD knob halves (already-split sub-elements, single BTN each) ───────
	'AMPCD_switch_positive':                                simpleDiscrete,
	'AMPCD_switch_negative':                                simpleDiscrete,

	# ── Relative LEV knob (cycled, relative=True) ─────────────────────────────
	'default_axis_cycle':                                   relativeAxis,

	# ── Standard LEV axis ─────────────────────────────────────────────────────
	'default_axis_limited':                                 continuousAxis,

	# ── Mixed controls (BTN + LEV on different args → dispatch per arg group) ──
	# buttonOrAxis inspects controlClass per arg-group call and delegates:
	#   BTN/TUMB → simpleDiscrete, LEV → continuousAxis (which handles relative=True).
	'default_button_lever':                                 buttonOrAxis,
	'default_button_lever_cycled':                          buttonOrAxis,
	'LDG_Gear_Control_Handle':                              buttonOrAxis,
}

if __name__ == '__main__':
	runMapping('AV8BNA', HELPER_MAP)
