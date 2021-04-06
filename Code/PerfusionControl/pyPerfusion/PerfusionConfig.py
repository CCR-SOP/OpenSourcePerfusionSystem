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
LP_FILE['syringe'] = LP_PATH['config'] / 'syringe.ini'


def set_base(basepath='~/Documents'):
    global LP_PATH
    base = Path(os.path.expanduser(basepath))

    LP_PATH['base'] = base / 'LiverPerfusion'
    LP_PATH['config'] = LP_PATH['base'] / 'config'
    LP_PATH['data'] = LP_PATH['base'] / 'data'
    LP_PATH['tmp'] = LP_PATH['base'] / 'tmp'

    LP_FILE['hwcfg'] = LP_PATH['config'] / 'hardware.ini'
    LP_FILE['syringe'] = LP_PATH['config'] / 'syringe.ini'

    for key in LP_PATH.keys():
        LP_PATH[key].mkdir(parents=True, exist_ok=True)

def update_hwcfg_section(name, updated_info):
    config = ConfigParser()
    config.optionxform = str
    config.read(LP_FILE['hwcfg'])
    if not config.has_section(name):
        config.add_section(name)
    config[name] = updated_info
    with open(LP_FILE['hwcfg'], 'w') as file:
        config.write(file)

def get_hwcfg_section(name):
    config = ConfigParser()
    config.optionxform = str
    section = {}
    config.read(LP_FILE['hwcfg'])
    if config.has_section(name):
        section = config[name]
    return section

def save_syringe_info(codes, volumes):
    config = ConfigParser()
    config.read(LP_FILE['syringe'])
    if not config.has_section('Codes'):
        config.add_section('Codes')
    config['Codes'] = codes

    if not config.has_section('Volumes'):
        config.add_section('Volumes')
    # Changed the way syringe volumes are stored in the config file:
    volume = {}
    for key, val in volumes.items():
        volume[key] = str(val)[1:-1].replace("'", '')
    config['Volumes'] = volume

    with open(LP_FILE['syringe'], 'w') as file:
        config.write(file)

def open_syringe_info():
    config = ConfigParser()
    config.read(LP_FILE['syringe'])
    volumes = {}
    for key, val in config['Volumes'].items():
        volumes[key] = val.split(', ')
    return config['Codes'], volumes

def update_stream_folder(base=''):
    if not base:
        base = datetime.now().strftime('%Y-%m-%d')
    LP_PATH['stream'] = LP_PATH['data'] / base
    LP_PATH['stream'].mkdir(parents=True, exist_ok=True)
