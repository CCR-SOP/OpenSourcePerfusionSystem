# -*- coding: utf-8 -*-
""" Unit test for pyAI_NIDAQ class
    Requires NI DAQ device

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import os
from time import sleep

import pyHardware.pyAI_NIDAQ as pyAI
from pyHardware.pyAI import AIDeviceException
import pyHardware.pyAI_Finite_NIDAQ as pyAIFinite


DEVICE_UNDER_TEST = 'Dev1'
SAMPLES_PER_READ = 17

@pytest.fixture
def delete_file(filename):
    os.remove(filename)


@pytest.fixture
def ai():
    ai = pyAI.NIDAQ_AI(period_ms=10, volts_offset=2.5, volts_p2p=5)
    yield ai
    ai.stop()


@pytest.fixture
def ai_finite():
    ai_finite = pyAIFinite.AI_Finite_NIDAQ(period_ms=100,
                                           volts_offset=2.5, volts_p2p=5,
                                           samples_per_read=SAMPLES_PER_READ)
    yield ai_finite
    ai_finite.stop()


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
    ai.open(f'{DEVICE_UNDER_TEST}')
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


def test_getids(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    assert ai.get_ids() == ['1']
    ai.add_channel('3')
    assert ai.get_ids() == ['1', '3']


def test_remove_channel(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    ai.add_channel('2')
    ai.remove_channel('1')
    assert ai.get_ids() == ['2']


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


def test_getdata(ai):
    ai.open(f'{DEVICE_UNDER_TEST}')
    ai.add_channel('1')
    ai.start()
    sleep(1.0)
    data, t = ai.get_data('1')
    assert len(data) > 0 and type(t) is float
    ai.stop()


def test_getdata_finite(ai_finite):
    ai_finite.open(f'{DEVICE_UNDER_TEST}')
    ai_finite.add_channel('1')
    ai_finite.start()
    sleep(2.0)
    assert ai_finite.is_done()
    data, t = ai_finite.get_data('1')
    assert len(data) == 17