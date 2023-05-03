# -*- coding: utf-8 -*-
"""Basic configuration constants for the LiverPerfusion app

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import logging
from dataclasses import asdict
from threading import Event
from configparser import ConfigParser
from pathlib import Path
import difflib

from pyPerfusion.folder_management import FolderManagement


# Set ACTIVE_CONFIG to either the StudyConfig or TestConfig objects
# This helps prevent overwriting real study configurations during testing
StudyConfig = FolderManagement('LiverPerfusion')
TestConfig = FolderManagement('LPTest')
ACTIVE_CONFIG = None
ALLOW_MOCKS = True

MASTER_HALT = Event()


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


def get_date_folder(fm: FolderManagement = None):
    fm = fm or ACTIVE_CONFIG
    return fm.get_folder('date')


def get_cfg_filename(name: str, fm: FolderManagement = None):
    fm = fm or ACTIVE_CONFIG
    return fm.get_folder('config') / f'{name}.ini'


def hw_cfg_name(fm: FolderManagement = None):
    fm = fm or ACTIVE_CONFIG
    return fm.get_folder('config') / 'hardware.ini'


def read_into_dataclass(cfg_name: str, section_name: str, cfg, fm: FolderManagement = None):
    fm = fm or ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name, fm)
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
                # most configs should contain an entry "class" which is not
                # part of the actual config for a class
                if key != 'class':
                    logging.getLogger(__name__).debug(f'Config contained entry {key} which is not part of dataclass {cfg}')
                continue
            try:
                # check if value is a list (i.e.: #, #)
                normal_value = True
                if ',' in value:
                    try:
                        value = [float(x.strip()) for x in ''.join(value).split(',')]
                        normal_value = False
                    except ValueError:
                        # a comma was found, but the values are not all numbers, so this
                        # probably isn't a list. Treat it normally
                        pass
                if normal_value:
                    value = type(dummy)(value)
                setattr(cfg, key, value )
            except ValueError:
                logging.getLogger(__name__).error(f'Error reading {filename}[{section_name}]:{key} = {value}')
                logging.getLogger(__name__).error(f'Expected value type is {type(dummy)}')
    else:
        raise MissingConfigSection(f'{section_name} in {filename}')


def write_from_dataclass(cfg_name: str, section_name: str, cfg, fm: FolderManagement = None):
    fm = fm or ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name, fm)
    if filename:
        parser.read(filename)
    if not parser.has_section(section_name):
        parser.add_section(section_name)
    parser[section_name] = asdict(cfg)
    with open(filename, 'w') as file:
        parser.write(file)


def write_section(cfg_name: str, section_name: str, info: dict, fm: FolderManagement = None):
    fm = fm or ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name, fm)
    if filename:
        parser.read(filename)
    if not parser.has_section(section_name):
        parser.add_section(section_name)
    parser[section_name] = info
    with open(filename, 'w') as file:
        parser.write(file)


def read_section(cfg_name: str, section_name: str, fm: FolderManagement = None) -> dict:
    fm = fm or ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name, fm)
    if filename:
        parser.read(filename)
    section = {}
    if parser.has_section(section_name):
        section = parser[section_name]
    return section


def get_section_names(cfg_name: str, fm: FolderManagement = None):
    fm = fm or ACTIVE_CONFIG
    parser = ConfigParser()
    parser.optionxform = str
    filename = get_cfg_filename(cfg_name, fm)
    sections = {}
    if filename:
        parser.read(filename)
        sections = parser.sections()
    return sections
