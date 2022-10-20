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
from threading import Thread, Lock, Event
from time import perf_counter, sleep, time
from collections import deque
import logging
from dataclasses import dataclass, field, asdict

import numpy as np
import numpy.typing as npt
from configparser import ConfigParser

import pyPerfusion.PerfusionConfig as PerfusionConfig


class AIDeviceException(Exception):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class AIChannelConfig:
    name: str = 'Channel'
    line: int = 0
    cal_pt1_target: np.float64 = 0
    cal_pt1_reading: np.float64 = 0
    cal_pt2_target: np.float64 = 0
    cal_pt2_reading: np.float64 = 0


@dataclass
class AIDeviceConfig:
    name: str = ''
    device_name: str = ''
    sampling_period_ms: int = 0
    read_period_ms: int = 0
    data_type: npt.DTypeLike = np.dtype(np.float64).name
    buf_type: npt.DTypeLike = np.dtype(np.uint16).name
    ch_info: dict[str, AIChannelConfig] = field(default_factory=dict)


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
        self.__acq_start_t = 0

    def write_config(self):
        info = asdict(self.cfg)
        info['data_type'] = np.dtype(self.cfg.data_type).name
        info['buf_type'] = np.dtype(self.cfg.buf_type).name
        # remove ch_info as that data will be written to a separate section
        del info['ch_info']
        PerfusionConfig.write_section(self.cfg.name, 'General', info)
        for ch_name, ch_cfg in self.cfg.ch_info.items():
            PerfusionConfig.write_section(self.cfg.name, ch_name, asdict(ch_cfg))

    def read_config(self):
        info = PerfusionConfig.read_section(self.cfg.name, 'General')
        self._lgr.debug(f'{info}')
        self.cfg.device_name = info['device_name']
        self.cfg.sampling_period_ms = int(info['sampling_period_ms'])
        self.cfg.read_period_ms = int(info['read_period_ms'])
        self.cfg.data_type = info['data_type']
        self.cfg.buf_type = info['buf_type']
        channel_names = PerfusionConfig.get_section_names(self.cfg.name)
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
    def start_time(self):
        return self.__acq_start_t

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
        channels_valid = [not ch == '' for ch in self.cfg.ch_info.values()]
        valid_name = self.cfg.device_name != ''
        return valid_name and any(channels_valid)

    def add_channel(self, cfg: AIChannelConfig):
        if cfg.name in self.ai_channels.keys():
            self._lgr.warning(f'Channel {cfg.name} already exists. Overwriting with new config')
        self.stop()
        self.cfg.ch_info[cfg.name] = cfg
        self.ai_channels[cfg.name] = AIChannel(cfg=cfg, device=self)

    def remove_channel(self, name: str):
        if name in self.ai_channels.keys():
            self._lgr.info(f'Removing channel {name} from device {self.cfg.device_name}')
            del self.ai_channels[name]
            del self.cfg.ch_info[name]

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
        self.__acq_start_t = perf_counter()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyAI {self.cfg.name}'
        self.__thread.start()

    def stop(self):
        if self.__thread and self.__thread.is_alive():
            self._event_halt.set()
            self.__thread.join(2.0)
            self.__thread = None

    def run(self):
        next_t = time()
        offset = 0
        while not self._event_halt.is_set():
            next_t += offset + self.cfg.read_period_ms / 1000.0
            delay = next_t - time()
            if delay > 0:
                sleep(delay)
                offset = 0
            else:
                offset = -delay
            self._acq_samples()

    def _acq_samples(self):
        sleep_time = self.cfg.read_period_ms / self.cfg.sampling_period_ms / 1000.0
        sleep(sleep_time)
        buffer_t = perf_counter()
        for channel in self.ai_channels.values():
            val = np.random.random_sample()  # * self._demo_amp[ch] + self._demo_offset[ch])
            buffer = np.ones(self.samples_per_read, dtype=self.cfg.data_type) * val
            channel.put_data(buffer, buffer_t)


class AIChannel:
    def __init__(self, cfg: AIChannelConfig, device: AIDevice):
        self._lgr = logging.getLogger(__name__)
        self.cfg = cfg
        self.device = device

        self._queue = deque(maxlen=100)

        # parameters for randomly generated data when there is no underlying hardware
        # used for testing and demo purposes
        self._demo_amp = {}
        self._demo_offset = {}

    def write_config(self):
        info = asdict(self.cfg)
        PerfusionConfig.write_section(self.device.cfg.name, self.cfg.name, info)

    def read_config(self, channel_name: str = None):
        if channel_name is None:
            channel_name = self.cfg.name
        info = PerfusionConfig.read_section(self.device.cfg.name, channel_name)
        self.cfg.line = int(info['line'])
        self.cfg.cal_pt1_target = np.float64(info['cal_pt1_target'])
        self.cfg.cal_pt1_reading = np.float64(info['cal_pt1_reading'])
        self.cfg.cal_pt2_target = np.float64(info['cal_pt2_target'])
        self.cfg.cal_pt2_reading = np.float64(info['cal_pt2_reading'])

    def put_data(self, buf, t):
        data = self._calibrate(buf)
        self._queue.append((data, t))

    def get_data(self):
        buf = None
        t = None
        try:
            buf, t = self._queue.pop()
        except IndexError:
            # this can occur if there are attempts to read data before it has been acquired
            # this is not unusual, so catch the error but do nothing
            pass
        return buf, t

    def clear(self):
        self._queue.clear()

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
