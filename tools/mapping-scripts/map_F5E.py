"""Control-mapping generator for the F-5E Tiger II.

Reads config/nativeExtractions/F-5E.json and writes
config/controlMappings/F-5E-3.json using the explicit archetype dispatch.

DCS internal name: F-5E-3  (→ output file and moduleName)
Extraction name:   F-5E    (→ input file, install-dir name)

28 helpers.  All explicitly mapped.  Zero STRUCTURAL_FALLBACK.

Helper notes:

  # Buttons (single BTN, stop_action, argVal=1)
  default_button / default_button2 / default_button_stick
    -- single or pair of BTN, stop_action → simpleDiscrete
  default_trimmer_button
    -- wraps default_button with custom argVal/argLim → simpleDiscrete
  springloaded_2_pos_tumb
    -- BTN+BTN same cmd, both stop_action, argVal=1 → simpleDiscrete

  # 2-position TUMB controls
  default_2_position_tumb / default_2_position_tumb2
    -- 2x TUMB same cmd, argVals=[−1,+1], argLim=[0,1] → simpleDiscrete
  default_CB_button
    -- wraps default_2_position_tumb, argVals=[1,0] → simpleDiscrete
  default_red_cover
    -- wraps default_2_position_tumb → simpleDiscrete
  default_animated_lever
    -- wraps default_2_position_tumb, argVals=[1,−1] → simpleDiscrete

  # 3-position TUMB controls
  default_3_position_tumb / default_3_position_tumb2
    -- 2x TUMB same cmd, argVals=[−av,+av] → simpleDiscrete (3-pos)

  # Multi-position TUMB controls
  multiposition_switch
    -- 2x TUMB same cmd, delta-step → simpleDiscrete
  multiposition_switch3
    -- wraps multiposition_switch, adds MULTY_TUMB visual → simpleDiscrete
  multiposition_switch_2_cl
    -- sound variant of multiposition_switch → simpleDiscrete

  # Springloaded 3-pos with TWO different commands (one per direction)
  default_button_tumb
    -- BTN+TUMB, DIFFERENT cmds (cmd1,cmd2), same arg, stop_action={cmd1,0}
       argVals=[−1,+1], argLim=[−1,0]/[0,1] → twoCommandSpringloaded
  springloaded_3_pos_tumb / springloaded_3_pos_tumb2
    -- BTN+BTN, DIFFERENT cmds (cmd1,cmd2), both stop_action
       argVals=[val1,val3], argLim=[−1,0]/[0,1] → twoCommandSpringloaded

  # Springloaded 3-pos with ONE command (complementary argLims per sub-control)
  default_springloaded_switch2
    -- TUMB+BTN, same cmd for both halves, complementary argLim pairs
       (generateControlMapping.py detectSpringloadedSwitch merges both halves
       into a single 3-pos control; requires 'default_springloaded_switch2'
       in its helper-name allowlist) → springloadedTumb
    -- Used for all 6 IFF mode-select switches (M-1, M-2, M-3/A, M-C,
       RAD TEST/MON, MIC IDENT)

  # Axis controls
  default_axis
    -- single LEV; relative=True → relative axis, else → continuous
       → continuousAxis
  default_axis_limited
    -- wraps default_axis with custom argLim → continuousAxis

  # Multi-arg elements (each arg group dispatched separately by buttonOrAxis)
  IFF_Code4_multiposition_spring_switch
    -- BTN+BTN+LEV across TWO different args (arg_, arg2_) → buttonOrAxis
  IFF_Master_multiposition_switch
    -- TUMB+TUMB+LEV across TWO different args (arg_, arg2_) → buttonOrAxis
  default_air_inlet
    -- LEV+LEV across TWO different args (arg_hor_, arg_ver_) → buttonOrAxis
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mapUtils import (
	runMapping,
	simpleDiscrete, continuousAxis, springloadedTumb, twoCommandSpringloaded,
	buttonOrAxis,
)


def _iffCode4(elem, indices, ctx):
	"""IFF CODE 4-position selector (arg199) + gate lever (arg197).

	BTN group (arg199): relative/wheel with incValue=-1 (sends command -1 to
	advance toward HOLD).  Live-probed positions: ZERO=0.0, B=0.1, A=0.2,
	HOLD=0.3 (ZERO gated by lever).  The BTN sub-control argLims in the
	extraction ([-1,0] and [0,1]) are mouse-drag regions, not arg ranges.
	LEV group (arg197): gate lever, passed to continuousAxis unchanged.
	"""
	classes = elem.get('controlClass', [])
	cls = classes[indices[0]] if indices[0] < len(classes) else 'BTN'
	if cls == 'LEV':
		return continuousAxis(elem, indices, ctx)
	# BTN group: expect exactly 2 BTN sub-controls.
	if len(indices) != 2:
		return None
	i0, i1 = indices
	actions = elem.get('action', [])
	argValues = elem.get('argValue', [])
	args = elem.get('arg', [])
	v0 = argValues[i0] if i0 < len(argValues) else 0
	# incIdx = sub-control with the negative argValue (advances arg per live probe).
	incIdx, decIdx = (i0, i1) if v0 < 0 else (i1, i0)
	actionId = actions[incIdx] if incIdx < len(actions) else 0
	if not actionId:
		return None
	incValue = round(argValues[incIdx], 6)
	decValue = round(argValues[decIdx], 6)
	arg = args[incIdx] if incIdx < len(args) else 0
	canonical = ctx.canonical(actionId, arg)
	control = {
		**ctx.meta(),
		'type': 'relative',
		'wheel': True,
		'deviceId': ctx.deviceId,
		'commandId': actionId,
		'argLim': [0.0, 0.3],
		'incrementValue': incValue,
		'decrementValue': decValue,
	}
	if arg != 0:
		control['arg'] = arg
	return {canonical: control}

HELPER_MAP = {
	# ── Button controls ───────────────────────────────────────────────────────
	'default_button':                               simpleDiscrete,
	'default_button2':                              simpleDiscrete,
	'default_button_stick':                         simpleDiscrete,
	'default_trimmer_button':                       simpleDiscrete,
	'springloaded_2_pos_tumb':                      simpleDiscrete,

	# ── 2-position TUMB / lever / cover / CB controls ─────────────────────────
	'default_2_position_tumb':                      simpleDiscrete,
	'default_2_position_tumb2':                     simpleDiscrete,
	'default_CB_button':                            simpleDiscrete,
	'default_red_cover':                            simpleDiscrete,
	'default_animated_lever':                       simpleDiscrete,

	# ── 3-position TUMB controls ──────────────────────────────────────────────
	'default_3_position_tumb':                      simpleDiscrete,
	'default_3_position_tumb2':                     simpleDiscrete,

	# ── Multi-position TUMB controls ──────────────────────────────────────────
	'multiposition_switch':                         simpleDiscrete,
	'multiposition_switch3':                        simpleDiscrete,
	'multiposition_switch_2_cl':                    simpleDiscrete,

	# ── Springloaded 3-pos with TWO commands (one per direction) ──────────────
	'default_button_tumb':                          twoCommandSpringloaded,
	'springloaded_3_pos_tumb':                      twoCommandSpringloaded,
	'springloaded_3_pos_tumb2':                     twoCommandSpringloaded,

	# ── Springloaded 3-pos with ONE command (merged via detectSpringloadedSwitch)
	'default_springloaded_switch2':                 springloadedTumb,

	# ── Axis controls ─────────────────────────────────────────────────────────
	'default_axis':                                 continuousAxis,
	'default_axis_limited':                         continuousAxis,

	# ── Multi-arg elements (two independent arg groups per element) ───────────
	'IFF_Code4_multiposition_spring_switch':        _iffCode4,
	'IFF_Master_multiposition_switch':              buttonOrAxis,
	'default_air_inlet':                            buttonOrAxis,
}

if __name__ == '__main__':
	runMapping('F-5E-3', HELPER_MAP, extractionName='F-5E')
