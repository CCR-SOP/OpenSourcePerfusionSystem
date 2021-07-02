# -*- coding: utf-8 -*-
"""Unit test for ProcessingStrategy class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest

import numpy as np

from pyPerfusion.ProcessingStrategy import ProcessingStrategy, RMSStrategy, SaveStreamToFile

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


def test_base_strategy():
    strategy = ProcessingStrategy('PassThrough', 5, 10)
    data = np.array([1]*10 + [2]*10)
    buf1 = strategy.process_buffer(data[0:10])
    assert len(buf1) == 10
    buf2 = strategy.process_buffer(data[10:20])
    assert len(buf2) == 10
    results = np.append(buf1, buf2)
    assert len(results) == 20
    assert np.array_equal(data, results)


def test_rms_strategy():
    strategy = RMSStrategy('RMS', 5, 10)
    data = np.array([1]*10 + [2]*10, dtype=np.float32)
    expected_results = np.array([0.4472136, 0.6324555, 0.7745967, 0.8944272, 1,
                                 1,         1,         1,         1,         1,
                                 1.264911,  1.4832397, 1.67332,   1.8439089, 2,
                                 2,         2,         2,         2,         2])
    buf1 = strategy.process_buffer(data[0:10])
    assert len(buf1) == 10
    buf2 = strategy.process_buffer(data[10:20])
    assert len(buf2) == 10
    results = np.append(buf1, buf2)
    assert len(results) == 20
    assert np.isclose(expected_results, results).all()


def test_streamtofile_strategy(tmpdir):
    strategy = SaveStreamToFile('StreamToFile', 1, 10)
    strategy.open(tmpdir, {'Param1': 'test', 'Param2': 1})
    test_file = tmpdir.join('StreamToFile.dat')
    expected = f'File Format: 1\nAlgorithm: StreamToFile\nWindow Length: 1\nParam1: test\nParam2: 1\n'
    fid = open(test_file, 'rt')
    fid.seek(0)
    file_contents = fid.read()
    assert file_contents == expected
    data = np.array([1]*10 + [2]*10)
    buf1 = strategy.process_buffer(data[0:10])
    buf2 = strategy.process_buffer(data[10:20])
    results = np.append(buf1, buf2)
    data = np.fromfile(fid, dtype=np.int32)
    fid.close()
    assert len(data) == len(results)
    assert np.array_equal(data, results)
