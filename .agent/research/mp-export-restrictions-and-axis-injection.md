# MP export restrictions and axis injection (live-tested 2026-10-04/05, DCS 2.9.30, FA-18C)

## Axis injection with LoSetCommand

`L:2001:<v>` (`iCommandPlanePitch`), `2002` roll, `2003` rudder, `2004` thrust common (1 = idle, -1 = max), `2005`/`2006` thrust left/right, `2087` collective.  Values -1..1.  FA-18C cockpit args that follow them: 71 stick pitch, 74 stick roll, 500 pedals, 104/105 throttles.

- A single send sets the axis and holds until the physical axis next reports a change.  A moving or jittery stick reports nearly every frame.
- Resending every frame wins: the stick arg held the injected value 99.5-99.7% of frames while the stick was being stirred.  At 20 Hz it held only ~12%.
- The Export reads TCP commands once per frame (`LuaExportBeforeNextFrame`), so a Python send/receive loop locks to the frame rate by itself (~79 Hz here).  For anything real, repeat the value in the Export Lua instead of over TCP.
- While injecting every frame the pilot is locked out, so an autopilot needs an obvious disengage.

### Held values (`H:command:seconds:stop:value`, `scriptSimCommand` `value` + `hold`), live-tested 2026-10-05 in the C-130J

- The C-130J's power levers are cockpit args 21-24 (603 follows them).  Lever = -axis exactly, on -1 (fully back) .. 1: `iCommandPlaneThrustCommon` at 0.678 puts all four at -0.678, the GND IDLE detent.  The detent isn't in the module's Lua (probably compiled in), so it was found by reading the args with the player's levers at GND IDLE.
- A `ThrustCommon` hold beat the player's separately bound Throttle Left/Right axes (2005/2006) while they were being moved: 276 of 276 samples at GND IDLE.  The module's per-lever axes are `JOYSTICK.throttle1`-`4` = 4003-4006 (from command_defs.lua via lupa).
- After release the levers follow the hardware at its next change.  With jitter (this HOTAS jitters unless fully back) that's immediate.
- A single `L:` send can't even be read back on a jittery axis: the hardware overrides it within a frame or two, so diff scans for axis args need a hold.
- A dropped client's holds end (the Export releases them when the socket closes).  To test that from Python, close the `makefile()` reader as well as the socket: `socket.close()` alone leaves it open.

## Servers that block player export

Server settings `allow_ownship_export` / `allow_object_export` / `allow_sensor_export` (Saved Games/DCS/Config/serverSettings.lua).  Tacview logs what was granted in dcs.log: `Export rights granted by the host: PlayerPlane=[0] PlayerSensors=[0] OtherObjects=[0]`.

- **The host is exempt.**  A server run from the game client still gives its own player everything.  Test as a client of a dedicated server.
- As a blocked client:
  - Every `LoGet*` flight-data function returns `null`.  `LoGetModelTime`, `LoGetMissionStartTime`, `LoGetPilotName` and `LoGetVersionInfo` still answer.
  - `LoGetSelfData` keeps only Name, Type, Coalition, CoalitionID, Country, GroupName and UnitName.  No `LatLongAlt`, Pitch, Bank or Heading.  DCSAutoMate uses the missing `LatLongAlt` to detect a blocking server (`DCSSeqExecute.checkSimCommands`).
  - `LoSetCommand` is ignored completely: axes, even resent every frame, and plain commands such as `iCommandToggleCommandMenu`.
  - Cockpit args (`get_argument_value`), `list_indication`, `performClickableAction` (`C:`) and `SetCommand` (`S:`) all still work.
- In a survey of the top ~100 MP servers by player count, only 1 blocked player export.  PvP servers allow it too, as cockpit builders rely on it.

## Consequences for scripts

- `telemetry/...` waits never finish on a blocking server.  The executor now warns and pauses at script start, and Skip Wait ends any wait.
- `scriptSimCommand` steps do nothing there.  The executor now warns at start and prompts the player to do each step by hand.  Keystrokes (`scriptKeyboard`) still work, being real input.
- `arg.`/`ind.` controls work everywhere, so prefer a cockpit gauge where a script must work on every server.

## Open

- `G:LoGetWorldObjects` never replies, probably because the reply is too large for one non-blocking send (see `todos/other.md`).
