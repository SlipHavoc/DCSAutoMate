Metadata: I search duckduckgo for 'dcs a_cockpit_highlight' and this document was the first hit.  Appears to be an old forum attachment.  The document was originally a PDF, I converted it to markdown.


# Digital Combat Simulator — Cockpit Triggers Guide

## Introduction

The cockpit triggers utilized in Digital Combat Simulator allow a mission designer to create a wide variety of triggers that evaluate the state of cockpit switches and instruments. This data can be used to provide feedback and instruction to the player using text and voice prompts, as well as 3D graphical highlights of cockpit elements.

Although cockpit triggers are considered a developer's tool, most of their functionality is open to the player. There are some examples, however, which require the use of the in-game console, which is disabled in public builds.

Cockpit triggers are utilized similarly for all DCS flyable aircraft. A number of aircraft script files (`.LUA`) are used to obtain data used by the triggers. Each DCS aircraft includes a collection of script files in its own dedicated folder, found in `X:\Game Directory\Scripts\Aircrafts`. The specific `.LUA` files used by cockpit triggers will be referenced below. To ease the workload of a mission designer working with cockpit triggers, a cockpit arguments guide has been prepared for the A-10C cockpit and can be found here: <http://files.digitalcombatsimulator.com/en/84654/>

`.LUA` files should only be opened with a proper code editor, such as Notepad++. When working with the scripts, the Search function (`Ctrl + F`) can be very helpful in locating the desired sections of code.

---

## Conditions

### Cockpit Argument In Range

The position of every cockpit control and instrument is defined by a custom argument ID and valid value range. This trigger checks for a set cockpit argument to be within a set value range. This is most often used to evaluate switch and button states with discrete argument values (such as `0` for off and `1` for on, or in decimal values between 0 and 1 for multi-position switches). However, it can also be used to evaluate the position of needle instruments, such as airspeed or vertical velocity, etc.

- **Argument** – sets the ID number of the cockpit argument to check. Clickable cockpit functions (switches, buttons, knobs, etc.) are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\clickabledata.lua`. Non-clickable cockpit arguments, such as instruments, are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\mainpanel_init.lua`. The variable `arg` describes the argument ID. The variable `arg_value` describes the increment of each movement of the argument. The variable `arg_limit` describes the limits of the argument's range of movement.
- **MIN** – sets the minimum value of the set argument, which will satisfy the condition to execute the trigger. Valid value range is -1 to 1.
- **MAX** – sets the maximum value of the set argument, which will satisfy the condition to execute the trigger. Valid value range is -1 to 1.

> **Note:** to successfully evaluate an argument, you may need to enter a MIN and MAX range that is inclusive of the desired value. For example, when evaluating an argument to equal `0.5`, enter `0.49` for MIN and `0.51` for MAX.

### Cockpit Highlight Is Visible

Checks for a set cockpit highlight to be displayed. Each cockpit highlight is assigned an ID by the mission designer. This trigger evaluates whether a specific highlight is displayed in the cockpit.

- **ID** – sets the ID value of the cockpit highlight to check (as set by COCKPIT HIGHLIGHT ELEMENT/INDICATION/POINT trigger actions).

### Cockpit Indication Text Is Equal To *(requires console)*

Checks the contents of a set cockpit digital indication string. Digital indicators in the cockpit are individually identified by an ID number in the `.LUA` files. Each indicator displays a collection of display elements. This trigger evaluates whether a specific display element of a set indicator matches the desired string of characters. This is a very useful method of evaluating whether the correct avionics parameters are set up on the digital displays.

- **Indicator ID** – sets the ID value of the cockpit indicator containing the desired element. Indicator IDs are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\device_init.lua`. To quickly locate the indicator IDs in the `.LUA` file, perform a search function for `indicators`. Indicator IDs begin with `0` at the top of the table and are increased by 1 with each subsequent indicator in the table. For example, the HUD ID for A-10C is `5`.
- **Elem name (element name)** – sets the name of the display element containing the desired string. To obtain an element name, run a mission with the desired element string displayed in the cockpit, open the game console and execute the `console.out(list_indication(n))` command (where `n` is the desired indicator's ID). The game console can be accessed by pressing the `` ` `` command in-game. The `console.out(list_indication(n))` console command will list all currently displayed elements with their associated strings for the set indicator. Note, the element name entry must match the element name exactly, including capitals and spaces (spaces may be present as initial characters).
- **String (not labeled)** – sets the character string, which will satisfy the condition to execute the trigger. Note, the string entry must match the element string exactly, including capitals and spaces (spaces may be present as initial characters).

> **Example:** To set up a trigger in A-10C that checks for the TAD map range to be set to 40 miles, enter `1` for indicator ID to set this to the left MFCD, enter `TAD_scale` as the element name, and enter `40` as the desired string.

### Cockpit Param Equal To *(requires console)*

