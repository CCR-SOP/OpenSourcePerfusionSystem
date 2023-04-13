# -*- coding: utf-8 -*-
""" Script to show differences between example configs and test/study configs


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from pathlib import Path
import dataclasses

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.folder_management import FolderManagement
from pyHardware.pyAI import AIDeviceConfig, AIChannelConfig
from pyHardware.pyAI_NIDAQ import NIDAQAIDevice
from pyHardware.pyCDI import CDI, MockCDI
from pyHardware.pyPump11Elite import Pump11Elite, MockPump11Elite
from pyHardware.pyGB100 import GasDevice, MockGasDevice
from pyHardware.pyDC_NIDAQ import NIDAQDCDevice
from pyHardware.pyDC import DCDevice
from pyPerfusion.Sensor import Sensor
from pyPerfusion.Strategy_Processing import RMS, MovingAverage, RunningSum
from pyPerfusion.Strategy_ReadWrite import WriterStream, WriterPoints


def print_diff(local_data, git_data, hdr_msg):
    local_only = set(local_data) - set(git_data)
    git_only = set(git_data) - set(local_data)
    diffs_found = len(local_only) + len(git_only) > 0
    if diffs_found:
        print(hdr_msg)
    if len(local_only) > 0:
        print('\tFound in local, but not git:')
        for each_diff in local_only:
            print(f'\t\t{each_diff}')
    if len(git_only) > 0:
        print('\tFound in git, but not local:')
        for each_diff in git_only:
            print(f'\t\t{each_diff}')
    if diffs_found:
        print('====')


def print_dataclass_diff(section_keys, dataclass, hdr_msg):
    class_ = globals().get(dataclass, None)
    obj = class_(name='')
    fields = dataclasses.fields(obj.cfg)
    # the class key is not a part of the dataclass, so remove it
    section_keys = [name for name in section_keys if name != 'class']
    dataclass_attr = [field.name for field in fields if field.name != 'class']

    cfg_only = set(section_keys) - set(dataclass_attr)
    git_only = set(dataclass_attr) - set(section_keys)
    diffs_found = len(cfg_only) + len(git_only) > 0
    if diffs_found:
        print(hdr_msg)
    if len(cfg_only) > 0:
        print(f'\tFound in config, but not in {dataclass}:')
        for each_diff in cfg_only:
            print(f'\t\t{each_diff}')
    if len(git_only) > 0:
        print(f'\tFound in {dataclass}, but not config:')
        for each_diff in git_only:
            print(f'\t\t{each_diff}')
    if diffs_found:
        print('====')


def compare_file(file, git_fm):
    print(f'Comparing {file}.ini')
    # check section names in hardware.ini
    hw_local = PerfusionConfig.get_section_names(file)
    hw_git = PerfusionConfig.get_section_names(file, git_fm)

    print_diff(hw_local, hw_git, 'Comparing section names:')

    for section in hw_local:
        if section in hw_git:
            pairs_local = PerfusionConfig.read_section(file, section)
            pairs_git = PerfusionConfig.read_section(file, section, git_fm)
            local_opt = []
            for key, value in pairs_local.items():
                local_opt.append(f'{key} = {value}')
            git_opt = []
            for key, value in pairs_git.items():
                git_opt.append(f'{key} = {value}')
            print_diff(local_opt, git_opt, f'Comparing section {section} keys')

            class_name = pairs_local['class']
            print_dataclass_diff(pairs_local.keys(), class_name,
                                 f'Comparing local {section} keys to {class_name} config')
            print_dataclass_diff(pairs_git.keys(), class_name,
                                 f'Comparing git {section} keys to {class_name} config')


def main():
    PerfusionConfig.set_test_config()
    git_fm = FolderManagement(project_name='PerfusionControl', base_path=Path('../'), default_structure=False)
    git_fm.add_folder('config')
    compare_file('hardware', git_fm)
    compare_file('sensors', git_fm)
    compare_file('strategies', git_fm)


if __name__ == "__main__":
    main()


