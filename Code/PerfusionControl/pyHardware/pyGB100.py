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
                                  'K factor gas', 'SCCM', 'dummy', 'Target SCCM'],
                                  start=0)


# The names and order need to match the GB100 instrument
GasNames = IntEnum('GasNames', ['Air', 'Nitric Oxide', 'Nitrogen', 'Oxygen',
                                'Carbon Dioxide', 'Argon', 'Methane', 'Ethylene',
                                'Ethane', 'Hydrogen', 'Helium', 'Sulfur Exafluoride',
                                'Propane', 'Butane', 'DME'],
                   start=0)


@dataclass
class GasDeviceConfig:
    name: str = 'GasDevice'
    port: str = ''
    CO2_range: List = field(default_factory=lambda: [0, 100])
    O2_range: List = field(default_factory=lambda: [0, 100])
    pH_range: List = field(default_factory=lambda: [0, 100])


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

        self.co2_adjust = 1  # %
        self.o2_adjust = 1  # %
        self.flow_adjust = 5  # mL/min

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
            self._lgr.debug(f'Opening modbus instrument at {self.cfg.port}')
            self.hw = modbus.Instrument(self.cfg.port, 1, modbus.MODE_RTU, debug=False)
            self.hw.serial.baudrate = self.baud
            self.hw.serial.bytesize = 8
            self.hw.serial.parity = serial.PARITY_NONE
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
        pass

    # channel id's are assumed to start numbering at 1 to match GB100 notation
    def get_gas_type(self, channel_num: int) -> str:
        gas_type = 'NA'
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Id gas'].value
            # self._lgr.debug(f'addr is {addr}')
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

    def set_total_flow(self, total_flow: int):
        if self.hw is not None:
            addr = MainBoardOffsets['Total flow'].value
            self.hw.write_long(addr, int(total_flow))
            if self._queue:
                buf = [addr, self.data_type(total_flow)]
                self._queue.put((buf, get_epoch_ms()))

    def get_percent_value(self, channel_num: int) -> float:
        value = 0.0
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Percent value'].value
            value = self.hw.read_register(addr, number_of_decimals=2)
        return value

    def set_percent_value(self, channel_num: int, new_percent: float):
        if self.hw is not None:
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['Percent value'].value
            percent = int(new_percent * 100)
            self._lgr.debug(f'percent is {percent}, type is {type(percent)}')
            self.hw.write_register(addr, percent)
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
            addr = ChannelAddr[channel_num - 1] + ChannelRegisterOffsets['SCCM'].value
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

    def update_pH(self, CDI_input):
        pH = CDI_input.venous_pH
        total_flow = self.get_total_flow()
        if 5 <= total_flow <= 250:
            if pH == -1:
                self._lgr.warning(f'Venous pH is out of range. Cannot be adjusted automatically')
                return None
            elif pH < self.cfg.pH_range[0]:
                new_flow = total_flow + self.flow_adjust
                self.set_total_flow(new_flow)
                self._lgr.info(f'Total flow in PV increased to {new_flow}')
                return new_flow
            elif pH > self.cfg.pH_range[1]:
                new_flow = total_flow - self.flow_adjust
                self.set_total_flow(new_flow)
                self._lgr.info(f'Total flow in PV decreased to {new_flow}')
                return new_flow
        elif total_flow >= 250:
            self._lgr.warning(f'Total flow in PV at or above 250 mL/min. Cannot be run automatically')
            return None
        elif total_flow <= 5:
            self._lgr.warning(f'Total flow in portal vein at or below 5 mL/min. Cannot be run automatically')
            return None
        else:
            return None

    def update_CO2(self, CDI_input):
        new_percentage_mix = None
        pH = CDI_input.arterial_pH
        CO2 = CDI_input.arterial_CO2

        gas = self.get_gas_type(2)
        if gas == "Carbon Dioxide":
            gas_index = 2
        else:
            gas_index = 1

        percentage_mix = self.get_percent_value(gas_index)
        check_CO2 = False
        if 0 <= percentage_mix <= 100:
            if pH == -1:
                self._lgr.warning(f'{self.name}: pH is out of range. Cannot be adjusted automatically')
                check_CO2 = True
            elif pH >= self.cfg.pH_range[1]:
                new_percentage_mix = percentage_mix + self.co2_adjust
                self._lgr.warning(f'{self.name}: Blood alkalotic, increasing CO2')
            elif pH <= self.cfg.pH_range[0]:
                new_percentage_mix = percentage_mix - self.co2_adjust
                self._lgr.warning(f'{self.name}: Blood acidotic, decreasing CO2')
            else:
                self._lgr.debug(f' Arterial pH is stable at {pH}.')
                check_CO2 = True

            if check_CO2 is True:
                if CO2 == -1:
                    self._lgr.warning(f'{self.name}: CO2 is out of range. Cannot be adjusted automatically')
                elif CO2 >= self.cfg.CO2_range[1]:
                    new_percentage_mix = percentage_mix - self.co2_adjust
                    self._lgr.warning(f'{self.name}: CO2 high, decreasing CO2')
                elif CO2 <= self.cfg.CO2_range[0]:
                    new_percentage_mix = percentage_mix + self.co2_adjust
                    self._lgr.warning(f'{self.name}: CO2 low, increasing CO2')
                else:
                    self._lgr.warning(f'Arterial CO2 is stable at {CO2}.')
        else:
            self._lgr.warning(f'{self.name}: CO2 % is out of range and cannot be changed automatically')

        return new_percentage_mix

    def update_O2(self, CDI_input):
        new_percentage_mix = None
        O2 = CDI_input.venous_sO2

        gas = self.get_gas_type(1)
        if gas == "Oxygen":
            gas_index = 1
        else:
            gas_index = 2

        percentage_mix = self.get_percent_value(gas_index)
        if 0 <= percentage_mix < 100:
            if O2 == -1:
                self._lgr.warning(f'{self.name}: O2 is out of range. Cannot be adjusted automatically')
            elif O2 <= self.cfg.O2_range[0]:
                new_percentage_mix = percentage_mix + self.o2_adjust
                self._lgr.warning(f'{self.name}: O2 is low. Increasing oxygen flow')
            elif O2 >= self.cfg.O2_range[1]:
                new_percentage_mix = percentage_mix - self.o2_adjust
                self._lgr.warning(f'{self.name}: O2 is high. Decreasing oxygen flow')
        else:
            self._lgr.warning(f'{self.name}: O2 % is out of range and cannot be changed automatically')

        return new_percentage_mix

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
