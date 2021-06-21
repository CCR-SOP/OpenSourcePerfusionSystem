from pyPerfusion.SensorStream import SensorStream
import numpy as np
from os import SEEK_SET
from time import perf_counter
import struct

DATA_VERSION = 2


class DexcomPoint(SensorStream):
    def __init__(self, name, unit_str, hw, valid_range):
        super().__init__(name, unit_str, hw, valid_range)
        self._samples_per_ts = 1
        self._bytes_per_ts = 4
        self._time = None

    def _get_stream_info(self):
        stamp_str = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        header = [f'File Format: {DATA_VERSION}',
                  f'Sensor: {self.name}',
                  f'Unit: {self._unit_str}',
                  f'Data Format: {str(np.dtype(self.hw.data_type))}',
                  f'Samples Per Timestamp: {self._samples_per_ts}',
                  f'Sampling Period (ms): {self.hw.period_sampling_ms}',
                  f'Start of Acquisition: {stamp_str}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def run(self):
        while not self._SensorStream__evt_halt.wait(self.hw.period_sampling_ms / 1000.0):
            t = perf_counter()
            data_buf, self._time = self.hw.get_data()
            if data_buf is not None and self._fid_write is not None:
                buf_len = len(data_buf)
                self._write_to_file(data_buf, t)
                self._last_idx += buf_len
                self._fid_write.flush()

    def _write_to_file(self, data_buf, t):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid_write.write(ts_bytes)
        data_buf.tofile(self._fid_write)

    def __read_chunk(self, _fid):
        ts = 0
        data_buf = []
        ts_bytes = _fid.read(self._bytes_per_ts)
        if len(ts_bytes) == 4:
            ts, = struct.unpack('i', ts_bytes)
            data_buf = np.fromfile(_fid, dtype=self.hw.data_type, count=self._samples_per_ts)
        return data_buf, ts

    def get_data(self, last_ms, samples_needed):
        _fid, tmp = self._open_read()
        cur_time = int(perf_counter() * 1000.0)
        _fid.seek(0)
        chunk = [1]
        data_time = []
        data = []
        while chunk:
            chunk, ts = self.__read_chunk(_fid)
            if chunk and (cur_time - ts < last_ms or last_ms == 0):
                data.append(chunk)
                data_time.append(ts / 1000.0)
        _fid.close()
        if data and data[-1] == 5000:
            self.stop()
            print('stopped')
        return self._time, data
