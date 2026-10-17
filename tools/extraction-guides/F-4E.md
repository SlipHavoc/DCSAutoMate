# DCS Native Control Extraction — F-4E Phantom II

Module-specific extraction notes for the F-4E Phantom II. Read `general.md` first for universal patterns.

## File Locations

- **Scripts directory:** `<DCS Install>/Mods/aircraft/F-4E/Cockpit/`
- **clickabledata.lua:** `Cockpit/clickabledata.lua`
- **clickable_dsl.lua:** `Cockpit/clickable_dsl.lua` (F-4E uses `_dsl` not `_defs`)
- **devices.lua:** `Cockpit/devices.lua`
- **command_defs.lua:** `Cockpit/command_defs.lua`
- **device_init.lua:** `Cockpit/device_init.lua`
- **mainpanel_init.lua:** `Cockpit/mainpanel_init.lua`
- **sounds.lua:** `Cockpit/sounds.lua`
- **draw_args.lua:** `Cockpit/draw_args.lua`

**Note:** Unlike FA-18C/AH-64D/F-16C, Lua files are in `Cockpit/` directly, NOT `Cockpit/Scripts/`.
Use `scriptsRelPath = 'Mods/aircraft/F-4E/Cockpit'`.

## Module Names

| Context | Name |
|---|---|
| DCS install directory | `F-4E` |
| DCS-reported name (`LoGetSelfData().Name`) | `F-4E-45MC` |
| JSON key in controlMappings | `F-4E-45MC` |
| nativeExtractions file | `F-4E.json` |
| controlMappings file | `F-4E-45MC.json` |

## Crew Architecture

The F-4E is a two-seat aircraft (pilot + WSO). Every clickable element has a `crew_member_access`
field that is a Lua table: `{0}` for pilot-only, `{1}` for WSO-only. No elements use `{0,1}` (both).

This maps to the `crewAccess` field in the extracted JSON:
- `crewAccess: [0]` — pilot (front seat)
- `crewAccess: [1]` — WSO (back seat)

270 pilot elements, 214 WSO elements in the 484-element total.

## Devices

91 devices. Standard `counter()` pattern in `devices.lua`. Slots 28, 37, 43, 57–59, 61 are
empty (no device assigned to those counter values).

| ID | Device Name | Notes |
|---|---|---|
| 1 | PROXY | |
| 2 | ICS | Intercom system |
| 3 | ARC164 | UHF radio |
| 4 | IFF | |
| 5 | COUNTERMEASURES | |
| 6 | EPOXY | |
| 7 | COCKPITMECHANICS | Canopy, mirrors, pilot/WSO panels |
| 8 | MULTICREW | |
| 9 | INPUTCONTROLS | |
| 10 | MAGNETICCOMPASS | |
| 11 | CLOCK | |
| 12 | RADARALTIMETER | |
| 13 | AOASYSTEM | Angle of attack |
| 14 | INS_AN_ASN_63 | Inertial navigation |
| 15 | AN_ASN_63 | |
| 16 | NavigationComputer_AN_ASN_46A | |
| 17 | PNEUMATICGAUGE | |
| 18 | HYDRAULICGAUGE | |
| 19 | TESTDEVICE | |
| 20 | GEARANDHOOK | |
| 21 | AVIONICSCORE | |
| 22 | INDICATORSANDLIGHTS | |
| 23 | CANOPYCONTROLS | |
| 24 | ENGINECONTROLS | |
| 25 | CONTROLSURFACES | |
| 26 | OXYGENSYSTEM | |
| 27 | WEAPONS | |
| 29 | TURNANDSLIP | |
| 30 | COCKPITSOUNDS | |
| 31 | HUD_AN_ASG_26 | |
| 32 | DEBUGDISPLAY | |
| 33 | SENSORS | |
| 34 | FMSENSOR | |
| 35 | ACCELEROMETER | |
| 36 | PITOTSTATIC | |
| 38 | CADC | Central air data computer |
| 39 | MACHANDSPEEDINDICATOR | |
| 40 | BAROMETRICALTIMETER | |
| 41 | VERTICALVELOCITYINDICATOR | |
| 42 | TASINDICATOR | |
| 44 | ADI_ARU_11_A | Attitude direction indicator |
| 45 | CNI_AN_ASQ_19A | |
| 46 | GSINDICATOR | |
| 47 | EMERGENCYATTITUDEINDICATOR | |
| 48 | TACAN_AN_ARN_118 | |
| 49 | FLIGHTDIRECTORCOMPUTER | |
| 50 | HSI_AF_A24J_1 | Horizontal situation indicator |
| 51 | RADAR_SCOPE | |
| 52 | RADAR | AN/APQ-120 |
| 53 | BDHI | Bearing distance heading indicator |
| 54 | COMPASSSYSTEM | |
| 55 | ELECTRICS | |
| 56 | ATTITUDEINDICATOR_ARU13A | |
| 60 | FuelControls | |
| 62 | ATTITUDEREFERENCE | |
| 63 | AIRCRAFTEFFECTS | |
| 64 | EO_TGT_DESIGNATOR_SYSTEM_AN_ASQ_153 | Pave Spike TGP |
| 65 | WSO_FRONT_PANEL | |
| 66 | GROUND_CREW | |
| 67 | RWR_INTERFACE | ALR-46 RWR |
| 68 | IFF_INTERROGATOR_AN_APX_80A | |
| 69 | EXTERIOR_LIGHTS | |
| 70 | VOR_ILS | |
| 71 | EJECTION_SEAT_SYSTEM | |
| 72 | INTERIOR_LIGHTS | |
| 73 | AIRBORNE_VIDEO_TAPE_RECORDER | |
| 74 | PILOT_FRONT_PANEL | |
| 75 | MOVABLE_CLICKABLE_UPDATER | |
| 76 | WSO_COURSEINDICATOR | |
| 77 | BROWSERS | |
| 78 | JESTER_WHEEL | |
| 79 | JESTER_DIALOG | |
| 80 | MANUAL | |
| 82 | GREASE_PENCIL | |
| 83 | SIM_INFO_INTERFACE | |
| 84 | CIRCUIT_BREAKERS | |
| 85 | SEAT | |
| 86 | JESTER | AI WSO |
| 87 | TODO | |
| 88 | AUTO_START | |
| 89 | VIDEO | |
| 90 | BOMBING_TABLE | |
| 91 | ECM | |
| 92 | KNEEBOARD | |
| 93 | VIRTUAL_BROWSER | |
| 94 | HELMET_DEVICE | |
| 95 | VERY_HIGH_FREQUENCY_SYSTEM | |
| 96 | TAPE_PLAYER | |
| 97 | JESTER_CONSOLE | |
| 98 | EFB | |
| 99 | CHARACTER_CUSTOMIZER | |

