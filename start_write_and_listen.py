import argparse
import logging
from pathlib import Path
import subprocess
import time

from namedpipelistener import PCListener
from portal import PortalController
import utils


logging.basicConfig(level=logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument('--ahk_exe_path', dest='ahk_exe_path', required=True,
                    help='Full path to Autohotkey executable.',
                    type=lambda path: utils.get_proper_path(parser, path))
args = parser.parse_args()
pipename = r'\\.\pipe\ahk_py_pipe'
dir_this_file = Path(__file__).resolve().parent
ahk_script_path = dir_this_file / 'namedpipewriter.ahk'
cmd = [str(args.ahk_exe_path), '/restart', str(ahk_script_path)]
process = subprocess.Popen(cmd)
time.sleep(0.5) # To allow Autohotkey to open before we query the pipe.
PC = PortalController(n_splits=2)
pc_listener = PCListener(PC, pipename, ahk_process=process)
pc_listener.listen()
