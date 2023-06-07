# -*- coding: utf-8 -*-
"""Simple class for managing folders for applications
Allows for the creation and management of a folder structure (data, config, logs)
for applications, and provides simple helper functions for returning folder names

@project: Liver Perfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import os
from pathlib import Path
import logging
from datetime import datetime


class FolderManagement:
    def __init__(self, project_name: str,
                 base_path: Path = Path(os.path.expanduser('~/Documents')),
                 default_structure: bool = True):
        self._lgr = logging.getLogger(__name__)
        self._cfg_ext: str = '.cfg'
        self._log_ext: str = '.log'
        self._project_name = project_name
        self._base_path = Path(base_path) / project_name
        self._base_path.mkdir(parents=True, exist_ok=True)
        self._folders = {}
        self._config_files = {}
        self._date_folder = None
        if default_structure:
            self.create_default_structure()

    @classmethod
    def get_default_base(cls):
        return Path(os.path.expanduser('~/Documents'))

    @property
    def basepath(self):
        return self._base_path

    @property
    def project_name(self):
        return self._project_name

    @property
    def config_files(self):
        return self._config_files

    def set_base(self, base_path: Path, recreate_structure: bool = True):
        self._base_path = base_path / self._project_name
        self._base_path.mkdir(parents=True, exist_ok=True)
        if recreate_structure:
            folder_names = self._folders.keys()
            if not folder_names:
                self.create_default_structure()
            else:
                self._folders = {}
                for name in folder_names:
                    self.add_folder(name)
            files = self._config_files.keys()
            for cfg in files:
                self.add_config_file(cfg)

    def create_default_structure(self):
        self.add_folder('logs')
        self.add_folder('config')
        self.add_folder('data')
        # add a folder with the current date to the data folder automatically
        # this will help prevent overwriting a previous study's data
        self._date_folder = Path('data') / datetime.now().strftime('%Y-%m-%d')
        self.add_folder(self._date_folder)

    def read_existing_structure(self):
        valid = ['logs', 'config', 'data']
        if len(self._folders) > 0:
            self._lgr.warning(f'in _read_existing_structure, _folders already contains values ({self._folders.keys()}')
        self._lgr.debug(f'Looking for folders in {self._base_path}')
        self._folders = {f.name:f.path for f in os.scandir(self._base_path) if f.is_dir() and f.name in valid}
        self._lgr.debug(f'Found existing folders {self._folders.keys()}')

    def add_folder(self, folder_name, base_path=None):
        if not base_path:
            base_path = self._base_path
        self._folders[folder_name] = Path(base_path) / folder_name
        self._folders[folder_name].mkdir(parents=True, exist_ok=True)

    def add_config_file(self, cfg_name):
        fqpn = self._folders['config'] / f'{cfg_name}{self._cfg_ext}'
        self._config_files[cfg_name] = fqpn
        if not os.path.exists(fqpn):
            with open(fqpn, 'a+'):
                self._lgr.info(f'Creating new config file: {fqpn}')

    def get_folder(self, name):
        if name == 'base':
            folder = self._base_path
        else:
            if name == 'date':
                name = self._date_folder
            folder = self._folders.get(name, None)
        return folder

    def get_config_file(self, name):
        file = self._config_files.get(name, None)
        return file

    def get_data_folder(self, yyyy_mm_dd: str):
        return Path('data') / yyyy_mm_dd
