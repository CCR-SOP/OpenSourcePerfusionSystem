# -*- coding: utf-8 -*-
"""Unit test for FileProcessing strategy with SensorStream class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest

import numpy as np

from pyPerfusion.FileStrategy import StreamToFile
from pyPerfusion.SensorStream import SensorStream


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
