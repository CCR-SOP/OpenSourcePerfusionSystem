# -*- coding: utf-8 -*-
"""Unit test for FileProcessing strategy with SensorStream class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
from time import sleep
from pathlib import Path
import os

from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.SensorStream import SensorStream
import pyHardware.pyAI as pyAI
import pyPerfusion.PerfusionConfig as PerfusionConfig


CHANNEL_NAME = 'Pytest Channel'
@pytest.fixture
def data_path():
    data_path = PerfusionConfig.get_date_folder()
    files = [data_path / f'{CHANNEL_NAME}.txt', data_path / f'{CHANNEL_NAME}.dat']
    # if a test fails, the files may not get deleted after the yield
    # so insure the test starts with the files deleted
    for file in files:
        if os.path.exists(file):
            os.remove(file)

    yield Path(data_path)

    for file in files:
        if os.path.exists(file):
            os.remove(file)


@pytest.fixture
def ai(data_path):
    cfg = pyAI.AIDeviceConfig(name='PyTest AI', sampling_period_ms=1,
                              read_period_ms=200)
    dev = pyAI.AIDevice()
    ch_cfg = pyAI.AIChannelConfig(name=CHANNEL_NAME, line=0)
    dev.add_channel(ch_cfg)
    dev.open(cfg)
    ai = dev.ai_channels[CHANNEL_NAME]
    yield ai
    dev.stop()
    dev.close()



def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))
    PerfusionConfig.set_test_config()


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_sensorstream_to_file_no_strategy(data_path, ai):
    sensor = SensorStream(ai, 'units/time')
    sensor.open()
    sensor.start()
    sleep(2)
    sensor.stop()
    assert not os.path.exists(data_path / f'{CHANNEL_NAME}.txt')
    assert not os.path.exists(data_path / f'{CHANNEL_NAME}.dat')


def test_sensorstream_to_files_created(data_path, ai):
    sensor = SensorStream(ai, 'units/time')
    sensor.add_strategy(StreamToFile('StreamToFileRaw', 1, 10))
    sensor.open()
    sensor.start()
    sleep(1)
    sensor.stop()
    assert os.path.exists(data_path / f'{CHANNEL_NAME}.txt')
    assert os.path.exists(data_path / f'{CHANNEL_NAME}.dat')


def test_sensorstream_to_file(ai, data_path):
    sensor = SensorStream(ai, 'units/time')
    sensor.add_strategy(StreamToFile('StreamToFileRaw', 1, 10))
    sensor.open()
    sensor.start()
    sensor.hw.device.start()
    sleep(1)
    sensor.stop()
    sensor.hw.device.stop()

    strategy = sensor.get_file_strategy('StreamToFileRaw')
    t, full_buf = strategy.retrieve_buffer(-1, 100)
    strategy.close()

    assert len(full_buf) == 100
