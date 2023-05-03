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
from dataclasses import dataclass

import numpy as np

import pyPerfusion.PerfusionConfig as PerfusionConfig
import pyPerfusion.utils as utils
import pyHardware.pyGeneric as pyGeneric


class AIDeviceException(pyGeneric.HardwareException):
    """Exception used to pass simple device configuration error messages, mostly for display in GUI"""


@dataclass
class AIChannelConfig:
    line: int = 0
    cal_pt1_target: np.float64 = 0.0
    cal_pt1_reading: np.float64 = 0.0
    cal_pt2_target: np.float64 = 0.0
    cal_pt2_reading: np.float64 = 0.0


@dataclass
class AIDeviceConfig:
    device_name: str = ''
    sampling_period_ms: int = 0
    read_period_ms: int = 0
    data_type: str = 'float64'


class AIDevice(pyGeneric.GenericDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self.__thread = None
        self._event_halt = Event()

        self.cfg = AIDeviceConfig()
        self.buf_dtype = np.dtype(np.uint16)
        self.ai_channels = []

    def write_config(self):
        PerfusionConfig.write_from_dataclass(self.name, 'General', self.cfg)
        for ch in self.ai_channels:
            PerfusionConfig.write_from_dataclass(self.name, ch.name, ch.cfg)

    def read_config(self):
        PerfusionConfig.read_into_dataclass('hardware', self.name, self.cfg)
        channel_names = PerfusionConfig.get_section_names(self.name)
        for ch_name in channel_names:
            ch_cfg = AIChannelConfig()
            self.add_channel(ch_name=ch_name, cfg=ch_cfg)
            self._lgr.info(f'read_config: added channel {ch_name} with cfg: {ch_cfg}')

        self.open()

    @property
    def devname(self):
        """
        Creates a string as required by the hardware to define the analog input device and analog lines used
        """
        lines = [ch.cfg.line for ch in self.ai_channels]
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

    def channel_exists(self, ch_name: str):
        ch_exists = any(ch.name == ch_name for ch in self.ai_channels)
        return ch_exists

    def add_channel(self, ch_name: str, cfg: AIChannelConfig):
        if self.channel_exists(ch_name):
            self._lgr.warning(f'Channel {ch_name} already exists!')
        else:
            self.stop()
            ai = AIChannel(name=ch_name)
            ai.cfg = cfg
            ai.device = self
            ai.read_config()
            self.ai_channels.append(ai)

    def remove_channel(self, ch_name: str):
        if self.channel_exists(ch_name):
            self._lgr.info(f'Removing channel {ch_name} from device {self.name}')
            self.ai_channels = [ch for ch in self.ai_channels if ch.name != ch_name]
        else:
            self._lgr.warning(f'Attempt to remove non-existent channel {ch_name} from device {self.name}')

    def get_channel(self, ch_name: str):
        channel = [ch for ch in self.ai_channels if ch.name == ch_name]
        if len(channel) > 0:
            return channel[0]
        else:
            return None

    def remove_all_channels(self):
        self.ai_channels = []

    def start(self):
        super().start()
        self._event_halt.clear()

        self.__thread = Thread(target=self.run)
        self.__thread.name = f'pyAI {self.name}'
        self.__thread.start()

    def stop(self):
        super().stop()
        if self.__thread and self.__thread.is_alive():
            self._event_halt.set()
            self.__thread.join(2.0)
            self.__thread = None

    def run(self):
        while not PerfusionConfig.MASTER_HALT.is_set():
            period_timeout = self.cfg.read_period_ms / 1_000.0
            if not self._event_halt.wait(timeout=period_timeout):
                self._acq_samples()
            else:
                break

    def _acq_samples(self):
        buffer_t = utils.get_epoch_ms()
        for channel in self.ai_channels:
            val = np.random.random_sample()
            buffer = np.ones(self.samples_per_read, dtype=self.buf_dtype) * val
            channel.put_data(buffer, buffer_t)


class AIChannel(pyGeneric.GenericDevice):
    def __init__(self, name: str):
        super().__init__(name)
        self.cfg = AIChannelConfig()
        self.device = None

    @property
    def buf_len(self):
        return self.device.buf_len

    @property
    def sampling_period_ms(self):
        return self.device.cfg.sampling_period_ms

    @property
    def samples_per_read(self):
        return self.device.samples_per_read

    def write_config(self):
        PerfusionConfig.write_from_dataclass(self.device.name, self.name, self.cfg)

    def read_config(self, channel_name: str = None):
        if channel_name is None:
            channel_name = self.name
        PerfusionConfig.read_into_dataclass(self.device.name, channel_name, self.cfg)

    def put_data(self, buf, t):
        data = self._calibrate(buf)
        self._queue.put((data, t))

    def clear(self):
        with self._queue.mutex:
            self._queue.queue.clear()

    def _calibrate(self, buffer):
        if self.cfg.cal_pt2_reading - self.cfg.cal_pt1_reading == 0:
            data = buffer.astype(self.data_dtype)
        else:
            data = np.zeros(len(buffer), dtype=self.data_dtype)
            for i in range(len(buffer)):
                data[i] = ((((buffer[i] - self.cfg.cal_pt1_reading)
                           * (self.cfg.cal_pt2_target - self.cfg.cal_pt1_target))
                           / (self.cfg.cal_pt2_reading - self.cfg.cal_pt1_reading))
                           + self.cfg.cal_pt1_target)
        return data
