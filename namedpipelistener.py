import json
import logging
import sys
import traceback

import pywintypes
import win32con
import win32file
import win32gui

import utils


class NamedPipeListener:
    def __init__(self, pipename, n_bytes_to_read=4096):
        self.pipename = pipename
        self.n_bytes_to_read = n_bytes_to_read
        self.set_handle()

    def listen(self):
        while True:
            status, msg = win32file.ReadFile(self.handle, self.n_bytes_to_read)
            logging.debug('Message received: %s', msg)
            if status != 0:
                logging.warning('ReadFile error with status %s. '
                                'Message was %s', status, msg)
            self.process_msg(msg)
            continue

    def set_handle(self):
        self.handle = win32file.CreateFile(
            self.pipename,
            win32file.GENERIC_READ,
            0, None,
            win32file.OPEN_EXISTING,
            0, None
        )

    def process_msg(self, msg):
        raise NotImplementedError


class TestListener(NamedPipeListener):
    def process_msg(self, msg):
        print(msg)


class PCListener(NamedPipeListener):
    """
    Listens for messages from Autohotkey and causes a PortalController to do
    things.
    """
    def __init__(self, pc, *args, ahk_process=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pc = pc
        self.ahk_process = ahk_process

    def process_msg(self, msg_raw):
        # Autohotkey sends strings encoded as utf-16 little endian.
        msg = msg_raw.decode('utf-16le')
        try:
            msg_dict = json.loads(msg)
        except json.decoder.JSONDecodeError:
            print(traceback.format_exc())
            print(msg)
            return
        try:
            method, args = utils.parse_method_and_args(self, msg_dict)
        except AttributeError:
            logging.warning(f'Requested method in dictionary {msg_dict} not found.')
            return
        try:
            method(*args)
        except TypeError:
            print(traceback.format_exc())
            return

    def exit(self):
        if self.ahk_process:
            self.ahk_process.kill()
        sys.exit()

    def show(self, msg):
        print(msg)

    def snap_created_window(self, hwnd_hex):
        """ hwnd_hex is a hexadecimal string """
        hwnd = int(hwnd_hex, 16)
        class_name = win32gui.GetClassName(hwnd)
        win_text = win32gui.GetWindowText(hwnd)
        logging.debug('class_name %s', class_name)
        logging.debug('win_text %s', win_text)
        win_texts = ('Chrome', 'Command Prompt', 'CPUID HWMonitor', 'KeePassX')
        class_names = ('SUMATRA_PDF_FRAME', 'ConsoleWindowClass')
        mon_idx = self.pc.mon_idx_def
        portal_idx = None
        if any(x in win_text for x in win_texts) or any(x in class_name for x in class_names):
            portal_idx = 0
        win_texts = ('Firefox', 'notepad', 'Double Commander')
        class_names = ('CabinetWClass', 'FM', 'NotebookFrame')
        if any(x in win_text for x in win_texts) or any(x in class_name for x in class_names):
            portal_idx = 1
        if ('MozillaWindowClass' in class_name) and ('Write' in win_text):
            portal_idx = 1
        if portal_idx is not None:
            try:
                # It feels more right to snap the `hwnd` window, but when we
                # open, e.g., a new Firefox window from Firefox itself, using
                # `hwnd` snaps the ORIGINAL firefox window, not the new one!
                self.pc.snap_hwnd_to_portal_at_idx('active', mon_idx, portal_idx)
            except pywintypes.error:
                print(traceback.format_exc())
            logging.debug(f'Snapping window {class_name}, {win_text} '
                        f'to monitor {mon_idx}, idx {portal_idx}')
        if 'SpotifyMainWindow' in class_name:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
