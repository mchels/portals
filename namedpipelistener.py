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
            try:
                status, msg = win32file.ReadFile(self.handle, self.n_bytes_to_read)
                logging.debug('Message received: %s', msg)
                if status != 0:
                    logging.warning('ReadFile error with status %s. Message was %s', status, msg)
                self.process_msg(msg)
                continue
            except KeyboardInterrupt:
                sys.exit()

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

    def process_msg(self, msg):
        # Autohotkey sends strings encoded as utf-16 little endian.
        drc = int(msg.decode('utf-16le'))
        # self.pc.snap_active_in_drc(drc)
        self.pc.move_focus_in_drc(drc)


if __name__ == '__main__':
    from portal import PortalController

    PIPENAME = r'\\.\pipe\testpipe'
    # test_listener = TestListener(PIPENAME)
    # test_listener.listen()
    PC = PortalController(n_splits=2)
    PC_LISTENER = PCListener(PC, PIPENAME)
    PC_LISTENER.listen()
