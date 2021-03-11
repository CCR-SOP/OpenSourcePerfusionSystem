import numpy as np
from pyPerfusion.SensorStream import SensorStream

DATA_VERSION = 1


class DexcomStream(SensorStream):
    def __init__(self, name, unit_str, hw, valid_range):
        super().__init__(name, unit_str, hw, valid_range)
        self._time = None

    def run(self):
        while not self._SensorStream__evt_halt.wait(self.hw.period_sampling_ms / 1000.0):
            data_buf, self._time = self.hw.get_data()
            if data_buf is not None and self._fid_write is not None:
                buf_len = len(data_buf)
                self._write_to_file(data_buf, self._time)
                self._last_idx += buf_len
                self._fid_write.flush()

    def get_data(self, last_ms, samples_needed):
        _fid, data = self._open_read()
        file_size = len(data)
        if last_ms > 0:
            data_size = int(last_ms / self.hw.period_sampling_ms)
            if samples_needed > data_size:
                samples_needed = data_size
            start_idx = file_size - data_size
            if start_idx < 0:
                start_idx = 0
        else:
            start_idx = 0
        idx = np.linspace(start_idx, file_size-1, samples_needed, dtype=np.int)
        data = data[idx]

        _fid.close()

        if data[-1] == 5000:  # Signifies end of run
            self.stop()

        return self._time, data
