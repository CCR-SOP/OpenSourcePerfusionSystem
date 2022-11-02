import logging

import numpy as np

from pyPerfusion.SensorStream import SensorStream


class SensorPoint(SensorStream):
    def __init__(self, name, unit_str, hw):
        self._logger = logging.getLogger(__name__)
        super().__init__(name, unit_str, hw)
        self._samples_per_ts = hw.samples_per_read
        self._bytes_per_ts = 4
        self._params = {'Sensor': self.name,
                        'Unit': self._unit_str,
                        'Data Format': str(np.dtype(self.hw.data_type)),
                        'Sampling Period (ms)': self.hw.period_sampling_ms,
                        'Samples Per Timestamp': self._samples_per_ts,
                        'Bytes Per Timestamp': self._bytes_per_ts,
                        'Start of Acquisition': 0
                        }

    def run(self):
        while not self._evt_halt.is_set():
            data_buf, t = self.hw.get_data(self._ch_id)
            if data_buf is not None:
                buf = data_buf
                for strategy in self._strategies:
                    buf = strategy.process_buffer(buf, t)


class ReadOnlySensorPoint(SensorPoint):
    def run(self):
        pass
