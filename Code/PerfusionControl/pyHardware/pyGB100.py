""" Class for controlling MCQ Instruments GB100 gas mixer

Uses minimalmodbus directly instead of using MCQ Python Library

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
from threading import Lock
from time import sleep

import minimalmodbus as modbus
import serial
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyHardware.pyGeneric as pyGeneric


class GasDeviceException(pyGeneric.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


# addresses are taken from Gas Blender GB3000 series Modbus communication protocol manual
ChannelAddr = [10, 25, 40, 55, 70, 85]


class WriteAddr(IntEnum):
    IdxChannelBalance = 6
    TotalFlow = 7
    WorkingStatus = 9


# Ordering of values saved to queue (and Sensor). Can be used by a reader to easily select
# the right index for the variable of interest
ReaderIndex = IntEnum('ReaderIndex',
                      ['Status', 'TotalFlow', 'Ch1Percent', 'Ch2Percent', 'Ch3Percent'], start=0)


# names and ordering are taken from Gas Blender GB3000 series Modbus communication protocol manual
MainBoardOffsets = IntEnum('MainBoardOffsets',
                           ['FW Version', 'HW Version', 'Status', 'Alert',
                            'Temperature', 'Number of channels', 'Idx channel balance',
                            'Total flow', 'dummy', 'Working status'],
                           start=0)


# names and ordering are taken from Gas Blender GB3000 series Modbus communication protocol manual
ChannelRegisterOffsets = IntEnum('ChannelRegisterOffsets',
                                 ['FW Version', 'HW Version', 'Alert',
                                  'ID gas - calibration', 'K factor - calibration',
                                  'Channel Enabled', 'Percent value', 'Id gas',
                                  'K factor gas', 'SCCM', 'sccmdummy', 'Target SCCM',
                                  'targetsccmdummy', 'SCCM AV'],
                                  start=0)


# The names and order need to match the GB100 instrument
GasNames = IntEnum('GasNames', ['Air', 'Nitric Oxide', 'Nitrogen', 'Oxygen',
                                'Carbon Dioxide', 'Argon', 'Methane', 'Ethylene',
                                'Ethane', 'Hydrogen', 'Helium', 'Sulfur Exafluoride',
                                'Propane', 'Butane', 'DME'],
                   start=0)


def get_gas_index(gas_name: str):
    return [gas.value for gas in GasNames if gas.name == gas_name][0]


@dataclass
class GasDeviceConfig:
    port: str = ''
    flow_limits: List = field(default_factory=lambda: [0, 100])


class GasDevice(pyGeneric.GenericDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = GasDeviceConfig()

        self.baud = 115200
        self.mutex = Lock()
        self.hw = None

        self.total_flow = 0
        self.last_flow = 0
        # assume a max of 3 channels
        self.percent = [0, 0, 0]
        self.status = False

    def open(self):
        super().open()
        if self.cfg.port != '':
            self._lgr.info(f'Opening GB100 gas mixer at {self.cfg.port}')
            try:
                with self.mutex:
                    self.hw = modbus.Instrument(self.cfg.port, 1, modbus.MODE_RTU, debug=False)
                    self.hw.serial.baudrate = self.baud
                    self.hw.serial.bytesize = 8
                    self.hw.serial.parity = serial.PARITY_NONE
                    self.hw.serial.stopbits = 1
                    self.hw.serial.timeout = 3
            except serial.serialutil.SerialException as e:
                self._lgr.error(f'Could not open instrument using port {self.cfg.port}.'
                                f'Exception: {e}')
                raise GasDeviceException('Could not open gas device')

    def close(self):
        if self.hw:
            with self.mutex:
                self.hw.serial.close()
            self.stop()
        super().close()

    # channel id's are assumed to start numbering at 1 to match GB100 notation
    def get_gas_type(self, channel_num: int) -> str:
        gas_type = 'NA'
        if self.hw is not None:
            with self.mutex:
                addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Id gas'].value
                gas_id = self.hw.read_register(addr)

            try:
                gas_type = GasNames(gas_id).name
            except IndexError:
                self._lgr.error(f'Channel {channel_num} at addr {addr} has invalid gas id {gas_id}')
        return gas_type

    def get_total_channels(self):
        channels = 0
        if self.hw is not None:
            with self.mutex:
                channels = self.hw.read_register(MainBoardOffsets['Number of channels'].value)
        return channels

    def get_total_flow(self) -> int:
        flow = 0
        if self.hw is not None:
            with self.mutex:
                flow = self.hw.read_long(MainBoardOffsets['Total flow'].value)
                self.total_flow = flow
        return flow

    def adjust_flow(self, adjust_flow: int):
        flow = self.get_total_flow()
        self.set_total_flow(flow + adjust_flow)

    def cancel_flow(self):
        self.set_total_flow(0)

    def resume_flow(self):
        flow = self.get_total_flow()
        self.set_total_flow(flow + 5)


    def bolus_CO2(self):
        self.set_percent_value(2, 100)

    def bolus_O2(self):
        self.set_percent_value(1, 100)

    def set_total_flow(self, total_flow: int):
        if self.hw is not None:
            if total_flow < self.cfg.flow_limits[0]:
                total_flow = self.cfg.flow_limits[0]
                self._lgr.warning(f'Attempt set flow {total_flow} '
                                  f'lower than limit {self.cfg.flow_limits[0]}. '
                                  f'Flow being set to limit.')
            if total_flow > self.cfg.flow_limits[1]:
                total_flow = self.cfg.flow_limits[1]
                self._lgr.warning(f'Attempt set flow {total_flow} '
                                  f'higher than limit {self.cfg.flow_limits[1]}. '
                                  f'Flow being set to limit.')
            with self.mutex:
                addr = MainBoardOffsets['Total flow'].value

                self.hw.write_long(addr, int(total_flow))
                self.total_flow = total_flow
                self._lgr.info(f'Total flow changed to {int(total_flow)}')
                self.push_data()

    def get_percent_value(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            if 0 <= channel_num <= 3:
                with self.mutex:
                    addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Percent value'].value
                    value = self.hw.read_register(addr, number_of_decimals=2)
                    self.percent[channel_num - 1] = value
            else:
                self._lgr.warning(f'Attempt to read percent value from unsupported channel {channel_num}')

        return value

    def set_percent_value(self, channel_num: int, new_percent: float):
        gas_name = self.get_gas_type(1)
        if self.hw is not None:
            if 0 <= channel_num <= 3:
                if new_percent < 0:
                    new_percent = 0
                    self._lgr.warning(f'Attempt to set channel {channel_num} percent to '
                                      f'{new_percent}. Capping at 0')
                if new_percent > 100:
                    new_percent = 100
                    self._lgr.warning(f'Attempt to set channel {channel_num} percent to '
                                      f'{new_percent}. Capping at 100')
                with self.mutex:
                    addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Percent value'].value
                    # self._lgr.debug(f'requesting new percent {new_percent}')
                    percent = int(new_percent * 100)
                    # self._lgr.debug(f'writing {percent}')
                    self.hw.write_register(addr, percent)
                    self._lgr.info(f'Setting {gas_name} channel to {100 - percent/100} %')
                    self.push_data()
            else:
                self._lgr.warning(f'Attempt to set percent value from unsupported channel {channel_num}')

    def get_sccm(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            if 0 <= channel_num <= 3:
                with self.mutex:
                    addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['SCCM'].value
                    value = self.hw.read_long(addr)
                    value /= 100
            else:
                self._lgr.warning(f'Attempt to get sccm value from unsupported channel {channel_num}')

        return value

    def get_sccm_av(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            if 0 <= channel_num <= 3:
                with self.mutex:
                    addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['SCCM AV'].value
                    value = self.hw.read_long(addr)
                    value /= 100
            else:
                self._lgr.warning(f'Attempt to get sccm_av value from unsupported channel {channel_num}')

        return value

    def get_target_sccm(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            if 0 <= channel_num <= 3:
                with self.mutex:
                    addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Target SCCM'].value
                    value = self.hw.read_long(addr)
                    value /= 100
            else:
                self._lgr.warning(f'Attempt to get target sccm value from unsupported channel {channel_num}')


        return value

    def get_working_status(self):
        status_on = False
        if self.hw is not None:
            with self.mutex:
                addr = MainBoardOffsets['Working status'].value
                status_on = self.hw.read_register(addr) == 1
                self.status = status_on
        return status_on

    def set_working_status(self, turn_on: bool):
        if self.hw is not None:
            with self.mutex:
                addr = MainBoardOffsets['Working status'].value
                self.hw.write_register(addr, int(turn_on))
                self.status = turn_on
                self.push_data()

    def push_data(self):
        if self._queue:
            buf = self.data_dtype.type([self.status, self.total_flow, self.percent[0], self.percent[1], self.percent[2]])
            self._queue.put((buf, utils.get_epoch_ms()))


class MockGasDevice(GasDevice):
    def __init__(self, name: str):
        super().__init__(name)

    def open(self, cfg=None):
        if cfg is not None:
            self.cfg = cfg
        self._queue = Queue()
        self.hw = MockGB100()

    def close(self):
        if self.hw:
            self.stop()


class MockGB100:
    def __init__(self):
        self.name = 'MockGB100'
        self.total_flow = 0
        self.percent = [0, 0]
        self.status = False

    def read_register(self, addr, number_of_decimals=0):
        if addr == ChannelAddr[0] + ChannelRegisterOffsets['Id gas'].value:
            return 3
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Id gas'].value:
            return 4
        elif addr == MainBoardOffsets['Number of channels'].value:
            return 2
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['Percent value'].value:
            return self.percent[0] / 100
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Percent value'].value:
            return self.percent[1] / 100
        elif addr == MainBoardOffsets['Working status'].value:
            return self.status

    def write_register(self, addr, value):
        if addr == MainBoardOffsets['Working status'].value:
            self.status = bool(value)
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['Percent value'].value:
            self.percent[0] = value
            self.percent[1] = 10_000 - value
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Percent value'].value:
            self.percent[1] = value
            self.percent[0] = 10_000 - value

    def read_long(self, addr):
        if addr == MainBoardOffsets['Total flow'].value:
            return self.total_flow
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['Target SCCM'].value:
            return self.total_flow * (self.percent[0] / 100)
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Target SCCM'].value:
            return self.total_flow * (self.percent[1] / 100)
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['SCCM'].value:
            return self.total_flow * (self.percent[0] / 100)
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['SCCM'].value:
            return self.total_flow * (self.percent[1] / 100)
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['SCCM AV'].value:
            return self.total_flow * (self.percent[0] / 100)
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['SCCM AV'].value:
            return self.total_flow * (self.percent[1] / 100)

    def write_long(self, addr, value):
        if addr == MainBoardOffsets['Total flow'].value:
            self.total_flow = value
