import logging
from dataclasses import dataclass
import warnings

import numpy as np

from pyPerfusion.FileStrategy import StreamToFile
import pyPerfusion.PerfusionConfig as PerfusionConfig
from pyPerfusion.SensorStream import SensorStream


@dataclass
class FlowOverPressureConfig:
    name: str = ''


class FlowOverPressure:
    def __init__(self, name: str, flow: StreamToFile, pressure: StreamToFile):
        self._lgr = logging.getLogger(__name__)
        self.cfg = FlowOverPressureConfig(name=name)
        self._window_len = 100
        self.buf_len = self._window_len
        self.data_type = np.float64
        self.sampling_period_ms = 100
        self.name = name
        self._flow = flow
        self._pressure = pressure

    def get_data(self):
        flow_t, flow = self._flow.retrieve_buffer(0, self._window_len)
        pressure_t, pressure = self._pressure.retrieve_buffer(0, self._window_len)
        if flow is not None and pressure is not None:
            f_over_p = np.float64(flow) / np.float64(pressure)
            t = np.float64(flow_t)
        else:
            f_over_p = None
            t = None

        return f_over_p, t


class VolumeByFlow:
    def __init__(self, name: str, flow: SensorStream):
        self._lgr = logging.getLogger(__name__)
        self.cfg = FlowOverPressureConfig(name=name)
        self._window_len = 5
        self.buf_len = self._window_len
        self.data_type = np.float64
        self.sampling_period_ms = flow.hw.sampling_period_ms
        self.name = name
        self._flow = flow.get_file_strategy('Stream2File')
        self.last_volume = 0.0
        self.flow_offset = 0.0

    def calibrate_offset(self, total_samples):
        flow_t, flow = self._flow.retrieve_buffer(0, total_samples)
        self.flow_offset = np.mean(flow)
        # self._lgr.debug(f'flow is {flow[-1:-10]}')

    def get_data(self):
        flow_t, flow = self._flow.retrieve_buffer(0, self._window_len)
        if flow is not None and len(flow) > 0:
            # self._lgr.debug(f' flow is {flow}, flow_offset is {self.flow_offset}')
            flow = flow - self.flow_offset
            # self._lgr.debug(f'mean is {np.mean(flow)}, flow is {flow}')
            volume = np.cumsum(flow, dtype=np.float64) + self.last_volume
            self.last_volume = volume[-1]
            t = np.float64(flow_t)
        else:
            volume = None
            t = None

        return volume, t
