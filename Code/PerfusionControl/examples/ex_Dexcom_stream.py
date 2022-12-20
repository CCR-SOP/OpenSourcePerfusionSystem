# -*- coding: utf-8 -*-
""" Test script to test functionality of Dexcom with SensorPoint


@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import logging
import time

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyPerfusion.pyDexcom as pyDexcom
from pyPerfusion.FileStrategy import PointsToFile
from pyPerfusion.SensorPoint import SensorPoint


def main():
    dexcom = pyDexcom.DexcomReceiver('Hepatic Artery')
    dexcom.read_config()

    sensorpt = SensorPoint(dexcom, 'na')
    sensorpt.add_strategy(strategy=PointsToFile('write', 1, 1))

    sensorpt.start()
    dexcom.start()

    print('Sleeping for 60 seconds')
    time.sleep(60.0)
    ts, last_samples = sensorpt.get_strategy('write').retrieve_buffer(60000, 2)
    for ts, samples in zip(ts, last_samples):
        print(f'{ts}: sample is {samples}')

    dexcom.stop()
    sensorpt.stop()


if __name__ == '__main__':
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)
    PerfusionConfig.set_test_config()
    main()
