from ctypes import windll
from ctypes import GetLastError
import time

import win32api
import win32gui


SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
# https://msdn.microsoft.com/en-us/library/windows/desktop/ms681382(v=vs.85).aspx
ERROR_INVALID_PARAMETER = 87
SW_MAXIMIZE = 3
SW_RESTORE = 9


class Portal:
    def __init__(self, left, top, width, height, mon_idx, local_idx, idx):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.mon_idx = mon_idx
        self.local_idx = local_idx
        self.idx = idx
        self.right = left + width
        self.bottom = top + height

    def get_com(self):
        return get_com(self.left, self.right, self.top, self.bottom)

    def get_hwnd_at_com(self):
        com = self.get_com()
        return win32gui.WindowFromPoint(com)

    def __str__(self):
        return str(vars(self))


class PortalController:
    def __init__(self, n_splits):
        self.portals = make_portals(n_splits)
        self.set_main_mon_idx()

    def get_closest_portal(self):
        """
        Only take horizontal direction into account since we don't support managing windows in the y direction yet.
        """
        hwnd_x_com, _ = get_hwnd_com()
        dists = [abs(hwnd_x_com-(p.left+p.width/2)) for p in self.portals]
        idx_min = dists.index(min(dists))
        return self.portals[idx_min]

    def get_adjacent_portal(self, drc, portal):
        new_idx = (portal.idx+drc) % len(self.portals)
        return self.portals[new_idx]

    def snap_active_in_drc(self, drc):
        """ drc: +1 (right) or -1 (left) """
        hwnd = win32gui.GetForegroundWindow()
        cur_portal = self.get_closest_portal()
        if not hwnd_is_snapped_to_portal(hwnd, cur_portal):
            if is_maximized(hwnd):
                win32gui.ShowWindow(hwnd, SW_RESTORE)
            new_portal = self.get_next_portal_on_monitor(cur_portal, drc)
        else:
            new_portal = self.get_adjacent_portal(drc, cur_portal)
        snap_hwnd_to_portal(hwnd, new_portal)

    def get_next_portal_on_monitor(self, portal, drc):
        """
        Gets the portal adjacent to `portal` in direction `drc` but only if
        they are on the same monitor. Otherwise `portal` is returned.
        """
        next_idx = (portal.idx+drc) % len(self.portals)
        candidate_portal = self.portals[next_idx]
        if candidate_portal.mon_idx == portal.mon_idx:
            return candidate_portal
        return portal

    def move_focus_in_drc(self, drc):
        active_portal = self.get_closest_portal()
        active_hwnd = active_portal.get_hwnd_at_com()
        candidate_portal = active_portal
        candidate_is_valid = False
        while not candidate_is_valid:
            candidate_portal = self.get_adjacent_portal(drc, candidate_portal)
            candidate_hwnd = candidate_portal.get_hwnd_at_com()
            candidate_is_valid = hwnd_is_valid(candidate_hwnd, active_hwnd)
            if candidate_portal == active_portal:
                # We tried all possibilities and we're back at the start so we
                # return without doing anything.
                return
        new_hwnd = candidate_hwnd
        window_activate(new_hwnd)

    def set_main_mon_idx(self):
        mons = win32api.EnumDisplayMonitors()
        mon_infos = [win32api.GetMonitorInfo(mon[0]) for mon in mons]
        def_mon_info = mon_infos[0]
        mon_infos.sort(key=lambda info: info['Work'][0])
        self.mon_idx_def = mon_infos.index(def_mon_info)

    def snap_hwnd_to_portal_at_idx(self, hwnd='active', mon_idx=0, portal_idx=0):
        if hwnd == 'active':
            hwnd = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(hwnd, SW_RESTORE)
        portal = self.get_portal_at_idx(mon_idx, portal_idx)
        snap_hwnd_to_portal(hwnd, portal)

    def get_portal_at_idx(self, mon_idx, portal_idx):
        for portal in self.portals:
            if (portal.local_idx == portal_idx) and (portal.mon_idx == mon_idx):
                return portal
        raise ValueError('Portal not found')

def snap_hwnd_to_portal(hwnd, portal):
    win32gui.SetWindowPos(hwnd, HWND_TOPMOST, portal.left, portal.top,
                          portal.width, portal.height, SWP_NOZORDER)

def hwnd_is_snapped_to_portal(hwnd, portal):
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    if ((portal.left == left) and (portal.top == top) and
        (portal.right == right) and (portal.bottom == bottom)):
        return True
    return False

