TODO list

C-101CC validation: SYSTEMS.PNT-HND-CNPY and SYSTEMS.PNT-HND-CNPY-BACK are `type=toggle` and work correctly on a fresh start. Validation fails because an earlier control in the sweep jettisons the canopy, making these controls inaccessible for the rest of the run. Keep these in the skip list — the controls are correct, the failure is a validation ordering issue. (The canopy safety catch is a physical handle on the canopy itself.)

C-101CC validation: SYSTEMS.PNT-RUDREG-CPD_arg311 and SYSTEMS.PNT-RUDREG-CPD-BACK_arg1202 fail because the pedals_adj_control has an inverted argLim ({1,0},{0,1}) in Lua — pos 1 expects 1.0 but gets 0.0. Needs either: (a) inverted-argLim detection in the mapper/validator, or (b) a per-control argLim override.

Announce time to first keyboard command?

Announce when done with avionics, or mfds

Investigate the possibility of a time estimate for a script.  If a script runs successfully, store the time it took in a file.  When it runs again, use that time to provide an estimated time until finished.

Optionally, make appearance of ingame overlay configurable by the user, especially transparency, text box size and line count, and grid size.

Add docblocks to all files, and maybe also add comment blocks to functions.

Detect if user is running a script for a different module than they're in, and pause the execution so they can cancel if they want.

Move Auto-Select button to top of in-game interface window.

~~Make control documentation page to replace DCS BIOS's control-reference.html.  The page should be searchable and display all controls in the controlMappings in a neat, readable format for script authors.~~  Done: Help > Control Reference (`docs/controlReference.html`, data built by `utils/controlReference.py`); raw controls are highlighted with this note as a tooltip.
	For `type: "raw"` controls, these should be clearly delineated as 'use at your own risk' — they have no known argLim, step, or readback arg.  You'll need to experiment to find the right values to send.  A good starting point is the module's `Input/<variant>/keyboard/default.lua` and `Input/<variant>/joystick/default.lua` files, which map key and axis bindings to `{device, action, value}` triples — those `value` fields are the native DCS values and are often exactly what you'd pass to a raw control.

Investigate the possiblity of dynamic script timing...  The timing is set to 0.3 sec right now to ensure that it works in high-lag MP servers.  Could we instead have the script execute a command and then immediately check the cockpit state for that command and see if it's been completed, and don't execute the next command until it is?  (Partial: scriptLoopUntilStart/End now provides a building block for this — wrap the execute-then-check pattern in those markers.  A general "auto-confirm every command" mode would still be a separate feature.)
	This is already being done in the validation script, where we send the command, then start reading until the value has stabilized before sending the next command.
	One tricky thing is 'discrete indicator' controls, where the value you read from the control will not be the same as the value you sent it.  For those, and maybe other controls, there may be no way to positively confirm that the control is in the correct position.  In that case, we may need to default to a 0.3 second wait.

~~Add the ability to have do-loops that execute until a cockpit state condition have been met.~~  Done — scriptLoopUntilStart / scriptLoopUntilEnd commands implemented.  Currently single-condition only; multi-condition AND/OR loops are deferred (see below).

Add multi-condition (AND/OR) support to scriptLoopUntilStart/End.  For now, sequential nested loops cover most cases.  If multi-condition usage grows, consider whether a richer expression evaluator is worth the complexity, or whether scripts should drop into Python-native form for arbitrary logic.

Is there a way we can test the control mapping interface by having a script go through and move every control, and the check if the control has been moved?

Detect if the game is paused (mission timer stops?  or stop receiving telemetry data from DCS?) and automatically pause the script.

Add a visual reminder in the in-game interface when waiting for keyboard commands.

DCSMonitor improvements:
	General interface improvements:
		Double click to add/remove, search in the list boxes, other...
	A control finder, where it builds a cockpit state, and then shows any controls that change, so if you're looking for the DCS BIOS name for a switch, you move the switch, and it detects the change.
	Migrate DCSMonitor.py from DCSBIOSExportManager to DCSDirectManager (eliminate-dcs-bios branch work).

============

Scripts:

F-18
add "setup options" options with sets of setups to do after startup.  One could be setting up radar presets for various missile types.

AH-64
vid background brightness lower on right mfd

Mi-24 sight grid brightness 50%?

F-4
master caution reset at end
set fuze switch to nose and tail
release number to singles (1)
turn on radio!  front and back seat??

oxygen supply lever ... on, not sure why this isn't working
instrument panel and console panel brightness knobs maxed

wso countermeasures mode knobs ... SGL for both chaff and flares
pilot countermeasure dispense switch ... normal (default)

jester
	active radar
	auto focus
	countermeasures?


change kneeboard mapping reference to dispense button on throttle grip

Make startup scripts for:
F-86
MiG-15
MiG-19?
L-39
Mirage 2000
MB-339
Mirage F1
TF-51?
P-47?

~~DCSAutoMateHook.lua: received-message wire logging never fires.  The RX check compares `string.sub(text, 1, 13)` against the 15-character "DCSAUTOMATE_UI;", and `string.sub(text, 1, 23)` against the 26-character "DCSAUTOMATE_COORD_CONVERT;", so neither prefix ever matches.  With "Log in-game overlay network traffic in DCS" on, the hook log only shows messages DCS sends, not ones it receives.  Fix the lengths (or use `#prefix`) and add a lupa test.~~  Done: prefix check moved into `wireRxLabel()` (tested in `tests/test_hookWireLogging.py`).

scriptCockpitState with `duration: 0` always needs two reads to finish: `handleScriptCockpitState` takes `stateCurrentTime` before setting `stateStartTime` on the first met read, so the first elapsed time is slightly negative.  Harmless (one extra 10 ms poll, or one extra 1 s timeout if DCS is slow to answer), but setting `stateStartTime = stateCurrentTime` would fix it.
