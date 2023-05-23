# -*- coding: utf-8 -*-
""" Class to auto adjust the dialysate inflow and outflow pumps
    of the dialysis circuit

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from threading import Thread, Event
from dataclasses import dataclass, field
from typing import List

from pyHardware.pyCDI import CDIData
from pyPerfusion.utils import get_epoch_ms
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


@dataclass
class AutoDialysisConfig:
    pump: str = ''
    data_source: str = ''
    adjust_rate: float = 0.5
    adjust_rate_ms: int = 600_000
    flow_range: List = field(default_factory=lambda: [0, 100])


@dataclass
class AutoDialysisInflowConfig(AutoDialysisConfig):
    K_min: float = 2.0
    K_max: float = 6.0


@dataclass
class AutoDialysisOutflowConfig(AutoDialysisConfig):
    K_min: float = 2.0
    K_max: float = 6.0
    hct_min: float = 2.0
    hct_max: float = 6.0


class AutoDialysis:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.pump = None
        self.data_source = None
        self.cfg = AutoDialysisConfig()

        self.acq_start_ms = 0
        self._event_halt = Event()
        self.__thread = None
        self.is_streaming = False

    @property
    def is_running(self):
        return self.is_streaming

    def write_config(self):
        PerfusionConfig.write_from_dataclass('automations', self.name, self.cfg, classname=self.__class__.__name__)

    def read_config(self):
        PerfusionConfig.read_into_dataclass('automations', self.name, self.cfg)

    def run(self):
        self.is_streaming = True
        # JWK, this assumes the time to get the data and make the
        # adjustments is small compared to the adjust rate so timing drift is small
        while not PerfusionConfig.MASTER_HALT.is_set():
            timeout = self.cfg.adjust_rate_ms / 1_000.0
            if self._event_halt.wait(timeout):
                break
            if self.pump and self.data_source:
                ts, all_vars = self.data_source.get_last_acq()
                if all_vars is not None:
                    cdi_data = CDIData(all_vars)
                    self.update_on_input(cdi_data)
                else:
                    self._lgr.debug(f'{self.name} No CDI data. Cannot run dialysis automatically')

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'{__name__} {self.name}'
        self.__thread.start()
        self._lgr.debug(f'{self.name} started')

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False
            self._lgr.debug(f'{self.name} stopped')

    def update_on_input(self, cdi_data):
        # this is the base class, it is only used when no actual automation is required
        pass


class AutoDialysisInflow(AutoDialysis):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoDialysisInflowConfig()
        self._lgr = utils.get_object_logger(__name__, self.name)

    def update_on_input(self, cdi_data):
        try:
            self._update_speed(cdi_data.K)
        except AttributeError:
            # this will happen if there is invalid CDI data
            pass

    def _update_speed(self, K: float):
        if K == -1:
            self._lgr.warning(f'{self.name} K is out of range. Cannot be adjusted automatically')
        elif K < self.cfg.K_min:
            self._lgr.info(f'K ({K}) below min of {self.cfg.K_min}')
            self.pump.hw.adjust_flow_rate(-self.cfg.adjust_rate)
        elif K > self.cfg.K_max:
            self._lgr.info(f'K ({K}) above max of {self.cfg.K_max}')
            self.pump.hw.adjust_flow_rate(self.cfg.adjust_rate)


class AutoDialysisOutflow(AutoDialysis):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = AutoDialysisOutflowConfig()

    def update_on_input(self, cdi_data):
        self._lgr.debug('updating outflow automation')
        try:
            self._update_speed(cdi_data.hct, cdi_data.K)
        except AttributeError:
            # this will happen if there is invalid CDI data
            pass

    def _update_speed(self, hct: float, K: float):
        if K == -1:
            self._lgr.warning(f'{self.name} K is out of range. Cannot be adjusted automatically')
        elif K < self.cfg.K_min:
            self._lgr.info(f'K ({K}) below min of {self.cfg.K_min}')
            self.pump.hw.adjust_flow_rate(-self.cfg.adjust_rate)
        elif K > self.cfg.K_max:
            self._lgr.info(f'K ({K}) above max of {self.cfg.K_max}')
            self.pump.hw.adjust_flow_rate(self.cfg.adjust_rate)

        if hct == -1:
            self._lgr.warning(f'{self.name} hct is out of range. Cannot be adjusted automatically')
        elif hct < self.cfg.hct_min:
            self._lgr.info(f'hct ({hct}) below min of {self.cfg.hct_min}')
            self.pump.hw.adjust_flow_rate(self.cfg.adjust_rate)
        elif hct > self.cfg.hct_max:
            self._lgr.info(f'hct ({hct}) above max of {self.cfg.hct_max}')
            self.pump.hw.adjust_flow_rate(-self.cfg.adjust_rate)
