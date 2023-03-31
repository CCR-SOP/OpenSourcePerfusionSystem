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

import minimalmodbus as modbus
import serial
import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.utils import get_epoch_ms


class GasDeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


# addresses are taken from Gas Blender GB3000 series Modbus communication protocol manual
ChannelAddr = [10, 25, 40, 55, 70, 85]


class WriteAddr(IntEnum):
    IdxChannelBalance = 6
    TotalFlow = 7
    WorkingStatus = 9


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
    name: str = 'GasDevice'
    port: str = ''
    CO2_range: List = field(default_factory=lambda: [0, 100])
    O2_range: List = field(default_factory=lambda: [0, 100])
    pH_range: List = field(default_factory=lambda: [0, 100])
    flow_limits: List = field(default_factory=lambda: [5, 250])


class GasDevice:
    def __init__(self, name):
        self._lgr = logging.getLogger(__name__)
        self.name = name
        self.hw = None
        self.cfg = GasDeviceConfig(name=name)
        

        self._queue = None
        self.acq_start_ms = 0
        self.baud = 115200

        self.data_type = np.uint32

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def write_config(self):
        PerfusionConfig.write_from_dataclass('hardware', self.cfg.name, self.cfg)

    def read_config(self):
        self._lgr.debug(f'Reading config for {self.cfg.name}')
        PerfusionConfig.read_into_dataclass('hardware', self.cfg.name, self.cfg)
        self._lgr.debug(f'Config = {self.cfg}')
        # update the valid_range attribute to a list of integers
        # as it will be read in as a list of characters
        self.cfg.CO2_range = [int(x) for x in ''.join(self.cfg.CO2_range).strip(' ').split(',')]
        self.cfg.O2_range = [int(x) for x in ''.join(self.cfg.O2_range).strip(' ').split(',')]
        self.cfg.pH_range = [float(x) for x in ''.join(self.cfg.pH_range).strip(' ').split(',')]
        self._lgr.debug(f'CO2_range is {self.cfg.CO2_range}, O2_range is {self.cfg.O2_range}, ph_range is {self.cfg.pH_range}')
        self.open()

    def open(self, cfg=None):
        self._lgr.debug(f'Attempting to open {self.name} with config {cfg}')
        if cfg is not None:
            self.cfg = cfg
        if self.cfg.port != '':
            self._lgr.info(f'Opening GB100 gas mixer at {self.cfg.port}')
            try:
                self.hw = modbus.Instrument(self.cfg.port, 1, modbus.MODE_RTU, debug=False)
                self.hw.serial.baudrate = self.baud
                self.hw.serial.bytesize = 8
                self.hw.serial.parity = serial.PARITY_NONE
                self.hw.serial.stopbits = 1
                self.hw.serial.timeout = 3
            except serial.serialutil.SerialException as e:
                self._lgr.error(f'{self.name}: Could not open instrument using port {self.cfg.port}.'
                                f'Exception: {e}')
                raise GasDeviceException('Could not open gas device')
        self._queue = Queue()

    def close(self):
        if self.hw:
            self.hw.serial.close()
            self.stop()

    def start(self):
        self.acq_start_ms = get_epoch_ms()

    def stop(self):
        pass

    # channel id's are assumed to start numbering at 1 to match GB100 notation
    def get_gas_type(self, channel_num: int) -> str:
        gas_type = 'NA'
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Id gas'].value
            self._lgr.debug(f'addr is {addr}')
            gas_id = self.hw.read_register(addr)
            try:
                gas_type = GasNames(gas_id).name
            except IndexError:
                self._lgr.error(f'Channel {channel_num} at addr {addr} ahd invalid gas id {gas_id}')
        return gas_type

    def get_total_channels(self):
        channels = 0
        if self.hw is not None:
            channels = self.hw.read_register(MainBoardOffsets['Number of channels'].value)
        return channels

    def get_total_flow(self) -> int:
        flow = 0
        if self.hw is not None:
            flow = self.hw.read_long(MainBoardOffsets['Total flow'].value)
        return flow

    def adjust_flow(self, adjust_flow: int):
        flow = self.get_total_flow()
        self.set_total_flow(flow + adjust_flow)

    def set_total_flow(self, total_flow: int):
        if self.hw is not None:
            if total_flow < self.cfg.flow_limits[0]:
                total_flow = self.cfg.flow_limits[0]
                self._lgr.warning(f'{self.name}: Attempt set flow {total_flow} '
                                  f'lower than limit {self.cfg.flow_limits[0]}. '
                                  f'Flow being set to limit.')
            if total_flow > self.cfg.flow_limits[1]:
                total_flow = self.cfg.flow_limits[1]
                self._lgr.warning(f'{self.name}: Attempt set flow {total_flow} '
                                  f'higher than limit {self.cfg.flow_limits[1]}. '
                                  f'Flow being set to limit.')
            addr = MainBoardOffsets['Total flow'].value
            self.hw.write_long(addr, int(total_flow))
            self._lgr.info(f'{self.name}: Total flow changed to {int(total_flow)}')
            if self._queue:
                buf = [addr, self.data_type(total_flow)]
                self._queue.put((buf, get_epoch_ms()))

    def get_percent_value(self, channel_num:int) -> float:
        value = 0.0
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Percent value'].value
            value = self.hw.read_register(addr, number_of_decimals=2)
        return value

    def set_percent_value(self, channel_num: int, new_percent: float):
        if self.hw is not None:
            if new_percent < 0:
                new_percent = 0
                self._lgr.warning(f'{self.name}: Attempt to set channel percent to '
                                  f'{new_percent}. Capping at 0')
            if new_percent > 0:
                new_percent = 100
                self._lgr.warning(f'{self.name}: Attempt to set channel percent to '
                                  f'{new_percent}. Capping at 100')

            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Percent value'].value
            percent = int(new_percent * 100)
            self.hw.write_register(addr, percent)
            self._lgr.info(f'{self.name} Setting channel {channel_num} to {percent} %')
            if self._queue:
                buf = [addr, self.data_type(percent)]
                self._queue.put((buf, get_epoch_ms()))

    def get_sccm(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['SCCM'].value
            value = self.hw.read_long(addr)
            value /= 100
        return value

    def get_sccm_av(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['SCCM AV'].value
            value = self.hw.read_long(addr)
            value /= 100
        return value

    def get_target_sccm(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Target SCCM'].value
            value = self.hw.read_long(addr)
            value /= 100
        return value

    def get_working_status(self):
        status_on = False
        if self.hw is not None:
            addr = MainBoardOffsets['Working status']
            status_on = self.hw.read_register(addr) == 1
        return status_on

    def set_working_status(self, turn_on: bool):
        if self.hw is not None:
            addr = MainBoardOffsets['Working status']
            self.hw.write_register(addr, int(turn_on))
            if self._queue:
                buf = [addr, self.data_type(turn_on)]
                self._queue.put((buf, get_epoch_ms()))

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


class MockGB100:
    def __init__(self):
        self.total_flow = 0
        self.percent = [0, 0]
        self.sccm = [0, 0]
        self.target_sccm = [0, 0]
        self.sccm_av = [0, 0]
        self.status = False

    def read_register(self, addr):
        if addr == ChannelAddr[0] + ChannelRegisterOffsets['Id gas'].value:
            return 3
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Id gas'].value:
            return 4
        elif addr == MainBoardOffsets['Number of channels'].value:
            return 2
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['Percent value']:
            return self.percent[0]
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Percent value']:
            return self.percent[1]
        elif addr == MainBoardOffsets['Working status']:
            return self.status

    def write_register(self, addr, value):
        if addr == MainBoardOffsets['Working status']:
            self.status = bool(value)

    def read_long(self, addr):
        if addr == MainBoardOffsets['Total flow'].value:
            return self.total_flow
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['Target SCCM'].value:
            return self.sccm[0]
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Target SCCM'].value:
            return self.sccm[1]
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['SCCM'].value:
            return self.sccm[0]
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['SCCM'].value:
            return self.sccm[1]
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['SCCM AV'].value:
            return self.sccm_av[0]
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['SCCM AV'].value:
            return self.sccm_av[1]

    def write_long(self, addr, value):
        if addr == MainBoardOffsets['Total flow'].value:
            self.total_flow = value
        elif addr == ChannelAddr[0] + ChannelRegisterOffsets['Percent value']:
            self.percent[0] = value
        elif addr == ChannelAddr[1] + ChannelRegisterOffsets['Percent value']:
            self.percent[1] = value


