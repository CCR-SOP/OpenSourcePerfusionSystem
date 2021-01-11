# -*- coding: utf-8 -*-
"""Basic configuration constants for the LiverPerfusion app

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import os
from pathlib import Path
from configparser import ConfigParser
from datetime import datetime


LP_PATH = {}
LP_PATH['base'] = Path(os.path.expanduser('~')) / 'Documents/LiverPerfusion'
LP_PATH['config'] = LP_PATH['base'] / 'config'
LP_PATH['data'] = LP_PATH['base'] / 'data'
LP_PATH['tmp'] = LP_PATH['base'] / 'tmp'
LP_FILE = {}
LP_FILE['hwcfg'] = LP_PATH['config'] / 'hardware.ini'


def set_base(basepath='~/Documents'):
    global LP_PATH
    base = Path(os.path.expanduser(basepath))

    LP_PATH['base'] = base / 'LiverPerfusion'
    LP_PATH['config'] = LP_PATH['base'] / 'config'
    LP_PATH['data'] = LP_PATH['base'] / 'data'
    LP_PATH['tmp'] = LP_PATH['base'] / 'tmp'

    LP_FILE['hwcfg'] = LP_PATH['config'] / 'hardware.ini'

    for key in LP_PATH.keys():
        LP_PATH[key].mkdir(parents=True, exist_ok=True)

def update_hwcfg_section(name, updated_info):
    config = ConfigParser()
    config.read(LP_FILE['hwcfg'])
    if not config.has_section(name):
        config.add_section(name)
    config[name] = updated_info
    with open(LP_FILE['hwcfg'], 'w') as file:
        config.write(file)

def get_hwcfg_section(name):
    config = ConfigParser()
    config.read(LP_FILE['hwcfg'])
    if config.has_section(name):
        section = config[name]
    else:
        section = {}
    return section

def update_stream_folder(base=''):
    if not base:
        base = datetime.now().strftime('%Y-%m-%d')
    LP_PATH['stream'] = LP_PATH['data'] / base
    LP_PATH['stream'].mkdir(parents=True, exist_ok=True)
