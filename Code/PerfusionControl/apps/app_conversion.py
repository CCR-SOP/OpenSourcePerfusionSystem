# -*- coding: utf-8 -*-
""" Application for reading all saved files from folder and
    converting to CSV formats for analysis


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import os
import pathlib
import sys

import pyPerfusion.Strategy_ReadWrite as ReadWrite
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


def main():
    date_str = sys.argv[1]
    base_folder = PerfusionConfig.ACTIVE_CONFIG.basepath / \
                  PerfusionConfig.ACTIVE_CONFIG.get_data_folder(date_str)

    if not os.path.isdir(base_folder):
        print(f'Could not find folder {base_folder}')
    else:
        for file in os.scandir(base_folder):
            ext = os.path.splitext(file.name)[-1].lower()
            if ext == '.dat':
                print(f'converting {file.name}')
                ReadWrite.save_to_csv(pathlib.Path(file.path))


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_conversion', logging.DEBUG)

    main()
