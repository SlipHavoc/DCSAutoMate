"""Control-mapping generator for the F-16C Viper.

Reads config/nativeExtractions/F-16C.json and writes
config/controlMappings/F-16C_50.json using the explicit archetype dispatch.

All helpers are mapped to explicit archetype functions.  Controls without
a helper tag (anonymous inline table elements in clickabledata.lua) fall
through to the structural processElements() path inside mapUtils.

22 helpers in this module, zero STRUCTURAL_FALLBACK entries.

Helper notes (from clickable_defs.lua):
  default_button / mfd_button / short_way_button  -- BTN single command
  Rocker_switch_positive                           -- BTN, arg_value=+1, arg_lim={0,1}
  Rocker_switch_negative                           -- BTN, arg_value=-1, arg_lim={-1,0}
  default_2_position_tumb / _small                 -- 2x TUMB same command, 2 positions
  default_3_position_tumb / _small                 -- 2x TUMB same command, 3 positions
  default_red_cover                                -- 2x TUMB same command, 2 positions
  multiposition_switch / _tumb                     -- 2x TUMB same command, delta-step
  springloaded_2_pos_tumb / _small                 -- 2x BTN same command (spring returns to 0)
  default_axis / _limited / _limited_1_side        -- LEV single command (default_axis is
                                                      relative=True, the other two are non-relative)
  default_button_knob                              -- BTN(arg_push) + LEV(arg_rotate, relative),
                                                      split into two controls by arg group
  default_button_tumb                              -- BTN(cmd1, arg_lim={-1,0}) + TUMB(cmd2,
                                                      arg_lim={0,1}), same arg, different commands
  default_tumb_button                              -- TUMB(cmd1, arg_lim={-1,0}) + BTN(cmd2,
                                                      arg_lim={0,1}), same arg, different commands
  springloaded_3_pos_tumb / _small                 -- BTN(cmd1) + BTN(cmd2), complementary
                                                      arg_lims, spring-return to center
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, twoCommandSpringloaded, buttonOrAxis,
)

HELPER_MAP = {
	# ── Single BTN controls ───────────────────────────────────────────────────
	'default_button':                     simpleDiscrete,
	'mfd_button':                         simpleDiscrete,
	'short_way_button':                   simpleDiscrete,
	'Rocker_switch_positive':             simpleDiscrete,  # BTN, arg_value=+1, arg_lim={0,1}
	'Rocker_switch_negative':             simpleDiscrete,  # BTN, arg_value=-1, arg_lim={-1,0}

	# ── TUMB/BTN same-command (all use simpleDiscrete via indices[0]) ─────────
	'default_2_position_tumb':            simpleDiscrete,  # 2x TUMB same cmd, 2 positions
	'default_2_position_tumb_small':      simpleDiscrete,  # 2x TUMB same cmd, 2 positions
	'default_3_position_tumb':            simpleDiscrete,  # 2x TUMB same cmd, 3 positions
	'default_3_position_tumb_small':      simpleDiscrete,  # 2x TUMB same cmd, 3 positions
	'default_red_cover':                  simpleDiscrete,  # 2x TUMB same cmd, 2 positions
	'multiposition_switch':               simpleDiscrete,  # 2x TUMB same cmd, delta-step multi-pos
	'multiposition_switch_tumb':          simpleDiscrete,  # 2x TUMB same cmd, delta-step multi-pos
	'springloaded_2_pos_tumb':            simpleDiscrete,  # 2x BTN same cmd, spring returns to 0
	'springloaded_2_pos_tumb_small':      simpleDiscrete,  # 2x BTN same cmd, spring returns to 0

	# ── LEV axis controls ─────────────────────────────────────────────────────
	'default_axis':                       continuousAxis,  # LEV, relative=True → type=relative
	'default_axis_limited':               continuousAxis,  # LEV, relative=False → type=continuous
	'default_axis_limited_1_side':        continuousAxis,  # LEV, relative=False → type=continuous

	# ── Multi-arg compound: BTN(push arg) + LEV(rotate arg) ──────────────────
	# buttonOrAxis dispatches per-arg-group to simpleDiscrete or continuousAxis.
	'default_button_knob':                buttonOrAxis,

	# ── Two-command springloaded switches: complementary arg_lims, different cmds ─
	# default_button_tumb: BTN(cmd1, {-1,0}) + TUMB(cmd2, {0,1}), same arg
	# default_tumb_button: TUMB(cmd1, {-1,0}) + BTN(cmd2, {0,1}), same arg
	# springloaded_3_pos_tumb: BTN(cmd1, {-1,0}) + BTN(cmd2, {0,1}), same arg
	# springloaded_3_pos_tumb_small: same pattern as springloaded_3_pos_tumb
	'default_button_tumb':                twoCommandSpringloaded,
	'default_tumb_button':                twoCommandSpringloaded,
	'springloaded_3_pos_tumb':            twoCommandSpringloaded,
	'springloaded_3_pos_tumb_small':      twoCommandSpringloaded,
}

if __name__ == '__main__':
	runMapping('F-16C_50', HELPER_MAP, extractionName='F-16C')
