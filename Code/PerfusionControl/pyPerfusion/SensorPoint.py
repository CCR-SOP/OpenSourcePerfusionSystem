import logging
from time import perf_counter, sleep
import struct
from os import SEEK_END, SEEK_CUR
from collections import deque

import numpy as np

from pyPerfusion.SensorStream import SensorStream

DATA_VERSION = 2


class SensorPoint(SensorStream):
    def __init__(self, name, unit_str, hw):
        self._logger = logging.getLogger(__name__)
        super().__init__(name, unit_str, hw)
        self._samples_per_ts = hw.samples_per_read
        self._bytes_per_ts = 4

    def _get_stream_info(self):
        stamp_str = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        header = [f'File Format: {DATA_VERSION}',
                  f'Sensor: {self.name}',
                  f'Unit: {self._unit_str}',
                  f'Data Format: {str(np.dtype(self.hw.data_type))}',
                  f'Samples Per Timestamp: {self._samples_per_ts}',
                  f'Bytes Per Timestamp: {self._bytes_per_ts}',
                  f'Sampling Period (ms): {self.hw.period_sampling_ms}',
                  f'Start of Acquisition: {stamp_str}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

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
        cur_time = int(perf_counter() * 1000)
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
        return data_time, data

    def get_last_data(self):
        _fid, tmp = self._open_read()
        dtype_size = self.hw.data_type(1).itemsize
        bytes_per_chunk = self._bytes_per_ts + (self._samples_per_ts * dtype_size)
        _fid.seek(-bytes_per_chunk, SEEK_END)
        chunk, ts = self.__read_chunk(_fid)
        self._logger.debug(f'ts is {ts}, chunk={chunk}')
        _fid.close()
        return ts, chunk

    def get_data_from_last_read(self, timestamp):
        _fid, tmp = self._open_read()
        dtype_size = self.hw.data_type(1).itemsize
        bytes_per_chunk = self._bytes_per_ts + (self._samples_per_ts * dtype_size)
        ts = timestamp + 1
        data = deque()
        data_t = deque()
        _fid.seek(0, SEEK_END)
        loops = 0
        while ts > timestamp:
            loops += 1
            offset = bytes_per_chunk * loops
            try:
                _fid.seek(-offset, SEEK_END)
            except OSError:
                # attempt to read before beginning of file
                break
            else:
                chunk, ts = self.__read_chunk(_fid)
                if ts and ts > timestamp:
                    data_t.extendleft([ts])
                    data.extendleft(chunk)
        _fid.close()
        return data_t, data
