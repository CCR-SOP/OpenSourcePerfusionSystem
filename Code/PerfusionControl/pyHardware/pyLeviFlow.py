""" Class for controlling Levitronix LeviFlow sensor

Uses minimalmodbus
Based on LEVIFLOWTM LFSC-IX MODBUS INTERFACE document provided by Levitronix

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

import logging
from dataclasses import dataclass
from enum import IntEnum
from queue import Queue, Empty
from threading import Lock, Thread, Event

import minimalmodbus as modbus
import serial
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyHardware.pyGeneric as pyGeneric


class LeviFlowException(pyGeneric.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


EquipmentStatusBits = IntEnum('EquipmentStatusBits',
                              ['Bubble Detected', 'MeasurementError', 'ReverseFlow',
                               'VolumeCounterPulseSetError', 'ZeroAdjustmentActive',
                               'ZeroAdjustmentError', 'UnusedBit6', 'UnusedBit7',
                               'FlowAlarmHigh', 'FlowAlarmLow', 'VolumeCounterAlarmH',
                               'VolumeCounterAlarmHH', 'OutputTest', 'UnusedBit13',
                               'UnusedBit14', 'FirmwareUpdateActive'
                               ], start=0)


class ModbusFunction(IntEnum):
    HoldRegister = 3
    InputRegister = 4


class ControlBits(IntEnum):
    ZeroAdjust = 0
    Reset = 2
    FactorySetting = 5


class SensorType(IntEnum):
    i06 = 100
    i10 = 101
    i14 = 103
    i16 = 104
    i19 = 105
    i25 = 106
    i35 = 107


class FlowLevelOnMeasurementOptions(IntEnum):
    ZeroOutput = 0
    PercentMinus25 = 1
    Percent105 = 2
    Hold = 3


class DigitalInputSettings(IntEnum):
    VolumeCounterReset = 0
    ZeroAdjust = 1
    InverseFlow = 2


class AnalogOutputSettingBits(IntEnum):
    Out1 = 0
    Out2 = 8


class VolumeCounterBaseUnits(IntEnum):
    mL = 0
    L = 1
    m3 = 2


DigitOutputSetting = IntEnum('DigitOutputSetting',
                              ['FlowAlarmHigh', 'FlowAlarmLow',
                               'VolumeCounterAlarmH', 'VolumeCounterAlarmHH',
                               'VolumeCounterPulse', 'MeasurementError',
                               'FlowAsFrequency', 'BubbleDetect', 'Custom Value'
                               ], start=0)


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
             'EquipmentStatus': Register(addr=0),
             'CurrentFlowRate': Register(addr=1, scaling=0.01),
             'VolumePulseCounter': Register(addr=2, word_len=2),
             'Temperature': Register(addr=6, scaling=0.01),
             'SignalStrength': Register(addr=8, scaling=1, word_len=2),
             'Flow': Register(addr=8, word_len=2),
             }

WriteRegisters = {
             'Control': Register(addr=0),
             'SensorType': Register(addr=1),
             'FullScale': Register(addr=2, word_len=2, scaling=0.001),
             'K-factor': Register(addr=6, scaling=0.001),
             'DampingTime': Register(addr=7, scaling=0.1),
             'LowCutoff': Register(addr=8, scaling=0.1),
             'MeasurementErrorIgnoreTime': Register(addr=9),
             'FlowLevelOnMeasurementError': Register(addr=10),
             'BubbleDetectHoldTime': Register(addr=11),
             'DigitalOutput1Logic': Register(addr=12),
             'DigitalOutput2Logic': Register(addr=13),
             'AGCControl': Register(addr=14),
             'DigitalInputSetting': Register(addr=15),
             'AnalogOutputSetting': Register(addr=16),
             'DigitalOutput1Setting': Register(addr=17),
             'DigitalOutput2Setting': Register(addr=18),
             'FlowAlarmHighValue': Register(addr=19, scaling=0.1),
             'FlowAlarmLowValue': Register(addr=20, scaling=0.1),
             'AlarmHysteresis': Register(addr=21, scaling=0.1),
             'VolumeCounterEnable': Register(addr=24),
             'VolumeCounterReset': Register(addr=25),
             'VolumeCounterBaseUnit': Register(addr=26),
             'VolumeCounterMultiplierFactor': Register(addr=27),
             'SerialNumber': Register(addr=119),
             'Version': Register(addr=4097, word_len=2),
            }


@dataclass
class LeviFlowConfig:
    port: str = ''
    baud: int = 57600
    device_addr: int = 0
    sampling_period_ms: int = 1_000


class LeviFlow(pyGeneric.GenericDevice):
    def __init__(self, name):
        super().__init__(name)
        self.cfg = LeviFlowConfig()
        self.hw = None

        self.mutex = Lock()

        self.buffer = np.zeros(1, dtype=self.data_dtype)
        self._evt_halt = Event()
        self.__thread = None
        self.is_streaming = False
        self._timeout = 1.0

    @property
    def sampling_period_ms(self):
        if self.cfg:
            val = self.cfg.sampling_period_ms
        else:
            val = 0
        return val

    def open(self):
        self._lgr.debug(f'Attempting to open {self.name} with config {self.cfg}')
        self._queue = Queue()
        if self.cfg.port != '':
            self._lgr.info(f'{self.name}: Opening LeviFlow at {self.cfg.port}')
            try:
                with self.mutex:
                    self.hw = modbus.Instrument(self.cfg.port, 1, modbus.MODE_RTU, debug=False)
                    self.hw.serial.baudrate = self.cfg.baud
                    self.hw.serial.bytesize = 8
                    self.hw.serial.parity = serial.PARITY_EVEN
                    self.hw.serial.stopbits = 1
                    self.hw.serial.timeout = 3
            except serial.serialutil.SerialException as e:
                self._lgr.error(f'{self.name}: Could not open instrument using port {self.cfg.port}.'
                                f'Exception: {e}')
                raise LeviFlowException(f'Could not open LeviFlow {self.name} - {self.cfg}')

    def close(self):
        if self.hw:
            with self.mutex:
                self.hw.serial.close()
            self.stop()

    def start(self):
        super().start()
        self._evt_halt.clear()
        self.acq_start_ms = utils.get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'{__name__} {self.name}'
        self.__thread.start()

    def stop(self):
        if self.is_streaming:
            self._evt_halt.set()
            self.__thread.join(2.0)
            self.__thread = None
            super().stop()

    def run(self):
        while not PerfusionConfig.MASTER_HALT.is_set():
            period_timeout = self.cfg.sampling_period_ms / 1_000.0
            if not self._event_halt.wait(timeout=period_timeout):
                self._acq_samples()

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

    def clear(self):
        with self.mutex:
            self._queue.queue.clear()

    def _acq_samples(self):
        buffer_t = utils.get_epoch_ms()
        self.buffer[0] = self.get_flow()
        self._queue.put((self.buffer, buffer_t))

    def get_flow(self):
        flow = 0
        if self.hw:
            with self.mutex:
                reg = ReadRegisters['Flow']
                flow = self.hw.read_long(reg.addr, functioncode=ModbusFunction.InputRegister)
        return flow / 1000.0

    def get_version(self):
        val = 0
        if self.hw:
            with self.mutex:
                reg = WriteRegisters['Version']
                val = self.hw.read_long(reg.addr, functioncode=ModbusFunction.HoldRegister)
        return val

    def get_sn(self):
        val = 0
        if self.hw:
            with self.mutex:
                reg = WriteRegisters['SerialNumber']
                val = self.hw.read_string(reg.addr, functioncode=ModbusFunction.HoldRegister, number_of_registers=8)
        return val

    def get_sensor_type(self):
        val = 0
        if self.hw:
            with self.mutex:
                reg = WriteRegisters['SensorType']
                val = self.hw.read_register(reg.addr, functioncode=ModbusFunction.HoldRegister)
        return val

    def get_parameter(self, param):
        val = 0
        if self.hw:
            with self.mutex:
                reg = ReadRegisters[param]
                val = self.hw.read_long(reg.addr, functioncode=ModbusFunction.HoldRegister)
        return val


class MockLeviFlow(pyGeneric.GenericDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self.flow = 0

    def read_register(self, addr, number_of_decimals=0):
        pass

    def write_register(self, addr, value):
        pass

    def read_long(self, addr):
        if addr == ReadRegisters['Flow'].addr:
            rand = np.random.random_sample() * 10_000
            return self.flow + rand

    def write_long(self, addr, value):
        pass
