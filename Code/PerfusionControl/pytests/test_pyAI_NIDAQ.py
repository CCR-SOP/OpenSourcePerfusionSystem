# -*- coding: utf-8 -*-
"""Unit test for pyAI_NIDAQ class

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import os

import pyHardware.pyAI_NIDAQ as pyAI
from pyHardware.pyAI import AIDeviceException


DEVICE_UNDER_TEST = 'Dev4'

@pytest.fixture
def delete_file(filename):
    os.remove(filename)


@pytest.fixture
def ai():
    ai = pyAI.NIDAQ_AI(period_ms=10, volts_offset=2.5, volts_p2p=5)
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


def test_default_devname(ai):
    assert ai.devname == 'None/ai'


def test_devname(ai):
    ai.open('Dev4')
    assert ai.devname == f'{DEVICE_UNDER_TEST}/ai'


def test_devname_1ch(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    assert ai.devname == f'{DEVICE_UNDER_TEST}/ai1'


def test_devname_2ch_consecutive(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    ai.add_channel('2')
    assert ai.devname == f'{DEVICE_UNDER_TEST}/ai1,{DEVICE_UNDER_TEST}/ai2'


def test_devname_2ch_nonconsecutive(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    ai.add_channel('3')
    assert ai.devname == f'{DEVICE_UNDER_TEST}/ai1,{DEVICE_UNDER_TEST}/ai3'


def test_is_not_open(ai):
    assert not ai.is_open()


def test_isopen_channel_no_call_to_open(ai):
    with pytest.raises(AIDeviceException):
        ai.add_channel('1')


def test_isopen_call_to_open(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    assert ai.is_open()


def test_isopen_remove(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    assert ai.is_open()
    ai.remove_channel('1')
    assert not ai.is_open()


def test_is_acquiring(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    assert not ai.is_acquiring
    ai.start()
    assert ai.is_acquiring
    ai.stop()
    assert not ai.is_acquiring


def test_open2ch_close1(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    ai.add_channel('2')
    assert ai.is_open()
    ai.remove_channel('1')
    assert not ai.is_acquiring
    ai.add_channel('1')
    ai.start()
    ai.remove_channel('1')
    assert ai.is_acquiring