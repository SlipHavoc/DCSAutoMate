The in-game GUI in DCS is called dxgui.  Code and many examples can be found in the DCS install folder in the /dxgui and the /Scripts/UI folders.  It is very powerful, but almost entirely undocumented.  I had AI generate the DXGUI_Developer_Guide.md file but that should **not** be treated as gospel.

It's worth exploring what else we could do with it, and not just for DCSAutoMate.

Some ideas:
* Use it to draw an graphical representation of the air refueling tanker lights, similar to how the carrier IFLOS is displayed.  Maybe see https://github.com/unicorndog1/DCS-AccMod as an example, extracting data from the game and displaying it in a DXGUI window.
* Some cheating may be possible, by extracting data from the various globals that are accessible to Lua scripts and then displaying them.
* It might be possible to make something like an autopilot for planes that don't have one, with an interface for the controls, and then a back-end that sends joystick commands to the game in a feedback loop.  I wonder if that's how https://dcs.silver.ru/ gets their data.