## Command Architecture (UNIQUE — differs from all other modules)

The F-4E does NOT use per-device `*_commands` globals. Instead, `command_defs.lua` defines:

```lua
local device_subcommands = {
    ICS = { SwitchSomething = 3001, ... },
    ARC164 = { RadioFreqDial1 = 3108, ... },
    -- ... 64 device sub-tables total
}

-- Metatable proxy for backward compatibility
device_commands = setmetatable({}, {
    __index = function(t, k)
        for _, subcmds in pairs(device_subcommands) do
            if subcmds[k] then return subcmds[k] end
        end
    end
})
```

Because `device_subcommands` is `local`, it never enters the Lua global scope. After executing
`clickabledata.lua` (which dofile-loads `command_defs.lua`), recover it via `debug.getupvalue`:

```lua
_f4eDeviceSubcmds = nil
if device_commands then
    local mt = getmetatable(device_commands)
    if mt then
        local indexFn = rawget(mt, '__index')
        if type(indexFn) == 'function' then
            local i = 1
            while true do
                local name, val = debug.getupvalue(indexFn, i)
                if name == nil then break end
                if name == 'device_subcommands' then
                    _f4eDeviceSubcmds = val
                    break
                end
                i = i + 1
            end
        end
    end
end
```

This Lua snippet is executed immediately after `dofile(clickabledata.lua)`, before extracting anything.
The result is a global `_f4eDeviceSubcmds` that `extractCommandTables()` reads via lupa.

**Consequence:** The `deviceTableMap` is built directly from `device_subcommands` keys — it is exact
by construction. The access logger (`installCmdAccessLogger`/`uninstallCmdAccessLogger` from
`extractUtils.py`) is NOT used.

64 devices have entries in `device_subcommands`. The 27 unmapped devices (EPOXY, MULTICREW,
MAGNETICCOMPASS, etc.) are pure indicator/display/AI devices with no clickable elements.
`generateControlMapping.py` falls back to name-similarity heuristics for those.

## Command Tables

65 tables. Counts after extraction:

