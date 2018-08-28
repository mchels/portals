import argparse
import logging
from pathlib import Path
import subprocess
import time

from namedpipelistener import PCListener
from portal import PortalController
import utils


parser = argparse.ArgumentParser()
parser.add_argument('--ahk_exe_path', dest='ahk_exe_path', required=True,
                    help='Full path to Autohotkey executable.',
                    type=lambda path: utils.get_proper_path(parser, path))
parser.add_argument('--debug', action='store_true', default=False)
parser.add_argument('--debug_to_file', action='store_true', default=False)
args = parser.parse_args()

if args.debug:
    logging.getLogger().setLevel(logging.DEBUG)

if args.debug_to_file:
    logger = logging.getLogger()
    log_file_path = Path('~').expanduser() / 'portals.log'
    handler = logging.FileHandler(log_file_path)
    logger.addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

# Make sure that WSL is instantiated.
subprocess.call(['bash', '-c', ':'])

pipename = r'\\.\pipe\ahk_py_pipe'
dir_this_file = Path(__file__).resolve().parent
ahk_script_path = dir_this_file / 'namedpipewriter.ahk'
cmd = [str(args.ahk_exe_path), '/restart', str(ahk_script_path)]
process = subprocess.Popen(cmd)
time.sleep(0.5) # To allow Autohotkey to open before we query the pipe.
PC = PortalController(n_splits=2)
pc_listener = PCListener(PC, pipename, ahk_process=process)
pc_listener.listen()
