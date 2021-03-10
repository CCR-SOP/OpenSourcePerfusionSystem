from pyPerfusion.SensorStream import SensorStream
import numpy as np

DATA_VERSION = 2


class DexcomStream(SensorStream):
    def __init__(self, name, unit_str, hw, valid_range):
        super().__init__(name, unit_str, hw, valid_range)
        self._time = None

    def run(self):  # Find to also write time data to file, and pair this with CGM data?
        while not self._SensorStream__evt_halt.wait(self.hw.period_sampling_ms / 1000.0):
            data_buf, self._time = self.hw.get_data()
            if data_buf is not None and self._fid_write is not None:
                buf_len = len(data_buf)
                self._write_to_file(data_buf, self._time)  # find a way to write times to a file too?
                self._last_idx += buf_len
                self._fid_write.flush()

    def get_data(self, last_ms, samples_needed):  # 5000, 200
        _fid, data = self._open_read()
        file_size = len(data)
        if last_ms > 0:
            data_size = int(last_ms / self.hw.period_sampling_ms)  # 5
            if samples_needed > data_size:
                samples_needed = data_size  # 5
            start_idx = file_size - data_size
            if start_idx < 0:
                start_idx = 0
        else:
            start_idx = 0
        idx = np.linspace(start_idx, file_size-1, samples_needed, dtype=np.int)
        data = data[idx]

        _fid.close()

        return self._time, data
