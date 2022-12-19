# -*- coding: utf-8 -*-
""" Test script to test functionality of CDI multi-variable reading/saving


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import time
from datetime import datetime

import serial

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyCDI as pyCDI
from pyPerfusion.FileStrategy import MultiVarToFile, MultiVarFromFile
from pyPerfusion.SensorPoint import SensorPoint, ReadOnlySensorPoint

PerfusionConfig.set_test_config()

def main():
    cdi = pyCDI.CDIStreaming('Test CDI')
    cdi.read_config()
    fake_cdi = None
    if not cdi.is_open():
        print('Real CDI is not connected, send fake data for testing')
        print('This requires a loop between COM5 and COM10')
        cdi.cfg.port = 'COM10'
        cdi.open()
        data = list(range(18))
        fake_cdi = serial.Serial()
        fake_cdi.port = 'COM5'
        fake_cdi.baud_rate = 9600
        fake_cdi.open()
        for i in range(10):
            now = datetime.now().strftime('%H:%M:%S')
            cdi_str = f'{0x2}abc{now}\t' + '\t'.join(f'{d:02x}{d + i:04d}' for d in data) + f'\tCRC{0x3}'
            print(f'writing {cdi_str}')
            fake_cdi.write(bytes(cdi_str + '\n', 'ascii'))
            time.sleep(1.0)

    sensorpt = SensorPoint(cdi, 'na')
    sensorpt.add_strategy(strategy=MultiVarToFile('write', 1, 17))

    ro_sensorpt = ReadOnlySensorPoint(cdi, 'na')
    read_strategy = MultiVarFromFile('multi_var', 1, 17, 1)
    ro_sensorpt.add_strategy(strategy=read_strategy)

    sensorpt.start()
    cdi.start()

    if fake_cdi is None:
        print('Sleeping for 60 seconds')
        time.sleep(60.0)
    else:
        # give data a chance to flush to disk
        time.sleep(2.0)
    ts, last_samples = read_strategy.retrieve_buffer(60000, 2)
    for ts, samples in zip(ts, last_samples):
        print(f'{ts}: sample is {samples}')

    cdi.stop()
    sensorpt.stop()
    ro_sensorpt.stop()


if __name__ == '__main__':
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    PerfusionConfig.set_test_config()
    main()
