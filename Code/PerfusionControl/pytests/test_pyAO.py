# -*- coding: utf-8 -*-
"""Unit test for pyAO class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import os

import pyHardware.pyAO as pyAO


@pytest.fixture
def delete_file(filename):
    os.remove(filename)


@pytest.fixture
def ao():
    ao = pyAO.AO()
    yield ao
    ao.halt()


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