| Table | Commands | Notes |
|---|---|---|
| JESTER_WHEEL | 231 | Jester AI wheel menu entries |
| WEAPONS | 155 | SMS, ordnance release |
| RADAR | 115 | AN/APQ-120 radar |
| ARC164 | 107 | UHF radio (pilot + WSO) |
| ICS | 57 | Intercommunication system |
| RWR_INTERFACE | 56 | ALR-46 RWR |
| IFF | 67 | IFF transponder |
| IFF_INTERROGATOR_AN_APX_80A | 46 | IFF interrogator |
| EO_TGT_DESIGNATOR_SYSTEM_AN_ASQ_153 | 60 | Pave Spike TGP |
| INTERIOR_LIGHTS | 63 | |
| EXTERIOR_LIGHTS | 27 | |
| COUNTERMEASURES | 65 | |
| TACAN_AN_ARN_118 | 53 | |
| VOR_ILS | 30 | |
| FuelControls | 26 | |
| GEARANDHOOK | 27 | |
| COCKPITMECHANICS | 35 | |
| CONTROLSURFACES | 27 | |
| CIRCUIT_BREAKERS | 33 | |
| PROXY | 41 | |
| TODO | 41 | Placeholder commands |
| CANOPYCONTROLS | 14 | |
| COMPASSSYSTEM | 16 | |
| NavigationComputer_AN_ASN_46A | 24 | |
| OXYGENSYSTEM | 18 | |
| INPUTCONTROLS | 30 | |
| INS_AN_ASN_63 | 20 | |
| ATTITUDEREFERENCE | 16 | |
| ELECTRICS | 17 | |
| ENGINECONTROLS | 17 | |
| HUD_AN_ASG_26 | 14 | |
| EJECTION_SEAT_SYSTEM | 12 | |
| AOASYSTEM | 12 | |
| BAROMETRICALTIMETER | 12 | |
| CLOCK | 12 | |
| AIRBORNE_VIDEO_TAPE_RECORDER | 19 | |
| UNASSIGNED | 12 | |
| JESTER | 14 | |
| FLIGHTDIRECTORCOMPUTER | 11 | |
| ADI_ARU_11_A | 6 | |
| HSI_AF_A24J_1 | 6 | |
| GREASE_PENCIL | 6 | |
| SEAT | 6 | |
| MACHANDSPEEDINDICATOR | 4 | |
| ACCELEROMETER | 4 | |
| CADC | 4 | |
| CNI_AN_ASQ_19A | 4 | |
| ECM | 12 | |
| AVIONICSCORE | 2 | |
| ATTITUDEINDICATOR_ARU13A | 3 | |
| RADARALTIMETER | 6 | |
| WSO_FRONT_PANEL | 8 | |
| PILOT_FRONT_PANEL | 3 | |
| INDICATORSANDLIGHTS | 9 | |
| BOMBING_TABLE | 4 | |
| AUTO_START | 2 | |
| PITOTSTATIC | 3 | |
| EMERGENCYATTITUDEINDICATOR | 2 | |
| MANUAL | 6 | |
| JESTER_CONSOLE | 4 | |
| CHARACTER_CUSTOMIZER | 4 | |
| EFB | 4 | |
| VIDEO | 4 | |
| VIRTUAL_BROWSER | 4 | |
| WSO_COURSEINDICATOR | 3 | |

## Elements

484 clickable elements — verified: `grep -cP '^elements\["[^"]+"\] =' clickabledata.lua` = 484.

Standard extraction from `lua.globals().elements`, plus the F-4E-specific `crewAccess` field
(see Crew Architecture section above).

## Indicators

18 indicators. The F-4E does NOT use a numeric indication ID like other modules; all `id` fields
are `None` in the extraction. The IDs are assigned by `device_init.lua` order when DCS runs.

| Index | C++ Class | Init File |
|---|---|---|
| 1 | `F4EAvionics::ccHUD_AN_ASG_26` | `Scripts/HeadUpDisplay/Indicator/init.lua` |
| 2 | `F4EAvionics::ccDebugDisplay` | *(no init file)* |
| 3 | `F4EAvionics::ccRadar` | `Scripts/DSCG/indicator/init.lua` |
| 4 | `F4EAvionics::ccRadarScope` | `Scripts/DSCG/indicator/TV_Indicator/init.lua` |
| 5 | `F4EAvionics::ccSensor` | `Scripts/DSCG/indicator/TV_Sensor/init.lua` |
| 6 | `F4EAvionics::ccDSCGPilot` | `Scripts/DSCG/indicator/DSCG_Pilot/init_bake.lua` |
| 7 | `F4EAvionics::ccDSCGWSO` | `Scripts/DSCG/indicator/DSCG_WSO/init_bake.lua` |
| 8 | `F4EAvionics::ccTgtDesignatorBitDisplay` | `Scripts/EoTgtDesignatorSystem/Indicator/BitDisplay/init.lua` |
| 9 | `F4EAvionics::ccRangeIndicator` | `Scripts/EoTgtDesignatorSystem/Indicator/RangeIndicator/init.lua` |
| 10 | `F4EAvionics::ccFrequencyChannelIndicator_ARC_164_Pilot` | `Scripts/UHF_Radio/Indicator/FrequencyChannelIndicator/init.lua` |
| 11 | `F4EAvionics::ccFrequencyChannelIndicator_ARC_164_Wso` | `Scripts/UHF_Radio/Indicator/FrequencyChannelIndicator/init.lua` |
| 12 | `F4EAvionics::ccALR46` | `Scripts/RWR/indicator/init_46.lua` |
| 13 | `F4EAvionics::ccALR46_Display` | `Scripts/RWR/indicator/init_bake.lua` |
| 14 | `F4EAvionics::ccControlsIndicator` | `Scripts/ControlsIndicator/init.lua` |
| 15 | `F4EAvionics::ccAvtrTimeIndicatorWso` | `Scripts/Cameras/Indicator/AvtrTimeIndicatorWso/init.lua` |
| 16 | `F4EAvionics::ccAvtrTimeIndicatorPilot` | `Scripts/Cameras/Indicator/AvtrTimeIndicatorPilot/init.lua` |
| 17 | `F4EAvionics::ccFog` | `Scripts/Fog/indicator/init.lua` |
| 18 | `F4EAvionics::DCS_Browsers` | *(no init file)* |

