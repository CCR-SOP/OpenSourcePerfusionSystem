# -*- coding: utf-8 -*-
""" Unit test for pyAI_NIDAQ class
    Requires NI DAQ device

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import logging
from time import sleep

import pyHardware.pyAI as pyAI
import pyHardware.pyAI_NIDAQ as pyAI_NIDAQ
import pyHardware.pyAI_Finite_NIDAQ as pyAI_Finite_NIDAQ
import pyPerfusion.utils as utils

DEVICE_UNDER_TEST = 'Dev2'
SAMPLES_PER_READ = 17


@pytest.fixture
def ai_device_cfg():
    ai_device_cfg = pyAI_NIDAQ.AINIDAQDeviceConfig(name='PyTest AIDevice',
                                                   device_name=DEVICE_UNDER_TEST,
                                                   sampling_period_ms=100,
                                                   read_period_ms=100*17)
    yield ai_device_cfg


@pytest.fixture
def ai_device(ai_device_cfg):
    ai_device = pyAI_NIDAQ.NIDAQAIDevice()
    ai_device.open(ai_device_cfg)
    yield ai_device
    ai_device.close()


@pytest.fixture
def ai_channel_config():
    ai_channel_config = pyAI.AIChannelConfig(name='PyTest AIChannel')
    yield ai_channel_config


@pytest.fixture
def ai_finite_device_cfg():
    ai_finite_device_cfg = pyAI_Finite_NIDAQ.FiniteNIDAQAIDeviceConfig(
        name='PyTest Finite AIDevice',
        device_name=DEVICE_UNDER_TEST,
        sampling_period_ms=100,
        samples_per_read=SAMPLES_PER_READ)
    yield ai_finite_device_cfg


@pytest.fixture
def ai_finite(ai_finite_device_cfg):
    ai_finite = pyAI_Finite_NIDAQ.FiniteNIDAQAIDevice()
    ai_finite.open(ai_finite_device_cfg)
    yield ai_finite
    ai_finite.stop()


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))
    utils.setup_stream_logger(logging.getLogger(), logging.DEBUG)


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_default_devname(ai_device):
    assert ai_device.devname == f'{DEVICE_UNDER_TEST}/ai'


def test_devname_1ch(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    assert ai_device.devname == f'{DEVICE_UNDER_TEST}/ai0'


def test_devname_2ch_consecutive(ai_device, ai_channel_config):
    ai_channel_config2 = pyAI.AIChannelConfig(name='2nd AI Channel')
    ai_channel_config2.line = 1
    ai_device.add_channel(ai_channel_config)
    ai_device.add_channel(ai_channel_config2)
    assert ai_device.devname == f'{DEVICE_UNDER_TEST}/ai0,{DEVICE_UNDER_TEST}/ai1'
    assert list(ai_device.ai_channels.keys()) == [ai_channel_config.name, ai_channel_config2.name]


def test_devname_2ch_nonconsecutive(ai_device, ai_channel_config):
    ai_channel_config2 = pyAI.AIChannelConfig(name='2nd AI Channel')
    ai_channel_config2.line = 2
    ai_device.add_channel(ai_channel_config)
    ai_device.add_channel(ai_channel_config2)
    assert ai_device.devname == f'{DEVICE_UNDER_TEST}/ai0,{DEVICE_UNDER_TEST}/ai2'
    assert list(ai_device.ai_channels.keys()) == [ai_channel_config.name, ai_channel_config2.name]


def test_is_not_open(ai_device):
    assert not ai_device.is_open()


def test_isopen(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    assert ai_device.is_open()


def test_isopen_remove(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    ai_device.remove_channel(ai_channel_config.name)
    assert not ai_device.is_open()


def test_remove_channel(ai_device, ai_channel_config):
    ai_channel_config2 = pyAI.AIChannelConfig(name='2nd AI Channel')
    ai_channel_config2.line = 2
    ai_device.add_channel(ai_channel_config)
    ai_device.add_channel(ai_channel_config2)
    ai_device.remove_channel(ai_channel_config.name)
    assert list(ai_device.ai_channels.keys()) == [ai_channel_config2.name]


def test_is_acquiring(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    assert not ai_device.is_acquiring
    ai_device.start()
    assert ai_device.is_acquiring
    ai_device.stop()
    assert not ai_device.is_acquiring


def test_get_channel(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    ch = ai_device.ai_channels[ai_channel_config.name]
    assert isinstance(ch, pyAI.AIChannel)
    assert ch.cfg == ai_channel_config


def test_getdata(ai_device, ai_channel_config):
    ai_channel_config.cal_pt1_reading = 0
    ai_channel_config.cal_pt1_target = 0
    ai_channel_config.cal_pt2_reading = 1
    ai_channel_config.cal_pt2_target = 1
    ai_device.add_channel(ai_channel_config)
    ai_device.start()
    sleep(4.0)

    data, t = ai_device.ai_channels[ai_channel_config.name].get_data()
    assert len(data) > 0 and type(t) is float
    ai_device.stop()


def test_getdata_finite(ai_finite, ai_channel_config):
    ai_channel_config.cal_pt1_reading = 0
    ai_channel_config.cal_pt1_target = 0
    ai_channel_config.cal_pt2_reading = 1
    ai_channel_config.cal_pt2_target = 1
    ai_finite.add_channel(ai_channel_config)
    ai_finite.start()
    sleep(2.0)
    assert ai_finite.is_done()
    data, t = ai_finite.ai_channels[ai_channel_config.name].get_data()
    assert len(data) == 17
