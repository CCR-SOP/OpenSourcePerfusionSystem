# -*- coding: utf-8 -*-
"""Base class for generating analog output

Provides basic interface for accessing analog outputs.
Used directly only for testing other code without direct access to the hardware

Requires numpy library

Uses a thread to output a new data buffer at required intervals. For this base class, the thread allows outputting data
similar to how actual hardware would produce data. Derived classes can use this to output buffers as needed.

This class will output the data to a file to verify operation. This can also be used by derived classes to verify
the data being written to the analog output channel.

Provides functions to create a sine wave, DC voltage, and a ramp waveform. The ramp waveform is intended to provide
as lower acceleration/deceleration to DC value to prevent stalling of motors.

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from threading import Thread, Event, Lock
from time import perf_counter, sleep, time
from collections import deque
import logging
from dataclasses import dataclass, field, asdict
from typing import List

import numpy as np
import numpy.typing as npt

import pyPerfusion.PerfusionConfig as PerfusionConfig


class AODeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class OutputType:
    name = 'Generic'


@dataclass
class DCOutput(OutputType):
    name = 'DC'
    offset_volts: float = 0.0


@dataclass
class SineOutput:
    name = 'Sine'
    hz: float = 0.0
    pk2pk_volts: float = 0.0
    offset_volts: float = 0.0


@dataclass
class RampOutput:
    name = 'Ramp'
    start_volts: float = 0.0
    stop_volts: float = 0.0
    accel_s: float = 0.0


@dataclass
class AOChannelConfig:
    name: str = 'Channel'
    line: int = 0
    max_accel_volts_per_s: float = 1.0
    output_type: OutputType = DCOutput


CHANNEL_TYPE_MAPPING = {'DCOutput': 'DC',
                        'SineOutput': 'Ramp',
                        'RampOutput': 'Sine'}


@dataclass
class AODeviceConfig:
    name: str = ''
    device_name: str = ''
    sampling_period_ms: int = 1
    bits: int = 16
    data_type: npt.DTypeLike = np.dtype(np.float64).name
    buf_type: npt.DTypeLike = np.dtype(np.float64).name
    ch_names: List[str] = field(default_factory=list)


class AODevice:
    def __init__(self):
        self._lgr = logging.getLogger(__name__)

        self.cfg = None
        self.ao_channels = {}

        self.__thread = None
        self._event_halt = Event()
        self._lock_buf = Lock()

    @property
    def devname(self):
        return 'ao'

    def write_config(self):
        PerfusionConfig.write_from_dataclass(self.cfg.name, 'General', self.cfg)
        for ch in self.ao_channels.values():
            PerfusionConfig.write_from_dataclass(self.cfg.name, ch.cfg.name, ch.cfg)

    def read_config(self):
        PerfusionConfig.read_into_dataclass(self.cfg.name, 'General', self.cfg)
        channel_names = PerfusionConfig.get_section_names(self.cfg.name)
        # delete the ch_names variable as this will be recreated as
        # channels are re-added
        self.cfg.ch_names = []
        for ch_name in channel_names:
            if ch_name != 'General':
                ch_cfg = AOChannelConfig(name=ch_name)
                self.add_channel(ch_cfg)
                self.ao_channels[ch_name].read_config(ch_name)
                # self._lgr.info(f'read_config: added channel {ch_cfg}')

        self.open(self.cfg)

    def open(self, cfg: AODeviceConfig):
        self.cfg = cfg

    def close(self):
        self.stop()

    def add_channel(self, cfg: AOChannelConfig):
        if cfg.name in self.ao_channels.keys():
            self._lgr.warning(f'Channel {cfg.name} already exists. Overwriting with new config')
        else:
            # self._lgr.debug(f'Adding ao channel {cfg.name}')
            self.cfg.ch_names.append(cfg.name)
        self.stop()
        self.ao_channels[cfg.name] = AOChannel(cfg=cfg, device=self)

    def remove_channel(self, name: str):
        if name in self.ao_channels.keys():
            # self._lgr.info(f'Removing channel {name} from device {self.cfg.device_name}')
            del self.ao_channels[name]
            self.cfg.ch_names.remove(name)
        else:
            self._lgr.warning(f'Attempt to remove non-existent channel {name} from device {self.cfg.device_name}')

    def remove_all_channels(self):
        self.ao_channels = {}

    def open(self, cfg: AODeviceConfig):
        self.cfg = cfg

    def close(self):
        self.stop()

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.__acq_start_t = perf_counter()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyAO {self.cfg.name}'
        self.__thread.start()

    def stop(self):
        if self.__thread and self.__thread.is_alive():
            self._event_halt.set()
            self.__thread.join(2.0)
            self.__thread = None

    def _output_samples(self):
        for channel in self.ao_channels.values():
            channel.update_buffer()
            channel.put_data()

    def _calc_output_delay(self):
        # This delay really only works correctly if all periods are the same
        periods_ms = [ch.period_ms for ch in self.ao_channels.values()]
        max_period_ms = max(periods_ms)
        if max_period_ms == 0:
            max_period_ms = 100
        return max_period_ms / 1000.0

    def run(self):
        while not self._event_halt.wait(self._calc_output_delay()):
            with self._lock_buf:
                self._output_samples()


class AOChannel:
    def __init__(self, cfg: AOChannelConfig, device: AODevice):
        self._lgr = logging.getLogger(__name__)

        self.cfg = cfg
        self.device = device

        self._queue = deque(maxlen=100)

        self.__thread = None
        self._event_halt = Event()
        self._lock_buf = Lock()

        self._buffer = np.array([0] * 10, dtype=self.device.cfg.data_type)
        self.period_ms = 0


    def write_config(self):
        PerfusionConfig.write_from_dataclass(self.device.cfg.name, self.cfg.name, self.cfg)

    def read_config(self, channel_name: str = None):
        if channel_name is None:
            channel_name = self.cfg.name
        PerfusionConfig.read_into_dataclass(self.device.cfg.name, channel_name, self.cfg)


    def update_buffer(self):
        self.set_output(self.cfg.output_type)

    def set_output(self, output: OutputType):
        self.cfg.output_type = output
        if self.cfg.output_type.name == 'DC':
            self._buffer = np.full(1, self.cfg.output_type.offset_volts)
            # self._lgr.info(f'{self.cfg.name}: setting DC={self.cfg.output_type.offset_volts}')
        elif self.cfg.output_type.name == 'Sine':
            if self.cfg.output_type.hz > 0.0:
                hz = self.cfg.output_type.hz
                p2p = self.cfg.output_type.pk2pk_volts
                offset = self.cfg.output_type.offset_volts
                t = np.arange(0, 1 / hz, step=self.device.cfg.sampling_period_ms / 1000.0)
                self._buffer = p2p / 2.0 * np.sin(2 * np.pi * hz * t, dtype=self.device.cfg.buf_type) + offset
                # self._lgr.info(f'{self.cfg.name}: setting {p2p}*sin(2pi*{hz}) + {offset}')
            else:
                self._lgr.error(f"Attempt to create a non-positive frequency {self.cfg.output_type.hz}")
        elif self.cfg.output_type.name == 'Ramp':
            start_volts = self.cfg.output_type.start_volts
            stop_volts = self.cfg.output_type.stop_volts
            accel = self.cfg.output_type.accel
            if not start_volts == stop_volts:
                if accel > self.cfg.max_accel_volts_per_s:
                    accel = self.cfg.max_accel_volts_per_s
                seconds = abs(start_volts - stop_volts) / accel
                calc_len = int(seconds / (self.device.cfg.sampling_period_ms / 1000.0))
                if calc_len == 0:
                    calc_len = 1
                self._buffer = np.linspace(start_volts, stop_volts, num=calc_len)
                # self._lgr.info(f'{self.cfg.name}: setting ramp from {start_volts} to {stop_volts} '
                # f'over {seconds} seconds with {calc_len} samples')
            else:
                self._buffer = np.array([stop_volts], dtype=self.device.cfg.data_type)
                # self._lgr.info('no change, no ramp set')

    def put_data(self):
        self._queue.put(self._buffer)

    def get_data(self):
        buf = None
        try:
            buf = self._queue.get(timeout=1.0)
        except Empty:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf
