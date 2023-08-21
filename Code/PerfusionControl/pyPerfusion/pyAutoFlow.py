# -*- coding: utf-8 -*-
""" Class to adjust motor speed to output a desired flow

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""

from threading import Thread, Event
from dataclasses import dataclass

from simple_pid import PID
import pyPerfusion.utils as utils
import pyPerfusion.PerfusionConfig as PerfusionConfig


@dataclass
class AutoFlowConfig:
    device: str = ''
    data_source: str = ''
    adjust_rate_ms: int = 600_000
    kp: float = 0.0
    ki: float = 0.0
    kd: float = 0.0
    limit_high: float = 0.0
    limit_low: float = 0.0
    reverse_mode: bool = False


@dataclass
class StaticAutoFlowConfig(AutoFlowConfig):
    desired_flow: float = 0.0


# data source should return a value equal to the
# average value of the pulsatile flow (e.g. a moving average over several cycles)
@dataclass
class SinusoidalAutoFlowConfig(AutoFlowConfig):
    desired_max_flow: float = 0.0
    desired_min_flow: float = 0.0


class AutoFlow:
    def __init__(self, name: str):
        self.name = name
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.device = None
        self.data_source = None
        self.cfg = AutoFlowConfig()
        self.pid = PID(self.cfg.kp, self.cfg.ki, self.cfg.kd, setpoint=0)

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

    def update_tunings(self, kp, ki, kd):
        self.cfg.kp = kp
        self.cfg.ki = ki
        self.cfg.kd = kd
        self.pid.tunings = (self.cfg.kp, self.cfg.ki, self.cfg.kd)

    def run(self):
        self.is_streaming = True
        # JWK, this assumes the take to get the data and make the
        # adjustments is small compared to the adjust rate so timing drift
        # is small
        while not PerfusionConfig.MASTER_HALT.is_set():
            timeout = self.cfg.adjust_rate_ms / 1_000.0
            if self._event_halt.wait(timeout):
                break
            self._lgr.debug(f'device = {self.device}, source = {self.data_source}')
            if self.device and self.data_source:
                ts, flow = self.data_source.get_last_acq()
                self._lgr.debug(f'flow = {flow}')
                if flow is not None:
                    self.update_on_input(flow)

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = utils.get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'{__name__} {self.name}'
        self.__thread.start()
        self._lgr.info(f'{__name__} {self.name} started')

    def stop(self):
        if self.is_streaming:
            self._event_halt.set()
            self.is_streaming = False
            self._lgr.info(f'{__name__} {self.name} stopped')

    def update_on_input(self, flow):
        # this is the base class, so do nothing
        # This can be used when an automation object needs to be supplied
        # but no automation is necessary (e.g., panel_gas_mixers)
        pass


class StaticAutoFlow(AutoFlow):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = StaticAutoFlowConfig()

    def update_on_input(self, flow):
        new_speed = self.pid(flow)
        self._lgr.debug(f'Updating speed to {new_speed} based on flow {flow}')
        self.device.hw.set_speed(new_speed)


class SinusoidalAutoFlow(AutoFlow):
    def __init__(self, name: str):
        super().__init__(name)
        self._lgr = utils.get_object_logger(__name__, self.name)
        self.cfg = StaticAutoFlowConfig()

    def update_on_input(self, flow):
        new_speed = self.pid(flow)
        self._lgr.debug(f'Updating avg speed to {new_speed} based on flow {flow}')
        self.device.hw.set_avg_speed(new_speed)
