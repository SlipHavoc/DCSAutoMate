# DCSAutoMate
Python scripting engine for DCS World using DCS BIOS.

This script uses DCS BIOS (specifically, [the DCS BIOS fork for DCS Flightpanels](https://github.com/DCSFlightpanels/dcs-bios)) to send commands to DCS.  It also uses [pyWinAuto](https://github.com/pywinauto/pywinauto) to send keyboard commands.

This is intended to replace the existing built-in autostart scripts in DCS, which after v.2.8 became subject to the "Pure Scipts" flag on multiplayer servers.  In order to modify the built-in startup scripts, you have to change the actual game files, which makes them fail the IC check if Pure Scripts is enabled.  DCSAutoMate is not affected by this check because it sends the commands to DCS via DCS BIOS, which is in the user-editable files in Saved Games.

DCS AutoMate can also be used to script any other cockpit commands, such as adding waypoints or setting countermeasures programs.

# How to use this program:
**Basic use (unless you're into programming, this is probably all you need):**

1. Download the DCSAutoMate.7z file and extract to a folder of your choice.
2. Double-click **DCSAutoMate.exe** to run the program, which will open a command prompt window.
3. Start DCS.
4. When you're in cockpit and ready to run a script, alt-tab out to the DCSAutoMate window and select the module (the plane you're in) by entering a number, then the function (script) you want to run.
5. The script will start running, and sending commands to the DCS window.  You can alt-tab back into DCS at that point.  (If the script has keyboard commands, the DCS window will automatically get focus when those commands are sent.)
6. After the script is done, it will show the module menu again.

You can run any script at any time; it's up to you to run the right scripts at the right time.  To stop a script, alt-tab to the DCSAutoMate window and press Ctrl-C a few times, or just close the window.

(Optionally, you can set a few configuration options configure the program by editing DCSAutoMateConfig.ini, see below for explanation of settings.

**Advanced use:**

DCS AutoMate can be run in **standalone mode** (above), which has a menu to select from available modules and functions, or in **command line mode**, where you specify which module and function to run:

$> DCSAutoMate --file \<scriptFile\> --function \<functionName\> [--debug] [--nospeech] [--dvorak]

\<scriptFile\> should be the name of the .py file in the DCSAutoMateScripts subfolder.  Do not include the .py extension.

\<functionName\> should be the name of a function in that file.

Optional parameters (if passed, these override the settings in the .ini file):

--debug If passed, disables actually sending the commands to DCS (DCS doesn't have to be running either).  Everything else in the script works as normal.

--nospeech If passed, disables the text-to-speech commands for silent running.

--dvorak If passed, sets a flag for the script functions to read so that certain keyboard commands can be changed depending on whether you have a Dvorak keyboard layout or not.  (If you don't know whether you do or not, you don't, and shouldn't pass this parameter.)

All of the parameters are case-sensitive.  If the filename has a space, enclose it in "double quotes".
	
Example: $> DCSAutoMate FA-18C ColdStartGroundDay

# How to make your own scripts or modify existing scripts:
Use the scripts that come with DCSAutoMate as examples.  The script functions in the .py files in the DCSAutoMateScripts subfolder return a Python List.  Each element in the list must be a Dictionary with the following keys:

{  
	'time': \<float\>, # The number of seconds after the script starts that the command will be executed.  
	'cmd': \<string\>, # The command to be executed.  This must be an exact (and case-sensitive) DCS BIOS command string, or 'scriptKeyboard', or 'scriptSpeech'.  
	'arg': \<mixed\>, # The value that will be sent.  For DCS BIOS commands, this is the numeric or string parameter value for the command.  For scriptKeyboard, this is the pyWinAuto key string.  For scriptSpeech, the string will be spoken out loud by Microsoft Text-To-Speech.  
	'msg': \<string\>, # A message to be displayed when the command executes.  
}

DCSAutoMate executes the script by running a timing loop.  Every 0.01 seconds, it runs the next command in the List if the current time is after that command's time parameter.  This is intentionally almost identical to how DCS's built-in startup scripts work, but should be adaptable to other scripting needs.

Open C:\Users\\<username\>\Saved Games\DCS.openbeta\Scripts\DCS-BIOS\doc\control-reference.html in your browser for a full list of everything that DCS BIOS can control.

Because the script files are in Python, you can use the full power of Python to build the script sequence.  I've made my scripts very similar to the built-in startup scripts in DCS, but in principle the scripts can do almost anything, including startup, shutdown, entering waypoints, setting up the cockpit after a hotstart or air start, or setting countermeasures programs.

# Requirements:
You will need to install the [DCS Flightpanels fork of DCS BIOS](https://github.com/DCSFlightpanels/dcs-bios).  To install, copy the DCS-BIOS folder into C:\Users\\<username\>\Saved Games\DCS.openbeta\Scripts, and add the line in Export.lua to your Export.lua (see instructions on DCS BIOS page for details).

Download DCSAutoMate.7z and extract to a folder of your choice.

If using DCSAutoMate.exe, no installation or other programs should be needed.  The exe is made using [auto-py-to-exe](https://github.com/brentvollebregt/auto-py-to-exe) and should be completely standalone.

If using DCSAutoMate.py, you will need to have [Python 3.7](https://www.python.org/downloads/windows/) installed, as well as [pyWinAuto](https://github.com/pywinauto/pywinauto) (```pip install pywinauto```, or see instructions in pyWinAuto documentation).

# Known limitations:
* **Important!**  I cannot get pyWinAuto to send RCtrl or RAlt to DCS, so any scripts that rely on those (often used for things like advancing throttles to idle during startup) will need to have their keys remapped.  I have just been adding a mapping, usually with the left-key equivalent (e.g. a command using RAlt-Home gets a mapping for LAlt-Home as well).  So far I haven't encountered any key conflicts that way.  If anyone can find a way to fix this problem, please let me know.
* In order for the keyboard commands to work, you must be sitting in the cockpit when they execute.  Do not go to any other view, or open any menus, maps, rearming screen, etc.  However, all the regular DCS BIOS commands will work correctly regardless of what view you are in.  DCSAutoMate outputs (and speaks via TTS) a warning when it detects keyboard commands in the script, telling you to stay in the cockpit.  When the last keyboard command in the script is executed, you are free to go to other views, and the program will notifiy you of that as well.
* I've only tested this progarm with the openbeta version of DCS.  The program looks for a window with "DCS.openbeta" in the title.  If it doesn't find one, it looks for one with just "DCS" in the title (I've never tested that).  If it doesn't find either one (and --debug is not passed), it will error out.  I don't know what happens if it should find more than one window with that title.
* Because the script is being run by an external program on its own clock, it will not work correctly if you do time accel in the game (unlike the built-in startup scripts, which work fine with time accel).  Likewise, if you pause in the game, the program has no way to tell, and will continue sending commands.
* DCSAutoMate will continue to send commands even if the script has failed somehow in the game (e.g. if you clicked something in the cockpit and changed the state, etc.).  There is no condition-checking like the built-in startup scripts have.  It's up to you to monitor the script as it runs.
* If commands are sent too fast, sometimes they may not be caught by the game.  So far, even in busy MP servers, 0.3 seconds between commands has been enough for me, but if you have a slower computer or more network lag or something, you may have to increase that time.  Simply change the "dt = " value near the top of each script function.

# TODO, in no particular priority:
* General code cleanup and refactoring.  In particular, wrap the whole thing up in at least one class for neatness.
* Make a GUI with tkInter.  Should have a list of all script files, and when clicking on a script file, a list of all functions in the file.  Then when executing, show countdown timer as it executes, and have a neater layout for the various output messages, maybe filterable.
* ~~Make config file system.  Config file should be stored in same folder as main program.  If no config file found, should be created with default values.~~  Possible things to store: text-to-speech speaking speed, voiceId, volume.
* Allow user to pass params to the function the script is executing; currently if you want to pass params into a script function, you need to make another function with a different name that calls the function you want and passes hard-coded params.
* Figure out some fix for the pyWinAuto RCtrl and RAlt problem.
* Receive data from DCS BIOS to determine what type of plane you're in, and present scripts or functions for that plane automatically.  Especially useful for C-101.  Could also get time of day and run automatic day vs night scripts.  Maybe could also detect carrier start or air start and run scripts accordingly?
* Investigate possibility of detecting a hotkey or joystick button so a script can be triggered that way.

# Author's note:
My goal here was not neatness or elegance but raw functionality.  Error checking is minimal, **use at your own risk.**
