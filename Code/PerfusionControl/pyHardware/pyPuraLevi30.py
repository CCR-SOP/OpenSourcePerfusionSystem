""" Class for controlling PuraLev i30 Pump

Uses minimalmodbus
Based on Firmware H2.48 R03 document provided by Levitronix

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import logging
from dataclasses import dataclass, field
from typing import List
from enum import IntEnum
from queue import Queue, Empty

import minimalmodbus as modbus
import serial
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.utils import get_epoch_ms


BROADCAST_ADDR = 0x0


class PumpState(IntEnum):
    Off = 1
    SpeedControl = 2
    ProcessControl = 3
    SpeedSafetyControl = 7
    ProcessSafetyControl = 8
    Error = 4


class RegisterMode(IntEnum):
    WriteSingle = 0x06
    WriteMultiple = 0x10


@dataclass
class Register:
    addr: int = 0x0
    word_len: int = 1
    scaling: float = 1.0


# Taken from page 31 Section 2.3.2.4.1 of Firmware H2.48 docs
ReadRegisters = {
             'ID': Register(addr=0x3FE0, word_len=5),
             'DeviceType': Register(addr=0x3FE5),
             'FW': Register(addr=0x3FE6, word_len=8),
             'SN': Register(addr=0x3FEE),
             'State': Register(addr=0x4000),
             'ActualSpeed': Register(addr=0x4001),
             'ActualProcess': Register(addr=4002, scaling=0.01),
             'SetpointSpeed': Register(addr=0x4003),
             'SetpointProcess': Register(addr=0x4004, scaling=0.01),
             'Error': Register(addr=0x4005),
             'Warning': Register(addr=0x4006),
             'Message': Register(addr=4007),
             'DriverTemp': Register(addr=0x4008),
             'ImpellerZ': Register(addr=0x4009),
             'LastError': Register(addr=0x400A),
             'LastWarning': Register(addr=0x4006),
             'LastMessage': Register(addr=4007),
             'BearingPhaseV': Register(addr=0x400D, scaling=7.123/32767),
             'BearingPhaseW': Register(addr=0x400E, scaling=7.123/32767),
             'DrivePhaseV': Register(addr=0x400F, scaling=15/32767),
             'DrivePhaseW': Register(addr=0x4010, scaling=15/32767),
             'SupplyVoltage': Register(addr=0x40011, scaling=0.1),
             'PLCAnalogInput1': Register(addr=0x4012, scaling=0.002),
             'PLCAnalogInputCal1': Register(addr=0x4012, scaling=0.002),
             'PLCAnalogInputPercent1': Register(addr=0x4014, scaling=0.0125),
             'PLCAnalogInput2': Register(addr=0x4015, scaling=0.001),
             'PLCAnalogInputCal2': Register(addr=0x4016, scaling=0.001),
             'PLCAnalogInputPercent2': Register(addr=0x4017, scaling=0.01),
             'PLCProcessValue': Register(addr=0x4018, scaling=0.01),
             'PLCSetpointSpeed': Register(addr=0x4019),
             'PLCSetpointProcess': Register(addr=0x401A, scaling=0.01),
             'PLCAnalogOutput': Register(addr=0x401B, scaling=0.01),
             'PLCDigitalInput1': Register(addr=0x401C),
             'PLCDigitalInput2': Register(addr=0x401D),
             'PLCDigitalOutput1': Register(addr=0x401E),
             'PLCDigitalOutput2': Register(addr=0x401F),
             'BufferedError': Register(addr=0x4020),
             'BufferedWarning': Register(addr=0x4021),
             'BufferedMessage': Register(addr=0x4022)
             }


WriteRegisters = {
             'State': Register(addr=0x4000),
             'SetpointSpeed': Register(addr=0x4001),
             'SetpointProcess': Register(addr=0x4002, scaling=0.01),
             'Baud': Register(addr=0x4005),
             'DeviceAddress': Register(addr=0x4006),
             'InterframeTimeout': Register(addr=4007, scaling=0.2284148),
             'ActivateSettings': Register(addr=0x4008),
             'AnalogInputAssignment': Register(addr=0x4009),
             'AnalogOutputAssignment': Register(addr=0x400A),
             'DigitalOutput1Logic': Register(addr=0x400B),
             'DigitalOutput1Config': Register(addr=0x400C),
             'DigitalOutput2Logic': Register(addr=0x400D),
             'DigitalOutput2Config': Register(addr=0x400E),
             'CustomDigitalOutputConfig': Register(addr=0x400F)
             }


@dataclass
class PuraLevi30Config:
    name: str = 'i30'
    port: str = ''
    baud: int = 57600
    serial_num: str = 'nnnnnn-nnnn'
    device_addr: int = 0


class PuraLevi30:
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        self.name = name
        self.hw = None
        self.cfg = PuraLevi30Config(name=name)

        self._queue = None
        self.acq_start_ms = 0

        self.data_type = np.uint32

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.cfg.name, self.cfg)

    def read_config(self):
        self._lgr.debug(f'Reading config for {self.cfg.name}')
        PerfusionConfig.read_into_dataclass('hardware', self.cfg.name, self.cfg)
        self._lgr.debug(f'Config = {self.cfg}')
        self.open()

    def open(self, cfg=None):
        self._lgr.debug(f'Attempting to open {self.name} with config {cfg}')
        if cfg is not None:
            self.cfg = cfg
        if self.cfg.port != '':
            self._lgr.debug(f'Opening modbus instrument at {self.cfg.port}')
            self.hw = modbus.Instrument(self.cfg.port, 1, modbus.MODE_RTU, debug=False)
            self.hw.serial.baudrate = self.cfg.baud
            self.hw.serial.bytesize = 8
            self.hw.serial.parity = serial.PARITY_EVEN
            self.hw.serial.stopbits = 1
            self.hw.serial.timeout = 3
        self._queue = Queue()

    def close(self):
        if self.hw:
            self.hw.serial.close()
            self.stop()

    def start(self):
        self.acq_start_ms = get_epoch_ms()

    def stop(self):
        reg = WriteRegisters['State']
        self.hw.write_register(reg, PumpState.Off)

    def set_speed(self, rpm: int):
        reg = WriteRegisters['SetpointSpeed']
        self.hw.write_register(reg.addr, rpm)
        reg = WriteRegisters['State']
        self.hw.write_register(reg, PumpState.SpeedControl)

    def set_flow(self, percent_of_max: float):
        reg = WriteRegisters['SetpointProcess']
        self.hw.write_register(reg.addr, int(percent_of_max*100))
        reg = WriteRegisters['State']
        self.hw.write_register(reg, PumpState.SpeedControl)

    def get_speed(self) -> int:
        reg = ReadRegisters['SetpointSpeed']
        rpm = self.hw.read_register(reg.addr)
        return rpm

    def get_flow(self) -> float:
        reg = ReadRegisters['SetpointProcess']
        percent = self.hw.read_register(reg.addr)
        return percent / 100.0

    def get_data(self):
        buf = None
        t = None
        try:
            buf, t = self._queue.get(timeout=1.0)
        except Empty:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t