Checks for the desired setting of a set cockpit parameter. This trigger evaluates a number of specially-designed cockpit parameter trackers for the A-10C (such as TGP zoom level, steerpoint name, etc.).

- **Param (parameter)** – sets the name of the parameter to check. To obtain a parameter name, run a mission with the desired parameter active, open the game console and execute the `console.out(list_cockpit_params())` command. The game console can be accessed by pressing the `` ` `` command in-game. The `console.out(list_cockpit_params())` console command will display the current states of all cockpit parameters.
- **Value** – sets the parameter setting, which will satisfy the condition to execute the trigger. Note, depending on the parameter, the value may be a numerical or alphabetical string.

### Cockpit Param In Range *(requires console)*

Checks for the set cockpit parameter to be within the set value range. This trigger evaluates a number of specially-designed cockpit parameter trackers (such as TGP zoom level, steerpoint name, etc.).

- **Param (parameter)** – sets the name of the parameter to check. To obtain a parameter name, run a mission with the desired parameter in effect, open the game console and execute the `console.out(list_cockpit_params())` command. The game console can be accessed by pressing the `` ` `` command in-game. The `console.out(list_cockpit_params())` console command will display the current states of all cockpit parameters.
- **MIN** – sets the minimum value of the set parameter, which will satisfy the condition to execute the trigger. Valid value range is -1^9 to 1^9.
- **MAX** – sets the maximum value of the set parameter, which will satisfy the condition to execute the trigger. Valid value range is -1^9 to 1^9.

### Cockpit Param Is Equal To Another

Checks for the set parameter value to be identical to another parameter's value. This trigger can be used in conjunction with the COCKPIT PARAM SAVE AS action in order to compare parameter values at different points in the mission.

- **Param (parameter)** – sets the name of the first parameter to evaluate. To obtain a parameter name, run a mission with the desired parameter in effect, open the game console and execute the `console.out(list_cockpit_params())` command. The game console can be accessed by pressing the `` ` `` command in-game. The `console.out(list_cockpit_params())` console command will display the current states of all cockpit parameters.
- **Param (parameter)** – sets the name of the second parameter to evaluate.

> **Note:** one of the two parameter variables may be a custom parameter name saved using the COCKPIT PARAM SAVE AS action.

---

## Actions

### Start Wait User Response

Start listening for input of the SPACE BAR key to set the specified flag to on. This can be a convenient way to progress a training mission based on the player's signal. Using this trigger will prevent an input command normally mapped to the Space Bar key (usually fire gun).

- **Flag** – sets the flag number to set to on when the SPACE BAR key is pressed while the action is in effect.

### Stop Wait User Response

Stop listening for input of the SPACE BAR key. This trigger disables the START WAIT USER RESPONSE action.

### Cockpit Highlight Element

Enables a cockpit highlight of the specified cockpit control (switch, button, knob, etc.).

- **ID** – sets the ID of the highlight. The ID can be referenced by other triggers to evaluate the status of or remove the highlight.
- **Elem name (element name)** – sets the name of the cockpit control to highlight. Clickable cockpit functions (switches, buttons, knobs, etc.) are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\clickabledata.lua`.
- **Size of box** – sets the span of the highlight in meters. A setting of `0` will automatically conform the highlight to the 3D shape of the cockpit control.

### Cockpit Highlight Indication *(requires console)*

Enables a cockpit highlight of the specified digital indication element (such as HUD display elements).

- **ID** – sets the ID of the highlight. The ID can be referenced by other triggers to evaluate the status of or remove the highlight.
- **Indicator ID** – sets the ID value of the cockpit indicator containing the desired indication. Indicator IDs are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\device_init.lua`. To quickly locate the indicator IDs in the lua file, perform a search function for `indicators`. Indicator IDs begin with `0` at the top of the table and are increased by 1 with each subsequent indicator in the table. For example, the HUD ID for A-10C is `5`.
- **Elem name (element name)** – sets the name of the display element to highlight. To obtain an element name, run a mission with the desired element string displayed in the cockpit, open the game console and execute the `console.out(list_indication(n))` command (where `n` is the desired indicator's ID). The game console can be accessed by pressing the `` ` `` command in-game. The `console.out(list_indication(n))` console command will list all current element strings of the set indicator.
- **Size of box** – sets the span of the highlight in meters.

### Cockpit Highlight Point

Enables a cockpit highlight centered at the specified 3D cockpit coordinates. This action allows you to specify the 3D dimensions of the highlight, which can be useful for creating "flat" 2D highlights of panel instruments in either horizontal or vertical planes.

- **ID** – sets the ID of the highlight. The ID can be referenced by other triggers to evaluate the status of or remove the highlight.
- **X (fwd/aft)** – sets the highlight position on the X (forward/aft) axis of the cockpit in meters.
- **Y (up/dn)** – sets the highlight position on the Y (up/down) axis of the cockpit in meters.
- **Z (rgt/lft)** – sets the highlight position on the Z (right/left) axis of the cockpit in meters.
- **Box dim, X** – sets the span of the highlight's X axis in meters.
- **Box dim, Y** – sets the span of the highlight's Y axis in meters.
- **Box dim, Z** – sets the span of the highlight's Z axis in meters.

