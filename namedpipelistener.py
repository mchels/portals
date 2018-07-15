import json
import logging
import sys
import win32file


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
    def __init__(self, pc, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pc = pc

    def process_msg(self, msg_raw):
        # Autohotkey sends strings encoded as utf-16 little endian.
        msg = msg_raw.decode('utf-16le')
        msg_dict = json.loads(msg)
        try:
            requested_method = getattr(self, msg_dict['method'])
        except AttributeError:
            logging.warning(f'Requested method in dictionary {msg_dict} not found.')
            return
        args = msg_dict['args']
        try:
            requested_method(*args)
        except TypeError:
            logging.warning(f'Arguments {args} are inconsistent with the '
                            f'signature of method {requested_method}.')
            return

    @staticmethod
    def exit():
        sys.exit()

    # Ugly fixes for not bothering to recursively doing getattr for elements in
    # incoming json.
    def move_focus_in_drc(self, drc):
        return self.pc.move_focus_in_drc(drc)

    def snap_active_in_drc(self, drc):
        return self.pc.snap_active_in_drc(drc)
