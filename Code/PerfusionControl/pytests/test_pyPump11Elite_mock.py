# -*- coding: utf-8 -*-
""" Unit test for PHDSerial class with SensorStream using mocks

Used to verify that action data is saved properly and basic
error handling works as expected

requires pytest-mock package to be installed

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import os

import pyHardware.pyPump11Elite as pyPump11Elite


@pytest.fixture
def delete_file(filename):
    os.remove(filename)


@pytest.fixture
def syringe(mocker):
    syringe = pyPump11Elite.Pump11Elite(name='UnitTest')
    # mocker.patch("pyPerfusion.pyPump11Elite.Pump11Elite.send_wait4response", return_value='0 0')
    syringe.open('COM1', 9600)
    yield syringe
    mocker.patch("pyPerfusion.pyPump11Elite.Pump11Elite.send_wait4response", return_value='0 0')
    syringe.close()


def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_open(syringe, mocker):
    mocker.patch("pyPerfusion.pyPump11Elite.Pump11Elite.is_open", return_value=True)
    assert syringe.is_open() is True

def test_record_targeted_infusion(syringe, mocker):
    syringe.set_infusion_rate(rate_ul_min=10)
    syringe.set_target_volume(volume_ul=100)

    mocker.patch("pyPerfusion.pyPump11Elite.Pump11Elite.get_target_volume",
                 return_value=(100, 'ul'))
    mocker.patch("pyPerfusion.pyPump11Elite.Pump11Elite.get_infusion_rate",
                 return_value=(10, 'ul/min'))

    syringe.infuse_to_target_volume()
    data, t = syringe.get_data()
    assert data[0] == 100 and data[1] == 10


