# -*- coding: utf-8 -*-
"""Unit test for pyAI module

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import os

import pyHardware.pyAI as pyAI


@pytest.fixture
def delete_file(filename):
    os.remove(filename)


@pytest.fixture
def ai_device_cfg():
    ai_device_cfg = pyAI.AIDeviceConfig(name='PyTest AIDevice',
                                        device_name='FauxDev0',
                                        sampling_period_ms=200,
                                        read_period_ms=1000)
    yield ai_device_cfg


@pytest.fixture
def ai_device(ai_device_cfg):
    ai_device = pyAI.AIDevice()
    ai_device.open(ai_device_cfg)
    yield ai_device
    ai_device.close()


@pytest.fixture
def ai_channel_config():
    ai_channel_config = pyAI.AIChannelConfig(name='PyTest AIChannel')
    yield ai_channel_config


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_default_devname(ai_device):
    assert ai_device.devname == 'ai'


def test_devname_1ch(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    assert ai_device.devname == 'ai0'


def test_devname_2ch_consecutive(ai_device, ai_channel_config):
    ai_channel_config2 = pyAI.AIChannelConfig(name='2nd AI Channel')
    ai_channel_config2.line = 1
    ai_device.add_channel(ai_channel_config)
    ai_device.add_channel(ai_channel_config2)
    assert ai_device.devname == 'ai0,ai1'


def test_devname_2ch_nonconsecutive(ai_device, ai_channel_config):
    ai_channel_config2 = pyAI.AIChannelConfig(name='2nd AI Channel')
    ai_channel_config2.line = 2
    ai_device.add_channel(ai_channel_config)
    ai_device.add_channel(ai_channel_config2)
    assert ai_device.devname == 'ai0,ai2'


def test_is_not_open(ai_device):
    assert not ai_device.is_open()


def test_isopen(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    assert ai_device.is_open()


def test_isopen_remove(ai_device, ai_channel_config):
    ai_device.add_channel(ai_channel_config)
    ai_device.remove_channel(ai_channel_config.name)
    assert not ai_device.is_open()
