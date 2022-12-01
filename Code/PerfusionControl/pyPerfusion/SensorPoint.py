import logging
import time

import numpy as np

from pyPerfusion.SensorStream import SensorStream


class SensorPoint(SensorStream):
    def __init__(self, hw, unit_str):
        self._lgr = logging.getLogger(__name__)
        super().__init__(hw, unit_str)
        self._samples_per_ts = hw.samples_per_read
        self._bytes_per_ts = np.dtype(self.hw.data_type).itemsize
        self._params = {'Sensor': self.hw.cfg.name,
                        'Unit': self._unit_str,
                        'Data Format': np.dtype(self.hw.data_type).name,
                        'Sampling Period (ms)': self.hw.cfg.sampling_period_ms,
                        'Samples Per Timestamp': self._samples_per_ts,
                        'Bytes Per Timestamp': self._bytes_per_ts,
                        'Start of Acquisition': 0
                        }

    def run(self):
        while not self._evt_halt.is_set():
            data_buf, t = self.hw.get_data()
            if data_buf is not None:
                buf = data_buf
                for strategy in self._strategies:
                    buf = strategy.process_buffer(buf, t)
            else:
                # need a delay otherwise this loop eats up a lot of
                # CPU checking data. What is a good delay?
                time.sleep(0.1)

class ReadOnlySensorPoint(SensorPoint):
    def run(self):
        pass

