# -*- coding: utf-8 -*-
"""Unit test for pyAI module

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import os

import pyHardware.pyAI as pyAI
import pyPerfusion.PerfusionConfig as PerfusionConfig


CHANNEL1_NAME = 'Hepatic Artery Pressure'
CHANNEL2_NAME = 'Portal Vein Pressure'

@pytest.fixture
def delete_file(filename):
    os.remove(filename)


@pytest.fixture
def ai_device_cfg():
    ai_device_cfg = pyAI.AIDeviceConfig(device_name='FauxDev0',
                                        sampling_period_ms=200,
                                        read_period_ms=1000)
    yield ai_device_cfg


@pytest.fixture
def ai_device(ai_device_cfg):
    ai_device = pyAI.AIDevice(name='Dev1')
    ai_device.open(ai_device_cfg)
    yield ai_device
    ai_device.close()


@pytest.fixture
def ai_channel_config():
    ai_channel_config = pyAI.AIChannelConfig()
    yield ai_channel_config


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))
    PerfusionConfig.set_test_config()


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_default_devname(ai_device):
    assert ai_device.devname == 'ai'


def test_devname_1ch(ai_device, ai_channel_config):
    ai_device.add_channel(ch_name=CHANNEL1_NAME, cfg=ai_channel_config)
    assert ai_device.devname == 'ai0'


def test_devname_2ch_consecutive(ai_device, ai_channel_config):
    ai_channel_config2 = pyAI.AIChannelConfig()
    ai_device.add_channel(ch_name=CHANNEL1_NAME, cfg=ai_channel_config)
    ai_device.add_channel(ch_name=CHANNEL2_NAME, cfg=ai_channel_config2)
    assert ai_device.devname == 'ai0,ai1'


def test_devname_2ch_nonconsecutive(ai_device, ai_channel_config):
    ai_channel_config2 = pyAI.AIChannelConfig()
    ai_device.add_channel(ch_name=CHANNEL1_NAME, cfg=ai_channel_config)
    ai_device.add_channel(ch_name=CHANNEL2_NAME, cfg=ai_channel_config2)
    ai_channel_config2.line = 2
    assert ai_device.devname == 'ai0,ai2'


def test_is_not_open(ai_device):
    assert not ai_device.is_open()


def test_isopen(ai_device, ai_channel_config):
    ai_device.add_channel(ch_name=CHANNEL1_NAME, cfg=ai_channel_config)
    assert ai_device.is_open()


def test_isopen_remove(ai_device, ai_channel_config):
    ai_device.add_channel(ch_name=CHANNEL1_NAME, cfg=ai_channel_config)
    ai_device.remove_channel(ch_name=CHANNEL1_NAME)
    assert ai_device.is_open()
