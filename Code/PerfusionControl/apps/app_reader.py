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

import pyPerfusion.Strategy_ReadWrite as Strategy_ReadWrite
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils

def main():
    base_folder = PerfusionConfig.ACTIVE_CONFIG.basepath / PerfusionConfig.ACTIVE_CONFIG.get_data_folder('2023-06-05')
    sensor_name = 'Hepatic Artery Flow'
    output = 'Raw'

    fqpn = base_folder / f'{sensor_name}_{output}.dat'
    sensor = Strategy_ReadWrite.ReaderStreamSensor()
    reader = Strategy_ReadWrite.Reader(output, fqpn, Strategy_ReadWrite.WriterConfig(), sensor)
    reader.read_settings()

    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp((sensor.get_acq_start_ms()+ts) / 1000.0)} data={data}')
    ts, data = reader.get_all()
    print(f'total data points are {len(ts)}')
    print(f'sampling period is {sensor.sampling_period_ms} ms')
    with open(fqpn.with_suffix('.csv'), 'wt') as csv:
        for t, d in zip(ts, data):
            csv.write(f'{t/1000.0}, {d}\n')


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_reader', logging.DEBUG)

    main()
