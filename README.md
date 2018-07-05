# Use
1) Run `AutoHotkey.exe C:\git_repos\portals\namedpipe_mwe.ahk`.
2) Run `python namedpipelistener.py`.
3) Press Ctrl+Alt+u and Ctrl+Alt+i to move active window.

# Known issues
Switching focus is currently slow because it uses pywinauto's set_focus. We
know that it *can* be fast since Autohotkey's Winactivate is fast. Apart from
the fact that set_focus is slow it also moves the mouse off-screen. I've tested
that this is necessary for focus switching to work (!)
Source for Autohotkey's Winactivate and related functions:
https://github.com/Lexikos/AutoHotkey_L/blob/15ac5cf2d26e73a98897d99fab56ec8af96c03ad/source/window.cpp#L24
https://github.com/Lexikos/AutoHotkey_L/blob/15ac5cf2d26e73a98897d99fab56ec8af96c03ad/source/window.cpp#L147
Another implementation:
https://stackoverflow.com/questions/916259/win32-bring-a-window-to-top
Options:
- Find a better Python solution.
- Figure out what exactly the Autohotkey script is doing and redo it in Python.
- Use the Autohotkey C++ code or the other C++ implementatin.
