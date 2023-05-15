# -*- coding: utf-8 -*-
""" Class to auto adjust the percentages of gases in a GB100 gas mixer
    based on physiological values read from a CDI monitor

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from threading import Thread, Event
from dataclasses import dataclass, field
from typing import List

from pyHardware.pyCDI import CDIData
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class AutoGasMixerConfig:
    gas_device: str = ''
    data_source: str = ''
    adjust_rate_ms: int = 600_000


@dataclass
class ArterialAutoGasMixerConfig(AutoGasMixerConfig):
    pH_range: List = field(default_factory=lambda: [0, 100])
    flow_adjust: float = 0.0
    O2_channel: int = 0
    CO2_channel: int = 0
    CO2_adjust: float = 0.0


@dataclass
class VenousAutoGasMixerConfig(AutoGasMixerConfig):
    pH_range: List = field(default_factory=lambda: [0, 100])
    O2_range: List = field(default_factory=lambda: [0, 100])
    O2_adjust: float = 0.0
    flow_adjust: float = 0.0
    O2_channel: int = 0
    N2_channel: int = 0


class AutoGasMixer:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.gas_device = None
        self.data_source = None
        self.cfg = AutoGasMixerConfig()

        self.acq_start_ms = 0
        self._event_halt = Event()
        self.__thread = None
        self.is_streaming = False

    @property
    def is_running(self):
        return self.is_streaming

    def write_config(self):
        PerfusionConfig.write_from_dataclass('automations', self.name, self.cfg)

    def read_config(self):
        PerfusionConfig.read_into_dataclass('automations', self.name, self.cfg)

    def run(self):
        self.is_streaming = True
        # JWK, this assumes the take to get the data and make the
        # adjustments is small compared to the adjust rate so timing drift
        # is small
        while not PerfusionConfig.MASTER_HALT.is_set():
            timeout = self.cfg.adjust_rate_ms / 1_000.0
            if self._event_halt.wait(timeout):
                break
            if self.gas_device and self.data_source:
                ts, all_vars = self.data_source.get_last_acq()
                if all_vars is not None:
                    cdi_data = CDIData(all_vars)
                    self.update_on_input(cdi_data)
                # else:
                    # self._lgr.debug(f'{self.name} No CDI data. Cannot run gas mixers automatically')

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = utils.get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'AutoGasMixer {self.name}'
        self.__thread.start()
        self._lgr.info(f'AutoGasMixer {self.name} started')

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False
            self._lgr.info(f'AutoGasMixer {self.name} stopped')

    def update_on_input(self, data):
        # this is the base class, so do nothing
        # This can be used when an automation object needs to be supplied
        # but no automation is necessary (e.g., panel_gas_mixers)
        pass


class AutoGasMixerVenous(AutoGasMixer):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = VenousAutoGasMixerConfig()

    def update_on_input(self, data):
        try:
            self._update_O2(data.venous_sO2)
            self._update_flow(data.venous_pH)
        except AttributeError:
           # this will happen if there is invalid CDI data
            pass

    def _update_flow(self, pH: float):
        if pH == -1:
            self._lgr.warning(f'{self.name} pH is out of range. Cannot be adjusted automatically')
        elif pH < self.cfg.pH_range[0]:
            self.gas_device.adjust_flow(self.cfg.flow_adjust)
            self._lgr.info(f'{self.name} is acidotic, increasing total flow by {self.cfg.flow_adjust}')
            self._lgr.info(f'Flow updated')
        elif pH > self.cfg.pH_range[1]:
            self.gas_device.adjust_flow(-self.cfg.flow_adjust)
            self._lgr.info(f'{self.name} is alkalotic, decreasing total flow by {self.cfg.flow_adjust}')
            self._lgr.info(f'Flow updated')

    def _update_O2(self, O2: float):
        O2_adjust = 0

        self._lgr.debug(f'O2={O2}, limits={self.cfg.O2_range}')
        if O2 == -1:
            self._lgr.warning(f'{self.name}: O2 is out of range. Cannot be adjusted automatically')
        elif O2 < self.cfg.O2_range[0]:
            O2_adjust = self.cfg.O2_adjust
            self._lgr.info(f'{self.name}: O2 low. Increasing O2 percentage by {O2_adjust}')
        elif O2 > self.cfg.O2_range[1]:
            O2_adjust = -self.cfg.O2_adjust
            self._lgr.warning(f'{self.name}: O2 high. Decreasing O2 percentage by {O2_adjust}')
        if O2_adjust != 0:
            new_percent = self.gas_device.get_percent_value(self.cfg.O2_channel) + O2_adjust
            self.gas_device.set_percent_value(self.cfg.O2_channel, new_percent)
            self._lgr.debug(f'O2 updated')


class AutoGasMixerArterial(AutoGasMixer):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = ArterialAutoGasMixerConfig()
        self.o2_ch = 1  # is this obsolete?
        self.co2_ch = 2

    def update_on_input(self, data):
        try:
            self.update_CO2(data.arterial_pH, data.arterial_CO2)
        except AttributeError:
            # this will happen if there is invalid CDI data
            pass

    def update_CO2(self, pH: float, CO2: float):
        self._lgr.debug('update_CO2')
        co2_adjust = 0
        check_co2 = False
        self._lgr.debug(f'ph = {pH}, CO2={CO2}, pH limits={self.cfg.pH_range}')
        if pH == -1:
            self._lgr.warning(f'{self.name}: pH is out of range. Cannot be adjusted automatically')
            check_co2 = True
        elif pH > self.cfg.pH_range[1]:
            co2_adjust = self.cfg.CO2_adjust
            self._lgr.warning(f'{self.name}: pH high, blood alkalotic')
        elif pH < self.cfg.pH_range[0]:
            co2_adjust = -self.cfg.CO2_adjust
            self._lgr.warning(f'{self.name}: pH low, blood acidotic')
        else:
            check_co2 = True

        # only check CO2 is pH checking didn't work - pH more important parameter to monitor
        if check_co2 is True:
            if CO2 == -1:
                self._lgr.warning(f'{self.name}: CO2 is out of range. Cannot be adjusted automatically')
            elif CO2 < self.gas_device.cfg.CO2_range[0]:
                co2_adjust = self.cfg.CO2_adjust
                self._lgr.warning(f'{self.name}: CO2 low, blood alkalotic')
            elif CO2 > self.gas_device.cfg.CO2_range[1]:
                co2_adjust = -self.cfg.CO2_adjust
                self._lgr.warning(f'{self.name}: CO2 high, blood acidotic')

        if co2_adjust != 0:
            new_percent = self.gas_device.get_percent_value(self.cfg.CO2_channel) + co2_adjust
            self.gas_device.set_percent_value(self.cfg.CO2_channel, new_percent)
            self._lgr.debug(f'CO2 updated')

