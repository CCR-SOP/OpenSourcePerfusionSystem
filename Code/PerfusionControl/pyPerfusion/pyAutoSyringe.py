# -*- coding: utf-8 -*-
""" Class to auto adjust the syringe injections

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from threading import Thread, Event
from dataclasses import dataclass

from pyPerfusion.utils import get_epoch_ms
import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils


@dataclass
class AutoSyringeConfig:
    device: str = ''
    data_source: str = ''
    volume_ul: int = 0
    ul_per_min: int = 0
    basal: bool = False
    adjust_rate_ms: int = 0


@dataclass
class AutoSyringeGlucagonConfig(AutoSyringeConfig):
    glucose_min: int = 0
    glucose_max: int = 0


@dataclass
class AutoSyringeInsulinConfig(AutoSyringeConfig):
    glucose_min: int = 0
    glucose_max: int = 0
    max_ul_per_min: int = 0


@dataclass
class AutoSyringeEpoConfig(AutoSyringeConfig):
    pressure_mmHg_min: int = 0
    pressure_mmHg_max: int = 0

@dataclass
class AutoSyringePhenylConfig(AutoSyringeConfig):
    pressure_mmHg_min: int = 0
    pressure_mmHg_max: int = 0


@dataclass
class SyringeTPNConfig(AutoSyringeConfig):
    pass


@dataclass
class SyringeZosynConfig(AutoSyringeConfig):
    pass


class AutoSyringe:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.device = None
        self.data_source = None
        self.cfg = AutoSyringeConfig()

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
            timeout = self.cfg.adjust_rate_ms / 1000.0
            if self._event_halt.wait(timeout):
                break
            if self.device and self.data_source:
                ts, data = self.data_source.get_last_acq()
                if data is not None:
                    self.update_on_input(data)
                else:
                    self._lgr.debug(f'{self.name} No input data. Cannot run syringe automatically')

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'{__name__} {self.name}'
        self.__thread.start()
        self._lgr.debug(f'{__name__} {self.name} started')

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False
            self._lgr.info(f'{__name__} {self.name} stopped')

    def update_on_input(self, data):
        # this is the base class, so do nothing
        # self._lgr.warning('Attempting to use the base AutoSyringe class, no adjustment will be made')
        pass

    def _inject(self, value):
        if self.cfg.basal:
            self.device.hw.set_target_volume(0)
            self.device.hw.set_infusion_rate(value)
            self.device.hw.start_constant_infusion()
        else:
            self.device.hw.set_target_volume(value)
            self.device.hw.infuse_to_target_volume()


class AutoSyringeGlucagon(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringeGlucagonConfig()

    def update_on_input(self, glucose):
        if glucose < self.cfg.glucose_min:
            self._inject(self.cfg.volume_ul)
        elif glucose >= (self.cfg.glucose_min+self.cfg.glucose_max) / 2:
            self.stop()
            self._lgr.info(f'Glucagon injection stopped')


class AutoSyringeInsulin(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringeInsulinConfig()

    def update_on_input(self, glucose):
        rate = self.device.hw.get_infusion_rate()
        if glucose > self.cfg.glucose_max:
            if rate < self.cfg.max_ul_per_min:
                rate += 1
            else:
                self._lgr.warning(f'Max infusion rate of {self.cfg.max_ul_per_min} reached')
            self._inject(rate)
        elif glucose <= (self.cfg.glucose_min + self.cfg.glucose_max) / 2:
            self.stop()
            self._lgr.info(f'Insulin injection stopped')


class AutoSyringeEpo(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringeEpoConfig()
        self._lgr = utils.get_object_logger(__name__, self.name)

    def update_on_input(self, pressure):
        self._lgr.info(f'pressure is {pressure} and limit is {self.cfg.pressure_mmHg_max}')
        if pressure > self.cfg.pressure_mmHg_max:  # dilates, decreases pressure
            self._inject(self.cfg.ul_per_min)
            self._lgr.info(f'Epo injection set to {self.cfg.ul_per_min}')
        elif pressure <= (self.cfg.pressure_mmHg_min+self.cfg.pressure_mmHg_max) / 2:  # stop at midpoint
            self.stop()
            self._lgr.info(f'Epo injection stopped')


class AutoSyringePhenyl(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringePhenylConfig()
        self._lgr = utils.get_object_logger(__name__, self.name)

    def update_on_input(self, pressure):
        self._lgr.warning(f'pressure is {pressure} and limit is {self.cfg.pressure_mmHg_min}')
        if pressure < self.cfg.pressure_mmHg_min:  # constricts, increase pressure
            self._inject(self.cfg.ul_per_min)
            self._lgr.info(f'Phenyl injection set to {self.cfg.ul_per_min}')
        elif pressure >= (self.cfg.pressure_mmHg_min+self.cfg.pressure_mmHg_max) / 2:  # stop at midpoint
            self.stop()
            self._lgr.info(f'Phenyl injection stopped')


class SyringeTPN(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = SyringeTPNConfig()
        self._lgr = utils.get_object_logger(__name__, self.name)


class SyringeZosyn(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = SyringeZosynConfig()
        self._lgr = utils.get_object_logger(__name__, self.name)

