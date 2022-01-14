# -*- coding: utf-8 -*-
"""Unit test for pyMQTT class

This requires the underlying MQTT broker to be running

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
import pytest
import time
from unittest.mock import Mock

import pyPerfusion.pyMQTT as pyMQTT


@pytest.fixture
def pub():
    pub = pyMQTT.AlarmPublisher()
    pub.connect()
    yield pub
    pub.close()


@pytest.fixture
def sub():
    sub = pyMQTT.AlarmSubscriber()
    sub.connect()
    yield sub
    sub.close()


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_msg_creation():
    msg = pyMQTT.Msg()
    assert msg.name == 'None'


def test_pub_creation():
    pub = pyMQTT.AlarmPublisher()
    assert pub.is_open() is False


def test_sub_creation():
    sub = pyMQTT.AlarmSubscriber()
    assert sub.is_open() is False


def test_pub_connection():
    pub = pyMQTT.AlarmPublisher()
    pub.connect()
    assert pub.is_open() is True
    pub.close()
    assert pub.is_open() is False


def test_sub_connection():
    sub = pyMQTT.AlarmSubscriber()
    sub.connect()
    assert sub.is_open() is True
    sub.close()
    assert sub.is_open() is False


def test_pub_sub(pub, sub):
    cb = Mock()
    sub.set_callback(cb)
    sub.subscribe('test')
    pub.publish('test', 'abc')
    time.sleep(1.0)
    cb.assert_called_with('test', b'abc')
