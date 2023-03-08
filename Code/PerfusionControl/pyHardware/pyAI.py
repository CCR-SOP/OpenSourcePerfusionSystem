# -*- coding: utf-8 -*-
"""Base class for accessing analog inputs

Provides basic interface for accessing analog inputs.
Used directly only for testing other code without direct access to the hardware

Requires numpy library

Sample buffers are read periodically from the hardware and stored in a Queue for later processing. This helps to ensure
that no samples are dropped from the hardware due to slow processing. There is one queue per analog input line/channel

All data types use numpy data types. The buf_type parameter should represent the data type as acquired
from the hardware (e.g., unsigned 16-bit data). The data_type should represent the data after calibration or conversion
to other units (e.g., ml/min).

@project: LiverPerfusion NIH
@author: John Kakareka, NIH

This work was created by an employee of the US Federal Gov
and under the public domain.
"""
from threading import Thread, Event
from queue import Queue, Empty
from time import sleep, time_ns
import logging
from dataclasses import dataclass, field
from typing import List

import numpy as np
import numpy.typing as npt

import pyPerfusion.PerfusionConfig as PerfusionConfig


class AIDeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class AIChannelConfig:
    name: str = 'Channel'
    line: int = 0
    cal_pt1_target: np.float64 = 0.0
    cal_pt1_reading: np.float64 = 0.0
    cal_pt2_target: np.float64 = 0.0
    cal_pt2_reading: np.float64 = 0.0


@dataclass
class AIDeviceConfig:
    name: str = ''
    device_name: str = ''
    sampling_period_ms: int = 0
    read_period_ms: int = 0
    data_type: npt.DTypeLike = np.dtype(np.float64).name
    buf_type: npt.DTypeLike = np.dtype(np.uint16).name
    ch_names: List[str] = field(default_factory=list)


def get_epoch_ms():
    return int(time_ns() / 1_000_000.0)


class AIDevice:
    def __init__(self):
        self._lgr = logging.getLogger(__name__)

        self.__thread = None
        self._event_halt = Event()
        # self._lock_buf = Lock()

        self.cfg = AIDeviceConfig()
        self.ai_channels = {}

        # stores the perf_counter value at the start of the acquisition which defines the zero-time for all
        # following samples
        self.acq_start_ms = 0

    def write_config(self):
        PerfusionConfig.write_from_dataclass(self.cfg.name, 'General', self.cfg)
        for ch in self.ai_channels.values():
            PerfusionConfig.write_from_dataclass(self.cfg.name, ch.cfg.name, ch.cfg)

    def read_config(self):
        PerfusionConfig.read_into_dataclass(self.cfg.name, 'General', self.cfg)
        channel_names = PerfusionConfig.get_section_names(self.cfg.name)
        # delete the ch_names variable as this will be recreated as
        # channels are re-added
        self.cfg.ch_names = []
        for ch_name in channel_names:
            if ch_name != 'General':
                ch_cfg = AIChannelConfig(name=ch_name)
                self.add_channel(ch_cfg)
                self.ai_channels[ch_name].read_config(ch_name)
                self._lgr.info(f'read_config: added channel {ch_cfg}')

        self.open(self.cfg)

    @property
    def devname(self):
        """
        Creates a string as required by the hardware to define the analog input device and analog lines used
        """
        lines = [ch.cfg.line for name, ch in self.ai_channels.items()]
        if len(lines) == 0:
            dev_str = 'ai'
        else:
            dev_str = ','.join([f'ai{line}' for line in lines])
        return dev_str

    @property
    def samples_per_read(self):
        return int(self.cfg.read_period_ms / self.cfg.sampling_period_ms)

    @property
    def buf_len(self):
        return self.samples_per_read

    @property
    def is_acquiring(self):
        return self.__thread and self.__thread.is_alive()

    def is_open(self):
        channels_valid = len(self.ai_channels) > 0
        valid_name = self.cfg.device_name != ''
        return valid_name and channels_valid

    def get_acq_start_ms(self):
        return self.acq_start_ms

    def add_channel(self, cfg: AIChannelConfig):
        if cfg.name in self.ai_channels.keys():
            self._lgr.warning(f'Channel {cfg.name} already exists. Overwriting with new config')
        else:
            self.cfg.ch_names.append(cfg.name)
        self.stop()
        self.ai_channels[cfg.name] = AIChannel(cfg=cfg, device=self)

    def remove_channel(self, name: str):
        if name in self.ai_channels.keys():
            self._lgr.info(f'Removing channel {name} from device {self.cfg.device_name}')
            del self.ai_channels[name]
            self.cfg.ch_names.remove(name)
        else:
            self._lgr.warning(f'Attempt to remove non-existent channel {name} from device {self.cfg.device_name}')

    def remove_all_channels(self):
        self.ai_channels = {}

    def open(self, cfg: AIDeviceConfig):
        self.cfg = cfg

    def close(self):
        self.stop()

    def start(self):
        self.stop()
        self._event_halt.clear()
        self.acq_start_ms = get_epoch_ms()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyAI {self.cfg.name}'
        self.__thread.start()

    def stop(self):
        if self.__thread and self.__thread.is_alive():
            self._lgr.debug(f'Stopping {self.__thread.name}')
            self._event_halt.set()
            self.__thread.join(2.0)
            self.__thread = None

    def run(self):
        next_t = get_epoch_ms()
        offset = 0
        while not self._event_halt.is_set():
            next_t += offset + self.cfg.read_period_ms
            delay = next_t - get_epoch_ms()
            if delay > 0:
                sleep(delay / 1_000.0)
                offset = 0
            else:
                offset = -delay
            self._acq_samples()

    def _acq_samples(self):
        buffer_t = get_epoch_ms()
        for channel in self.ai_channels.values():
            val = np.random.random_sample()  # * self._demo_amp[ch] + self._demo_offset[ch])
            buffer = np.ones(self.samples_per_read, dtype=self.cfg.data_type) * val
            # self._lgr.debug(f'{self.cfg.name}: buffer_t = {buffer_t}')
            channel.put_data(buffer, buffer_t)


