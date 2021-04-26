# -*- coding: utf-8 -*-
"""Unit test for pyDIO class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import os

import pyHardware.pyDIO as pyDIO


@pytest.fixture
def delete_file(filename):
    os.remove(filename)


@pytest.fixture
def dio():
    dio = pyDIO.DIO()
    yield dio


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_default_devname(dio):
    assert dio.devname == 'portNone/lineNone'


def test_devname(dio):
    dio.open(port='0', line='1')
    assert dio.devname == 'port0/line1'
