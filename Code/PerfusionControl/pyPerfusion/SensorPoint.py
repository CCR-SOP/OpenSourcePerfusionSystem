from pyPerfusion.SensorStream import SensorStream
import numpy as np
from os import SEEK_SET
from time import perf_counter
import struct

DATA_VERSION = 2


class SensorPoint(SensorStream):
    def __init__(self, name, unit_str, hw):
        super().__init__(name, unit_str, hw)
        self._samples_per_ts = 1
        self._bytes_per_ts = 4

    def _get_stream_info(self):
        stamp_str = self._timestamp.strftime('%Y-%m-%d_%H:%M')
        header = [f'File Format: {DATA_VERSION}',
                  f'Sensor: {self._name}',
                  f'Unit: {self._unit_str}',
                  f'Data Format: {str(np.dtype(self._hw.data_type))}',
                  f'Samples Per Timestamp: {self._samples_per_ts}',
                  f'Bytes Per Timestamp: {self._bytes_per_ts}',
                  f'Sampling Period (ms): {self._hw.period_sampling_ms}',
                  f'Start of Acquisition: {stamp_str}'
                  ]
        end_of_line = '\n'
        hdr_str = f'{end_of_line.join(header)}{end_of_line}'
        return hdr_str

    def _write_to_file(self, data_buf, t):
        ts_bytes = struct.pack('i', int(t * 1000.0))
        self._fid_write.write(ts_bytes)
        data_buf.tofile(self._fid_write)

    def __read_chunk(self):
        ts = 0
        data_buf = []
        ts_bytes = self._fid_read.read(self._bytes_per_ts)
        if len(ts_bytes) == 4:
            ts, = struct.unpack('i', ts_bytes)
            data_buf = np.fromfile(self._fid_read, dtype=self._hw.data_type, count=self._samples_per_ts)
        return data_buf, ts

    def get_data(self, last_ms, samples_needed):
        self._open_read()
        cur_time = int(perf_counter() * 1000)
        self._fid_read.seek(0)
        chunk = [1]
        data_time = []
        data = []
        while chunk:
            chunk, ts = self.__read_chunk()
            if chunk and (cur_time - ts < last_ms or last_ms == 0):
                data.append(chunk)
                data_time.append(ts / 1000.0)
        self._fid_read.close()
        return data_time, data
