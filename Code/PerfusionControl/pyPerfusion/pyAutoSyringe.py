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
    volume_ul: int = 0
    ul_per_min: int = 0
    basal: bool = False
    check_rate_sec: int = 0


@dataclass
class AutoSyringeGlucagonConfig(AutoSyringeConfig):
    glucose_level: int = 0


@dataclass
class AutoSyringeInsulinConfig(AutoSyringeConfig):
    glucose_level: int = 0
    max_ul_per_min: int = 0


@dataclass
class AutoSyringeEpoConfig(AutoSyringeConfig):
    pressure_level_mmHg: int = 60


@dataclass
class AutoSyringePhenylConfig(AutoSyringeConfig):
    pressure_level_mmHg: int = 60


class AutoSyringe:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.syringe = None
        self.input_reader = None
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
        self._lgr.debug(f'Reading config for {self.name}')
        PerfusionConfig.read_into_dataclass('automations', self.name, self.cfg)
        self._lgr.debug(f'Config = {self.cfg}')

    def run(self):
        self.is_streaming = True
        # JWK, this assumes the take to get the data and make the
        # adjustments is small compared to the adjust rate so timing drift
        # is small
        while not PerfusionConfig.MASTER_HALT.is_set():
            timeout = self.cfg.check_rate_sec
            if self._event_halt.wait(timeout):
                break
            if self.syringe and self.input_reader:
                ts, data = self.input_reader.get_last_acq()
                if data is not None:
                    self.update_on_input(data)
                else:
                    self._lgr.debug(f'{self.name} No input data. Cannot run syringe automatically')

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'AutoSyringe {self.name}'
        self.__thread.start()
        self._lgr.debug(f'AutoSyringe {self.name} started')

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False
            self._lgr.debug(f'AutoSyringe {self.name} stopped')

    def update_on_input(self, data):
        # this is the base class, so do nothing
        self._lgr.warning('Attempting to use the base AutoSyringe class, no adjustment will be made')

    def _inject(self, value):
        if self.cfg.basal:
            self.syringe.set_target_volume(0)
            self.syringe.set_infusion_rate(value)
            self.syringe.start_constant_infusion()
        else:
            self.syringe.set_target_volume(value)
            self.syringe.infuse_to_target_volume()


class AutoSyringeGlucagon(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringeGlucagonConfig()

    def read_config(self):
        super().read_config()

    def update_on_input(self, glucose):
        if glucose < self.cfg.glucose_level:
            self._inject(self.cfg.volume_ul)


class AutoSyringeInsulin(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringeInsulinConfig()

    def read_config(self):
        super().read_config()

    def update_on_input(self, glucose):
        rate = self.syringe.get_infusion_rate()
        if glucose > self.cfg.glucose_level:
            if rate < self.cfg.max_ul_per_min:
                rate += 1
            else:
                self._lgr.warning(f'Max infusion rate of {self.cfg.max_ul_per_min} reached')
            self._inject(rate)
        else:
            self.syringe.stop()


class AutoSyringeEpo(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringeEpoConfig()

    def read_config(self):
        super().read_config()

    def update_on_input(self, pressure):
        if pressure > self.cfg.pressure_level_mmHg:
            self._inject(self.cfg.ul_per_min)


class AutoSyringePhenyl(AutoSyringe):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AutoSyringePhenylConfig()

    def read_config(self):
        super().read_config()

    def update_on_input(self, pressure):
        if pressure < self.cfg.pressure_level_mmHg:
            self._inject(self.cfg.ul_per_min)