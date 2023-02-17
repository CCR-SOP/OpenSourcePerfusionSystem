import logging
from dataclasses import dataclass

import numpy as np

from pyPerfusion.FileStrategy import StreamToFile
import pyPerfusion.PerfusionConfig as PerfusionConfig

@dataclass
class FlowOverPressureConfig:
    name: str = ''


class FlowOverPressureStream:
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
        f_over_p = np.float64(flow) / np.float64(pressure)
        return f_over_p, np.float64(flow_t)
