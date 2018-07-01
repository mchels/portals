# Use
1) Run `AutoHotkey.exe C:\git_repos\portals\namedpipe_mwe.ahk`.
2) Run `python namedpipelistener.py`.
3) Press Ctrl+Alt+u and Ctrl+Alt+i to move active window.

# Known issues
- There are 0-bytes between all bytes in the transmitted message. Maybe a unicode error?
- namedpipe_mwe.ahk freezes upon starting. It starts responding again when running `python namedlistener.py` so it's probably the CreateNamedPipe or ConnectNamedPipe call that causes the freeze.
