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


DEVICE_UNDER_TEST = 'Dev1'
SAMPLES_PER_READ = 10
SENSOR_NAME = 'TestSensor'


@pytest.fixture
def ai_finite():
    ai_finite = pyAIFinite.AI_Finite_NIDAQ(period_ms=100,
                                           volts_offset=2.5, volts_p2p=5,
                                           samples_per_read=SAMPLES_PER_READ)
    yield ai_finite
    ai_finite.stop()


@pytest.fixture
def strategy_pts2file(tmpdir):
    strategy_pts2file = PointsToFile('Points2File', 1, SAMPLES_PER_READ)
    strategy_pts2file.open(tmpdir, SENSOR_NAME,
                  {'Sampling Period (ms)': 100, 'Data Format': 'float32',
                   'Samples Per Timestamp': SAMPLES_PER_READ})
    yield strategy_pts2file


@pytest.fixture
def sensor_point(ai_finite):
    sensor_point = SensorPoint(SENSOR_NAME, 'Volts', ai_finite)
    yield sensor_point
    sensor_point.stop()


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_sensorpoint_fromlastread(ai_finite, sensor_point, strategy_pts2file):
    ai_finite.open(f'{DEVICE_UNDER_TEST}')
    ai_finite.add_channel('1')
    # Channel id must be set in order to save data properly
    sensor_point.set_ch_id('1')

    sensor_point.add_strategy(strategy_pts2file)
    sensor_point.open()
    sensor_point.start()
    ai_finite.start()

    sleep(2.0)

    assert ai_finite.is_done()

    ts, data = strategy_pts2file.get_data_from_last_read(0)
    assert data is not None and len(data) == SAMPLES_PER_READ


def test_sensorpoint_getlastacq(ai_finite, sensor_point, strategy_pts2file):
    ai_finite.open(f'{DEVICE_UNDER_TEST}')
    ai_finite.add_channel('1')
    # Channel id must be set in order to save data properly
    sensor_point.set_ch_id('1')

    sensor_point.add_strategy(strategy_pts2file)
    sensor_point.open()
    sensor_point.start()
    ai_finite.start()

    sleep(2.0)

    assert ai_finite.is_done()

    ts, data = strategy_pts2file.get_last_acq()
    assert data is not None and len(data) == SAMPLES_PER_READ


def test_sensorpoint_getcurrent(ai_finite, sensor_point, strategy_pts2file):
    ai_finite.open(f'{DEVICE_UNDER_TEST}')
    ai_finite.add_channel('1')
    # Channel id must be set in order to save data properly
    sensor_point.set_ch_id('1')

    sensor_point.add_strategy(strategy_pts2file)
    sensor_point.open()
    sensor_point.start()
    ai_finite.start()

    sleep(2.0)

    assert ai_finite.is_done()

    data = strategy_pts2file.get_current()
    assert type(data) == np.float32


def test_sensorpoint_read(ai_finite, sensor_point, strategy_pts2file):
    ai_finite.open(f'{DEVICE_UNDER_TEST}')
    ai_finite.add_channel('1')
    # Channel id must be set in order to save data properly
    sensor_point.set_ch_id('1')

    sensor_point.add_strategy(strategy_pts2file)
    sensor_point.open()
    sensor_point.start()
    ai_finite.start()
    sleep(2.0)
    assert ai_finite.is_done()



    data = strategy_pts2file.get_current()
    assert type(data) == np.float32