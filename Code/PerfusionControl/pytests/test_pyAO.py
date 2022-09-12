# -*- coding: utf-8 -*-
"""Unit test for pyAO class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import os
import threading
from time import sleep

import pytest

import pyHardware.pyAO as pyAO


@pytest.fixture
def output_file(tmp_path):
    return tmp_path / "ao.dat"


@pytest.fixture
def ao(output_file):
    ao = pyAO.AO(output_file)
    yield ao
    ao.stop()
    ao.close()


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_default_devname(ao):
    assert ao.devname == 'ao'


def test_open(ao, output_file):
    ao.open(10)
    assert ao.bits == 12
    assert ao.period_ms == 10
    assert os.path.exists(output_file)


def test_start(ao):
    ao.open(10)
    ao.start()
    assert 'pyAO ao' in [t.name for t in threading.enumerate()]


def test_stop(ao):
    ao.open(10)
    ao.start()
    ao.stop()
    assert 'pyAO ao' not in [t.name for t in threading.enumerate()]


def test_output_file_written(ao, output_file):
    ao.open(10)
    ao.start()
    sleep(1.0)
    ao.stop()
    fid = open(output_file, 'rb')
    data = fid.read()
    fid.close()
    assert len(data) > 0


def test_setdc(ao, output_file):
    ao.open(10)
    ao.set_dc(0.0)
    ao.start()
    sleep(1.0)
    ao.stop()
    fid = open(output_file, 'rb')
    data = fid.read()
    fid.close()
    assert data.count(data[0]) == len(data)
