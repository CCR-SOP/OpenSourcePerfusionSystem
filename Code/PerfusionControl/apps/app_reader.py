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


def read_stream_file(fqpn, output_type):
    sensor = Strategy_ReadWrite.ReaderStreamSensor()
    reader = Strategy_ReadWrite.Reader(output_type, fqpn, Strategy_ReadWrite.WriterConfig(), sensor)
    reader.read_settings()
    return reader


def read_points_file(fqpn, output_type):
    sensor = Strategy_ReadWrite.ReaderPointsSensor()
    reader = Strategy_ReadWrite.ReaderPoints(output_type, fqpn, Strategy_ReadWrite.WriterPointsConfig(), sensor)
    reader.read_settings()
    return reader


def convert_to_excel(fqpn, reader):
    ts, data = reader.get_all()
    with open(fqpn.with_suffix('.csv'), 'wt') as csv:
        for t, d in zip(ts, data):
            csv.write(f'{datetime.fromtimestamp(t / 1000.0)}, {d}\n')


def main():
    base_folder = PerfusionConfig.ACTIVE_CONFIG.basepath / PerfusionConfig.ACTIVE_CONFIG.get_data_folder('2023-08-09')

    sensor_name = 'Hepatic Artery Flow'
    output = 'Raw'
    fqpn = base_folder / f'{sensor_name}_{output}.dat'
    print(f'Reading {fqpn}')
    reader = read_stream_file(fqpn, output)
    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp(ts / 1000.0)} data={data}')
    convert_to_excel(fqpn, reader)

    sensor_name = 'Arterial Gas Mixer'
    output = 'GasMixerPoints'
    fqpn = base_folder / f'{sensor_name}_{output}.dat'
    print(f'Reading {fqpn}')
    reader = read_points_file(fqpn, output)
    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp(ts / 1000.0)} data={data}')
    convert_to_excel(fqpn, reader)



if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_reader', logging.DEBUG)

    main()
