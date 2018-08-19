from collections import namedtuple
import json
import logging
from pathlib import Path
import subprocess
import sys
import time
import traceback

import pywintypes
import pyperclip
import win32con
import win32file
import win32gui

import utils


TMAX = 0.3
TDELTA = 0.05


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

    def snap_created_window(self, hwnd):
        if isinstance(hwnd, str):
            try:
                hwnd = int(hwnd, 16)
            except ValueError:
                return
        win_text = win32gui.GetWindowText(hwnd)
        class_name = win32gui.GetClassName(hwnd)
        logging.debug('win_text %s', win_text)
        logging.debug('class_name %s', class_name)
        # Special cases.
        if 'Firefox' in win_text:
            time.sleep(0.15)
            self.pc.snap_hwnd_to_portal_at_idx('active', self.pc.mon_idx_def, 1)
            return
        if 'SpotifyMainWindow' in class_name:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return
        # General cases.
        attributes = ('win_text', 'class_name', 'mon_idx', 'portal_idx')
        Hwndmatcher = namedtuple('Hwndmatcher', attributes)
        hwndmatchers = [
            Hwndmatcher('Chrome', '', self.pc.mon_idx_def, 0),
            Hwndmatcher('Command Prompt', '', self.pc.mon_idx_def, 0),
            Hwndmatcher('CPUID HWMonitor', '', self.pc.mon_idx_def, 0),
            Hwndmatcher('KeePassX', '', self.pc.mon_idx_def, 0),
            Hwndmatcher('', 'SUMATRA_PDF_FRAME', self.pc.mon_idx_def, 0),
            Hwndmatcher('', 'ConsoleWindowClass', self.pc.mon_idx_def, 0),
            Hwndmatcher('notepad', '', self.pc.mon_idx_def, 1),
            Hwndmatcher('Double Commander', '', self.pc.mon_idx_def, 1),
            # Visual Studio Code only works for the first window.
            Hwndmatcher('Visual Studio Code', '', self.pc.mon_idx_def, 1),
            Hwndmatcher('Write', 'MozillaWindowClass', self.pc.mon_idx_def, 1),
        ]
        for matcher in hwndmatchers:
            if (matcher.win_text in win_text) and (matcher.class_name in class_name):
                break
        else:
            logging.debug('No match found. No snapping will be executed.')
            return
        logging.debug(f'Snapping window {win_text}, {class_name} '
                      f'to monitor {matcher.mon_idx}, idx {matcher.portal_idx}')
        t = 0
        while t < TMAX:
            hwnd_foreground = win32gui.GetForegroundWindow()
            logging.debug(hwnd_foreground)
            if hwnd == hwnd_foreground:
                try:
                    self.pc.snap_hwnd_to_portal_at_idx(hwnd, matcher.mon_idx,
                                                       matcher.portal_idx)
                except pywintypes.error:
                    print(traceback.format_exc())
            time.sleep(TDELTA)
            t += TDELTA
        return

    @staticmethod
    def convert_clipboard_path():
        """
        Manual tests:
        - Try to convert a valid Windows path. You should get the corresponding wslpath.
        - Try to convert an invalid Windows path. You should get an error.
        - Try to convert a binary file (exe, png, etc.). You should get an error.
        - Try to convert a wslpath. You should get an error.
        """
        clip_content = pyperclip.paste()
        clip_content_len = len(clip_content)
        clip_content_len_limit = 1e3
        if clip_content_len > clip_content_len_limit:
            logging.debug(f'Got clip_content with len {clip_content_len} which '
                          f'is above the limit of {clip_content_len_limit}. '
                          'Aborting.')
            return
        if not clip_content:
            logging.debug('Got clip_content with zero length. Aborting.')
            return
        clip_content_stripped = clip_content.strip('"')
        try:
            path_exists = Path(clip_content_stripped).exists()
        except OSError:
            path_exists = False
        if not path_exists:
            logging.debug(f'Clipboard content with lenth {clip_content_len} '
                          'is not a valid path. Aborting.')
            return
        new_clip_content = get_wslpath(clip_content_stripped)
        logging.debug(f'Converted clipboard content {clip_content} into '
                      f'{new_clip_content}.')
        pyperclip.copy(new_clip_content)


def get_wslpath(win_path):
    bash_cmd = f"wslpath '{win_path}'"
    cmd = ["bash", "-c", bash_cmd]
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    return result.stdout.decode('unicode_escape').strip()
