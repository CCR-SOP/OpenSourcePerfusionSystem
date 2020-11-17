# -*- coding: utf-8 -*-
"""Basic configuration constants for the LiverPerfusion app

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import os
from pathlib import Path

LP_PATH_BASE = Path(os.path.expanduser('~')) / 'Documents/LiverPerfusion'
LP_PATH_CONFIG = LP_PATH_BASE / 'config'
LP_PATH_DATA = LP_PATH_BASE / 'data'
LP_PATH_TMP = LP_PATH_BASE / 'tmp'


def set_base(basepath='~/Documents'):
    global LP_PATH_BASE, LP_PATH_CONFIG, LP_PATH_DATA, LP_PATH_TMP
    base = Path(os.path.expanduser(basepath))
    LP_PATH_BASE = base / 'LiverPerfusion'
    LP_PATH_CONFIG = LP_PATH_BASE / 'config'
    LP_PATH_DATA = LP_PATH_BASE / 'data'
    LP_PATH_TMP = LP_PATH_BASE / 'tmp'
    LP_PATH_BASE.mkdir(parents=True, exist_ok=True)
    LP_PATH_CONFIG.mkdir(parents=True, exist_ok=True)
    LP_PATH_DATA.mkdir(parents=True, exist_ok=True)
    LP_PATH_TMP.mkdir(parents=True, exist_ok=True)