In previous versions, I considered adding joystick input so the program could be controlled by mapping joystick buttons.  (There may still be some standalone test scripts, but all the joystick code should have been removed from the main program by now.)  This was a neat idea that turned out to be pretty awkward in practice:

* DCS demands many joystick buttons and users probably don't have many free to operate DCSAutoMate, so the controls had to be minimal.
* Joystick inputs can be watched, but not intercepted; that is, they always go through to DCS as well.  I partly got around that by having one button "activate" DCSAutoMate, which would then enable listening for the rest of the buttons, so you could map the controls in DCS to something that wouldn't matter if it was pressed at the beginning of the flight when DCSAutoMate was being used, but it wasn't a very good solution.
* Before DCSAutoMate had an in-game interface using the built-in DCS GUI system (DXGUI), it only had a Windows GUI.  If the user was in VR, or full-screen 2D, the only way to give feedback to the user for what script or settings they had selected was audio, which is not well suited to that.

The whole idea was rendered unnecessary when we went to the DXGUI in-game interface.  However it is worth keeping in mind the possibility that we can read joystick inputs, and probably output them also.  I believe this includes both buttons and axes.  Potentially that means we could move the throttle or stick directly with a script, or do other things.

---

Regarding keyboard input, we cannot intercept keystrokes when the DCS window has focus.  This is a Windows limitation, and when you think about it, it's obvious: that would allow other programs to read passwords and other sensitive information.  So keyboard shortcuts that control the program directly are not possible.  However, with the DXGUI interface, we can register keyboard shortcuts (that's how we open/close the in-game GUI), and we could potentially send commands to DCSAutoMate through the network connection and control it that way.  Another thing that I can't think of a use for right now, but worth keeping in mind.
