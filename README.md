# Functionality
An Autohotkey script listens for keystrokes and forwards them to Python via a NamedPipe which takes a window management action. Currently, actions include snapping windows and moving focus.


# Known issues
- When moving focus between two cmd.exe windows the `move_focus` command must be run twice to take effect.


# Background
Autohotkey is excellent at capturing keystrokes without interfering with built-in functionality. Python is an excellent scripting language. The combination is even excellenter.


# Related projects
- `petronia` is similar, but does too many things for my taste. I *think* it also doesn't capture keystrokes as well as Autohotkey. The "portals" name is taken from this project as well.
https://github.com/groboclown/petronia
- The `keyboard` package comes really close to being a replacement for Autohotkey, but doesn't quite perform as well for, e.g., windows keys: https://github.com/boppreh/keyboard