class AIChannel:
    def __init__(self, cfg: AIChannelConfig, device: AIDevice):
        self._lgr = logging.getLogger(__name__)
        self.cfg = cfg
        self.device = device

        self._queue = Queue()
        self._q_timeout = 0.5

        # parameters for randomly generated data when there is no underlying hardware
        # used for testing and demo purposes
        self._demo_amp = {}
        self._demo_offset = {}

    @property
    def buf_len(self):
        return self.device.buf_len

    @property
    def data_type(self):
        return self.device.cfg.data_type

    @property
    def sampling_period_ms(self):
        return self.device.cfg.sampling_period_ms

    @property
    def samples_per_read(self):
        return self.device.samples_per_read

    def get_acq_start_ms(self):
        return self.device.get_acq_start_ms()

    def write_config(self):
        PerfusionConfig.write_from_dataclass(self.device.cfg.name, self.cfg.name, self.cfg)

    def read_config(self, channel_name: str = None):
        if channel_name is None:
            channel_name = self.cfg.name
        PerfusionConfig.read_into_dataclass(self.device.cfg.name, channel_name, self.cfg)

    def put_data(self, buf, t):
        data = self._calibrate(buf)
        self._queue.put((data, t))

    def get_data(self):
        buf = None
        t = None
        try:
            buf, t = self._queue.get(timeout=self._q_timeout)
        except Empty:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t

    def clear(self):
        with self._queue.mutex:
            self._queue.queue.clear()

    def _calibrate(self, buffer):

        if self.cfg.cal_pt2_reading - self.cfg.cal_pt1_reading == 0:
            data = buffer.astype(self.device.cfg.data_type)
        else:
            data = np.zeros_like(buffer)
            for i in range(len(buffer)):
                data[i] = ((((buffer[i] - self.cfg.cal_pt1_reading)
                           * (self.cfg.cal_pt2_target - self.cfg.cal_pt1_target))
                           / (self.cfg.cal_pt2_reading - self.cfg.cal_pt1_reading))
                           + self.cfg.cal_pt1_target)
        return data
