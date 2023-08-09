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


def read_file(date_str, sensor_name, output_type, sensor):
    base_folder = PerfusionConfig.ACTIVE_CONFIG.basepath / \
                  PerfusionConfig.ACTIVE_CONFIG.get_data_folder(date_str)

    fqpn = base_folder / f'{sensor_name}_{output_type}.dat'
    if type(sensor) == Strategy_ReadWrite.ReaderStreamSensor:
        reader = Strategy_ReadWrite.Reader(output_type, fqpn, Strategy_ReadWrite.WriterConfig(), sensor)
    elif type(sensor) == Strategy_ReadWrite.ReaderPointsSensor:
        reader = Strategy_ReadWrite.ReaderPoints(output_type, fqpn, Strategy_ReadWrite.WriterPointsConfig(), sensor)
    else:
        reader = None
    if reader:
        reader.read_settings()
    return reader


def convert_to_excel(reader):
    ts, data = reader.get_all()
    array_data = True
    if type(reader) == Strategy_ReadWrite.Reader:
        array_data = False
    else:
        data = data.reshape(-1, reader.sensor.samples_per_timestamp)
    with open(reader.fqpn.with_suffix('.csv'), 'wt') as csv:
        for t, d in zip(ts, data):
            if array_data:
                data_str = ','.join(map(str, d))
            else:
                data_str = f'{d}'
            csv.write(f'{datetime.fromtimestamp(t / 1000.0)}, {data_str}\n')


def main():
    date_str = '2023-08-09'
    sensor_name = 'Hepatic Artery Flow'
    output_type = 'Raw'
    reader = read_file(date_str, sensor_name, output_type, Strategy_ReadWrite.ReaderStreamSensor())
    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp(ts / 1000.0)} data={data}')
    convert_to_excel(reader)

    sensor_name = 'Arterial Gas Mixer'
    output_type = 'GasMixerPoints'
    reader = read_file(date_str, sensor_name, output_type, Strategy_ReadWrite.ReaderPointsSensor())
    ts, data = reader.get_last_acq()
    print(f'Last acq was t={datetime.fromtimestamp(ts / 1000.0)} data={data}')
    convert_to_excel(reader)


if __name__ == "__main__":
    PerfusionConfig.set_test_config()
    utils.setup_default_logging('app_reader', logging.DEBUG)

    main()
