# -*- coding: utf-8 -*-
""" Application for reading saved files and converting to other formats for analysis


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
from datetime import datetime

import numpy as np

import pyPerfusion.Strategy_ReadWrite as Strategy_ReadWrite
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


def main():
    base_folder = PerfusionConfig.ACTIVE_CONFIG.basepath / PerfusionConfig.ACTIVE_CONFIG.get_data_folder('2023-06-05')
    sensor_name = 'Hepatic Artery Flow'
    output = 'Raw'
    start_timestamp_str = '2023-06-05 20:53:58.719000'
    start_ts = datetime.strptime(start_timestamp_str, '%Y-%m-%d %H:%M:%S.%f')
    start_ms = start_ts.timestamp()
    sensor = Strategy_ReadWrite.ReaderStreamSensor(data_dtype=np.dtype('float64'),
                                                   acq_start_ms=start_ms,
                                                   sampling_period_ms=100)
    fqpn = base_folder / f'{sensor_name}_{output}.dat'
    cfg = Strategy_ReadWrite.WriterConfig()
    reader = Strategy_ReadWrite.Reader(output, fqpn, cfg, sensor)
    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp(ts / 1000.0)} data={data}')
    ts, data = reader.get_all()
    print(f'total data points are {len(ts)}')
    for t, d in zip(ts, data):
        print(f't={datetime.fromtimestamp(t / 1000.0)} data={d}')


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_reader', logging.DEBUG)

    main()
