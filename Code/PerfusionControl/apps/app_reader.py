# -*- coding: utf-8 -*-
""" Application for reading saved files and converting to other formats for analysis


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from datetime import datetime
import os

import numpy as np

import pyPerfusion.Strategy_ReadWrite as RW
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


def main():
    date_str = '2023-08-09'
    sensor_name = 'Hepatic Artery Flow'
    output_type = 'Raw'
    reader = RW.read_file(date_str, sensor_name, output_type)
    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp(ts + reader.sensor.get_acq_start_ms() / 1000.0)} data={data}')
    RW.convert_to_csv(reader)

    sensor_name = 'Arterial Gas Mixer'
    output_type = 'GasMixerPoints'
    reader = RW.read_file(date_str, sensor_name, output_type)
    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp(ts / 1000.0)} data={data}')
    RW.convert_to_csv(reader)


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_reader', logging.DEBUG)

    main()
