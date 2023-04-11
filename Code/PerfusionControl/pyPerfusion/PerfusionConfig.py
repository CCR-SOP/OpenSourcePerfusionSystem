# -*- coding: utf-8 -*-
"""Basic configuration constants for the LiverPerfusion app

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import logging
from dataclasses import asdict

from configparser import ConfigParser

from pyPerfusion.folder_management import FolderManagement


# Set ACTIVE_CONFIG to either the StudyConfig or TestConfig objects
# This helps prevent overwriting real study configurations during testing
StudyConfig = FolderManagement('LiverPerfusion')
TestConfig = FolderManagement('LPTest')
ACTIVE_CONFIG = None
ALLOW_MOCKS = True


class MissingConfigFile(Exception):
    """Exception used to indicate a configuration file is not available"""


class MissingConfigSection(Exception):
    """Exception used to indicate a section within a file is not available"""


def set_test_config():
    global ACTIVE_CONFIG, TestConfig
    ACTIVE_CONFIG = TestConfig


def set_study_config():
    global ACTIVE_CONFIG, StudyConfig
    ACTIVE_CONFIG = StudyConfig


def get_date_folder():
    global ACTIVE_CONFIG
    return ACTIVE_CONFIG.get_folder('date')


def get_cfg_filename(name: str):
    global ACTIVE_CONFIG
    return ACTIVE_CONFIG.get_folder('config') / f'{name}.ini'


def hw_cfg_name():
    global ACTIVE_CONFIG
    return ACTIVE_CONFIG.get_folder('config') / 'hardware.ini'


def receiver_cfg_name():
    global ACTIVE_CONFIG
    return ACTIVE_CONFIG.get_folder('config') / 'receiver.ini'


def syringe_cfg_name():
    global ACTIVE_CONFIG
    return ACTIVE_CONFIG.get_folder('config') / 'syringe.ini'


""" In order to properly parse """
def read_into_dataclass(cfg_name: str, section_name: str, cfg):
    global ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name)
    if filename:
        parser.read(filename)
    else:
        raise MissingConfigFile(filename)
    if parser.has_section(section_name):
        section = parser[section_name]
        # print(section)
        # print(section.items())
        for key, value in section.items():
            try:
                dummy = getattr(cfg, key)
            except AttributeError as e:
                logging.getLogger(__name__).debug(f'Config contained entry {key} which is not part of dataclass {cfg}')
                # this can occur in the case of derived classes, so continue on
                continue
            try:
                setattr(cfg, key, type(dummy)(value))
            except ValueError:
                logging.getLogger(__name__).error(f'Error reading {filename}[{section_name}]:{key} = {value}')
                logging.getLogger(__name__).error(f'Expected value type is {type(dummy)}')
    else:
        raise MissingConfigSection(f'{section_name} in {filename}')


def write_from_dataclass(cfg_name: str, section_name: str, cfg):
    global ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name)
    if filename:
        parser.read(filename)
    if not parser.has_section(section_name):
        parser.add_section(section_name)
    parser[section_name] = asdict(cfg)
    with open(filename, 'w') as file:
        parser.write(file)


def write_section(cfg_name: str, section_name: str, info: dict):
    global ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name)
    if filename:
        parser.read(filename)
    if not parser.has_section(section_name):
        parser.add_section(section_name)
    parser[section_name] = info
    with open(filename, 'w') as file:
        parser.write(file)


def read_section(cfg_name: str, section_name: str) -> dict:
    global ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name)
    if filename:
        parser.read(filename)
    section = {}
    if parser.has_section(section_name):
        section = parser[section_name]
    return section


def get_section_names(cfg_name: str):
    global ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name)
    sections = {}
    if filename:
        parser.read(filename)
        sections = parser.sections()
    return sections

def open_receiver_info():
    config = ConfigParser()
    config.read(receiver_cfg_name())
    receiver_info = {}
    for key, val in config['Dexcom Receivers'].items():
        receiver_info[key] = val
    return receiver_info


def save_syringe_info(codes, volumes):
    config = ConfigParser()
    config.read(syringe_cfg_name())
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

    with open(syringe_cfg_name(), 'w') as file:
        config.write(file)


def open_syringe_info(self):
    config = ConfigParser()
    config.read(syringe_cfg_name())
    volumes = {}
    for key, val in config['Volumes'].items():
        volumes[key] = val.split(', ')
    return config['Codes'], volumes


def get_COMs_bauds():
    config = ConfigParser()
    config.read(syringe_cfg_name())
    COMs_bauds = {}
    for key, val in config['Syringes'].items():
        COMs_bauds[key] = val.split(', ')
    return COMs_bauds


def setup_file_logger(lgr, level, filename=None):
    global ACTIVE_CONFIG
    if not filename:
        filename = lgr.device_name
    lgr.setLevel(level)
    ch = logging.FileHandler(ACTIVE_CONFIG.get_folder('logs') / f'{filename}.log')
    ch.setLevel(level)
    formatter = logging.Formatter('%(asctime) s: %(name) s - %(levelname) s - %(message) s')
    ch.setFormatter(formatter)
    lgr.addHandler(ch)
