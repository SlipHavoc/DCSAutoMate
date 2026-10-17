"""Control-mapping generator for the Ka-50 Black Shark 3.

Reads config/nativeExtractions/Ka-50_3.json and writes
config/controlMappings/Ka-50_3.json using the explicit archetype dispatch.

All helpers are mapped to explicit archetype functions.  Controls without
a helper tag (13 anonymous inline table elements) fall through to the
structural processElements() path inside mapUtils.

6 helpers in this module, zero STRUCTURAL_FALLBACK entries.

Helper notes (from clickable_defs.lua):
  animated_guard_switch   -- 2x TUMB same cmd, val=±0.01 animation delta; toggled
                             as 2-position switch (step = full argLim range = 1.0).
  default_2_position_tumb -- 2x TUMB same cmd, val=±1.0, 2 pos
  default_3_position_tumb -- 2x TUMB same cmd, val=±0.1, 3 pos
  default_axis            -- LEV single command; mix of relative=True (→ type=relative)
                             and relative=False (→ type=continuous) instances
  default_button          -- 2x BTN same cmd, val=1.0
  multiposition_switch    -- 2x TUMB, delta-step multi-position; most have same cmd
                             but some override .action with two different commandIds
                             (dual-command rotary pattern, handled inside simpleDiscrete
                             via detectDualCommandRotary — uses inc-side commandId).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	binaryToggle, simpleDiscrete, continuousAxis,
)

HELPER_MAP = {
	# ── Animated guard/cover toggle (step = full range, positions = 2) ────────
	'animated_guard_switch':   binaryToggle,    # 2x TUMB same cmd, animation delta

	# ── Same-command TUMB/BTN controls ────────────────────────────────────────
	'default_2_position_tumb': simpleDiscrete,  # 2x TUMB same cmd, val=±1.0, 2 pos
	'default_3_position_tumb': simpleDiscrete,  # 2x TUMB same cmd, val=±0.1, 3 pos
	'default_button':          simpleDiscrete,  # 2x BTN same cmd, val=1.0
	'multiposition_switch':    simpleDiscrete,  # delta-step multi-pos; dual-cmd subset
	                                            # handled automatically via dualRotary

	# ── LEV axis controls ─────────────────────────────────────────────────────
	'default_axis':            continuousAxis,  # relative=True → type=relative,
	                                            # relative=False → type=continuous
}

if __name__ == '__main__':
	runMapping('Ka-50_3', HELPER_MAP)