107 indication fields total across 12 indicators (6 have no fields).

## Indication Fields by Indicator

| Indicator | Fields |
|---|---|
| ccHUD_AN_ASG_26 | 9 |
| ccRadar | 25 |
| ccRadarScope | 5 |
| ccSensor | 5 |
| ccTgtDesignatorBitDisplay | 4 |
| ccRangeIndicator | 4 |
| ccFrequencyChannelIndicator_ARC_164_Pilot | 4 |
| ccFrequencyChannelIndicator_ARC_164_Wso | 4 |
| ccALR46 | 27 |
| ccControlsIndicator | 12 |
| ccAvtrTimeIndicatorWso | 4 |
| ccAvtrTimeIndicatorPilot | 4 |

## Gauges and Lamps

Only 2 gauges/lamps extracted from `mainpanel_init.lua`. The F-4E uses fewer named gauge globals
than other modules; most cockpit animation is driven via DCS draw args rather than named CreateGauge
calls. This is expected and correct.

## Module-Specific Lupa Mocks

In addition to the universal mocks, the F-4E needs:

### `LockOn_Options.flight` sub-table
`mainpanel_init.lua` line ~22 accesses `LockOn_Options.flight.easy_radar` and
`LockOn_Options.flight.auto_lockon` directly. Must add these to the `LockOn_Options` mock:

```python
lua.execute('''
    LockOn_Options = {
        script_path = "...",
        common_script_path = "...",
        flight = { easy_radar = false, auto_lockon = false },
    }
''')
```

### `get_aircraft_type()`
Called near the top of `mainpanel_init.lua`. Must return a string (empty is fine):
```lua
function get_aircraft_type() return '' end
```

### `create_guid_string()`
Called in `common_defs.lua` (line ~209) which is dofile-loaded during indicator page extraction.
This is NOT needed in `createLuaRuntime()` — instead pass it as `extraLuaSetup` to
`extractTextFieldsLupa()` because that function creates its own independent Lua sandbox:

```python
f4eExtraSetup = '''
    local _guidCounter = 0
    function create_guid_string()
        _guidCounter = _guidCounter + 1
        return 'guid-' .. tostring(_guidCounter)
    end
    function GetRenderTarget() return 0 end
'''
```

### `GetRenderTarget()` override in indicator pages
The shared `_textFieldsLuaInit` in `extractUtils.py` defines `GetRenderTarget()` returning a
table `{width=256, height=256, aspect=1.0}`. F-4E indicator pages (`maverick_page.lua`,
`pave_spike_page.lua`, `walleye_page.lua`) use `GetRenderTarget() + 1` — arithmetic on the
return value. This fails when the return is a table. Fix: override `GetRenderTarget()` to return
`0` (a number) in the same `extraLuaSetup` string (see above).

### Missing VFS-provided files (expected, harmless)
These files are provided by the DCS engine at runtime via VFS and are not present in the module
directory. The error-tolerant `dofile` mock logs warnings and continues:

- `Cockpit/Fonts/symbols_locale.lua`
- `Cockpit/Fonts/fonts_cmn.lua`
- `Cockpit/Fonts/font_ALQ_213.lua`
- `Cockpit/Fonts/font_general.lua`
- `Cockpit/tools.lua`
- `Cockpit/KNEEBOARD/declare_kneeboard_device.lua`

These warnings are expected and do not affect extraction correctness.

## Extraction Results

| Metric | Count |
|---|---|
| Devices | 91 (slots 28, 37, 43, 57-59, 61 empty) |
| Command tables | 65 |
| Elements | 484 |
| crewAccess pilot [0] | 270 |
| crewAccess WSO [1] | 214 |
| Indicators | 18 |
| Indication fields | 107 |
| Gauges and lamps | 2 |
| deviceTableMap (exact) | 64/91 |
| deviceTableMap (heuristic) | 27/91 |
