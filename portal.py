"""
TODO:
- Focus switching is slow. Make it faster.
- If portal com is desktop, try focusing next portal.
"""
import pywinauto
from pywinauto.controls.hwndwrapper import HwndWrapper
import win32api
import win32gui


class Portal:
    def __init__(self, left, top, width, height, mon_idx, idx=None):
        self.left = left
        self.top = top
        self.width = width
        self.height = height
        self.mon_idx = mon_idx
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

    def get_active_portal(self):
        p_com = get_hwnd_com()
        for portal in self.portals:
            if point_in_portal(p_com, portal):
                return portal
        raise RuntimeError('No active portal found. This should never happen.')

    def get_adjacent_portal(self, drc, portal=None):
        active_portal = self.get_active_portal() if portal is None else portal
        new_idx = (active_portal.idx+drc) % len(self.portals)
        return self.portals[new_idx]

    def snap_hwnd_to_portal(self, hwnd=None, portal=None):
        portal = self.get_active_portal() if portal is None else portal
        hwnd = win32gui.GetForegroundWindow() if hwnd is None else hwnd
        # Consider changing to SetWindowPos which has more features and is "better"
        # http://timgolden.me.uk/pywin32-docs/win32gui__SetWindowPos_meth.html
        win32gui.MoveWindow(hwnd, portal.left, portal.top, portal.width, portal.height, True)

    def snap_active_in_drc(self, drc):
        """
        drc: +1 (right) or -1 (left)
        """
        new_portal = self.get_adjacent_portal(drc)
        self.snap_hwnd_to_portal(portal=new_portal)

    def move_focus_in_drc(self, drc):
        next_portal = self.get_adjacent_portal(drc)
        new_hwnd = next_portal.get_hwnd_at_com()
        elem = pywinauto.findwindows.find_elements(handle=new_hwnd)[0]
        HwndWrapper(elem).set_focus()


def hwnd_is_desktop(hwnd):
    # This is probably not robust.
    # Consider using win32gui.GetWindowText(desk_num).
    return hwnd == 65552

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
    for j in range(n_split):
        left = int(mon_left + j*portal_width)
        portal = Portal(left, mon_top, portal_width, portal_height, mon_idx)
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


if __name__ == '__main__':
    pc = PortalController(2)
    import IPython; IPython.embed()