### Cockpit Param Save As *(requires console)*

Save the current value of the specified cockpit parameter as a new parameter. This trigger allows you to save the state of a parameter for later evaluation during the mission.

- **Source** – sets the name of the parameter for which the value will be saved. To obtain a parameter name, run a mission with the desired parameter in effect, open the game console and execute the `console.out(list_cockpit_params())` command. The game console can be accessed by pressing the `` ` `` command in-game. The `console.out(list_cockpit_params())` console command will display the current states of all cockpit parameters.
- **Destination** – sets the name of the new parameter, under which the value of the saved parameter will be stored while the mission is running.

### Cockpit Perform Clickable Action

Sets the specified cockpit control to the specified position. This trigger can be used to force-set a required cockpit control (for example to engage autopilot mode).

- **Cockpit device** – sets the ID value of the cockpit device manipulated by the required control. Device IDs are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\devices.lua`. Device IDs begin with `1` at the top of the table and are increased by 1 with each subsequent device in the table. For example, the ID for autopilot is `38`.
- **Command** – sets the command value for the required control, starting with a base value of 3000. Command values are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\clickabledata.lua`, using the argument `device_commands.Button_n` (where `n` is the command value of interest). To quickly locate a desired command in the `.LUA` file, perform a search for relevant terms (such as `autopilot` or `MFCD`). For example, the command to engage the autopilot in A-10C is scripted as `device_commands.Button_2`. As such, it would be entered in the Command field as `3002`.
- **Value** – sets the argument value (control position in the cockpit). Control arguments are described in `Scripts\Aircrafts\Aircraft Name\Cockpit\clickabledata.lua`. The variable `arg` describes the argument ID (not necessary for this trigger). The variable `arg_value` describes the increment of each movement of the argument. The variable `arg_limit` describes the limits of the argument's range of movement.

### Cockpit Remove Highlight

Removes the specified cockpit highlight.

- **ID** – sets the ID of the cockpit highlight to remove.

### Set Command

Inputs the specified game command.

- **Command** – sets the ID value of the command to input. The command ID can be obtained in the Game Options > Controls screen by hovering the mouse over the command description (left side of the screen). This functionality can be enabled in `Mission Editor/Mission Editor.lua` by changing the `OPTIONS_ADD_COMMAND_CODES_TO_TOOLTIP` line from `false` to `true`.

### Set Command With Value

Inputs the specified game command with the specified value.

- **Command** – sets the value of the command to input. The command value can be obtained in the Game Options > Controls screen by hovering the mouse over the command description (left side of the screen). This functionality can be enabled in `Mission Editor/Mission Editor.lua` by changing the `OPTIONS_ADD_COMMAND_CODES_TO_TOOLTIP` line from `false` to `true`.
- **Value** – sets the value with which to enter the command.

### Start Listen Cockpit Event

Start listening for the specified cockpit event to set the specified flag to on. Cockpit events are limited to the Ka-50.

- **Event** – sets the event name to listen to. The following events are currently scripted in the engine:
  - `setup_HMS`
  - `setup_NVG`
  - `DisableTurboGear`
  - `GroundPowerOff`
  - `EnableTurboGear`
  - `GroundPowerOn`
  - `OnNewNetHelicopter`
  - `initChaffFlarePayload`
  - `switch_datalink`
  - `OnNewNetPlane`
  - `WeaponRearmFirstStep`
  - `WeaponRearmComplete`
  - `initChaffFlarePayload`
  - `repair`
  - `LinkNOPtoNet`
  - `UnlinkNOPfromNet`
- **Flag** – sets the flag number to set to on when the specified event occurs.

### Start Listen Command

Start listening for the specified input command to set the specified flag to on.

- **Command** – sets the value of the command to listen to. The command value can be obtained in the Game Options > Controls screen by hovering the mouse over the command description (left side of the screen). This functionality can be enabled in `Mission Editor/Mission Editor.lua` by changing the `OPTIONS_ADD_COMMAND_CODES_TO_TOOLTIP` line from `false` to `true`.
- **Flag** – sets the flag number to set to on when the specified event occurs.
- **Hit Count** – sets the number of times the command must be entered before the specified flag is set to on.
- **Val Lim Min** – sets the minimum value of the command input.
- **Val Lim Max** – sets the maximum value of the command input.

### Prevent Controls Synchronization

This trigger can be used at the start of the mission to disable synchronization of cockpit controls with the actual controls on the player's input hardware. When enabled in the player's Options > Miscellaneous tab, control synchronization may negatively affect missions with cockpit triggers by automatically setting cockpit controls to positions other than default.