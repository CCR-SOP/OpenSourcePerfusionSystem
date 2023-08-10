# -*- coding: utf-8 -*-
""" Application for reading saved files and converting to other formats for analysis


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging

import pyPerfusion.Strategy_ReadWrite as ReadWrite
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


def main():
    date_str = '2023-08-09'

    sensor_name = 'Hepatic Artery Flow'
    output_type = 'Raw'
    ReadWrite.save_to_csv(date_str, sensor_name, output_type)

    sensor_name = 'Arterial Gas Mixer'
    output_type = 'GasMixerPoints'
    ReadWrite.save_to_csv(date_str, sensor_name, output_type)


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_reader', logging.DEBUG)

    main()
