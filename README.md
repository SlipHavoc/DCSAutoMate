# DCSAutoMate
Python scripting engine for DCS World using DCS BIOS.

This script uses DCS BIOS (specifically, [the DCS BIOS fork for DCS Flightpanels](https://github.com/DCSFlightpanels/dcs-bios)) to send commands to DCS.  It also uses [pydirectinput](https://github.com/learncodebygaming/pydirectinput) to send keyboard commands.

This is intended to replace the existing built-in autostart scripts in DCS, which after v.2.8 became subject to the "Pure Scipts" flag on multiplayer servers.  In order to modify the built-in startup scripts, you have to change the actual game files, which makes them fail the IC check if Pure Scripts is enabled.  DCSAutoMate is not affected by this check because it sends the commands to DCS via DCS BIOS, which is in the user-editable files in Saved Games.

DCSAutoMate can also be used to script any other cockpit commands, such as adding waypoints or setting countermeasures programs.

# How to use this program

**Installation and setup**

1. Install the [DCS Flightpanels fork of DCS BIOS](https://github.com/DCSFlightpanels/dcs-bios).  To install, copy the DCS-BIOS folder into C:\Users\\<username\>\Saved Games\DCS\Scripts, and add the line in Export.lua to your Export.lua (see instructions on DCS BIOS page for details).
2. Download the DCSAutoMate.zip file and extract to a folder of your choice.
3. (Optional, but allows displaying additional realtime data in the program) Copy DCSAutoMateExport.lua to C:\Users\\<username\>\Saved Games\DCS\Scripts.  And add the following line to the Export.lua file in that folder:

	`dofile(lfs.writedir()..[[Scripts\DCSAutoMateExport.lua]])`

**Basic use**

1. Double-click **DCSAutoMate.exe** to run the program.  Keep the DCSAutoMate window open.
2. Start DCS.
3. When you're in cockpit and ready to run a script, alt-tab out to the DCSAutoMate window and select the module (the plane you're in), then the script you want to run, and any options for that script that appear.
4. Click the Start button to start running the script.  The script will start sending commands to the DCS window.  You can alt-tab back into DCS at that point.  (If the script has keyboard commands, the DCS window will automatically get focus when those commands are sent.)
5. After the script is done, you can close DCSAutoMate, or leave it open and ready to run another script.  (To stop a script while it's running, click the Stop button, or just close the DCSAutoMate window.)

You can run any script at any time; it's up to you to run the *right* script at the *right* time.

Optionally, you can set a few configuration options for the program by selecting the Config menu item.  See below for explanation of settings.

**Config options**

Open the config window in the app by clicking the **Config** menu item, then **Edit Config**.  Here are the options:

* **Debug** - If checked, you can still run scripts, but no data will be sent to DCS, and DCS doesn't even have to be running.  scriptCockpitState commands will automatically be assumed to meet their conditions (but will still wait for the required duration, if any).  This allows you to test scripts without having to be in the game.
* **Disable Text-to-Speech ouput** - If checked, no speech will be generated and DCSAutoMate will run silently.
* **Find DCS window by window title** - If checked, will make DCSAutoMate try to find the DCS window by searching for the title.  If not checked (default), DCSAutoMate will try to find the DCS window by searching for the Windows process executable, which should be more reliable.  The DCS window is needed in order to send keyboard commands.
* **DCS window title** - If filled in (and "Find DCS window by window title" is checked), DCSAutoMate will look for a window with this value anywhere in its title (case-insensitive) and send the script keyboard commands to the first one it finds.  If left blank, defaults to "Digital Combat Simulator".
* **DCS Saved Games folder path** - If filled in, DCSAutoMate will use this value for the path to the Saved Games folder.  You can use the string '%USERPROFILE%' to represent your personal Users folder.  This path is needed in order to get the DCS BIOS control descriptions.  If left blank, DCSAutoMate will look for '%USERPROFILE%\Saved Games\DCS', and if that folder doesn't exist it'll look for '%USERPROFILE%\Saved Games\DCS.openbeta'

**Saved config and settings files**

DCSAutoMate stores its configuration settings in DCSAutoMateConfig.json, and it remembers the last script and options you picked by storing them in DCSAutoMateSettings.json.  You can edit those files manually if you wish, but it's not recommended.  If they get messed up, you can just delete them, and DCSAutoMate will create new ones.

**Running DCSAutoMate.py as a Python program**

If using DCSAutoMate.exe, no installation or other programs should be needed.  The exe is made using [auto-py-to-exe](https://github.com/brentvollebregt/auto-py-to-exe) and should be completely standalone.

If using DCSAutoMate.py, you will need to have [Python 3.7 or greater](https://www.python.org/downloads/windows/) installed, as well as [pydirectinput](https://github.com/learncodebygaming/pydirectinput) and [pygetwindow](https://github.com/asweigart/PyGetWindow/tree/master) (pip install pydirectinput`and `pip install pygetwindow`, or see instructions in their documentation).

# Creating/modifying script files, script file output format, and available commands
Use the scripts that come with DCSAutoMate as examples.  The script functions in the .py files in the DCSAutoMateScripts subfolder ultimately return a Python List.  Each element in the list must be a Dictionary.  The dictionary keys you need depend on the command.  Here are the current valid commands, what they do, and the keys they must have in their dictionary:

All commands must have at least these 2 keys:

>'time': \<float\>, # The number of seconds after the previous command that this command will be executed.  I recommend **0.3** seconds to avoid problems with lag in MP servers, although in SP with a fast computer you can often use 0.1.  All the included scripts default to 0.3.

>'cmd': \<string\>, # The command to be executed.  This must either be an exact (and case-sensitive) DCS BIOS control identifier (e.g. 'APU_CONTROL_SW' for the F-18), or one of the following special command strings: 'scriptKeyboard', 'scriptSpeech', 'scriptCockpitState', 'scriptTimerStart', or 'scriptTimerEnd'.

Here are the additional keys supported by each command:

**DCS BIOS commands**

These send a command to move a cockpit control with DCS BIOS.

>'arg': \<string or int\>, # The string or int parameter value for the command.  For switches and knobs with discrete values, it's usually 0, 1, ..., N.  For continuously rotating knobs, it may be '-3200' or '+3200' to rotate the knob one 'click' (equivalent to one mouse scrollwheel notch).  For smoothly-rotating knobs with end stops, it's usually a number between 0 and 65535.

>'msg': \<string\>, # Optional, defaults to ''.  A message to be displayed when the command executes.

**scriptKeyboard**

These send a keyboard input to DCS, as if you had pressed a key.  Some cockpit controls (such as "Move throttle to idle") don't have DCS BIOS interfaces, so you need to send a key press to move the control.

>'arg': \<string\>, # The keyboard key to be sent to DCS.  A list of supported key names can be found here: https://pyautogui.readthedocs.io/en/latest/keyboard.html#keyboard-keys .  The string can be either a single key, or a key and an action, separated with a space.  Examples: 'a', presses and releases the letter A key.  'add', presses and releases the numpad + key.  'RCtrl down', presses and holds the RCtrl key.  'RCtrl up' releases the RCtrl key.  Only one key can be sent per command, so for combinations like RCtrl+Home, you need to send 'RCtrl down', 'home', 'RCtrl up' as three separate commands.  DCSAutoMate accepts several aliases for the keyboard keys so you can use 'RCtrl' instead of 'ctrlright' for instance, or 'num+' instead of 'add'.

>'msg': \<string\>, # Optional, defaults to ''.  A message to be displayed when the command executes.

**scriptSpeech**

This makes DCSAutoMate speak a message out loud.  Useful to let you know what's happening in the script as it runs, or remind you to do certain things.

>'arg': \<string\>, # This is a string which will be spoken out loud by Microsoft Text-To-Speech.

>'msg': \<string\>, # Optional, defaults to ''.  A message to be displayed when the command executes.

**scriptCockpitState**

This makes the script pause, and wait until a particular control in the cockpit is at/above/below a particular value before continuing.  For instance, you can set the canopy switch to down, and then monitor the canopy position until it's at 0, and then set the canopy switch to neutral.  Or start an engine, and then monitor the engine RPMs until they're over some value, and then move the throttle to the idle detent.  Previously you would have to time how long something takes and hardcode that number of seconds into the script.  You can still do that, but scriptCockpitState makes the script more natural, and lets the script respond to dynamic cockpit events, such as an alignment that takes a variable amount of time, or engines that take longer to come to idle in extreme cold weather.

Internally, when DCSAutoMate starts, it spawns a thread that monitors the UDP multicast data stream that DCS BIOS sends from the game.  It builds up a complete cockpit state based on that data.  (A complete state may take 5-10 seconds to assemble; currently there's no indication in DCSAutoMate when that is complete, so if you start running scripts immediately after starting the program that use the cockpit state near the beginning of the script, you may get some unexpected results).  scriptCockpitState commands make the script check the value of the given cockpit control, and then compare that to a desired value, using a provided comparison operator (equals, or greater/less than), and optionally wait for a given number of seconds during which the cockpit control has to stay within that condition.  Once the condition is met for the amount of time required, the script continues.

>'control': \<string\>, # The exact, case-sensitive DCS BIOS module/identifier for a control, e.g. 'FA-18C_hornet/APU_READY_LT'.  This can be found in the DCS BIOS control reference docs.

>'condition': \<string\>, # The comparison operator that will be used to compare the control's current state in the cockpit to the value.  Can be: '=', '<', '<=', '>', or '>='.  For string values, only '=' is supported.

>'value': \<string or int\>, # The value that will be compared to the control's current state in the cockpit.  The cockpit state value will be cast to this value's type (int or str) before comparing.

>'duration': \<int\>, # Optional, defaults to 0.  Number of seconds the condition and value must be met before continuing.

**scriptTimerStart and scriptTimerEnd**

These are used to time long-duration events, where you want to execute commands in the meantime.  For instance, with an INS alignment that takes a fixed amount of time, you start the alignment, then start a timer with scriptTimerStart for the required alignment time.  The script then continues executing commands until it gets to the scriptTimerEnd.  If enough time has elapsed already since the timer was started, it'll continue to the next command immediately.  Otherwise the script will wait until the timer duration has passed, and then continue.

>'name': \<string\>, # A unique name for the timer.

>'duration': \<int\>, # Only used with scriptTimerStart.  The number of seconds the timer should last.

DCSAutoMate executes the script by running a loop.  Every 0.01 seconds, if the time since the last command was executed is greater than the current command's 'time' value, it runs the current command, and then queues up the next command in the list.  This is intentionally very similar to how DCS's built-in startup scripts work, but is based on relative times between commands instead of absolute times for each command.

Open C:\Users\\<username\>\Saved Games\DCS\Scripts\DCS-BIOS\doc\control-reference.html in your browser for a full list of everything that DCS BIOS can control.

Because the script files are in Python, you can use the full power of Python to build the script sequence.  I've made my scripts very similar to the built-in startup scripts in DCS, but in principle the scripts can do almost anything, including startup, shutdown, entering waypoints, setting up the cockpit after a hotstart or air start, or setting countermeasures programs.



# Known limitations:
* If DCS is running As Administrator, DCSAutoMate must also be running As Administrator in order to be able to send keyboard commands.  If DCSAutoMate detects that it is not running As Administrator but DCS itself is (or it can't tell), it will show a warning in the script output.
* In order for the keyboard commands to work, you must be sitting in the cockpit when they execute.  Do not go to any other view, or open any menus, maps, rearming screen, notepads, etc. (anything that could take the keyboard focus).  However, all the regular DCS BIOS commands will work correctly regardless of what view you are in.  DCSAutoMate outputs (and speaks via TTS) a warning when it detects keyboard commands in the script, telling you to stay in the cockpit.  When the last keyboard command in the script is executed, you are free to go to other views, and the program will notifiy you of that as well.
* Because the script is being run by an external program on its own clock, it will not work correctly if you do time accel in the game (unlike the built-in startup scripts, which work fine with time accel).  Likewise, if you pause in the game, the program has no way to tell, and will continue sending commands.
* DCSAutoMate will continue to send commands even if the script has failed somehow in the game (e.g. if you clicked something in the cockpit and changed the state, etc.).  The included scripts do not check for incorrect conditions like the built-in startup scripts do, although DCSAutoMate now has the ability to do so with the scriptCockpitState command.  It's up to you to monitor the script as it runs.
* If commands are sent too fast, sometimes they may not be caught by the game.  So far, even in busy MP servers, 0.3 seconds between commands has been enough for me, but if you have a slower computer or more network lag or something, you may have to increase that time.  Simply change the "dt = " value near the top of each script function.
* In some cases, DCSAutoMate may not be able to find the DCS window.  This may happen when running DCS through third-party launchers, or for other reasons.  If you have this problem, you should be able to get around it by entering the title of the DCS window as it appears on your computer in DCSAutoMate's config window and checking the "Find DCS window by window title" box.

# TODO, in no particular priority:
* General code cleanup and refactoring.  Add more error catching and validation.
* Improve the output format.  Could use a grid control to line up the columns better, or add color for different command types.  Figure out some way to predict the time, maybe by storing the time it took to run the script last time.  Add the time until the next command, so you can tell when it has a long delay in the script.
* Store more items in the config, such as: text-to-speech reading speed, voice, and volume; ports for the DCS BIOS communication; anything else I can think of.
* Pre-select module, script, and options based on data received from DCS BIOS and/or the DCSAutoMateExport.lua.  Could also pass in game state to a function in the script file that could map game state flags to scripts.  This should always be overridable by the user though.
* Investigate possibility of detecting a hotkey or joystick button so a script can be triggered that way.  I believe this is possible using some Python libraries.
* For scriptCockpitState commands where the value is a string, support 'startsWith', 'endsWith', and 'contains', as well as '='.
* Investigate whether it's possible to extract the map name and especially the mission name or title.  It would already be possible to build scripts specialized for certain MP servers, where it would automatically input some known waypoints, set radios to particular channels, etc.
* The DCSAutoMateExport.lua data includes the current loadout.  See if it's possible to map those to more readable weapon names (see Quaggle's datamine for extensive data and docs about this, plus some code).  Not sure how useful that would be, but could then allow scripts to be made that detect a particular loadout.  I've already got the Apache detecting whether it has the Longbow radar equipped.
* See if there's any benefit to using PySide6 instead of tkinter for the GUI library.
* For scriptCockpitState, show the monitored control's real-time value in the script output while it's waiting for it to get to the correct state.
* Add the ability to have some kind of branching logic or conditions in the script, to do different things depending on cockpit state.  This might have to be a fundamental change from a pre-determined sequence of commands to more like running an actual program.
* Put the DCS BIOS command 'description' text into the output for each command, to make the output easier to read.
* Add a command to pause a script until the user clicks a Resume button, to allow scripts to wait while the user enters information or does other stuff in the game, before continuing.

# Author's note:
My main goal here was functionality, not neatness or elegance.  This is my first serious use of Python GUI libraries, and there may be unknown bugs.  **Use at your own risk.**

Special thanks to:
* The makers of DCS BIOS.
* The makers of pywinauto, pyautogui, and pydirectinput.
* All of the staff at Eagle Dynamics.
* ChatGPT, GitHub Copilot, and VS Code, without which this version would have taken a lot longer, or might never have been made.

# Release notes:
* 2025/02/19 - Changes:
* Version 1.0 - I believe the program is now developed enough to deserve a 1.0 version.  It's pretty close to the vision I had for it back when I started it.
* Converted from console-based to GUI app.  This is my first Python tkinter app, and may still be rough around the edges, but I think it's a lot better interface than the console version and doesn't look like an ancient DOS program.
* Now has ability to monitor DCS BIOS output from the game so the scripts can react dynamically to the cockpit state (e.g. gauge readings, switch positions, lights on/off, etc.).
* Fixed inability to send RCtrl and RAlt by switching to a different keyboard library and solving several bugs.  Now all keys are supported, and no remapping is needed from the defaults in the game.  (Except the OH-58, which doesn't have a default mapping for throttle to idle.)
* Removed need to have special option for Dvorak keyboard.  Very few people would have had a problem with this, but it was fixed by the new keyboard library as well.
* Added ability to monitor additional data sent from the game with a custom export script, DCSAutoMateExport.lua.  This should make it possible to pre-select options for the scripts based on your position, time, altitude, etc., but that isn't implemented yet.
* Changed script command timing to be relative to the previous command rather than absolute.  This is needed to allow the dynamic responses to DCS BIOS export data.  The way the scripts are constructed is almost identical though.
* Changed to a different timing system for long-term timers, like alignment timers.  This does require minor changes to the scripts, but is less fiddly and easier to read in the scripts.
* Selected module, script, and options are saved, so you can re-run the last script easily, and it will have the same selections when you open the program again after closing it.
* More error handling and better error messages.  There may still be uncaught exceptions and other errors, but I've tried to get most of them.
* Improved the way it searches for the DCS window.  By default it now searches all running processes for "*\\bin\\DCS.exe" or "*\\bin-mt\\DCS.exe".  If that fails for some reason, you can tell it to search by window title instead.
* Included a utility program called DCSMonitor, which is an easy way to see the raw data coming from DCS BIOS and the DCSAutoMateExport script.  This one is still pretty rough, but it works.  I may improve it in future releases.