def window_activate(hwnd):
    """
    Set focus to hwnd. This is the Microsoft Magic Focus Dance.

    Function adapted from the petronia project by groboclown on GitHub:
    https://github.com/groboclown/petronia/blob/master/src/petronia/arch/funcs_any_win.py#L529
    Credit for inventing the phrase "Microsoft Magic Focus dance" also goes to
    groboclown.

    Another implementation that may be superior:
    https://stackoverflow.com/questions/17879890/understanding-attachthreadinput-detaching-lose-focus
    """
    current_hwnd = windll.user32.GetForegroundWindow()
    current_thread_id = windll.kernel32.GetCurrentThreadId()
    thread_process_id = windll.user32.GetWindowThreadProcessId(current_hwnd, None)
    if thread_process_id != current_thread_id:
        res = windll.user32.AttachThreadInput(thread_process_id, current_thread_id, True)
        time.sleep(0.075)
        # ERROR_INVALID_PARAMETER means that the two threads are already
        # attached.
        err = GetLastError()
        if (res == 0) and (err != ERROR_INVALID_PARAMETER):
            # TODO better logging
            print('WARN: could not attach thread input to thread '
                  '{0} ({1})'.format(thread_process_id, err))
            return True
    flags = SWP_NOSIZE | SWP_NOMOVE
    res = windll.user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, flags)
    if res == 0:
        return False
    # At this point, the window hwnd is valid, so we don't need to fail out if
    # the results are non-zero.  Some of these will not succeed due to
    # attributes of the window, rather than the window not existing.
    windll.user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, flags)
    windll.user32.AttachThreadInput(thread_process_id, current_thread_id, False)
    windll.user32.SetForegroundWindow(hwnd)
    windll.user32.SetFocus(hwnd)
    windll.user32.SetActiveWindow(hwnd)
    return True

def hwnd_is_valid(candidate_hwnd, active_hwnd):
    return (not hwnd_is_desktop(candidate_hwnd)) and \
           (candidate_hwnd != active_hwnd)

def hwnd_is_desktop(hwnd):
    """
    Check whether hwnd is the desktop.
    This function is suspected to be unstable. Ideally we would want to do
    something like comparing class_name with #32769:
    https://docs.microsoft.com/en-us/windows/desktop/winmsg/about-window-classes
    We can get the element with class_name #32769 with pywinauto's
    pywinauto.win32functions.GetDesktopWindow.
    """
    class_name = win32gui.GetClassName(hwnd)
    name = win32gui.GetWindowText(hwnd)
    if (class_name == 'SysListView32') and (name == 'FolderView'):
        return True
    return False

def make_portals(n_splits):
    """
    n_splits: numbers of splits, iterable of positive ints.
    """
    mons = win32api.EnumDisplayMonitors()
    if isinstance(n_splits, int):
        n_splits = [n_splits] * len(mons)
    elif len(n_splits) != len(mons):
        raise ValueError('n_splits and mons must have same length.')
    mon_infos = [win32api.GetMonitorInfo(mon[0]) for mon in mons]
    mon_infos.sort(key=lambda info: info['Work'][0])
    portals = []
    for mon_idx, mon in enumerate(mon_infos):
        n_split = n_splits[mon_idx]
        portals_in_monitor = make_portals_in_monitor(n_split, mon, mon_idx)
        portals.extend(portals_in_monitor)
    # This is ugly.
    for i in range(len(portals)):
        portals[i].idx = i
    return portals

def make_portals_in_monitor(n_split, mon_info, mon_idx):
    mon_left, mon_top, mon_right, mon_bottom = mon_info['Work']
    mon_width = int(mon_right-mon_left)
    mon_height = int(mon_bottom-mon_top)
    portal_width = int(mon_width / n_split)
    portal_height = mon_height
    portals = []
    for local_idx in range(n_split):
        left = int(mon_left + local_idx*portal_width)
        portal = Portal(left, mon_top, portal_width, portal_height, mon_idx, local_idx, idx=None)
        portals.append(portal)
    return portals

def get_hwnd_com(hwnd=None):
    """ Get window center-of-mass """
    hwnd = win32gui.GetForegroundWindow() if hwnd is None else hwnd
    left, top, right, bottom = win32gui.GetWindowRect(hwnd)
    return get_com(left, right, top, bottom)

def get_com(left, right, top, bottom):
    x_com = int((left+right)/2)
    y_com = int((top+bottom)/2)
    return x_com, y_com

def point_in_portal(point, portal):
    x_com, y_com = point
    x_in_portal = (x_com >= portal.left) and (x_com <= portal.right)
    y_in_portal = (y_com >= portal.top) and (y_com <= portal.bottom)
    return x_in_portal and y_in_portal

def is_maximized(hwnd):
    temp = win32gui.GetWindowPlacement(hwnd)
    if temp[1] == SW_MAXIMIZE:
        return True
    return False


if __name__ == '__main__':
    pc = PortalController(2)
    import IPython; IPython.embed()
