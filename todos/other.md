## Native Control Research (DONE — see `.agent/research/dcs-native-control-types.md`)

The following questions have been answered with live testing and documented:

* ✅ How do the control definitions in the DCS lua files determine which values or value ranges the controls need?
* ✅ Some controls have multiple sub-controls or commands.  Engine Crank Switch seems to be one of these.  Canopy is another.  Can we tell from the control definition which commands and values are needed, or do we have to guess and experiment?  We need to figure out how to store those in the command mapping.
* ✅ Some controls take a continuous value range, but they may move either continuously like Radar Altimeter, or in discrete steps like the INS knob.  How can we tell which is which by the definitions?  In the game itself, the INS knob cannot be rotated smoothly, it only moves in discrete steps from position to position.  Is that behavior defined in the lua files somewhere and can we use it to inform our value ranges?
* ✅ Include examples from our testing.

## Remaining TODO Items

### ~~Control Reference HTML Page~~
Done: Help > Control Reference (`docs/controlReference.html`, data built by `utils/controlReference.py`).  Generate a control reference page, similar to the DCS BIOS JSON files and how they can be displayed with the control-reference.html, but a simpler and more streamlined version that just shows what we need for DCSAutoMate.  Design is in research doc §8.

### Text Extraction Verification
All testing so far was in cold & dark cockpit.  Still need to verify:
* IFEI text extraction with engines running
* UFC display text
* Other text displays

### Export Lua Logging
`DCSAutoMate-export.lua` has `logEnabled` flag hardcoded to `false`.  Add remote toggle command (e.g., a new `LOG:1` message; `L:` is taken by LoSetCommand) for debugging without editing the Lua file.

### Servers That Block Ownship Export
Tested 2026-10-04 as a client on a dedicated server with `allow_ownship_export`/`allow_object_export`/`allow_sensor_export` all false (the host is exempt, so test as a client).  All `LoGet*` flight data returns `null`, `LoGetSelfData` keeps only identity fields (Name, Coalition, UnitName...), and `LoSetCommand` is ignored completely (axes and the comms menu, not just axes).  Cockpit args (`BULKQ`), `list_indication` (`T:`), `C:` performClickableAction and `S:` SetCommand all still work.
* ~~`scriptCockpitState` on a `telemetry/...` control waits forever~~ Done on `telemetry-check-skip-wait`: the script warns and pauses at start if DCS doesn't answer a `LoGet*` function it waits on, and **Skip Wait** ends any wait.
* `scriptSimCommand` steps silently do nothing.  LoSetCommand gives no error to detect, but a blocked `LoGetSelfData` (no `LatLongAlt`) could trigger a warning.
* Auto Select's engine-running rule reads `LoGetEngineInfo`, so it can't tell Hot from Cold.

### `G:LoGetWorldObjects` Never Replies
Found 2026-10-04 while probing MP export restrictions: `G:LoGetWorldObjects` gets no reply, even with a 20 s client timeout, while other `G:` calls on a new connection work.  Likely causes: `sendToClient` ignores partial sends on the non-blocking socket (a large reply loses its tail and newline), or `JSON:encode` throws on the table and the error escapes `processCommand`.  Fix by queuing unsent bytes per client and wrapping the encode in `pcall`.

### F-4E Jester Startup
The Jester cold start runs, but Jester asks for the INS alignment twice.  Probably a module bug; the correct Jester startup sequence wasn't clear on the forums last time it was checked.  The no-Jester startup works, and Jester works otherwise.  Recheck after F-4E updates.

### Notes
For things like the radar altimeter on the F-18, don't worry that it seems nonlinear or inverted.  The reason for the apparent nonlinearity is that the min value is at the top of the gauge, but max is not one full revolution, so it's hard to guess during testing what is 25%, 50%, etc.  When developing a new startup script, I'll just test until I find the right number I need to send it to set it where I want.
