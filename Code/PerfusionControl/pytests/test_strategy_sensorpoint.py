# -*- coding: utf-8 -*-
""" Unit test for SensorPoint with PointsToFile strategy
    Test capabilities exclusive to SensorPoint and PointsToFile
    Requires NI DAQ hardware with finite acq capability

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
from time import sleep
import os.path

import numpy as np

from pyPerfusion.FileStrategy import PointsToFile
from pyPerfusion.SensorPoint import SensorPoint
import pyHardware.pyAI_Finite_NIDAQ as pyAIFinite
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyHardware.pyAI as pyAI

DEVICE_UNDER_TEST = 'Dev2'
SAMPLES_PER_READ = 10
SENSOR_NAME = 'TestSensor'


@pytest.fixture
def ai_finite():
    dev_cfg = pyAIFinite.FiniteNIDAQAIDeviceConfig(name='Pytest Device',
                                                   device_name=DEVICE_UNDER_TEST,
                                                   samples_per_read=SAMPLES_PER_READ,
                                                   sampling_period_ms=1)
    ch_cfg = pyAI.AIChannelConfig(name=SENSOR_NAME, line=0)
    dev = pyAIFinite.FiniteNIDAQAIDevice()
    dev.open(dev_cfg)
    dev.add_channel(ch_cfg)
    ai_finite = dev.ai_channels[SENSOR_NAME]
    yield ai_finite
    dev.stop()


@pytest.fixture
def sensor_point(ai_finite):
    sensor_point = SensorPoint(ai_finite, 'Volts')
    yield sensor_point
    sensor_point.stop()


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))
    PerfusionConfig.set_test_config()


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_sensorpoint_fromlastread(ai_finite, sensor_point):
    sensor_point.add_strategy(PointsToFile('Points2File', 1, SAMPLES_PER_READ))
    print(sensor_point._params)
    sensor_point.open()
    sensor_point.start()
    ai_finite.device.start()

    sleep(2.0)

    assert ai_finite.device.is_done()

    ts, data = sensor_point.get_file_strategy('Points2File').get_data_from_last_read(0)
    assert data is not None and len(data) == SAMPLES_PER_READ


def test_sensorpoint_getlastacq(ai_finite, sensor_point):
    sensor_point.add_strategy(PointsToFile('Points2File', 1, SAMPLES_PER_READ))
    sensor_point.open()
    sensor_point.start()
    ai_finite.device.start()

    sleep(2.0)

    assert ai_finite.device.is_done()

    ts, data = sensor_point.get_file_strategy('Points2File').get_last_acq()
    assert data is not None and len(data) == SAMPLES_PER_READ


def test_sensorpoint_getcurrent(ai_finite, sensor_point):
    sensor_point.add_strategy(PointsToFile('Points2File', 1, SAMPLES_PER_READ))
    sensor_point.open()
    sensor_point.start()
    ai_finite.device.start()

    sleep(2.0)
    assert ai_finite.device.is_done()

    data = sensor_point.get_file_strategy('Points2File').get_current()
    assert type(data) == np.float64
