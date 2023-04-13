# -*- coding: utf-8 -*-
""" Script to show differences between example configs and test/study configs


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from pathlib import Path

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.folder_management import FolderManagement


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


PerfusionConfig.set_test_config()
git_fm = FolderManagement(project_name='PerfusionControl', base_path=Path('../'), default_structure=False)
git_fm.add_folder('config')


print('Comparing hardware.ini')
# check section names in hardware.ini
hw_local = PerfusionConfig.get_section_names('hardware')
hw_git = PerfusionConfig.get_section_names('hardware', git_fm)

print_diff(hw_local, hw_git, 'Comparing section names:')

for section in hw_local:
    if section in hw_git:
        pairs_local = PerfusionConfig.read_section('hardware', section)
        pairs_git = PerfusionConfig.read_section('hardware', section, git_fm)
        local_opt = []
        for key, value in pairs_local.items():
            local_opt.append(f'{key} = {value}')
        git_opt = []
        for key, value in pairs_git.items():
            git_opt.append(f'{key} = {value}')
        print_diff(local_opt, git_opt, f'Comparing section {section} keys')


