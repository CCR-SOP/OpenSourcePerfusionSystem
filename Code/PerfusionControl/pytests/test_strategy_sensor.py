# -*- coding: utf-8 -*-
"""Unit test for FileProcessing strategy with SensorStream class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
from time import sleep
import os.path

import numpy as np

from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.SensorStream import SensorStream
import pyHardware.pyAI as pyAI


@pytest.fixture
def ai():
    ai = pyAI.AI(period_sample_ms=10)
    yield ai
    ai.stop()


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_streamtofile_strategy(tmpdir):
    strategy = StreamToFile('StreamToFile', 1, 10)
    strategy.open(tmpdir, 'StreamToFile', {'Sampling Period (ms)': 100, 'Data Format': 'int32'})
    test_file = tmpdir.join('StreamToFile.txt')
    expected = f'Algorithm: PassThrough\nWindow Length: 1\nFile Format: 1\nSampling Period (ms): 100\nData Format: int32\n'
    file_contents = test_file.read()
    assert file_contents == expected
    data = np.array([1]*10 + [2]*10, dtype=np.int32)
    buf1 = strategy.process_buffer(data[0:10])
    buf2 = strategy.process_buffer(data[10:20])
    results = np.append(buf1, buf2)
    test_file = tmpdir.join('StreamToFile.dat')
    data = np.fromfile(test_file, dtype=np.int32)
    assert len(data) == len(results)
    assert np.array_equal(data, results)

def test_readfromfile(tmpdir):
    strategy = StreamToFile('StreamToFile', 1, 10)
    strategy.open(tmpdir, 'StreamToFile',
                  {'Sampling Period (ms)': 100, 'Data Format': 'int32'})
    data = np.array([1]*10 + [2]*10, dtype=np.int32)
    buf1 = strategy.process_buffer(data)
    t, full_buf = strategy.retrieve_buffer(-1, 20)
    assert np.array_equal(full_buf, buf1)

def test_sensorstream_to_file_no_strategy(tmpdir, ai):
    sensor = SensorStream('test', 'units/time', ai)
    sensor.open(tmpdir)
    sensor.set_ch_id('0')
    ai.open()
    ai.add_channel('0')
    ai.start()
    sensor.start()
    sleep(2)
    sensor.stop()
    ai.stop()
    assert not os.path.exists(tmpdir.join('test.dat'))
    assert not os.path.exists(tmpdir.join('test.txt'))

def test_sensorstream_to_file_not_added(tmpdir, ai):
    strategy = StreamToFile('StreamToFileRaw', 1, 10)
    strategy.open(tmpdir, 'test',
                  {'Sampling Period (ms)': 100, 'Data Format': 'int32'})

    sensor = SensorStream('test', 'units/time', ai)
    sensor.open(tmpdir)
    sensor.set_ch_id('0')
    ai.open()
    ai.add_channel('0')
    ai.start()
    sensor.start()
    sleep(1)
    sensor.stop()
    ai.stop()
    assert os.path.exists(tmpdir.join('test.dat'))
    assert os.path.exists(tmpdir.join('test.txt'))

def test_sensorstream_to_file(tmpdir, ai):
    strategy = StreamToFile('StreamToFileRaw', 1, 10)
    strategy.open(tmpdir, 'test',
                  {'Sampling Period (ms)': 100, 'Data Format': 'float32'})

    sensor = SensorStream('test', 'units/time', ai)
    sensor.open(tmpdir)
    sensor.add_strategy(strategy)
    ai.add_channel('0')
    ai.open()
    ai.set_demo_properties('0', 2, 1)
    ai.start()
    sensor.set_ch_id('0')
    sensor.start()
    sleep(1)
    sensor.stop()
    ai.stop()

    t, full_buf = strategy.retrieve_buffer(-1, 100)
    assert len(full_buf) == 100
